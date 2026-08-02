#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/tests/test_package.py" --root "$ROOT"
python3 -m unittest discover -s "$ROOT/tests" -p 'test_chinese_lingo.py' -v

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
