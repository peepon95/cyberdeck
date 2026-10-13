# Windows Workshop Setup

This guide takes a participant from a blank microSD card to the Cyberdeck menu
and Ee's Wardrobe. Commands shown after the SSH step run on the Raspberry Pi,
even though they are typed into Windows PowerShell.

## Before the workshop

Each participant needs:

- a Windows 10 or Windows 11 laptop with Wi-Fi and a microSD reader;
- Raspberry Pi Imager installed from <https://www.raspberrypi.com/software/>;
- a Raspberry Pi Zero 2 W, 16 GB or larger microSD card, tested 3.5-inch screen,
  stylus, and stable 5 V / 2 A power supply;
- the workshop Wi-Fi name and password. The Pi Zero 2 W requires 2.4 GHz Wi-Fi.

The screen driver is hardware-specific. A facilitator should test the exact
screen model before the workshop and provide its matching driver instructions.
The Cyberdeck software supports a working 480x320 RGB565 framebuffer at
`/dev/fb0` or `/dev/fb1` and an XPT2046/ADS7846-compatible touch device.

## 1. Flash Raspberry Pi OS in Windows

1. Insert the microSD card into the Windows laptop.
2. Open **Raspberry Pi Imager**.
3. Choose **Raspberry Pi Zero 2 W** as the device.
4. Choose **Raspberry Pi OS (Legacy, 32-bit) Lite** as the operating system.
5. Choose the microSD card as storage.
6. Open the customisation settings before writing and set:
   - hostname: `cyberdeck3` (give each group a different number);
   - username: `ee2` (or record the username you choose);
   - a password the participant can type during the workshop;
   - the workshop Wi-Fi name, password and country;
   - the correct timezone;
   - **Enable SSH** with password authentication.
7. Write the card, wait for verification to finish, then eject it safely.

Never publish workshop Wi-Fi passwords or participant passwords in GitHub.

## 2. Start the Raspberry Pi

1. With power disconnected, insert the microSD card into the Pi.
2. Fit the screen carefully onto the GPIO header.
3. Connect power and wait three to five minutes for the first boot.
4. Keep the Windows laptop on the same Wi-Fi network as the Pi.

## 3. Connect from Windows PowerShell

Open **PowerShell** from the Start menu and run:

```powershell
ssh ee2@cyberdeck3.local
```

Replace `ee2` and `cyberdeck3` if different values were chosen in Imager. Type
`yes` the first time Windows asks about the host key. The password will not
display while typing; press Enter when finished.

If `.local` does not resolve, find the Pi's IP address in the Wi-Fi router or
phone hotspot's connected-device list, then use it directly:

```powershell
ssh ee2@192.168.1.50
```

When the prompt looks similar to `ee2@cyberdeck3:~ $`, SSH is working.

## 4. Prepare the display and verify touch

Follow the facilitator's tested instructions for the exact 3.5-inch screen,
then reboot and reconnect with SSH. Confirm that Linux created a framebuffer:

```bash
ls -l /dev/fb0 /dev/fb1 2>/dev/null
```

At least one framebuffer should appear. The game installer cannot repair a
missing screen driver.

## 5. Download the complete workshop package

Run these commands in the SSH window:

```bash
sudo apt update
sudo apt install -y curl unzip
mkdir -p ~/cyberdeck-download
cd ~/cyberdeck-download
curl -fL -o cyberdeck-workshop.zip https://github.com/peepon95/cyberdeck/releases/latest/download/cyberdeck-workshop.zip
curl -fL -o SHA256SUMS https://github.com/peepon95/cyberdeck/releases/latest/download/SHA256SUMS
sha256sum -c SHA256SUMS
```

Continue when the final command reports `cyberdeck-workshop.zip: OK`.

## 6. Extract and test

```bash
unzip -o cyberdeck-workshop.zip
cd cyberdeck-workshop
./scripts/check.sh
sudo ./scripts/check-touch.sh
```

Tap and drag with the stylus during the ten-second touch test. Continue only
when it reports `[OK] Touchscreen responded`.

## 7. Install all games and start the menu

```bash
sudo ./install.sh --all
```

The installer validates all nine apps, keeps timestamped backups of an older
installation, starts the menu immediately, and enables it for later boots.

If the menu does not appear after several seconds, check it through SSH:

```bash
sudo systemctl restart cyberdeck-menu.service
sudo systemctl status cyberdeck-menu.service --no-pager
```

## 8. Reboot and open Ee's Wardrobe

```bash
sudo reboot
```

The SSH window will disconnect. Wait about one minute. The small screen should
show **CYBERDECK 2.0**. Tap **EE'S WARDROBE**, browse the starter tops and
bottoms, then tap **DRESS ME** to see the full pixel-art outfit.

## 9. Add personal clothing photos

1. Put the phone and Cyberdeck on the same Wi-Fi network.
2. Open Ee's Wardrobe and note the upload address at the bottom of the screen.
3. Open `http://cyberdeck3.local:8765` on the phone.
4. Choose **Tops** or **Bottoms**, select photos, and tap **Add to Closet**.
5. Return to the wardrobe carousel and use the arrows to browse the new items.

Photograph one garment at a time against a plain, contrasting background. The
photos stay on the Raspberry Pi in `~/cyberdeck-wardrobe`.

## 10. Shut down safely

Reconnect with SSH if necessary, then run:

```bash
sync
sudo shutdown -h now
```

Wait until disk activity has stopped before disconnecting power.

## Quick recovery commands

Check whether the Pi is reachable:

```powershell
ping cyberdeck3.local
ssh ee2@cyberdeck3.local
```

Restart the menu after connecting:

```bash
sudo systemctl restart cyberdeck-menu.service
```

Show the latest menu error:

```bash
sudo journalctl -u cyberdeck-menu.service -n 50 --no-pager
```

Update an already-installed Cyberdeck to the latest release by repeating Steps
5 through 8. The installer preserves the wardrobe photo folder.
