#!/usr/bin/env python3
"""Makan Ninja - framebuffer + XPT2046 edition.

No third-party packages are required on the cyberdeck.  The game writes RGB565
pixels directly to /dev/fb1 and reads Linux input events from the touchscreen.
"""

import math
import mmap
import os
import random
import struct
import sys
import time

W, H = 480, 320
BPP = 2
FBSIZE = W * H * BPP
FPS = 30.0
FRAME_TIME = 1.0 / FPS


def c565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


C_BLACK = c565(0, 0, 0)
C_WHITE = c565(255, 255, 255)
C_CYAN = c565(0, 255, 220)
C_MAGENTA = c565(255, 0, 180)
C_YELLOW = c565(255, 220, 0)
C_RED = c565(255, 40, 40)
C_GREEN = c565(0, 255, 80)
C_DARK = c565(25, 25, 40)
C_OVER = c565(10, 5, 20)
C_CUT = c565(255, 225, 175)

buf = bytearray(FBSIZE)
fb_fd = None
fb_mm = None
_packed = {}
_clip_side = None
_clip_x = 0


def packed(color):
    value = _packed.get(color)
    if value is None:
        value = struct.pack("<H", color)
        _packed[color] = value
    return value


def open_framebuffer(path):
    global fb_fd, fb_mm
    flags = os.O_RDWR
    if path != "/dev/fb1":
        flags |= os.O_CREAT
    fb_fd = os.open(path, flags, 0o644)
    if path != "/dev/fb1":
        os.ftruncate(fb_fd, FBSIZE)
    fb_mm = mmap.mmap(
        fb_fd, FBSIZE, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ
    )


def close_framebuffer():
    global fb_fd, fb_mm
    if fb_mm is not None:
        fb_mm.close()
        fb_mm = None
    if fb_fd is not None:
        os.close(fb_fd)
        fb_fd = None


def sp(x, y, color):
    if not (0 <= x < W and 0 <= y < H):
        return
    if _clip_side == "left" and x >= _clip_x:
        return
    if _clip_side == "right" and x < _clip_x:
        return
    pos = (y * W + x) * BPP
    buf[pos : pos + 2] = packed(color)


def rect(x1, y1, x2, y2, color):
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(W, int(x2)), min(H, int(y2))
    if _clip_side == "left":
        x2 = min(x2, _clip_x)
    elif _clip_side == "right":
        x1 = max(x1, _clip_x)
    if x2 <= x1 or y2 <= y1:
        return
    row = packed(color) * (x2 - x1)
    for y in range(y1, y2):
        pos = (y * W + x1) * BPP
        buf[pos : pos + len(row)] = row


def ellipse(cx, cy, rx, ry, color):
    if rx <= 0 or ry <= 0:
        return
    for dy in range(-ry, ry + 1):
        ratio = 1.0 - (dy * dy) / float(ry * ry)
        span = int(rx * math.sqrt(max(0.0, ratio)))
        rect(cx - span, cy + dy, cx + span + 1, cy + dy + 1, color)


def line(x1, y1, x2, y2, color, width=1):
    dx, dy = x2 - x1, y2 - y1
    steps = max(abs(dx), abs(dy), 1)
    radius = max(0, width // 2)
    for i in range(steps + 1):
        x = int(x1 + dx * i / float(steps))
        y = int(y1 + dy * i / float(steps))
        if radius:
            ellipse(x, y, radius, radius, color)
        else:
            sp(x, y, color)


def triangle(p1, p2, p3, color):
    min_x = max(0, min(p1[0], p2[0], p3[0]))
    max_x = min(W - 1, max(p1[0], p2[0], p3[0]))
    min_y = max(0, min(p1[1], p2[1], p3[1]))
    max_y = min(H - 1, max(p1[1], p2[1], p3[1]))

    def edge(a, b, p):
        return (p[0] - a[0]) * (b[1] - a[1]) - (p[1] - a[1]) * (b[0] - a[0])

    area = edge(p1, p2, p3)
    if area == 0:
        return
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            p = (x, y)
            a, b, c = edge(p1, p2, p), edge(p2, p3, p), edge(p3, p1, p)
            if (a >= 0 and b >= 0 and c >= 0) or (a <= 0 and b <= 0 and c <= 0):
                sp(x, y, color)


def flush():
    fb_mm.seek(0)
    fb_mm.write(buf)


# ---- Recognisable Malaysian pixel-art targets ----


def rambutan(cx, cy):
    dark, red, coral = c565(145, 8, 35), c565(225, 20, 55), c565(255, 95, 90)
    for degree in range(0, 360, 30):
        angle = math.radians(degree)
        x1, y1 = cx + int(math.cos(angle) * 15), cy + int(math.sin(angle) * 15)
        x2, y2 = cx + int(math.cos(angle) * 25), cy + int(math.sin(angle) * 25)
        line(x1, y1, x2, y2, dark, 3)
    ellipse(cx, cy, 17, 17, red)
    ellipse(cx - 5, cy - 5, 7, 6, coral)
    line(cx + 2, cy - 16, cx + 9, cy - 25, c565(25, 170, 55), 3)


def durian(cx, cy):
    skin, light, dark = c565(155, 145, 30), c565(215, 205, 65), c565(95, 100, 20)
    for degree in range(0, 360, 30):
        angle = math.radians(degree)
        base = (cx + int(math.cos(angle) * 17), cy + int(math.sin(angle) * 15))
        side = math.radians(degree + 10)
        p2 = (cx + int(math.cos(side) * 12), cy + int(math.sin(side) * 11))
        tip = (cx + int(math.cos(angle) * 26), cy + int(math.sin(angle) * 23))
        triangle(base, p2, tip, skin)
    ellipse(cx, cy, 19, 16, skin)
    for ox, oy in [(-10, -5), (0, -8), (10, -4), (-7, 6), (5, 5)]:
        triangle((cx + ox - 3, cy + oy + 3), (cx + ox + 3, cy + oy + 3),
                 (cx + ox, cy + oy - 4), light)
    line(cx, cy - 15, cx + 4, cy - 23, dark, 4)


def mangosteen(cx, cy):
    purple, light, green = c565(75, 5, 105), c565(140, 25, 165), c565(25, 155, 45)
    ellipse(cx, cy + 2, 19, 18, purple)
    ellipse(cx - 6, cy - 4, 8, 7, light)
    triangle((cx, cy - 14), (cx - 17, cy - 10), (cx - 5, cy - 3), green)
    triangle((cx, cy - 14), (cx + 17, cy - 10), (cx + 5, cy - 3), green)
    triangle((cx, cy - 16), (cx - 5, cy - 4), (cx + 7, cy - 5), green)


def limau(cx, cy):
    dark, lime, shine = c565(30, 135, 25), c565(105, 215, 45), c565(205, 255, 95)
    ellipse(cx, cy + 2, 18, 17, dark)
    ellipse(cx - 2, cy, 16, 15, lime)
    ellipse(cx - 7, cy - 6, 5, 4, shine)
    triangle((cx + 3, cy - 15), (cx + 21, cy - 22), (cx + 14, cy - 8), dark)


def nasi_lemak(cx, cy):
    leaf, leaf2 = c565(20, 105, 45), c565(35, 165, 65)
    rice, sambal, yolk = c565(250, 245, 220), c565(190, 35, 25), c565(255, 205, 20)
    triangle((cx - 25, cy + 18), (cx + 26, cy + 18), (cx, cy - 25), leaf)
    triangle((cx - 20, cy + 15), (cx + 20, cy + 15), (cx, cy - 18), leaf2)
    ellipse(cx - 4, cy + 1, 13, 10, rice)
    ellipse(cx + 11, cy + 8, 8, 6, sambal)
    ellipse(cx - 10, cy - 1, 8, 6, C_WHITE)
    ellipse(cx - 10, cy - 1, 3, 3, yolk)
    line(cx + 5, cy - 4, cx + 19, cy - 9, c565(100, 65, 25), 4)


def roti_canai(cx, cy):
    plate, edge = c565(205, 220, 225), c565(90, 120, 135)
    bread, toast = c565(235, 190, 95), c565(175, 105, 35)
    ellipse(cx, cy + 5, 25, 13, edge)
    ellipse(cx, cy + 3, 22, 11, plate)
    ellipse(cx, cy, 19, 12, bread)
    line(cx - 13, cy - 4, cx + 11, cy + 5, toast, 2)
    line(cx - 9, cy + 6, cx + 13, cy - 2, toast, 2)
    ellipse(cx - 6, cy - 3, 3, 2, c565(255, 225, 145))


def teh_tarik(cx, cy):
    glass, tea, foam = c565(190, 225, 245), c565(175, 85, 25), c565(255, 240, 190)
    rect(cx - 15, cy - 16, cx + 13, cy + 17, glass)
    triangle((cx - 12, cy - 12), (cx + 10, cy - 12), (cx + 8, cy + 14), tea)
    ellipse(cx - 1, cy - 12, 12, 5, foam)
    line(cx + 13, cy - 8, cx + 24, cy - 5, glass, 3)
    line(cx + 24, cy - 5, cx + 23, cy + 9, glass, 3)
    line(cx + 23, cy + 9, cx + 13, cy + 11, glass, 3)
    line(cx - 6, cy - 21, cx - 3, cy - 27, C_WHITE, 2)
    line(cx + 3, cy - 21, cx + 6, cy - 27, C_WHITE, 2)


def satay(cx, cy):
    stick, meat, char = c565(235, 190, 80), c565(180, 95, 30), c565(75, 40, 18)
    for offset in (-12, 0, 12):
        line(cx + offset - 11, cy + 23, cx + offset + 10, cy - 23, stick, 2)
        for step in (-10, 0, 10):
            px = cx + offset + int(step * 0.45)
            py = cy - step
            ellipse(px, py, 6, 5, meat)
            rect(px - 2, py - 4, px + 2, py - 1, char)


def curry_puff(cx, cy):
    edge, pastry, shine = c565(155, 80, 20), c565(235, 155, 45), c565(255, 210, 90)
    ellipse(cx, cy + 3, 23, 15, edge)
    triangle((cx - 21, cy + 1), (cx + 21, cy + 1), (cx, cy - 14), pastry)
    rect(cx - 20, cy, cx + 21, cy + 11, pastry)
    line(cx - 18, cy + 9, cx + 18, cy + 9, edge, 3)
    for x in range(cx - 15, cx + 16, 7):
        line(x, cy + 7, x + 3, cy + 11, edge, 2)
    line(cx - 12, cy - 3, cx + 7, cy - 9, shine, 2)


def kuih_lapis(cx, cy):
    plate = c565(195, 215, 225)
    ellipse(cx, cy + 17, 24, 7, plate)
    rect(cx - 18, cy - 17, cx + 18, cy + 15, c565(245, 245, 220))
    colors = [c565(230, 55, 90), c565(250, 170, 55), c565(65, 185, 85), c565(160, 70, 180)]
    y = cy - 15
    for color in colors:
        rect(cx - 16, y, cx + 16, y + 6, color)
        y += 7
    line(cx - 18, cy - 17, cx - 18, cy + 14, c565(100, 70, 80), 2)


def bomb(cx, cy):
    shell, light = c565(35, 35, 45), c565(85, 90, 105)
    ellipse(cx, cy + 3, 19, 19, shell)
    ellipse(cx - 6, cy - 4, 7, 6, light)
    rect(cx - 5, cy - 20, cx + 6, cy - 14, c565(120, 80, 35))
    line(cx + 2, cy - 20, cx + 12, cy - 28, c565(210, 120, 30), 3)
    ellipse(cx + 14, cy - 29, 4, 4, C_YELLOW)
    sp(cx + 14, cy - 29, C_WHITE)
    line(cx - 7, cy + 1, cx - 2, cy + 6, C_RED, 3)
    line(cx + 4, cy + 1, cx + 9, cy + 6, C_RED, 3)


FOOD = [
    ("RAMBUTAN", rambutan),
    ("DURIAN", durian),
    ("MANGOSTEEN", mangosteen),
    ("LIMAU", limau),
    ("NASI LEMAK", nasi_lemak),
    ("ROTI CANAI", roti_canai),
    ("TEH TARIK", teh_tarik),
    ("SATAY", satay),
    ("CURRY PUFF", curry_puff),
    ("KUIH LAPIS", kuih_lapis),
]


def draw_target(cx, cy, drawer, half=None):
    global _clip_side, _clip_x
    _clip_side, _clip_x = half, int(cx)
    drawer(int(cx), int(cy))
    _clip_side = None


def draw_sliced(left_x, left_y, right_x, right_y, drawer):
    draw_target(left_x, left_y, drawer, "left")
    draw_target(right_x, right_y, drawer, "right")
    rect(left_x - 2, left_y - 16, left_x + 1, left_y + 17, C_CUT)
    rect(right_x, right_y - 16, right_x + 3, right_y + 17, C_CUT)


FONT = {
    "A":["01110","10001","10001","11111","10001","10001","10001"],
    "B":["11110","10001","10001","11110","10001","10001","11110"],
    "C":["01110","10001","10000","10000","10000","10001","01110"],
    "D":["11110","10001","10001","10001","10001","10001","11110"],
    "E":["11111","10000","10000","11110","10000","10000","11111"],
    "F":["11111","10000","10000","11110","10000","10000","10000"],
    "G":["01110","10001","10000","10111","10001","10001","01110"],
    "H":["10001","10001","10001","11111","10001","10001","10001"],
    "I":["01110","00100","00100","00100","00100","00100","01110"],
    "J":["00111","00010","00010","00010","00010","10010","01100"],
    "K":["10001","10010","10100","11000","10100","10010","10001"],
    "L":["10000","10000","10000","10000","10000","10000","11111"],
    "M":["10001","11011","10101","10101","10001","10001","10001"],
    "N":["10001","10001","11001","10101","10011","10001","10001"],
    "O":["01110","10001","10001","10001","10001","10001","01110"],
    "P":["11110","10001","10001","11110","10000","10000","10000"],
    "Q":["01110","10001","10001","10001","10101","10010","01101"],
    "R":["11110","10001","10001","11110","10100","10010","10001"],
    "S":["01110","10001","10000","01110","00001","10001","01110"],
    "T":["11111","00100","00100","00100","00100","00100","00100"],
    "U":["10001","10001","10001","10001","10001","10001","01110"],
    "V":["10001","10001","10001","10001","01010","01010","00100"],
    "W":["10001","10001","10001","10101","10101","10101","01010"],
    "X":["10001","10001","01010","00100","01010","10001","10001"],
    "Y":["10001","10001","01010","00100","00100","00100","00100"],
    "Z":["11111","00001","00010","00100","01000","10000","11111"],
    " ":["00000","00000","00000","00000","00000","00000","00000"],
    "0":["01110","10011","10101","10101","10101","11001","01110"],
    "1":["00100","01100","00100","00100","00100","00100","01110"],
    "2":["01110","10001","00001","00010","00100","01000","11111"],
    "3":["01110","10001","00001","00110","00001","10001","01110"],
    "4":["00010","00110","01010","10010","11111","00010","00010"],
    "5":["11111","10000","11110","00001","00001","10001","01110"],
    "6":["00110","01000","10000","11110","10001","10001","01110"],
    "7":["11111","00001","00010","00100","01000","01000","01000"],
    "8":["01110","10001","10001","01110","10001","10001","01110"],
    "9":["01110","10001","10001","01111","00001","00010","01100"],
    ".":["00000","00000","00000","00000","00000","01100","01100"],
    "<":["00010","00100","01000","10000","01000","00100","00010"],
    "!":["00100","00100","00100","00100","00100","00000","00100"],
    "-":["00000","00000","00000","11111","00000","00000","00000"],
    "+":["00000","00100","00100","11111","00100","00100","00000"],
    ":":["00000","01100","01100","00000","01100","01100","00000"],
}


def text(value, x, y, color, scale=2):
    cursor = x
    for char in value.upper():
        glyph = FONT.get(char)
        if glyph:
            for row_index, row in enumerate(glyph):
                for col_index, bit in enumerate(row):
                    if bit == "1":
                        rect(cursor + col_index * scale, y + row_index * scale,
                             cursor + (col_index + 1) * scale,
                             y + (row_index + 1) * scale, color)
        cursor += 6 * scale


def text_width(value, scale=2):
    return len(value) * 6 * scale


def outlined(value, x, y, color, scale=2):
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            if ox or oy:
                text(value, x + ox, y + oy, C_BLACK, scale)
    text(value, x, y, color, scale)


def build_background():
    background = bytearray(FBSIZE)
    random.seed(77)
    for y in range(H):
        color = c565(8 + int(y * 0.04), 2 + int(y * 0.02), 20 + int(y * 0.08))
        row = packed(color) * W
        pos = y * W * BPP
        background[pos : pos + len(row)] = row

    saved = buf[:]
    buf[:] = background
    for _ in range(55):
        sp(random.randint(0, W - 1), random.randint(0, 100), C_WHITE)
    x = 0
    while x < W:
        width, height = random.randint(15, 35), random.randint(40, 100)
        rect(x, H - 20 - height, x + width, H - 20, c565(15, 8, 30))
        for wy in range(H - 15 - height, H - 25, 8):
            for wx in range(x + 3, x + width - 3, 6):
                if random.random() > 0.4:
                    sp(wx, wy, random.choice((c565(255, 200, 50), C_CYAN, C_MAGENTA)))
        x += width + random.randint(2, 6)
    rect(100, 85, 114, H - 20, c565(20, 10, 40))
    rect(124, 85, 138, H - 20, c565(20, 10, 40))
    sp(107, 80, C_MAGENTA)
    sp(131, 80, C_MAGENTA)
    rect(322, 75, 326, H - 20, c565(35, 18, 55))
    sp(324, 44, C_MAGENTA)
    rect(0, H - 20, W, H - 18, C_CYAN)
    rect(0, H - 18, W, H, c565(8, 5, 15))
    for gx in range(0, W, 25):
        rect(gx, H - 18, gx + 12, H - 16, C_MAGENTA)
    background[:] = buf
    buf[:] = saved
    random.seed()
    return background


def find_touch_device():
    candidates = []
    for name in sorted(os.listdir("/dev/input")) if os.path.isdir("/dev/input") else []:
        if not name.startswith("event"):
            continue
        path = "/dev/input/" + name
        candidates.append(path)
        sys_name = "/sys/class/input/{}/device/name".format(name)
        try:
            with open(sys_name, "r") as handle:
                device_name = handle.read().strip().lower()
            if "touch" in device_name or "ads7846" in device_name or "xpt2046" in device_name:
                return path
        except OSError:
            pass
    return candidates[0] if candidates else None


def map_touch(raw_x, raw_y):
    # Calibrated for this cyberdeck's rotated XPT2046 panel.  The display X
    # axis comes from reversed raw Y, while display Y comes from raw X.
    # Keep this in sync with the Cyberdeck menu and Chinese Lingo.
    screen_x = int((3708 - raw_y) / 3300.0 * W)
    screen_y = int((raw_x - 670) / 2918.0 * H)
    return max(0, min(W - 1, screen_x)), max(0, min(H - 1, screen_y))


def segment_distance(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    amount = ((px - x1) * dx + (py - y1) * dy) / float(dx * dx + dy * dy)
    amount = max(0.0, min(1.0, amount))
    near_x, near_y = x1 + amount * dx, y1 + amount * dy
    return math.hypot(px - near_x, py - near_y)


def run_preview(path):
    open_framebuffer(path)
    background = build_background()
    buf[:] = background
    outlined("MALAYSIAN TARGETS", (W - text_width("MALAYSIAN TARGETS", 2)) // 2,
             10, C_CYAN, 2)
    for index, (name, drawer) in enumerate(FOOD):
        col, row = index % 5, index // 5
        x, y = 48 + col * 96, 95 + row * 125
        draw_target(x, y, drawer)
        label = name if len(name) <= 10 else name[:10]
        text(label, x - text_width(label, 1) // 2, y + 34, C_WHITE, 1)
    flush()
    close_framebuffer()


def main():
    open_framebuffer(os.environ.get("CYBERDECK_FB", "/dev/fb1"))
    background = build_background()
    touch_path = find_touch_device()
    if not touch_path:
        print("No touchscreen found")
        close_framebuffer()
        return
    touch_fd = os.open(touch_path, os.O_RDONLY | os.O_NONBLOCK)

    best_path = os.environ.get(
        "MAKAN_NINJA_BEST",
        os.path.join(os.path.expanduser("~"), ".makan_ninja_best"),
    )
    try:
        with open(best_path, "r") as handle:
            high_score = int(handle.read().strip())
    except (OSError, ValueError):
        high_score = 0

    state = "menu"
    targets = []
    popups = []
    trail = []
    score = 0
    lives = 3
    combo = 0
    combo_frames = 0
    frame = 0
    remaining = 60
    spawn_clock = 0
    spawn_rate = 28
    raw_x = raw_y = -1
    screen_x = screen_y = -1
    touching = False
    previous_point = None

    def reset_game():
        nonlocal targets, popups, trail, score, lives, combo, combo_frames
        nonlocal frame, remaining, spawn_clock, spawn_rate, previous_point
        targets = []
        popups = []
        trail = []
        score = 0
        lives = 3
        combo = 0
        combo_frames = 0
        frame = 0
        remaining = 60
        spawn_clock = 0
        spawn_rate = 28
        previous_point = None

    def spawn_target():
        name, drawer = random.choice(FOOD)
        is_bomb = random.random() < 0.12
        x = float(random.randint(60, W - 60))
        vx = random.uniform(-2.8, 2.8)
        if abs(vx) < 0.8:
            vx = 0.8 if vx >= 0 else -0.8
        vy = random.uniform(-11.5, -9.2)
        return {
            "x": x, "y": float(H + 26), "vx": vx, "vy": vy,
            "name": name, "drawer": bomb if is_bomb else drawer,
            "bomb": is_bomb, "sliced": False, "timer": 0,
            "left_x": x, "left_y": float(H + 26),
            "right_x": x, "right_y": float(H + 26),
            "left_vx": vx - 2.0, "left_vy": vy - 1.0,
            "right_vx": vx + 2.0, "right_vy": vy - 1.0,
        }

    def popup(x, y, value, color):
        popups.append({"x": int(x), "y": float(y), "value": value, "color": color, "life": 28})

    def draw_menu():
        buf[:] = background
        outlined("MAKAN NINJA", (W - text_width("MAKAN NINJA", 3)) // 2, 18, C_CYAN, 3)
        outlined("MALAYSIA", (W - text_width("MALAYSIA", 2)) // 2, 61, C_MAGENTA, 2)
        text("SLASH LOCAL FOOD   AVOID BOMBS",
             (W - text_width("SLASH LOCAL FOOD   AVOID BOMBS", 1)) // 2, 112, C_WHITE, 1)
        outlined("TAP TO START", (W - text_width("TAP TO START", 2)) // 2, 142, C_YELLOW, 2)
        if high_score:
            text("BEST: " + str(high_score),
                 (W - text_width("BEST: " + str(high_score), 1)) // 2, 171, C_GREEN, 1)
        text("< BACK", 10, 5, C_DARK, 1)
        showcase = (FOOD[0], FOOD[1], FOOD[4], FOOD[6], FOOD[7])
        for x, (_, drawer) in zip((48, 145, 240, 335, 430), showcase):
            draw_target(x, 244, drawer)
        for x, label in zip((48, 145, 240, 335, 430), ("RAMBUTAN", "DURIAN", "NASI", "TEH", "SATAY")):
            text(label, x - text_width(label, 1) // 2, 275, C_WHITE, 1)
        flush()

    def draw_game_over():
        buf[:] = background
        rect(70, 70, 410, 244, C_OVER)
        rect(70, 70, 410, 74, C_MAGENTA)
        rect(70, 240, 410, 244, C_MAGENTA)
        outlined("GAME OVER", (W - text_width("GAME OVER", 3)) // 2, 86, C_RED, 3)
        text("SCORE: " + str(score), (W - text_width("SCORE: " + str(score), 2)) // 2,
             137, C_CYAN, 2)
        text("BEST: " + str(high_score), (W - text_width("BEST: " + str(high_score), 2)) // 2,
             167, C_YELLOW, 2)
        text("TAP TO PLAY AGAIN", (W - text_width("TAP TO PLAY AGAIN", 1)) // 2,
             211, C_WHITE, 1)
        text("< BACK", 10, 5, C_DARK, 1)
        flush()

    draw_menu()
    next_frame = time.monotonic()

    try:
        while True:
            pressed = False
            released = False
            stroke_points = []
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
                    if value == 1:
                        touching = True
                        pressed = True
                    elif value == 0:
                        touching = False
                        released = True
                elif event_type == 0 and code == 0 and raw_x >= 0 and raw_y >= 0:
                    screen_x, screen_y = map_touch(raw_x, raw_y)
                    if touching:
                        stroke_points.append((screen_x, screen_y))

            if released:
                previous_point = None
                trail = []

            if state == "menu":
                if pressed and screen_x >= 0:
                    if screen_x < 90 and screen_y < 38:
                        return
                    reset_game()
                    state = "playing"

            elif state == "playing":
                frame += 1
                combo_frames = max(0, combo_frames - 1)
                if combo_frames == 0:
                    combo = 0
                remaining = max(0, 60 - frame // int(FPS))
                if remaining == 0 or lives <= 0:
                    if score > high_score:
                        high_score = score
                        try:
                            with open(best_path, "w") as handle:
                                handle.write(str(high_score))
                        except OSError:
                            pass
                    state = "dead"
                    draw_game_over()
                    continue

                spawn_clock += 1
                if spawn_clock >= spawn_rate:
                    spawn_clock = 0
                    targets.append(spawn_target())
                    if random.random() < min(0.35, frame / 6000.0):
                        targets.append(spawn_target())
                    spawn_rate = max(18, 28 - frame // 300)

                remove = []
                for index, target in enumerate(targets):
                    if target["sliced"]:
                        target["left_x"] += target["left_vx"]
                        target["left_y"] += target["left_vy"]
                        target["left_vy"] += 0.28
                        target["right_x"] += target["right_vx"]
                        target["right_y"] += target["right_vy"]
                        target["right_vy"] += 0.28
                        target["timer"] -= 1
                        if target["timer"] <= 0:
                            remove.append(index)
                    else:
                        target["x"] += target["vx"]
                        target["y"] += target["vy"]
                        target["vy"] += 0.28
                        if target["y"] > H + 45 and target["vy"] > 0:
                            remove.append(index)
                            if not target["bomb"]:
                                lives -= 1
                                popup(W // 2, 145, "MISSED -1", C_RED)
                for index in reversed(remove):
                    targets.pop(index)

                for point in stroke_points:
                    if previous_point is None:
                        previous_point = point
                    trail.append([point[0], point[1], 8])
                    for target in targets:
                        if target["sliced"]:
                            continue
                        distance = segment_distance(
                            target["x"], target["y"], previous_point[0], previous_point[1],
                            point[0], point[1]
                        )
                        if distance > 27:
                            continue
                        target["sliced"] = True
                        target["timer"] = 24
                        target["left_x"] = target["x"] - 3
                        target["right_x"] = target["x"] + 3
                        target["left_y"] = target["right_y"] = target["y"]
                        if target["bomb"]:
                            lives -= 1
                            combo = 0
                            combo_frames = 0
                            popup(point[0] - 32, point[1] - 24, "BOOM -1", C_RED)
                        else:
                            combo += 1
                            combo_frames = 30
                            points = min(combo, 5)
                            score += points
                            popup(point[0] - 18, point[1] - 24, "+" + str(points),
                                  C_YELLOW if combo == 1 else C_MAGENTA)
                    previous_point = point

                for entry in trail:
                    entry[2] -= 1
                trail = [entry for entry in trail if entry[2] > 0]
                for item in popups:
                    item["y"] -= 0.8
                    item["life"] -= 1
                popups = [item for item in popups if item["life"] > 0]

                buf[:] = background
                for x, y, life in trail:
                    radius = 2 + life // 3
                    ellipse(x, y, radius, radius, C_CYAN if life > 4 else C_WHITE)
                for target in targets:
                    if target["sliced"]:
                        if target["bomb"]:
                            draw_target(target["left_x"], target["left_y"], bomb)
                        else:
                            draw_sliced(target["left_x"], target["left_y"],
                                        target["right_x"], target["right_y"], target["drawer"])
                    else:
                        draw_target(target["x"], target["y"], target["drawer"])

                outlined(str(score), 10, 8, C_CYAN, 3)
                timer_text = str(remaining)
                timer_color = C_RED if remaining <= 10 else C_YELLOW if remaining <= 25 else C_WHITE
                outlined(timer_text, (W - text_width(timer_text, 2)) // 2, 8, timer_color, 2)
                if combo > 1 and combo_frames:
                    combo_text = str(combo) + "X"
                    outlined(combo_text, (W - text_width(combo_text, 2)) // 2, 39, C_YELLOW, 2)
                for index in range(3):
                    color = C_RED if index < lives else c565(40, 40, 60)
                    ellipse(W - 14 - index * 25, 12, 8, 7, color)
                for item in popups:
                    outlined(item["value"], item["x"], int(item["y"]), item["color"], 1)
                flush()

            elif state == "dead":
                if pressed and screen_x >= 0:
                    if screen_x < 90 and screen_y < 38:
                        state = "menu"
                        draw_menu()
                    else:
                        reset_game()
                        state = "playing"

            next_frame += FRAME_TIME
            delay = next_frame - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            elif delay < -0.25:
                next_frame = time.monotonic()
    finally:
        os.close(touch_fd)
        close_framebuffer()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--preview":
        run_preview(sys.argv[2])
    else:
        main()
