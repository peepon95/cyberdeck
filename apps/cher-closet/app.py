#!/usr/bin/env python3
"""Ee's Wardrobe — a Clueless-inspired wardrobe carousel for Cyberdeck 2.0."""

import glob
import mmap
import os
import random
import socket
import struct
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import TCPServer
from urllib.parse import parse_qs, urlparse

W, H, BPP = 480, 320, 2
FB_SIZE = W * H * BPP
FB_PATH = os.environ.get("CYBERDECK_FB", "/dev/fb1")
WARDROBE = os.path.expanduser(
    os.environ.get("CYBERDECK_WARDROBE", "~/cyberdeck-wardrobe")
)
UPLOAD_PORT = int(os.environ.get("CYBERDECK_WARDROBE_PORT", "8765"))


def c565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


INK = c565(11, 11, 24)
NAVY = c565(20, 20, 49)
FRAME = c565(76, 75, 91)
SILVER = c565(157, 157, 169)
LIGHT = c565(218, 225, 230)
STAGE = c565(91, 108, 137)
WHITE = c565(252, 252, 250)
BLUE = c565(77, 87, 235)
PINK = c565(231, 72, 178)
CREAM = c565(200, 191, 173)
TAN = c565(166, 126, 99)
BROWN = c565(104, 57, 52)
SKIN = c565(226, 174, 147)

buf = bytearray(FB_SIZE)
fb_fd = None
fb_mm = None
IMAGE_CACHE = {}
UPLOAD_REVISION = 0

DEMO_TOPS = [
    "demo:top-black-tee",
    "demo:top-white-singlet",
    "demo:top-pink-tee",
    "demo:top-blue-shirt",
    "demo:top-yellow-plaid",
    "demo:top-green-singlet",
]
DEMO_BOTTOMS = [
    "demo:bottom-blue-jeans",
    "demo:bottom-black-jeans",
    "demo:bottom-white-skirt",
    "demo:bottom-pink-skirt",
    "demo:bottom-green-skirt",
    "demo:bottom-brown-shorts",
]
DEMO_COLORS = {
    "top-black-tee": "black",
    "top-white-singlet": "white",
    "top-pink-tee": "pink",
    "top-blue-shirt": "blue",
    "top-yellow-plaid": "yellow",
    "top-green-singlet": "green",
    "bottom-blue-jeans": "denim",
    "bottom-black-jeans": "black",
    "bottom-white-skirt": "white",
    "bottom-pink-skirt": "pink",
    "bottom-green-skirt": "green",
    "bottom-brown-shorts": "brown",
}

FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01110",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10101 10011 01110 00001",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01110 10001 10000 01110 00001 10001 01110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 01010 01010 00100",
    "W": "10001 10001 10101 10101 10101 10101 01010",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10011 10101 10101 10101 11001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "01110 10001 00001 00110 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    " ": "00000 00000 00000 00000 00000 00000 00000",
    "'": "00100 00100 00000 00000 00000 00000 00000",
    ".": "00000 00000 00000 00000 00000 01100 01100",
    ":": "00000 01100 01100 00000 01100 01100 00000",
    "/": "00001 00010 00010 00100 01000 01000 10000",
    "-": "00000 00000 00000 11111 00000 00000 00000",
}
FONT = {key: value.split() for key, value in FONT.items()}


def packed(color):
    return struct.pack("<H", color)


def pixel(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        pos = (y * W + x) * 2
        buf[pos : pos + 2] = packed(color)


def rect(x1, y1, x2, y2, color):
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(W, int(x2)), min(H, int(y2))
    if x2 <= x1 or y2 <= y1:
        return
    row = packed(color) * (x2 - x1)
    for y in range(y1, y2):
        pos = (y * W + x1) * 2
        buf[pos : pos + len(row)] = row


def line(x1, y1, x2, y2, color, width=1):
    steps = max(abs(x2 - x1), abs(y2 - y1), 1)
    for step in range(steps + 1):
        x = int(x1 + (x2 - x1) * step / float(steps))
        y = int(y1 + (y2 - y1) * step / float(steps))
        radius = width // 2
        rect(x - radius, y - radius, x + radius + 1, y + radius + 1, color)


def ellipse(cx, cy, rx, ry, color):
    if rx <= 0 or ry <= 0:
        return
    for dy in range(-ry, ry + 1):
        amount = max(0.0, 1.0 - (dy * dy) / float(ry * ry))
        span = int(rx * (amount ** 0.5))
        rect(cx - span, cy + dy, cx + span + 1, cy + dy + 1, color)


def trapezoid(y1, y2, top_left, top_right, bottom_left, bottom_right, color):
    """Fill a simple four-sided shape one horizontal pixel row at a time."""
    height = max(1, y2 - y1)
    for row in range(height):
        amount = row / float(height)
        left = int(top_left + (bottom_left - top_left) * amount)
        right = int(top_right + (bottom_right - top_right) * amount)
        rect(left, y1 + row, right, y1 + row + 1, color)


def draw_text(value, x, y, color, scale=1):
    for char in value.upper():
        for row_number, row in enumerate(FONT.get(char, FONT[" "])):
            for column, bit in enumerate(row):
                if bit == "1":
                    rect(
                        x + column * scale,
                        y + row_number * scale,
                        x + (column + 1) * scale,
                        y + (row_number + 1) * scale,
                        color,
                    )
        x += 6 * scale


def text_width(value, scale=1):
    return len(value) * 6 * scale


def center_text(value, x1, x2, y, color, scale=1):
    draw_text(value, x1 + (x2 - x1 - text_width(value, scale)) // 2, y, color, scale)


def flush():
    fb_mm.seek(0)
    fb_mm.write(buf)


def frame_box(x1, y1, x2, y2, fill=LIGHT, edge=FRAME):
    rect(x1, y1, x2, y2, edge)
    rect(x1 + 3, y1 + 3, x2 - 3, y2 - 3, fill)
    line(x1 + 3, y1 + 3, x2 - 4, y1 + 3, WHITE)
    line(x1 + 3, y1 + 3, x1 + 3, y2 - 4, WHITE)


def side_panel(x1, x2, y1=34, y2=306):
    rect(x1, y1, x2, y2, CREAM)
    rect(x1, y1, x1 + 3, y2, TAN)
    rect(x2 - 3, y1, x2, y2, TAN)


def decode_ppm_bytes(raw):
    try:
        cursor = 0
        tokens = []
        while len(tokens) < 4:
            while cursor < len(raw) and raw[cursor] in b" \t\r\n":
                cursor += 1
            if cursor < len(raw) and raw[cursor] == 35:
                while cursor < len(raw) and raw[cursor] not in b"\r\n":
                    cursor += 1
                continue
            start = cursor
            while cursor < len(raw) and raw[cursor] not in b" \t\r\n":
                cursor += 1
            tokens.append(raw[start:cursor])
        magic, width, height, maximum = tokens
        width, height, maximum = int(width), int(height), int(maximum)
        if magic == b"P6":
            if raw[cursor : cursor + 2] == b"\r\n":
                cursor += 2
            elif cursor < len(raw) and raw[cursor] in b" \t\r\n":
                cursor += 1
            pixels = raw[cursor : cursor + width * height * 3]
            if maximum != 255:
                pixels = bytes(value * 255 // maximum for value in pixels)
        elif magic == b"P3":
            while cursor < len(raw) and raw[cursor] in b" \t\r\n":
                cursor += 1
            pixels = bytes(int(value) * 255 // maximum for value in raw[cursor:].split())
        else:
            return None
        if len(pixels) < width * height * 3:
            return None
        return width, height, pixels
    except (ValueError, IndexError, ZeroDivisionError):
        return None


def load_image(path):
    try:
        modified = os.path.getmtime(path)
    except OSError:
        return None
    cached = IMAGE_CACHE.get(path)
    if cached and cached[0] == modified:
        return cached[1]
    image = None
    try:
        with open(path, "rb") as handle:
            image = decode_ppm_bytes(handle.read())
    except OSError:
        pass
    if image is None:
        try:
            from PIL import Image

            loaded = Image.open(path).convert("RGB")
            loaded.thumbnail((360, 240))
            image = (loaded.width, loaded.height, loaded.tobytes())
        except Exception:
            pass
    if image is None:
        try:
            result = subprocess.run(
                ["convert", path, "-resize", "360x240>", "ppm:-"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            image = decode_ppm_bytes(result.stdout)
        except (OSError, subprocess.TimeoutExpired):
            pass
    IMAGE_CACHE[path] = (modified, image)
    return image


def background_color(width, height, pixels):
    points = ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))
    colors = []
    for x, y in points:
        pos = (y * width + x) * 3
        colors.append(pixels[pos : pos + 3])
    return tuple(sum(color[channel] for color in colors) // 4 for channel in range(3))


def object_bounds(width, height, pixels, background):
    threshold = 74 * 74
    left, top, right, bottom = width, height, -1, -1
    step = max(1, min(width, height) // 180)
    for y in range(0, height, step):
        for x in range(0, width, step):
            pos = (y * width + x) * 3
            distance = sum((pixels[pos + channel] - background[channel]) ** 2 for channel in range(3))
            if distance > threshold:
                left, top = min(left, x), min(top, y)
                right, bottom = max(right, x), max(bottom, y)
    if right < left or bottom < top:
        return 0, 0, width, height
    pad_x, pad_y = max(2, (right - left) // 15), max(2, (bottom - top) // 15)
    return max(0, left - pad_x), max(0, top - pad_y), min(width, right + pad_x + 1), min(height, bottom + pad_y + 1)


def demo_garment(path, x, y, width, height):
    name = path.split(":", 1)[1]
    cx, cy = x + width // 2, y + height // 2
    palette = {
        "black": (c565(31, 30, 38), SILVER),
        "white": (c565(244, 241, 225), c565(105, 110, 124)),
        "pink": (c565(225, 82, 151), c565(255, 190, 220)),
        "blue": (c565(48, 103, 178), c565(205, 226, 241)),
        "yellow": (c565(220, 183, 44), c565(70, 62, 55)),
        "green": (c565(49, 133, 87), c565(196, 228, 183)),
        "denim": (c565(45, 91, 150), c565(213, 184, 103)),
        "brown": (c565(136, 78, 48), c565(225, 171, 103)),
    }
    color_name = DEMO_COLORS.get(name, "black")
    color, trim = palette[color_name]
    outline = INK
    if name.startswith("top-"):
        if "singlet" in name:
            rect(cx - 30, cy - 31, cx + 30, cy + 33, outline)
            rect(cx - 27, cy - 28, cx + 27, cy + 31, color)
            rect(cx - 25, cy - 35, cx - 12, cy - 20, color)
            rect(cx + 12, cy - 35, cx + 25, cy - 20, color)
            ellipse(cx, cy - 26, 13, 9, STAGE)
        else:
            rect(cx - 43, cy - 29, cx + 43, cy + 34, outline)
            line(cx - 43, cy - 22, cx - 67, cy + 8, outline, 17)
            line(cx + 43, cy - 22, cx + 67, cy + 8, outline, 17)
            rect(cx - 40, cy - 26, cx + 40, cy + 31, color)
            line(cx - 40, cy - 20, cx - 64, cy + 8, color, 13)
            line(cx + 40, cy - 20, cx + 64, cy + 8, color, 13)
            ellipse(cx, cy - 25, 13, 7, STAGE)
        if "shirt" in name:
            line(cx, cy - 22, cx, cy + 29, trim, 2)
            ellipse(cx - 11, cy - 20, 10, 5, trim)
        elif "plaid" in name:
            for offset in (-27, -9, 9, 27):
                line(cx + offset, cy - 25, cx + offset, cy + 29, trim, 2)
            for offset in (-10, 9):
                line(cx - 38, cy + offset, cx + 38, cy + offset, trim, 2)
        else:
            line(cx - 32, cy + 20, cx + 32, cy + 20, trim, 2)
    elif "jeans" in name:
        rect(cx - 46, cy - 34, cx + 46, cy - 9, outline)
        rect(cx - 43, cy - 31, cx + 43, cy - 11, color)
        for row in range(56):
            taper = row // 18
            y1 = cy - 11 + row
            rect(cx - 45 + taper, y1, cx - 3, y1 + 2, outline)
            rect(cx + 3, y1, cx + 45 - taper, y1 + 2, outline)
            rect(cx - 41 + taper, y1, cx - 5, y1 + 1, color)
            rect(cx + 5, y1, cx + 41 - taper, y1 + 1, color)
        line(cx, cy - 29, cx, cy - 7, trim, 2)
        line(cx - 36, cy - 20, cx - 18, cy - 12, trim, 1)
        line(cx + 36, cy - 20, cx + 18, cy - 12, trim, 1)
    elif "shorts" in name:
        rect(cx - 46, cy - 31, cx + 46, cy + 21, outline)
        rect(cx - 43, cy - 28, cx + 43, cy + 18, color)
        rect(cx - 3, cy - 4, cx + 3, cy + 21, STAGE)
        line(cx - 38, cy - 18, cx + 38, cy - 18, trim, 2)
    else:
        for row in range(66):
            inset = max(0, 18 - row // 3)
            rect(cx - 52 + inset, cy - 34 + row, cx + 53 - inset, cy - 31 + row, outline)
        for row in range(60):
            inset = max(0, 16 - row // 3)
            rect(cx - 48 + inset, cy - 30 + row, cx + 49 - inset, cy - 29 + row, color)
        line(cx - 39, cy - 20, cx + 39, cy - 20, trim, 2)
    return True


def draw_photo(path, x, y, width, height, remove_background=True):
    if path.startswith("demo:"):
        return demo_garment(path, x, y, width, height)
    image = load_image(path)
    if image is None:
        return False
    image_width, image_height, pixels = image
    background = background_color(image_width, image_height, pixels)
    if remove_background:
        left, top, right, bottom = object_bounds(image_width, image_height, pixels, background)
    else:
        left, top, right, bottom = 0, 0, image_width, image_height
    crop_width, crop_height = right - left, bottom - top
    scale = min(width / float(crop_width), height / float(crop_height))
    draw_width, draw_height = max(1, int(crop_width * scale)), max(1, int(crop_height * scale))
    offset_x, offset_y = x + (width - draw_width) // 2, y + (height - draw_height) // 2
    threshold = 70 * 70
    for draw_y in range(draw_height):
        source_y = min(bottom - 1, top + int(draw_y / scale))
        for draw_x in range(draw_width):
            source_x = min(right - 1, left + int(draw_x / scale))
            pos = (source_y * image_width + source_x) * 3
            red, green, blue = pixels[pos], pixels[pos + 1], pixels[pos + 2]
            if remove_background:
                distance = (
                    (red - background[0]) ** 2
                    + (green - background[1]) ** 2
                    + (blue - background[2]) ** 2
                )
                if distance < threshold:
                    continue
            pixel(offset_x + draw_x, offset_y + draw_y, c565(red, green, blue))
    return True


GARMENT_NAMES = {
    "top-black-tee": "BLACK TEE",
    "top-white-singlet": "WHITE SINGLET",
    "top-pink-tee": "PINK TEE",
    "top-blue-shirt": "BLUE SHIRT",
    "top-yellow-plaid": "YELLOW PLAID",
    "top-green-singlet": "GREEN SINGLET",
    "bottom-blue-jeans": "BLUE JEANS",
    "bottom-black-jeans": "BLACK JEANS",
    "bottom-white-skirt": "WHITE SKIRT",
    "bottom-pink-skirt": "PINK SKIRT",
    "bottom-green-skirt": "GREEN SKIRT",
    "bottom-brown-shorts": "BROWN SHORTS",
}


def garment_name(path):
    if not path:
        return "NO ITEM"
    if path.startswith("demo:"):
        return GARMENT_NAMES.get(path.split(":", 1)[1], "CLOTHING")
    return os.path.splitext(os.path.basename(path))[0].replace("_", " ").replace("-", " ").upper()[:18]


PIXEL_FACE = [
    "      HHHHHHHHHH      ",
    "   HHHHHHHHHHHHHHHH   ",
    " HHHHHHHHHHHHHHHHHHHH ",
    "HHHHHHHHHHHHHHHHHHHHHH",
    "HHHHHSSSSSSSSSSSSHHHHH",
    "HHHHSSSSSSSSSSSSSSHHHH",
    "HHHSSSEESSSSSSEESSSHHH",
    "HHHSSSEESSSSSSEESSSHHH",
    "HHHSSSSSSSNSSSSSSSSHHH",
    "HHHSSPSSSSSSSSSSPSSHHH",
    "HHHSSSSSSMMMMSSSSSSHHH",
    "HHHHSSSSSSSSSSSSSSHHHH",
    "HHHHHSSSSSSSSSSSSHHHHH",
    "HHHHHHSSSSSSSSSSHHHHHH",
    "HHHHHHHHHHSSHHHHHHHHHH",
    " HHHHHHHH SS HHHHHHHH ",
    " HHHHHHH      HHHHHHH ",
    "  HHHHH        HHHHH  ",
]


def draw_pixel_face(cx, top, scale=3):
    colors = {
        "H": c565(28, 25, 39),
        "S": c565(202, 119, 67),
        "E": c565(28, 25, 39),
        "N": c565(105, 53, 41),
        "P": c565(218, 78, 91),
        "M": c565(52, 40, 48),
    }
    widest = max(len(row) for row in PIXEL_FACE)
    left = cx - widest * scale // 2
    for row_number, row in enumerate(PIXEL_FACE):
        for column, value in enumerate(row):
            if value in colors:
                rect(
                    left + column * scale,
                    top + row_number * scale,
                    left + (column + 1) * scale,
                    top + (row_number + 1) * scale,
                    colors[value],
                )


def demo_colors(path):
    palette = {
        "black": (c565(31, 30, 38), SILVER),
        "white": (c565(244, 241, 225), c565(105, 110, 124)),
        "pink": (c565(225, 82, 151), c565(255, 190, 220)),
        "blue": (c565(48, 103, 178), c565(205, 226, 241)),
        "yellow": (c565(220, 183, 44), c565(70, 62, 55)),
        "green": (c565(49, 133, 87), c565(196, 228, 183)),
        "denim": (c565(45, 91, 150), c565(213, 184, 103)),
        "brown": (c565(136, 78, 48), c565(225, 171, 103)),
    }
    name = path.split(":", 1)[1]
    return name, palette[DEMO_COLORS.get(name, "black")]


def draw_worn_demo_top(path):
    """Draw a demo top fitted to the avatar rather than as a loose thumbnail."""
    name, (color, trim) = demo_colors(path)
    if "singlet" in name:
        trapezoid(115, 204, 216, 264, 212, 268, INK)
        trapezoid(118, 201, 219, 261, 216, 264, color)
        line(218, 116, 218, 139, color, 7)
        line(262, 116, 262, 139, color, 7)
        ellipse(240, 116, 12, 7, SKIN)
    else:
        line(208, 124, 190, 150, INK, 23)
        line(272, 124, 290, 150, INK, 23)
        line(208, 124, 190, 150, color, 17)
        line(272, 124, 290, 150, color, 17)
        trapezoid(114, 204, 204, 276, 212, 268, INK)
        trapezoid(118, 200, 208, 272, 216, 264, color)
        # Skin-coloured neckline joins directly to the neck.
        ellipse(240, 115, 10, 6, SKIN)
    if "shirt" in name:
        line(240, 126, 240, 197, trim, 2)
        line(230, 119, 240, 127, trim, 2)
        line(250, 119, 240, 127, trim, 2)
    elif "plaid" in name:
        for offset in (-19, 0, 19):
            line(240 + offset, 124, 240 + offset, 197, trim, 2)
        for y in (143, 170):
            line(211, y, 269, y, trim, 2)
    else:
        line(217, 192, 263, 192, trim, 2)


def draw_worn_demo_bottom(path):
    """Draw demo bottoms directly on the avatar's waist and legs."""
    name, (color, trim) = demo_colors(path)
    if "jeans" in name:
        rect(211, 199, 269, 216, INK)
        rect(215, 202, 265, 215, color)
        trapezoid(214, 278, 214, 239, 216, 237, INK)
        trapezoid(214, 278, 241, 266, 243, 264, INK)
        trapezoid(217, 275, 217, 237, 219, 234, color)
        trapezoid(217, 275, 243, 263, 246, 261, color)
        line(240, 204, 240, 224, trim, 2)
        line(218, 210, 232, 217, trim, 1)
        line(262, 210, 248, 217, trim, 1)
    elif "shorts" in name:
        rect(211, 199, 269, 238, INK)
        rect(215, 202, 265, 234, color)
        rect(238, 218, 242, 238, INK)
        line(218, 211, 262, 211, trim, 2)
    else:
        trapezoid(199, 258, 213, 267, 196, 284, INK)
        trapezoid(203, 254, 216, 264, 202, 278, color)
        line(217, 211, 263, 211, trim, 2)


def wardrobe_files(category):
    folder = os.path.join(WARDROBE, category)
    files = []
    for extension in ("*.ppm", "*.pnm", "*.jpg", "*.jpeg", "*.png"):
        files.extend(glob.glob(os.path.join(folder, extension)))
    files = sorted(set(files))
    if files:
        return files
    if category == "tops":
        return DEMO_TOPS[:]
    return DEMO_BOTTOMS[:]


def placeholder_top(cx, cy):
    color, shade = c565(146, 74, 46), c565(91, 47, 36)
    rect(cx - 35, cy - 24, cx + 35, cy + 30, color)
    line(cx - 35, cy - 20, cx - 57, cy + 8, color, 13)
    line(cx + 35, cy - 20, cx + 57, cy + 8, color, 13)
    line(cx - 32, cy + 18, cx + 32, cy + 18, shade, 2)
    center_text("UPLOAD TOPS", cx - 80, cx + 80, cy + 39, FRAME, 1)


def placeholder_bottom(cx, cy):
    color, stripe = c565(84, 39, 71), c565(190, 91, 124)
    for row in range(52):
        inset = max(0, 15 - row // 3)
        rect(cx - 44 + inset, cy - 25 + row, cx + 45 - inset, cy - 24 + row, color)
    for offset in (-28, -9, 10, 29):
        line(cx + offset, cy - 22, cx + offset + 8, cy + 25, stripe, 2)
    center_text("UPLOAD BOTTOMS", cx - 90, cx + 90, cy + 36, FRAME, 1)


def arrow(x, y, direction, color):
    if direction < 0:
        for amount in range(9):
            rect(x + amount, y - amount, x + amount + 2, y + amount + 1, color)
    else:
        for amount in range(9):
            rect(x - amount, y - amount, x - amount + 2, y + amount + 1, color)


def nav_bar(y, selected_index, item_count):
    widths = ((116, 198), (201, 282), (285, 367))
    for number, (x1, x2) in enumerate(widths):
        frame_box(x1, y, x2, y + 25, BLUE if number == 2 else NAVY, FRAME)
    arrow(157, y + 12, -1, SILVER)
    arrow(148, y + 12, -1, SILVER)
    center_text("{} / {}".format(selected_index + 1 if item_count else 0, item_count), 201, 282, y + 9, WHITE, 1)
    arrow(327, y + 12, 1, WHITE)
    arrow(336, y + 12, 1, WHITE)


def draw_header(upload_name):
    rect(0, 0, W, 34, INK)
    draw_text("EE'S WARDROBE", 11, 10, SILVER, 2)
    frame_box(289, 5, 403, 30, NAVY, FRAME)
    center_text("UPLOAD", 289, 403, 12, WHITE, 1)
    draw_text("BACK", 437, 12, PINK, 1)
    draw_text(upload_name[:35], 3, 310, SILVER, 1)


def draw_closet(top_files, bottom_files, top_index, bottom_index, upload_name):
    buf[:] = packed(INK) * (W * H)
    draw_header(upload_name)
    side_panel(0, 113)
    side_panel(370, W)
    top_path = top_files[top_index] if top_files else None
    bottom_path = bottom_files[bottom_index] if bottom_files else None
    frame_box(116, 37, 367, 141, STAGE, FRAME)
    if top_files:
        draw_photo(top_path, 126, 43, 231, 90)
    else:
        placeholder_top(241, 88)
    nav_bar(143, top_index, len(top_files))
    frame_box(116, 170, 367, 274, STAGE, FRAME)
    if bottom_files:
        draw_photo(bottom_path, 126, 176, 231, 90)
    else:
        placeholder_bottom(241, 218)
    nav_bar(276, bottom_index, len(bottom_files))
    center_text("TOP", 4, 109, 60, INK, 1)
    center_text(garment_name(top_path)[:16], 4, 109, 76, INK, 1)
    center_text("BOTTOM", 4, 109, 184, INK, 1)
    center_text(garment_name(bottom_path)[:16], 4, 109, 200, INK, 1)
    center_text("BUILD", 373, 477, 83, INK, 1)
    center_text("YOUR LOOK", 373, 477, 100, INK, 1)
    frame_box(8, 272, 108, 307, BLUE, FRAME)
    center_text("BROWSE", 8, 108, 283, INK, 2)
    frame_box(375, 272, 473, 307, SILVER, FRAME)
    center_text("DRESS", 375, 473, 278, INK, 1)
    center_text("ME", 375, 473, 292, INK, 1)
    flush()


def draw_fashion_doll(top_path, bottom_path):
    """A single 64x116 pixel-art figure with shared garment landmarks."""
    ox, oy, scale = 176, 60, 2
    skin = c565(218, 157, 112)
    shade = c565(175, 112, 79)
    hair = c565(38, 29, 40)
    hair_light = c565(78, 51, 57)

    def shape(points, color, min_y=0):
        for y in range(max(min_y, min(p[1] for p in points)), max(p[1] for p in points)):
            crossings = []
            for a, b in zip(points, points[1:] + points[:1]):
                if min(a[1], b[1]) <= y < max(a[1], b[1]):
                    crossings.append(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
            crossings.sort()
            for left, right in zip(crossings[::2], crossings[1::2]):
                rect(ox + round(left) * scale, oy + y * scale,
                     ox + round(right) * scale, oy + (y + 1) * scale, color)

    def block(x, y, w, h, color):
        rect(ox + x * scale, oy + y * scale, ox + (x + w) * scale, oy + (y + h) * scale, color)

    # Hair sits behind the shoulders. The neck is only four pixels tall.
    shape([(24, 2), (39, 2), (44, 7), (44, 24), (46, 33),
           (39, 36), (24, 34), (19, 30), (20, 9)], hair)
    # Only exposed skin belongs behind clothes. The old full torso extended
    # outside the fitted shirt and appeared as a second body at the underarms.
    block(29, 22, 6, 9, skin)
    if top_path and top_path.startswith('demo:'):
        if 'singlet' in top_path:
            shape([(24, 29), (29, 28), (35, 28), (40, 29),
                   (38, 36), (26, 36)], skin)
        else:
            shape([(28, 28), (36, 28), (34, 31), (30, 31)], skin)
    # Relaxed arms: upper arm, elbow, wrist and a small hand silhouette.
    # Sleeved starter tops own the shoulder silhouette. Do not draw skin
    # outside their sloping edges; exposed arms begin at the sleeve opening.
    sleeved = bool(top_path and top_path.startswith('demo:') and 'singlet' not in top_path)
    arm_start = 40 if sleeved else 0
    for mirror in (False, True):
        def side(points):
            return [(64 - x if mirror else x, y) for x, y in points]
        shape(side([(21, 30), (25, 34), (20, 48), (16, 62), (15, 70),
                    (12, 72), (10, 70), (11, 65), (13, 60), (15, 46), (17, 34)]), shade, arm_start)
        shape(side([(20, 33), (23, 35), (18, 49), (15, 64),
                    (14, 70), (12, 70), (13, 62), (15, 48)]), skin, arm_start)
        if not (bottom_path and bottom_path.startswith('demo:') and 'jeans' in bottom_path):
            shape(side([(23, 61), (32, 63), (30, 84), (28, 107),
                        (28, 111), (23, 111), (23, 103), (22, 85)]), shade)
            shape(side([(24, 64), (30, 65), (28, 84), (26, 108),
                        (24, 108), (24, 85)]), skin)
        shape(side([(24, 105), (28, 105), (28, 110), (24, 110)]), skin)

    if bottom_path and bottom_path.startswith('demo:'):
        name, (color, trim) = demo_colors(bottom_path)
        if 'skirt' in name:
            shape([(25, 53), (39, 53), (46, 78), (18, 78)], INK)
            shape([(26, 55), (38, 55), (44, 76), (20, 76)], color)
            for x in (25, 31, 37):
                shape([(x, 58), (x + 1, 58), (x + 2, 75), (x, 75)], trim)
        else:
            end = 106 if 'jeans' in name else 73
            shape([(25, 53), (39, 53), (42, 63), (40, end), (33, end),
                   (32, 68), (31, end), (24, end), (22, 63)], INK)
            shape([(26, 55), (38, 55), (40, 63), (38, end - 2), (35, end - 2),
                   (34, 67), (30, 67), (29, end - 2), (26, end - 2), (24, 63)], color)
            block(31, 56, 1, 9, trim)
            block(25, 58, 4, 1, trim)
            block(35, 58, 4, 1, trim)
    elif bottom_path:
        draw_photo(bottom_path, ox + 18 * scale, oy + 53 * scale, 56, 106)

    if top_path and top_path.startswith('demo:'):
        name, (color, trim) = demo_colors(top_path)
        if 'singlet' in name:
            points = [(24, 29), (28, 29), (29, 35), (35, 35), (36, 29),
                      (40, 29), (39, 42), (37, 49), (39, 55), (25, 55), (27, 49), (25, 42)]
        else:
            points = [(23, 29), (28, 28), (30, 31), (34, 31), (36, 28),
                      (41, 29), (47, 39), (41, 42), (39, 37), (38, 47),
                      (39, 55), (25, 55), (26, 47), (25, 37), (23, 42), (17, 39)]
        shape(points, color)
        block(26, 53, 12, 1, trim)
        if 'plaid' in name:
            for x in (27, 31, 35):
                block(x, 35, 1, 17, trim)
            for y in (38, 44, 50):
                block(26, y, 12, 1, trim)
        elif 'shirt' in name:
            block(32, 33, 1, 19, trim)
    elif top_path:
        draw_photo(top_path, ox + 17 * scale, oy + 28 * scale, 60, 54)

    # Face and hair are authored on the same pixel grid as the body.
    shape([(25, 9), (38, 8), (40, 13), (39, 21), (35, 25),
           (29, 25), (24, 21), (23, 14)], skin)
    shape([(23, 7), (34, 4), (41, 9), (40, 15), (35, 10),
           (31, 9), (26, 14), (23, 16)], hair)
    shape([(23, 9), (28, 5), (35, 5), (28, 7), (24, 13), (22, 23), (21, 21)], hair_light)
    block(26, 16, 2, 2, hair)
    block(35, 16, 2, 2, hair)
    block(31, 18, 1, 2, shade)
    block(30, 22, 4, 1, c565(126, 62, 62))
    block(25, 20, 2, 1, c565(226, 128, 118))
    block(36, 20, 2, 1, c565(226, 128, 118))
    shape([(23, 109), (28, 109), (28, 114), (20, 114), (20, 112)], hair)
    shape([(36, 109), (41, 109), (44, 112), (44, 114), (36, 114)], hair)
    block(21, 113, 6, 1, SILVER)
    block(37, 113, 6, 1, SILVER)


def draw_outfit(top_path, bottom_path, upload_name):
    buf[:] = packed(INK) * (W * H)
    draw_header(upload_name)
    side_panel(0, 88)
    side_panel(392, W)
    frame_box(94, 40, 386, 306, STAGE, FRAME)
    draw_fashion_doll(top_path, bottom_path)
    center_text("TOP", 3, 85, 87, INK, 1)
    center_text(garment_name(top_path)[:12], 3, 85, 104, INK, 1)
    center_text("BOTTOM", 395, 477, 87, INK, 1)
    center_text(garment_name(bottom_path)[:12], 395, 477, 104, INK, 1)
    frame_box(7, 264, 82, 304, BLUE, FRAME)
    center_text("CLOSET", 7, 82, 280, INK, 1)
    frame_box(398, 264, 473, 304, BLUE, FRAME)
    center_text("SAVE", 398, 473, 280, INK, 1)
    flush()


def draw_upload(upload_name):
    buf[:] = packed(INK) * (W * H)
    draw_header(upload_name)
    side_panel(0, 76)
    side_panel(404, W)
    frame_box(83, 44, 397, 266, NAVY, FRAME)
    center_text("ADD YOUR CLOTHES", 83, 397, 62, PINK, 2)
    draw_text("1  USE THE SAME WIFI", 111, 104, WHITE, 1)
    draw_text("2  OPEN ON YOUR PHONE", 111, 132, WHITE, 1)
    frame_box(101, 158, 379, 195, LIGHT, FRAME)
    center_text(upload_name.replace("UPLOAD: ", "HTTP://"), 101, 379, 173, INK, 1)
    draw_text("3  CHOOSE TOPS OR BOTTOMS", 111, 218, WHITE, 1)
    draw_text("YOUR PHOTOS STAY HERE", 153, 244, SILVER, 1)
    frame_box(174, 274, 306, 307, BLUE, FRAME)
    center_text("CLOSET", 174, 306, 285, INK, 2)
    flush()


def save_outfit(top_path, bottom_path):
    os.makedirs(WARDROBE, exist_ok=True)
    with open(os.path.join(WARDROBE, "last-outfit.txt"), "w", encoding="utf-8") as handle:
        handle.write("TOP: {}\n".format(top_path or "none"))
        handle.write("BOTTOM: {}\n".format(bottom_path or "none"))


UPLOAD_PAGE = """<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Upload to Ee's Wardrobe</title><style>
*{box-sizing:border-box}body{margin:0;background:#171326;color:#fff;font:17px system-ui,sans-serif}
main{max-width:560px;margin:auto;padding:28px 20px}h1{color:#f0d857;font-size:30px;margin:0 0 8px}
p{line-height:1.5;color:#d4cad8}.card{background:#2a203c;border:2px solid #7d64ab;padding:18px;margin:22px 0}
label{display:block;margin:15px 0 7px;color:#f18fc0;font-weight:700}select,input,button{width:100%;font:inherit}
select,input{background:#fff;color:#171326;padding:12px;border:0}button{margin-top:18px;padding:14px;background:#665bff;color:#fff;border:0;font-weight:800}
button:disabled{opacity:.5}#status{min-height:28px;color:#aee58d}.tip{font-size:14px;color:#bcb1c1}
</style></head><body><main><h1>EE'S WARDROBE</h1><p>Add your own clothes to the Cyberdeck carousel.</p>
<div class="card"><label for="category">These photos are</label><select id="category"><option value="tops">Tops</option><option value="bottoms">Bottoms</option></select>
<label for="photos">Choose clothing photos</label><input id="photos" type="file" accept="image/*" multiple>
<button id="upload">ADD TO CLOSET</button><p id="status"></p></div>
<p class="tip">For the cleanest cut-out, photograph one item at a time on a plain, contrasting background. Your photos stay on this Cyberdeck.</p>
<script>
const button=document.querySelector('#upload'), input=document.querySelector('#photos'), status=document.querySelector('#status');
function imageFromFile(file){return new Promise((resolve,reject)=>{const img=new Image();const url=URL.createObjectURL(file);img.onload=()=>{URL.revokeObjectURL(url);resolve(img)};img.onerror=reject;img.src=url})}
async function asPPM(file){const img=await imageFromFile(file), max=360, scale=Math.min(1,max/img.width,max/img.height);const w=Math.max(1,Math.round(img.width*scale)),h=Math.max(1,Math.round(img.height*scale));const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0,w,h);const rgba=ctx.getImageData(0,0,w,h).data, head=new TextEncoder().encode(`P6\n${w} ${h}\n255\n`), out=new Uint8Array(head.length+w*h*3);out.set(head);for(let s=0,d=head.length;s<rgba.length;s+=4){out[d++]=rgba[s];out[d++]=rgba[s+1];out[d++]=rgba[s+2]}return out}
button.onclick=async()=>{const files=[...input.files];if(!files.length){status.textContent='Choose at least one photo.';return}button.disabled=true;let done=0;try{for(const file of files){status.textContent=`Preparing ${done+1} of ${files.length}…`;const ppm=await asPPM(file);const name=file.name.replace(/\\.[^.]+$/,'')+'.ppm';const response=await fetch(`/upload?category=${document.querySelector('#category').value}&name=${encodeURIComponent(name)}`,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:ppm});if(!response.ok)throw new Error(await response.text());done++}status.textContent=`Added ${done} photo${done===1?'':'s'}. They are now on the Cyberdeck.`;input.value=''}catch(error){status.textContent='Upload failed: '+error.message}finally{button.disabled=false}}
</script></main></body></html>"""


class UploadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path != "/":
            self.send_error(404)
            return
        body = UPLOAD_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        global UPLOAD_REVISION
        parsed = urlparse(self.path)
        if parsed.path != "/upload":
            self.send_error(404)
            return
        query = parse_qs(parsed.query)
        category = query.get("category", [""])[0]
        original_name = query.get("name", ["item.ppm"])[0]
        if category not in ("tops", "bottoms"):
            self.send_error(400, "Choose tops or bottoms")
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 5 * 1024 * 1024:
            self.send_error(400, "Photo is empty or too large")
            return
        body = self.rfile.read(length)
        if decode_ppm_bytes(body) is None:
            self.send_error(400, "The phone could not convert this photo")
            return
        stem = "".join(character for character in os.path.splitext(original_name)[0] if character.isalnum() or character in "-_")[:48]
        if not stem:
            stem = "item"
        folder = os.path.join(WARDROBE, category)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, stem + ".ppm")
        suffix = 2
        while os.path.exists(path):
            path = os.path.join(folder, "{}-{}.ppm".format(stem, suffix))
            suffix += 1
        with open(path, "wb") as handle:
            handle.write(body)
        UPLOAD_REVISION += 1
        response = b"OK"
        self.send_response(201)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, message, *args):
        print("Wardrobe upload: " + (message % args))


class WardrobeServer(ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self):
        # Avoid a slow reverse-DNS lookup when the wardrobe opens.
        TCPServer.server_bind(self)
        self.server_name = self.server_address[0]
        self.server_port = self.server_address[1]


def start_upload_server():
    try:
        server = WardrobeServer(("0.0.0.0", UPLOAD_PORT), UploadHandler)
    except OSError as error:
        print("Wardrobe upload server unavailable: {}".format(error))
        return None
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def upload_label():
    hostname = socket.gethostname().split(".")[0]
    return "UPLOAD: {}.LOCAL:{}".format(hostname, UPLOAD_PORT)


def find_touch_device():
    for path in sorted(glob.glob("/dev/input/event*")):
        try:
            name_path = "/sys/class/input/{}/device/name".format(os.path.basename(path))
            with open(name_path, encoding="utf-8") as handle:
                name = handle.read().lower()
            if any(word in name for word in ("touch", "ads7846", "xpt2046")):
                return path
        except OSError:
            pass
    return None


def map_touch(raw_x, raw_y):
    x = int((3708 - raw_y) / 3300.0 * W)
    y = int((raw_x - 670) / 2918.0 * H)
    return max(0, min(W - 1, x)), max(0, min(H - 1, y))


def write_preview(path):
    with open(path, "wb") as handle:
        handle.write("P6\n{} {}\n255\n".format(W, H).encode("ascii"))
        for position in range(0, len(buf), 2):
            value = struct.unpack("<H", buf[position : position + 2])[0]
            handle.write(bytes((((value >> 11) & 31) * 255 // 31, ((value >> 5) & 63) * 255 // 63, (value & 31) * 255 // 31)))


def main():
    global fb_fd, fb_mm
    os.makedirs(os.path.join(WARDROBE, "tops"), exist_ok=True)
    os.makedirs(os.path.join(WARDROBE, "bottoms"), exist_ok=True)
    server = start_upload_server()
    flags = os.O_RDWR if FB_PATH == "/dev/fb1" else os.O_RDWR | os.O_CREAT
    fb_fd = os.open(FB_PATH, flags, 0o644)
    if FB_PATH != "/dev/fb1":
        os.ftruncate(fb_fd, FB_SIZE)
    fb_mm = mmap.mmap(fb_fd, FB_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
    touch_path = find_touch_device()
    if not touch_path:
        print("No touchscreen found")
        return
    touch_fd = os.open(touch_path, os.O_RDONLY | os.O_NONBLOCK)
    state = "closet"
    top_index = bottom_index = 0
    seen_revision = UPLOAD_REVISION
    raw_x = raw_y = -1
    touching = False
    tap_armed = False
    last_refresh = 0.0
    label = upload_label()

    def refresh():
        nonlocal top_index, bottom_index, last_refresh
        tops, bottoms = wardrobe_files("tops"), wardrobe_files("bottoms")
        top_index = min(top_index, max(0, len(tops) - 1))
        bottom_index = min(bottom_index, max(0, len(bottoms) - 1))
        if state == "closet":
            draw_closet(tops, bottoms, top_index, bottom_index, label)
        elif state == "outfit":
            draw_outfit(tops[top_index] if tops else None, bottoms[bottom_index] if bottoms else None, label)
        else:
            draw_upload(label)
        last_refresh = time.monotonic()
        return tops, bottoms

    tops, bottoms = refresh()
    try:
        while True:
            tap = None
            while True:
                try:
                    data = os.read(touch_fd, 16)
                except OSError:
                    break
                if len(data) != 16:
                    break
                _, _, event_type, code, value = struct.unpack("IIHHi", data)
                if event_type == 3 and code == 0:
                    raw_x = value
                elif event_type == 3 and code == 1:
                    raw_y = value
                elif event_type == 1 and code == 330:
                    touching = value == 1
                    tap_armed = touching
                elif event_type == 0 and code == 0 and touching and tap_armed and raw_x >= 0 and raw_y >= 0:
                    tap = map_touch(raw_x, raw_y)
                    tap_armed = False
            if seen_revision != UPLOAD_REVISION or time.monotonic() - last_refresh > 5:
                seen_revision = UPLOAD_REVISION
                tops, bottoms = refresh()
            if tap:
                x, y = tap
                if x >= 425 and y < 35:
                    return
                if 285 <= x <= 408 and y < 35:
                    state = "upload"
                    tops, bottoms = refresh()
                    time.sleep(0.12)
                    continue
                if state == "upload":
                    if 160 <= x <= 320 and y > 260:
                        state = "closet"
                    tops, bottoms = refresh()
                    time.sleep(0.12)
                    continue
                if state == "outfit":
                    if x < 92 and y > 250:
                        state = "closet"
                    elif x > 390 and y > 250:
                        save_outfit(tops[top_index] if tops else None, bottoms[bottom_index] if bottoms else None)
                    tops, bottoms = refresh()
                    time.sleep(0.12)
                    continue
                if 143 <= y <= 169:
                    if tops:
                        if x < 200:
                            top_index = (top_index - 1) % len(tops)
                        elif x > 284:
                            top_index = (top_index + 1) % len(tops)
                        else:
                            top_index = random.randrange(len(tops))
                elif 276 <= y <= 306 and 110 <= x < 370:
                    if bottoms:
                        if x < 200:
                            bottom_index = (bottom_index - 1) % len(bottoms)
                        elif x > 284:
                            bottom_index = (bottom_index + 1) % len(bottoms)
                        else:
                            bottom_index = random.randrange(len(bottoms))
                elif x < 113 and y > 260:
                    IMAGE_CACHE.clear()
                elif x > 370 and y > 260:
                    state = "outfit"
                    save_outfit(tops[top_index] if tops else None, bottoms[bottom_index] if bottoms else None)
                tops, bottoms = refresh()
                time.sleep(0.12)
            time.sleep(0.02)
    finally:
        if server is not None:
            server.shutdown()
        os.close(touch_fd)
        fb_mm.close()
        os.close(fb_fd)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] in ("--preview", "--preview-outfit"):
        class PreviewFramebuffer:
            def seek(self, position):
                pass

            def write(self, data):
                pass

        fb_mm = PreviewFramebuffer()
        if sys.argv[1] == "--preview":
            draw_closet(DEMO_TOPS, DEMO_BOTTOMS, 0, 0, "UPLOAD: CYBERDECK3.LOCAL:8765")
        else:
            draw_outfit(DEMO_TOPS[0], DEMO_BOTTOMS[0], "UPLOAD: CYBERDECK3.LOCAL:8765")
        write_preview(sys.argv[2])
    else:
        main()
