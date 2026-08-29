# Blank Game Template

1. Copy this folder into `apps/` and give the folder a lowercase ID such as
   `memory-game`.
2. Change the `id`, `name`, `colour` and `order` in `app.json`.
3. Ask Codex to turn `app.py` into your game while keeping the 480×320 RGB565
   framebuffer and Linux input requirements.
4. Run `./scripts/check.sh` before installing it on the Cyberdeck.

Example Codex prompt:

> Turn this blank Cyberdeck app into a touchscreen memory-matching game. Keep
> it compatible with Python 3, the `CYBERDECK_FB` framebuffer, a 480×320 RGB565 display and Linux
> input events. Add a clear way to return to the main menu.
