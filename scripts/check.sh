#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/tests/test_package.py" --root "$ROOT" --require-all-apps
python3 -m unittest discover -s "$ROOT/tests" -p 'test_chinese_lingo.py' -v
bash -n "$ROOT/install.sh" "$ROOT/scripts/"*.sh
"$ROOT/tests/test_install.sh"

echo
echo "Hardware check (missing devices are expected on a laptop):"
if [[ -e "${CYBERDECK_FB:-/dev/fb1}" ]]; then
  echo "  [OK] framebuffer ${CYBERDECK_FB:-/dev/fb1}"
else
  echo "  [--] framebuffer /dev/fb1 not found"
fi

if compgen -G '/dev/input/event*' >/dev/null; then
  echo "  [OK] Linux input devices found"
else
  echo "  [--] no Linux input devices found"
fi

echo
echo "On the assembled Pi, verify real stylus input before installing games:"
echo "  sudo ./scripts/check-touch.sh"
