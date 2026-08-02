#!/usr/bin/env python3
"""Fast checks that run on a laptop and on the Raspberry Pi."""

import argparse
import importlib.util
import json
import py_compile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    apps_dir = root / "apps"
    manifests = sorted(apps_dir.glob("*/app.json"))
    if not manifests:
        raise SystemExit("No app manifests found")

    seen = set()
    for manifest_path in manifests:
        with manifest_path.open(encoding="utf-8") as handle:
            manifest = json.load(handle)
        required = {"id", "name", "entry", "color", "order", "enabled"}
        missing = required.difference(manifest)
        assert not missing, f"{manifest_path}: missing {sorted(missing)}"
        assert manifest["id"] == manifest_path.parent.name
        assert manifest["id"] not in seen
        seen.add(manifest["id"])
        entry = manifest_path.parent / manifest["entry"]
        assert entry.is_file(), f"Missing entry: {entry}"
        py_compile.compile(str(entry), doraise=True)

    menu = root / "core" / "menu.py"
    assert menu.is_file(), "Missing core/menu.py"
    py_compile.compile(str(menu), doraise=True)
    spec = importlib.util.spec_from_file_location("cyberdeck_menu", menu)
    menu_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(menu_module)
    assert len(menu_module.MENU) == len(manifests), "Menu did not discover every app"

    chinese_assets = apps_dir / "chinese-lingo" / "hanzi_assets.json"
    if chinese_assets.exists():
        with chinese_assets.open(encoding="utf-8") as handle:
            data = json.load(handle)
        assert len(data["characters"]) == 20
        for license_name in ("COPYING", "LGPL.txt", "APL-English.txt"):
            assert (apps_dir / "chinese-lingo" / "licenses" / license_name).is_file()

    print(f"Package checks passed for {len(manifests)} app(s).")


if __name__ == "__main__":
    main()
