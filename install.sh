#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_USER="${CYBERDECK_USER:-${SUDO_USER:-$(id -un)}}"
TARGET_HOME="${CYBERDECK_TARGET_HOME:-$(python3 - "$TARGET_USER" <<'PY'
import pwd, sys
try:
    print(pwd.getpwnam(sys.argv[1]).pw_dir)
except KeyError:
    pass
PY
)}"
if [[ -z "$TARGET_HOME" ]]; then
  TARGET_HOME="$(eval echo "~$TARGET_USER")"
fi
if [[ ! "$TARGET_USER" =~ ^[a-z_][a-z0-9_-]*[$]?$ ]]; then
  echo "Unsupported target username: $TARGET_USER" >&2
  exit 2
fi
INSTALL_ROOT="${CYBERDECK_INSTALL_ROOT:-$TARGET_HOME/cyberdeck}"
MENU_TARGET="${CYBERDECK_MENU_TARGET:-$TARGET_HOME/menu.py}"
STAMP="$(date +%Y%m%d-%H%M%S)"

usage() {
  cat <<'EOF'
Usage:
  sudo ./install.sh                 Choose apps interactively
  sudo ./install.sh --all           Install every workshop app
  sudo ./install.sh --apps ID,ID    Install selected app IDs
  ./install.sh --list               Show available app IDs
EOF
}

APP_IDS=()
while IFS= read -r id; do
  APP_IDS+=("$id")
done < <(find "$PACKAGE_DIR/apps" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)

app_name() {
  python3 - "$PACKAGE_DIR/apps/$1/app.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    print(json.load(handle)["name"])
PY
}

list_apps() {
  local index=1 id
  for id in "${APP_IDS[@]}"; do
    printf '  %d. %-18s %s\n' "$index" "$id" "$(app_name "$id")"
    index=$((index + 1))
  done
}

MODE="interactive"
REQUESTED=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) MODE="all"; shift ;;
    --apps) MODE="selected"; REQUESTED="${2:-}"; shift 2 ;;
    --list) list_apps; exit 0 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

SELECTED_IDS=()
if [[ "$MODE" == "interactive" ]]; then
  echo "Cyberdeck 2.0 workshop installer"
  echo
  list_apps
  echo "  A. Install everything (recommended for the workshop)"
  echo
  read -r -p "Choose numbers separated by commas, or press Enter for all: " REQUESTED
  REQUESTED_LOWER="$(printf '%s' "$REQUESTED" | tr '[:upper:]' '[:lower:]')"
  if [[ -z "$REQUESTED" || "$REQUESTED_LOWER" == "a" || "$REQUESTED_LOWER" == "all" ]]; then
    MODE="all"
  else
    IFS=',' read -ra CHOICES <<< "$REQUESTED"
    for choice in "${CHOICES[@]}"; do
      choice="${choice//[[:space:]]/}"
      if [[ ! "$choice" =~ ^[0-9]+$ ]] || (( choice < 1 || choice > ${#APP_IDS[@]} )); then
        echo "Invalid selection: $choice" >&2
        exit 2
      fi
      SELECTED_IDS+=("${APP_IDS[choice-1]}")
    done
  fi
fi

if [[ "$MODE" == "all" ]]; then
  SELECTED_IDS=("${APP_IDS[@]}")
elif [[ "$MODE" == "selected" ]]; then
  IFS=',' read -ra SELECTED_IDS <<< "$REQUESTED"
fi

if (( ${#SELECTED_IDS[@]} == 0 )); then
  echo "No apps selected." >&2
  exit 2
fi

for id in "${SELECTED_IDS[@]}"; do
  if [[ ! "$id" =~ ^[a-z0-9-]+$ || ! -f "$PACKAGE_DIR/apps/$id/app.json" ]]; then
    echo "Unknown app ID: $id" >&2
    exit 2
  fi
done

if (( EUID != 0 )) && { [[ -e "$MENU_TARGET" && ! -w "$MENU_TARGET" ]] || [[ ! -w "$(dirname "$MENU_TARGET")" ]]; }; then
  echo "Installation needs permission to update $MENU_TARGET." >&2
  echo "Run: sudo ./install.sh" >&2
  exit 1
fi

STAGE="$(mktemp -d "${TMPDIR:-/tmp}/cyberdeck-install.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/cyberdeck/apps" "$STAGE/cyberdeck/core"
cp -a "$PACKAGE_DIR/core/." "$STAGE/cyberdeck/core/"

for id in "${SELECTED_IDS[@]}"; do
  cp -a "$PACKAGE_DIR/apps/$id" "$STAGE/cyberdeck/apps/$id"
done

echo "Checking selected apps..."
python3 "$PACKAGE_DIR/tests/test_package.py" --root "$STAGE/cyberdeck"

if [[ -e "$INSTALL_ROOT" ]]; then
  BACKUP_ROOT="$TARGET_HOME/cyberdeck-before-$STAMP"
  echo "Moving the previous install to $BACKUP_ROOT"
  mv "$INSTALL_ROOT" "$BACKUP_ROOT"
fi
mkdir -p "$(dirname "$INSTALL_ROOT")"
cp -a "$STAGE/cyberdeck" "$INSTALL_ROOT"

if [[ -e "$MENU_TARGET" ]]; then
  cp -p "$MENU_TARGET" "$TARGET_HOME/menu-before-cyberdeck-2-$STAMP.py"
fi
cp -p "$INSTALL_ROOT/core/menu.py" "$MENU_TARGET"
mkdir -p "$TARGET_HOME/books" "$TARGET_HOME/journal"

if (( EUID == 0 )); then
  TARGET_GROUP="$(id -gn "$TARGET_USER")"
  chown -R "$TARGET_USER:$TARGET_GROUP" "$INSTALL_ROOT" "$TARGET_HOME/books" "$TARGET_HOME/journal"
  chown "$TARGET_USER:$TARGET_GROUP" "$MENU_TARGET"

  if [[ "${CYBERDECK_SKIP_SYSTEMD:-0}" != "1" ]]; then
    SERVICE_STAGE="$STAGE/cyberdeck-menu.service"
    sed \
      -e "s|@TARGET_USER@|$TARGET_USER|g" \
      -e "s|@TARGET_HOME@|$TARGET_HOME|g" \
      -e "s|@MENU_TARGET@|$MENU_TARGET|g" \
      "$PACKAGE_DIR/scripts/cyberdeck-menu.service.in" > "$SERVICE_STAGE"
    install -o root -g root -m 644 "$SERVICE_STAGE" /etc/systemd/system/cyberdeck-menu.service
    systemctl daemon-reload
    systemctl enable cyberdeck-menu.service
  fi
else
  echo "Run the installer with sudo to enable automatic menu startup." >&2
fi

sync
echo
echo "Cyberdeck 2.0 installed for $TARGET_USER with ${#SELECTED_IDS[@]} app(s)."
echo "The menu will start automatically after reboot: sudo reboot"
