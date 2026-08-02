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

## Install Cyberdeck 2.0 yourself

These steps begin after Raspberry Pi OS, SSH and the 3.5-inch display are
working. The tested account name is `ee`. Connect the wired keyboard before
starting, then open an SSH terminal on the Pi.

### 1. Install the download tools

```bash
sudo apt update
sudo apt install -y curl unzip
```

### 2. Download the latest release

```bash
cd ~
mkdir -p cyberdeck-download
cd cyberdeck-download
curl -L -o cyberdeck-workshop.zip https://github.com/peepon95/cyberdeck/releases/latest/download/cyberdeck-workshop.zip
curl -L -o SHA256SUMS https://github.com/peepon95/cyberdeck/releases/latest/download/SHA256SUMS
```

### 3. Verify the download

```bash
sha256sum -c SHA256SUMS
```

Continue only when the result says `cyberdeck-workshop.zip: OK`.

### 4. Extract and check the package

```bash
unzip cyberdeck-workshop.zip
cd cyberdeck-workshop
./scripts/check.sh
```

The software checks should pass. The laptop-style hardware report may say that
`/dev/fb1` or Linux input devices are missing if the display driver has not been
finished yet; fix the hardware checkpoint before launching the menu.

### 5. Install the complete deck

```bash
sudo ./install.sh --all
```

The installer validates all eight apps, backs up an existing `/home/ee/menu.py`
and moves any previous Cyberdeck 2.0 installation into a timestamped recovery
folder. It does not reboot automatically.

To install only selected apps instead, list them first and then provide their
IDs:

```bash
./install.sh --list
sudo ./install.sh --apps chinese-lingo,makan-ninja,paint
```

### 6. Reboot and test

```bash
sudo reboot
```

After the Pi restarts, confirm that:

- The screen shows `CYBERDECK 2.0`.
- Touch can select and launch an app.
- Keyboard arrows and Enter move through the menu.
- Chinese Lingo and Makan Ninja both respond to the stylus.

### 7. Shut down safely

```bash
sync
sudo shutdown -h now
```

Wait until the display and activity light have stopped before removing power.

### Install from the source repository instead

People who want to read or modify the current source can use Git:

```bash
sudo apt install -y git
git clone https://github.com/peepon95/cyberdeck.git
cd cyberdeck
./scripts/check.sh
sudo ./install.sh --all
```

For a workshop, use the release ZIP because it points to a fixed, packaged
version. Use the Git clone when developing and customizing the code.

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
