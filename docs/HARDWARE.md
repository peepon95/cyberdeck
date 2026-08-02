# Hardware and Compatibility

## Participant equipment

| Item | Workshop guidance |
| --- | --- |
| Raspberry Pi Zero 2 W with header | Fully supported reference board; the pre-soldered header avoids soldering. |
| 3.5-inch GPIO touchscreen | Tested layout is 480×320 and uses GPIO pins 1–26. |
| microSD card | 16 GB or larger, plus a laptop card reader. |
| Power | Stable 5 V / 2 A micro-USB supply or power bank and a known-good cable. |
| Stylus | Recommended for the resistive touchscreen and Chinese stroke practice. |
| Wired USB keyboard | Workshop default for menu control and the Journal app. |
| Micro-USB OTG data adapter | Connects the keyboard to the Pi's USB data port. |
| Laptop | Mac or Windows with a terminal, Raspberry Pi Imager and Wi-Fi access. |

Bluetooth keyboards are an optional extension after the core deck works. Bring
a wired keyboard because Bluetooth pairing, battery and reconnection behaviour
varies between models.

## Facilitator spares

- Two or three boot-tested microSD cards
- Two known-good keyboards and OTG data adapters
- One USB 2.0 hub
- A spare screen, styluses and short power cables
- A printed card with each participant's hostname, username and shutdown command

Never put participant passwords or Wi-Fi credentials in this repository.

## Other Raspberry Pi boards

- **Pi Zero 2 W with header:** fully supported.
- **Pi Zero W/WH:** similar GPIO layout but substantially slower; test animation-heavy apps.
- **Pi 3B+ or Pi 4B:** adaptable, but physically larger with different USB and power arrangements.
- **Pi 5:** a separate porting track until display, touch and boot behaviour is tested.
- **Pico, Arduino and ESP32:** not compatible with this Linux/Python framebuffer package.

For any alternative, verify `/dev/fb1`, `/dev/input/event*`, the screen overlay,
touch calibration, RGB565 format, 480×320 dimensions and safe startup/shutdown.
