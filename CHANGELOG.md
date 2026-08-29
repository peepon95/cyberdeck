# Changelog

## v0.2.0 — fresh-SD workshop installer

- Added a system service that starts the Cyberdeck menu automatically after boot.
- Restored Journal to the tracked source and made all save folders username-independent.
- Added a raw ADS7846 touchscreen response check before game installation.
- Added an optional Bluetooth keyboard reconnect installer without a personal MAC address.
- Prevented the menu's keyboard scanner from consuming touchscreen events.
- Forced Journal frames to refresh reliably on the tested fbtft display.
- Added automatic `/dev/fb0` or `/dev/fb1` detection across the menu and every app.
- Added a two-app installation test and expanded release validation.

## v0.1.0 — first workshop package

- Cleaned the original working folder into a workshop-safe package.
- Added manifest-based app discovery and selectable installation.
- Renamed Hanzi Quest to Chinese Lingo and Slash Ninja to Makan Ninja.
- Added app-level customization notes and a blank game template.
- Added package checks, download guidance and hardware documentation.
- Excluded backups, personal data, ebooks, caches and development-only media.
