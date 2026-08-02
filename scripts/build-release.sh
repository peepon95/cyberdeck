#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT/dist"
ARCHIVE="$OUT_DIR/cyberdeck-workshop.zip"
RELEASE_STAGE="$(mktemp -d "${TMPDIR:-/tmp}/cyberdeck-release.XXXXXX")"
trap 'rm -rf "$RELEASE_STAGE"' EXIT

mkdir -p "$RELEASE_STAGE/cyberdeck-workshop" "$OUT_DIR"
for path in apps core docs scripts templates tests .github .gitignore CHANGELOG.md README.md THIRD_PARTY_NOTICES.md install.sh; do
  cp -R "$ROOT/$path" "$RELEASE_STAGE/cyberdeck-workshop/"
done
find "$RELEASE_STAGE" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$RELEASE_STAGE" -type f -name '*.pyc' -delete

(cd "$RELEASE_STAGE" && zip -qr "$ARCHIVE" cyberdeck-workshop)

if command -v sha256sum >/dev/null 2>&1; then
  (cd "$OUT_DIR" && sha256sum "$(basename "$ARCHIVE")" > SHA256SUMS)
else
  (cd "$OUT_DIR" && shasum -a 256 "$(basename "$ARCHIVE")" > SHA256SUMS)
fi

echo "Created $ARCHIVE"
echo "Created $OUT_DIR/SHA256SUMS"
