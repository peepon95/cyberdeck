#!/bin/sh
set -eu

MAC="${CYBERDECK_KEYBOARD_MAC:?Keyboard MAC address is not configured}"

while :; do
    if /usr/bin/bluetoothctl show 2>/dev/null | /usr/bin/grep -q 'Powered: yes'; then
        if ! /usr/bin/bluetoothctl info "$MAC" 2>/dev/null | /usr/bin/grep -q 'Connected: yes'; then
            /usr/bin/timeout 12 /usr/bin/bluetoothctl connect "$MAC" >/dev/null 2>&1 || true
        fi
    fi
    /usr/bin/sleep 15
done
