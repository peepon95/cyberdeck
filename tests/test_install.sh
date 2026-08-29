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

grep -Fxq 'After=local-fs.target getty@tty1.service' "$ROOT/scripts/cyberdeck-menu.service.in"
grep -Fxq 'Conflicts=getty@tty1.service' "$ROOT/scripts/cyberdeck-menu.service.in"
if grep -Fxq 'After=multi-user.target' "$ROOT/scripts/cyberdeck-menu.service.in"; then
  echo "Menu service must not create a multi-user.target ordering cycle." >&2
  exit 1
fi
grep -Fq 'systemctl restart cyberdeck-menu.service' "$ROOT/install.sh"

echo "Installer test passed for app selection and boot-safe menu startup."
