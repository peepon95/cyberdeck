#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/tests/test_package.py" --root "$ROOT" --require-all-apps
python3 -m unittest discover -s "$ROOT/tests" -p 'test_*.py' -v
bash -n "$ROOT/install.sh" "$ROOT/scripts/"*.sh
"$ROOT/tests/test_install.sh"

echo
echo "Hardware check (missing devices are expected on a laptop):"
FRAMEBUFFER="${CYBERDECK_FB:-}"
if [[ -z "$FRAMEBUFFER" ]]; then
  for candidate in /dev/fb1 /dev/fb0; do
    if [[ -e "$candidate" ]]; then
      FRAMEBUFFER="$candidate"
      break
    fi
  done
fi
if [[ -n "$FRAMEBUFFER" && -e "$FRAMEBUFFER" ]]; then
  echo "  [OK] framebuffer $FRAMEBUFFER"
else
  echo "  [--] no framebuffer found at /dev/fb1 or /dev/fb0"
fi

if compgen -G '/dev/input/event*' >/dev/null; then
  echo "  [OK] Linux input devices found"
else
  echo "  [--] no Linux input devices found"
fi

echo
echo "On the assembled Pi, verify real stylus input before installing games:"
echo "  sudo ./scripts/check-touch.sh"
