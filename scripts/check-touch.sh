#!/usr/bin/env bash
set -euo pipefail

if (( EUID != 0 )); then
  echo "Run this check with sudo: sudo ./scripts/check-touch.sh" >&2
  exit 2
fi

EVENT_NAME="$(awk '
  /^N: Name="ADS7846 Touchscreen"/ { touch=1; next }
  touch && /^H: Handlers=/ {
    for (i=1; i<=NF; i++) {
      if ($i ~ /^event[0-9]+$/) { print $i; exit }
    }
  }
  touch && /^$/ { touch=0 }
' /proc/bus/input/devices)"

if [[ -z "$EVENT_NAME" || ! -e "/dev/input/$EVENT_NAME" ]]; then
  echo "[FAIL] ADS7846 touchscreen input device was not found."
  echo "Finish the linked screen-driver step, reboot, and run this check again."
  exit 1
fi

irq_total() {
  awk '/ads7846/ {
    total=0
    for (i=2; i<=NF; i++) if ($i ~ /^[0-9]+$/) total += $i
    print total
    exit
  }' /proc/interrupts
}

CAPTURE="$(mktemp "${TMPDIR:-/tmp}/cyberdeck-touch.XXXXXX")"
trap 'rm -f "$CAPTURE"' EXIT
BEFORE="$(irq_total)"
BEFORE="${BEFORE:-0}"

echo "Touch test: press, tap and drag the stylus for the next 10 seconds."
timeout 10 dd if="/dev/input/$EVENT_NAME" of="$CAPTURE" bs=24 status=none || true

BYTES="$(wc -c < "$CAPTURE" | tr -d '[:space:]')"
AFTER="$(irq_total)"
AFTER="${AFTER:-0}"

if (( BYTES > 0 || AFTER > BEFORE )); then
  echo "[OK] Touchscreen responded ($BYTES input bytes; $((AFTER - BEFORE)) new interrupt(s))."
  exit 0
fi

echo "[FAIL] The driver exists, but the screen produced no touch signal."
echo "Power down before reseating the GPIO screen. Check physical pin 11 / GPIO17."
exit 1
