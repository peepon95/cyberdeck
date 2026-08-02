# Cyberdeck 2.0 Workshop

A beginner-friendly, offline game deck built with a Raspberry Pi, a 480×320
touchscreen and plain Python. Participants assemble the hardware, install a
tested collection of apps, then use the included examples and Codex to create
their own.

## Tested reference build

- Raspberry Pi Zero 2 W with a pre-soldered 40-pin header
- 3.5-inch 480×320 SPI/GPIO touchscreen using the `waveshare35c` overlay
- XPT2046/ADS7846-compatible resistive touch input and stylus
- 16 GB or larger microSD card
- Raspberry Pi OS Legacy (Bookworm), 32-bit Lite
- Stable 5 V / 2 A micro-USB power supply or power bank
- Wired USB keyboard and micro-USB OTG data adapter (recommended)
- Laptop with a microSD reader and 2.4 GHz Wi-Fi or hotspot

The Python game logic can be adapted to other Linux Raspberry Pi boards, but
the current package expects a 480×320 RGB565 framebuffer at `/dev/fb1` and a
Linux input device for touch. Other screens and Raspberry Pi models require
their display, input, power and boot settings to be tested.

## Included apps

- Chinese Lingo — guided simplified Chinese stroke practice
- Makan Ninja — slash Malaysian food and avoid bombs
- Tic-Tac-Toe
- Flappy Bird
- Minesweeper
- Paint
- E-Reader — bring your own legal `.txt` files
- Journal — entries stay on the participant's device

## Install on the Raspberry Pi

Keep the keyboard connected before starting. From an SSH terminal on the Pi:

```bash
git clone https://github.com/peepon95/cyberdeck.git
cd cyberdeck
sudo ./install.sh
```

Press Enter to install all apps, which is recommended for the first workshop.
To install a specific set without prompts:

```bash
sudo ./install.sh --apps chinese-lingo,makan-ninja,paint
```

The installer checks every selected app, moves an existing Cyberdeck 2.0
installation to a timestamped backup, backs up `/home/ee/menu.py`, and then
installs the new menu. It does not reboot automatically.

When the installer finishes:

```bash
sudo reboot
```

Always shut down safely before removing power:

```bash
sync
sudo shutdown -h now
```

Wait until screen and activity LEDs have stopped before unplugging power.

## Workshop approach

Everyone installs the same working foundation first. Each participant then
chooses one app to understand and customize. The `README.md` inside every app
suggests safe first changes, and `templates/blank-game` is the starting point
for an original app.

See:

- [Friend testing checklist](docs/FRIEND_TEST.md)
- [Hardware and compatibility](docs/HARDWARE.md)
- [Customizing with Codex](docs/CUSTOMIZE_WITH_CODEX.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## Development checks

On a laptop or Raspberry Pi:

```bash
./scripts/check.sh
```

These checks validate app manifests, compile all Python files and confirm the
Chinese Lingo asset bundle. Real touchscreen and framebuffer behaviour must
still be tested on the reference hardware.

Maintainers can create the website download asset with:

```bash
./scripts/build-release.sh
```

This produces `dist/cyberdeck-workshop.zip` and `dist/SHA256SUMS` for a GitHub
Release.

## Project status and licence

This is the first cleaned workshop package. The original workshop code is
available under the [MIT License](LICENSE), so participants can learn from,
modify and share it. Chinese Lingo includes separately licensed third-party
data; those terms and notices remain in `apps/chinese-lingo/licenses/`.

Releases labelled as test builds still need a fresh-card hardware test before
they should be used for a public workshop.
