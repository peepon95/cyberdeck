# Friend Testing Checklist

Test with a spare or newly flashed microSD card. Do not replace the working
Cyberdeck installation during the first independent test.

## Before starting

- [ ] Use the tested Pi Zero 2 W with header and 3.5-inch 480×320 screen.
- [ ] Have a stylus, wired USB keyboard and OTG data adapter ready.
- [ ] Confirm the Pi boots and SSH works.
- [ ] Record the OS version with `cat /etc/os-release`.
- [ ] Confirm the display exists with `ls -l /dev/fb1`.

## Download and install

- [ ] Clone the repository without help from the workshop author.
- [ ] Run `./scripts/check.sh` and record the output.
- [ ] Run `sudo ./install.sh`.
- [ ] Install all apps by pressing Enter.
- [ ] Confirm the installer reports eight selected apps.
- [ ] Reboot with `sudo reboot`.

## Menu and app test

- [ ] The menu shows `CYBERDECK 2.0`.
- [ ] Touch can select and launch every app.
- [ ] Keyboard arrows and Enter work when the keyboard is connected before boot.
- [ ] Every app can return to the menu.
- [ ] Chinese Lingo can complete the character 口 without becoming stuck.
- [ ] Makan Ninja detects a continuous stylus slash.
- [ ] E-Reader shows an empty-library message and contains no bundled books.
- [ ] Journal saves only to `/home/ee/journal`.

## Recovery and shutdown

- [ ] Re-running the installer creates a timestamped backup.
- [ ] `sync` followed by `sudo shutdown -h now` shuts down cleanly.
- [ ] Note every confusing instruction, even when the final result works.

When reporting a problem, include the step number, exact terminal message, a
photo of the screen and what happened immediately before the problem.
