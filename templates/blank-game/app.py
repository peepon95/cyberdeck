#!/usr/bin/env python3
"""Small starting point for a new 480x320 RGB565 Cyberdeck app."""

import os
import struct
import time

WIDTH, HEIGHT = 480, 320
FRAMEBUFFER = os.environ.get("CYBERDECK_FB", "/dev/fb1")


def rgb565(red, green, blue):
    return struct.pack("<H", ((red >> 3) << 11) | ((green >> 2) << 5) | (blue >> 3))


def rectangle(buffer, x1, y1, x2, y2, colour):
    pixel = rgb565(*colour)
    for y in range(max(0, y1), min(HEIGHT, y2)):
        start = (y * WIDTH + max(0, x1)) * 2
        width = max(0, min(WIDTH, x2) - max(0, x1))
        buffer[start:start + width * 2] = pixel * width


def main():
    background = rgb565(8, 8, 18)
    buffer = bytearray(background * (WIDTH * HEIGHT))

    # Change these shapes, colours and positions to make the screen your own.
    rectangle(buffer, 30, 30, 450, 290, (25, 25, 40))
    rectangle(buffer, 70, 80, 410, 240, (0, 255, 220))
    rectangle(buffer, 80, 90, 400, 230, (255, 0, 180))

    with open(FRAMEBUFFER, "wb") as framebuffer:
        framebuffer.write(buffer)

    print("MY GAME is running. Press Ctrl+C to return to the menu.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
