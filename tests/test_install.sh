#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/cyberdeck-install-test.XXXXXX")"
trap 'rm -rf "$TEST_ROOT"' EXIT
mkdir -p "$TEST_ROOT/home"

CYBERDECK_TARGET_HOME="$TEST_ROOT/home" \
CYBERDECK_INSTALL_ROOT="$TEST_ROOT/home/cyberdeck" \
CYBERDECK_MENU_TARGET="$TEST_ROOT/home/menu.py" \
CYBERDECK_SKIP_SYSTEMD=1 \
  "$ROOT/install.sh" --apps chinese-lingo,paint

test -f "$TEST_ROOT/home/menu.py"
test -f "$TEST_ROOT/home/cyberdeck/apps/chinese-lingo/app.py"
test -f "$TEST_ROOT/home/cyberdeck/apps/paint/app.py"
test ! -e "$TEST_ROOT/home/cyberdeck/apps/flappy-bird"

echo "Installer test passed for a two-app selection."
