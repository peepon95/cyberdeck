# Cyberdeck 2.0 — Workshop Download

## v0.2.1 startup fix

The menu now takes ownership of the small display during boot instead of racing
the Raspberry Pi `tty1` login prompt. Installation starts the menu immediately,
and later power-ons return directly to Cyberdeck 2.0 while SSH remains available.

This Cyberdeck 2.0 package can be installed on a freshly flashed workshop card.

## Which file should I download?

Download **`cyberdeck-workshop.zip`**. It contains the prepared installer,
eight apps, templates, documentation and the package checks used by the
workshop guide.

`SHA256SUMS` is optional. It lets you confirm that the ZIP downloaded without
corruption. GitHub also creates **Source code (zip)** and **Source code
(tar.gz)** automatically; participants should ignore those and use the named
workshop ZIP above.

## Package checks

- Eight app manifests and Python entry points
- Full and selective installation flows
- Automatic menu startup after reboot
- Small-screen login prompt cannot overwrite the Cyberdeck menu
- Ten-second raw touchscreen and GPIO interrupt test
- Optional per-keyboard Bluetooth reconnect installer
- Timestamped recovery backup flow
- Dynamic menu discovery
- Automatic `/dev/fb0` or `/dev/fb1` display detection
- Portable save folders for any Raspberry Pi username
- Journal framebuffer refresh fix
- Chinese Lingo asset, progress and stroke-grading tests
- Release archive contents and SHA-256 checksum

Start with the step-by-step instructions in the repository README.
