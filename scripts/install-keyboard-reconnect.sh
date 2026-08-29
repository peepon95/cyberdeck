#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAC="${1:-}"

if [[ ! "$MAC" =~ ^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$ ]]; then
  echo "Usage: sudo ./scripts/install-keyboard-reconnect.sh AA:BB:CC:DD:EE:FF" >&2
  exit 2
fi
if (( EUID != 0 )); then
  echo "Run this installer with sudo." >&2
  exit 2
fi

MAC="${MAC^^}"
bluetoothctl trust "$MAC"
install -o root -g root -m 755 "$ROOT/scripts/keyboard-reconnect.sh" /usr/local/sbin/cyberdeck-keyboard-reconnect
install -o root -g root -m 644 "$ROOT/scripts/cyberdeck-keyboard-reconnect.service" /etc/systemd/system/cyberdeck-keyboard-reconnect.service
printf 'CYBERDECK_KEYBOARD_MAC=%s\n' "$MAC" > /etc/default/cyberdeck-keyboard
systemctl daemon-reload
systemctl enable --now cyberdeck-keyboard-reconnect.service
echo "Automatic reconnect enabled for $MAC."
