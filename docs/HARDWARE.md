# Hardware and Compatibility

## Participant equipment

| Item | Workshop guidance |
| --- | --- |
| Raspberry Pi Zero 2 W with header | Fully supported reference board; the pre-soldered header avoids soldering. |
| 3.5-inch GPIO touchscreen | Tested layout is 480×320 and uses GPIO pins 1–26. |
| microSD card | 16 GB or larger, plus a laptop card reader. |
| Power | Stable 5 V / 2 A micro-USB supply or power bank and a known-good cable. |
| Stylus | Recommended for the resistive touchscreen and Chinese stroke practice. |
| Wired or Bluetooth keyboard | Optional for the first workshop; useful later for the Journal app and menu navigation. |
| Micro-USB OTG data adapter | Only needed when using a wired keyboard. |
| Laptop | Mac or Windows with a terminal, Raspberry Pi Imager and Wi-Fi access. |

The first workshop can be completed from the laptop over SSH and with the
touchscreen. Explore wired or Bluetooth keyboard setup only after the core deck
works, because adapters, batteries and reconnection behaviour vary by model.

## Facilitator spares

- Two or three boot-tested microSD cards
- Two known-good keyboards and OTG data adapters
- One USB 2.0 hub
- A spare screen, styluses and short power cables
- A printed card with each participant's hostname, username and shutdown command

Never put participant passwords or Wi-Fi credentials in this repository.

## Workshop board choices

- **Pi Zero 2 W with header — fully supported:** the board used by the workshop
  and the reference for every instruction.
- **Pi Zero W / Zero WH — experimental:** a cheaper board with a similar GPIO
  layout, but it is substantially slower and animation-heavy games may stutter.

The workshop uses the Pi Zero 2 W with header. Anyone choosing a Zero W / Zero
WH should expect to test performance and troubleshoot separately.
