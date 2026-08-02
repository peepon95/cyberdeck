#!/usr/bin/env python3
"""Chinese Lingo - offline simplified Chinese stroke trainer for Cyberdeck OS."""

import argparse
import json
import math
import mmap
import os
import select
import struct
import sys
import time


W, H, BPP = 480, 320, 2
FBSIZE = W * H * BPP
PRACTICE_X, PRACTICE_Y, PRACTICE_SIZE = 12, 54, 244
ASSET_INSET = 4
APP_VERSION = "1.2"


def c565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


BG = c565(8, 8, 18)
PANEL = c565(18, 20, 38)
PANEL_LIGHT = c565(31, 35, 58)
CYAN = c565(0, 255, 220)
CYAN_DIM = c565(0, 95, 88)
MAGENTA = c565(255, 0, 180)
GREEN = c565(0, 255, 90)
GREEN_DIM = c565(0, 105, 45)
YELLOW = c565(255, 220, 0)
RED = c565(255, 55, 65)
WHITE = c565(245, 247, 255)
MUTED = c565(112, 120, 145)
GRID = c565(50, 57, 79)
GHOST = c565(56, 63, 86)
BLACK = c565(0, 0, 0)


FONT = {
    "A": ["01110","10001","10001","11111","10001","10001","10001"],
    "B": ["11110","10001","10001","11110","10001","10001","11110"],
    "C": ["01110","10001","10000","10000","10000","10001","01110"],
    "D": ["11110","10001","10001","10001","10001","10001","11110"],
    "E": ["11111","10000","10000","11110","10000","10000","11111"],
    "F": ["11111","10000","10000","11110","10000","10000","10000"],
    "G": ["01110","10001","10000","10111","10001","10001","01110"],
    "H": ["10001","10001","10001","11111","10001","10001","10001"],
    "I": ["01110","00100","00100","00100","00100","00100","01110"],
    "J": ["00111","00010","00010","00010","00010","10010","01100"],
    "K": ["10001","10010","10100","11000","10100","10010","10001"],
    "L": ["10000","10000","10000","10000","10000","10000","11111"],
    "M": ["10001","11011","10101","10101","10001","10001","10001"],
    "N": ["10001","10001","11001","10101","10011","10001","10001"],
    "O": ["01110","10001","10001","10001","10001","10001","01110"],
    "P": ["11110","10001","10001","11110","10000","10000","10000"],
    "Q": ["01110","10001","10001","10001","10101","10010","01101"],
    "R": ["11110","10001","10001","11110","10100","10010","10001"],
    "S": ["01110","10001","10000","01110","00001","10001","01110"],
    "T": ["11111","00100","00100","00100","00100","00100","00100"],
    "U": ["10001","10001","10001","10001","10001","10001","01110"],
    "V": ["10001","10001","10001","10001","01010","01010","00100"],
    "W": ["10001","10001","10001","10101","10101","10101","01010"],
    "X": ["10001","10001","01010","00100","01010","10001","10001"],
    "Y": ["10001","10001","01010","00100","00100","00100","00100"],
    "Z": ["11111","00001","00010","00100","01000","10000","11111"],
    "0": ["01110","10011","10101","10101","10101","11001","01110"],
    "1": ["00100","01100","00100","00100","00100","00100","01110"],
    "2": ["01110","10001","00001","00010","00100","01000","11111"],
    "3": ["01110","10001","00001","00110","00001","10001","01110"],
    "4": ["00010","00110","01010","10010","11111","00010","00010"],
    "5": ["11111","10000","11110","00001","00001","10001","01110"],
    "6": ["00110","01000","10000","11110","10001","10001","01110"],
    "7": ["11111","00001","00010","00100","01000","01000","01000"],
    "8": ["01110","10001","10001","01110","10001","10001","01110"],
    "9": ["01110","10001","10001","01111","00001","00010","01100"],
    " ": ["00000","00000","00000","00000","00000","00000","00000"],
    ".": ["00000","00000","00000","00000","00000","01100","01100"],
    ":": ["00000","01100","01100","00000","01100","01100","00000"],
    "-": ["00000","00000","00000","11111","00000","00000","00000"],
    "+": ["00000","00100","00100","11111","00100","00100","00000"],
    "<": ["00010","00100","01000","10000","01000","00100","00010"],
    ">": ["01000","00100","00010","00001","00010","00100","01000"],
    "/": ["00001","00010","00010","00100","01000","01000","10000"],
    "!": ["00100","00100","00100","00100","00100","00000","00100"],
}


class Canvas(object):
    def __init__(self, framebuffer="/dev/fb1"):
        self.buffer = bytearray(FBSIZE)
        self.framebuffer = framebuffer
        self.fd = None
        self.mm = None
        if os.path.exists(framebuffer):
            self.fd = os.open(framebuffer, os.O_RDWR)
            self.mm = mmap.mmap(
                self.fd, FBSIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE
            )

    @staticmethod
    def packed(color):
        return struct.pack("<H", color)

    def close(self):
        if self.mm is not None:
            self.mm.close()
        if self.fd is not None:
            os.close(self.fd)

    def pixel(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            pos = (y * W + x) * BPP
            self.buffer[pos:pos + 2] = self.packed(color)

    def fill(self, color):
        self.buffer[:] = self.packed(color) * (W * H)

    def rect(self, x1, y1, x2, y2, color):
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(W, x2), min(H, y2)
        if x2 <= x1 or y2 <= y1:
            return
        row = self.packed(color) * (x2 - x1)
        for y in range(y1, y2):
            pos = (y * W + x1) * BPP
            self.buffer[pos:pos + len(row)] = row

    def border(self, x1, y1, x2, y2, color, width=2):
        self.rect(x1, y1, x2, y1 + width, color)
        self.rect(x1, y2 - width, x2, y2, color)
        self.rect(x1, y1, x1 + width, y2, color)
        self.rect(x2 - width, y1, x2, y2, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        radius = max(0, width // 2)
        while True:
            if radius:
                self.rect(x0 - radius, y0 - radius, x0 + radius + 1, y0 + radius + 1, color)
            else:
                self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def text(self, text, x, y, color, scale=2):
        cursor = x
        for char in text.upper():
            glyph = FONT.get(char, FONT[" "])
            for row_index, row in enumerate(glyph):
                for column_index, bit in enumerate(row):
                    if bit == "1":
                        self.rect(
                            cursor + column_index * scale,
                            y + row_index * scale,
                            cursor + (column_index + 1) * scale,
                            y + (row_index + 1) * scale,
                            color,
                        )
            cursor += 6 * scale

    def centered_text(self, text, y, color, scale=2):
        self.text(text, (W - text_width(text, scale)) // 2, y, color, scale)

    def present(self):
        if self.mm is not None:
            self.mm.seek(0)
            self.mm.write(self.buffer)

    def present_rect(self, x1, y1, x2, y2):
        if self.mm is None:
            return
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(W, x2), min(H, y2)
        for y in range(y1, y2):
            start = (y * W + x1) * BPP
            end = (y * W + x2) * BPP
            self.mm[start:end] = self.buffer[start:end]

    def save_ppm(self, path):
        with open(path, "wb") as handle:
            handle.write(("P6\n%d %d\n255\n" % (W, H)).encode("ascii"))
            rgb = bytearray(W * H * 3)
            for index in range(W * H):
                value = self.buffer[index * 2] | (self.buffer[index * 2 + 1] << 8)
                rgb[index * 3] = ((value >> 11) & 31) * 255 // 31
                rgb[index * 3 + 1] = ((value >> 5) & 63) * 255 // 63
                rgb[index * 3 + 2] = (value & 31) * 255 // 31
            handle.write(rgb)


def text_width(text, scale=2):
    return len(text) * 6 * scale


def wrap_text(text, max_chars):
    words = text.upper().split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def button(canvas, x1, y1, x2, y2, label, color=CYAN, enabled=True):
    edge = color if enabled else GRID
    canvas.rect(x1, y1, x2, y2, PANEL_LIGHT if enabled else PANEL)
    canvas.border(x1, y1, x2, y2, edge, 2)
    label_color = WHITE if enabled else MUTED
    scale = 1 if text_width(label, 2) > (x2 - x1 - 8) else 2
    tx = x1 + ((x2 - x1) - text_width(label, scale)) // 2
    ty = y1 + ((y2 - y1) - 7 * scale) // 2
    canvas.text(label, tx, ty, label_color, scale)


def point_in(point, rect):
    x, y = point
    x1, y1, x2, y2 = rect
    return x1 <= x < x2 and y1 <= y < y2


class TouchReader(object):
    EVENT_SIZE = 16

    def __init__(self, path="/dev/input/event0"):
        self.path = path
        self.fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        self.raw_x = -1
        self.raw_y = -1
        self.down = False
        self.last_point = None
        self.pending_down = False
        self.pending_up = False

    def close(self):
        os.close(self.fd)

    @staticmethod
    def map_touch(raw_x, raw_y):
        x = int((3708 - raw_y) / 3300.0 * W)
        y = int((raw_x - 670) / 2918.0 * H)
        return max(0, min(W - 1, x)), max(0, min(H - 1, y))

    def poll(self, timeout=0.05):
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return []
        output = []
        while True:
            try:
                data = os.read(self.fd, self.EVENT_SIZE)
            except OSError:
                break
            if len(data) != self.EVENT_SIZE:
                break
            _, _, event_type, code, value = struct.unpack("IIHHi", data)
            if event_type == 3 and code == 0:
                self.raw_x = value
            elif event_type == 3 and code == 1:
                self.raw_y = value
            elif event_type == 1 and code == 330:
                if value == 1 and not self.down:
                    self.down = True
                    self.pending_down = True
                elif value == 0 and self.down:
                    self.down = False
                    self.pending_up = True
            elif event_type == 0 and code == 0 and self.raw_x >= 0 and self.raw_y >= 0:
                point = self.map_touch(self.raw_x, self.raw_y)
                if self.pending_down:
                    self.pending_down = False
                    self.last_point = point
                    output.append(("down", point))
                elif self.pending_up:
                    self.pending_up = False
                    self.last_point = point
                    output.append(("up", point))
                elif self.down and point != self.last_point:
                    self.last_point = point
                    output.append(("move", point))
        return output

    def wait_tap(self):
        start = None
        while True:
            for event, point in self.poll(0.1):
                if event == "down":
                    start = point
                elif event == "up" and point is not None:
                    return point if start is None else point


def draw_grid(canvas):
    x, y, size = PRACTICE_X, PRACTICE_Y, PRACTICE_SIZE
    canvas.rect(x, y, x + size, y + size, PANEL)
    canvas.border(x, y, x + size, y + size, CYAN_DIM, 2)
    middle_x = x + size // 2
    middle_y = y + size // 2
    canvas.line(middle_x, y + 2, middle_x, y + size - 2, GRID, 1)
    canvas.line(x + 2, middle_y, x + size - 2, middle_y, GRID, 1)
    for offset in range(0, size // 2):
        if offset % 3 == 0:
            canvas.pixel(x + 2 + offset, y + 2 + offset, GRID)
            canvas.pixel(x + size - 3 - offset, y + 2 + offset, GRID)
            canvas.pixel(x + 2 + offset, y + size - 3 - offset, GRID)
            canvas.pixel(x + size - 3 - offset, y + size - 3 - offset, GRID)


def draw_spans(canvas, spans, color, offset_x, offset_y):
    for y, x1, x2 in spans:
        canvas.rect(offset_x + x1, offset_y + y, offset_x + x2, offset_y + y + 1, color)


def draw_character(canvas, character_data, stroke_colors, offset_x=None, offset_y=None):
    if offset_x is None:
        offset_x = PRACTICE_X + ASSET_INSET
    if offset_y is None:
        offset_y = PRACTICE_Y + ASSET_INSET
    for index, spans in enumerate(character_data["strokes"]):
        color = stroke_colors[index] if index < len(stroke_colors) else GHOST
        if color is not None:
            draw_spans(canvas, spans, color, offset_x, offset_y)


def draw_median(canvas, median, color, width=3):
    offset_x = PRACTICE_X + ASSET_INSET
    offset_y = PRACTICE_Y + ASSET_INSET
    for first, second in zip(median, median[1:]):
        canvas.line(
            offset_x + first[0], offset_y + first[1],
            offset_x + second[0], offset_y + second[1],
            color, width,
        )
    if median:
        start = median[0]
        canvas.rect(
            offset_x + start[0] - 3, offset_y + start[1] - 3,
            offset_x + start[0] + 4, offset_y + start[1] + 4, YELLOW,
        )


def distance(first, second):
    return math.hypot(first[0] - second[0], first[1] - second[1])


def path_length(points):
    return sum(distance(a, b) for a, b in zip(points, points[1:]))


def resample(points, count=24):
    if not points:
        return []
    filtered = [points[0]]
    for point in points[1:]:
        if distance(point, filtered[-1]) >= 1.0:
            filtered.append(point)
    if len(filtered) == 1:
        return filtered * count
    lengths = [0.0]
    for first, second in zip(filtered, filtered[1:]):
        lengths.append(lengths[-1] + distance(first, second))
    total = lengths[-1]
    if total <= 0:
        return [filtered[0]] * count
    result = []
    segment = 0
    for index in range(count):
        target = total * index / float(count - 1)
        while segment + 1 < len(lengths) and lengths[segment + 1] < target:
            segment += 1
        if segment + 1 >= len(filtered):
            result.append(filtered[-1])
            continue
        span = lengths[segment + 1] - lengths[segment]
        ratio = 0.0 if span == 0 else (target - lengths[segment]) / span
        first, second = filtered[segment], filtered[segment + 1]
        result.append((
            first[0] + (second[0] - first[0]) * ratio,
            first[1] + (second[1] - first[1]) * ratio,
        ))
    return result


def grade_stroke(user_points, target_points, forgiving=False):
    if len(user_points) < 2 or len(target_points) < 2:
        return False, "DRAW THE FULL STROKE"
    user = resample(user_points)
    target = resample(target_points)
    target_length = path_length(target_points)
    user_length = path_length(user_points)
    short = target_length < 28
    if forgiving:
        start_limit = 48
        end_limit = 65
        shape_limit = 42
    else:
        start_limit = 32 if not short else 38
        end_limit = 40 if not short else 42
        shape_limit = 31 if short else 27
    if distance(user[0], target[0]) > start_limit:
        return False, "START AT THE YELLOW DOT"
    if forgiving:
        # Guided mode intentionally checks stroke order rather than penmanship.
        # Resistive-screen calibration makes exact endpoints unreliable near
        # the edges, especially for compound corner strokes such as 口 stroke 2.
        if not short and user_length < target_length * 0.30:
            return False, "MAKE THE STROKE LONGER"
        target_dx = target[min(5, len(target) - 1)][0] - target[0][0]
        target_dy = target[min(5, len(target) - 1)][1] - target[0][1]
        user_dx = user[min(5, len(user) - 1)][0] - user[0][0]
        user_dy = user[min(5, len(user) - 1)][1] - user[0][1]
        if target_dx * user_dx + target_dy * user_dy < 0:
            return False, "CHECK THE STROKE DIRECTION"
        return True, "CORRECT"
    if distance(user[-1], target[-1]) > end_limit:
        return False, "FOLLOW THE STROKE TO THE END"
    minimum_ratio = 0.35 if forgiving else 0.45
    maximum_ratio = 3.0 if forgiving else 2.35
    if not short and user_length < target_length * minimum_ratio:
        return False, "MAKE THE STROKE LONGER"
    if user_length > max(42, target_length * maximum_ratio):
        return False, "KEEP CLOSER TO THE GUIDE"
    mean_error = sum(distance(a, b) for a, b in zip(user, target)) / len(target)
    if mean_error > shape_limit:
        return False, "FOLLOW THE STROKE SHAPE"
    forward = distance(user[0], target[0]) + distance(user[-1], target[-1])
    reverse = distance(user[0], target[-1]) + distance(user[-1], target[0])
    if not short and reverse + 15 < forward:
        return False, "CHECK THE STROKE DIRECTION"
    return True, "CORRECT"


class Progress(object):
    def __init__(self, path, level_count):
        self.path = path
        self.level_count = level_count
        self.data = {"unlocked": 0, "completed": {}, "xp": 0}
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                saved = json.load(handle)
            if isinstance(saved, dict):
                self.data.update(saved)
        except (OSError, ValueError):
            pass
        self.data["unlocked"] = max(0, min(self.level_count - 1, int(self.data["unlocked"])))

    def save(self):
        temp = self.path + ".tmp"
        with open(temp, "w", encoding="utf-8") as handle:
            json.dump(self.data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, self.path)

    def level_score(self, level_id):
        return len(set(self.data["completed"].get(level_id, [])))

    def complete_character(self, level_index, level_id, char):
        completed = self.data["completed"].setdefault(level_id, [])
        new = char not in completed
        if new:
            completed.append(char)
            self.data["xp"] = int(self.data.get("xp", 0)) + 10
        if len(set(completed)) >= 4 and level_index + 1 < self.level_count:
            self.data["unlocked"] = max(self.data["unlocked"], level_index + 1)
        self.save()
        return new


class HanziQuest(object):
    def __init__(self, asset_path, progress_path, framebuffer="/dev/fb1", touch_path="/dev/input/event0"):
        with open(asset_path, "r", encoding="utf-8") as handle:
            bundle = json.load(handle)
        self.course = bundle["course"]
        self.characters = bundle["characters"]
        self.canvas = Canvas(framebuffer)
        self.progress = Progress(progress_path, len(self.course))
        self.touch = TouchReader(touch_path) if os.path.exists(touch_path) else None
        self.running = True

    def close(self):
        if self.touch:
            self.touch.close()
        self.canvas.close()

    def header(self, title, subtitle=""):
        self.canvas.fill(BG)
        self.canvas.text("< BACK", 8, 8, MUTED, 1)
        self.canvas.text(title, 76, 7, CYAN, 2)
        if subtitle:
            self.canvas.text(subtitle, 300, 11, MAGENTA, 1)
        self.canvas.rect(8, 35, W - 8, 37, CYAN_DIM)

    def course_screen(self):
        self.canvas.fill(BG)
        self.canvas.text("< BACK", 8, 10, MUTED, 1)
        self.canvas.centered_text("CHINESE LINGO", 8, CYAN, 3)
        self.canvas.centered_text("LEARN ONE STROKE AT A TIME", 36, MAGENTA, 1)
        self.canvas.text("XP " + str(self.progress.data.get("xp", 0)), 395, 10, YELLOW, 1)
        y = 58
        zones = []
        for index, level in enumerate(self.course):
            unlocked = index <= self.progress.data["unlocked"]
            score = self.progress.level_score(level["id"])
            color = [CYAN, MAGENTA, GREEN, YELLOW, c565(255, 120, 20)][index]
            self.canvas.rect(18, y, 462, y + 43, PANEL if unlocked else c565(13, 14, 27))
            self.canvas.border(18, y, 462, y + 43, color if unlocked else GRID, 2)
            badge_color = color if unlocked else GRID
            self.canvas.rect(27, y + 8, 53, y + 34, badge_color)
            self.canvas.text(str(index + 1), 34, y + 14, BLACK if unlocked else MUTED, 2)
            self.canvas.text(level["name"], 66, y + 7, WHITE if unlocked else MUTED, 2)
            status = ("%d/4" % score) if unlocked else "LOCKED"
            self.canvas.text(status, 388, y + 17, color if unlocked else MUTED, 1)
            self.canvas.text(level["description"], 67, y + 28, MUTED, 1)
            if unlocked:
                zones.append(((18, y, 462, y + 43), index))
            y += 49
        self.canvas.centered_text("COMPLETE A LEVEL TO UNLOCK THE NEXT", 307, MUTED, 1)
        self.canvas.text("V" + APP_VERSION, 446, 307, GRID, 1)
        self.canvas.present()
        return zones

    def study_screen(self, level_index, character_index):
        level = self.course[level_index]
        char, meaning = level["characters"][character_index]
        data = self.characters[char]
        self.header("LEVEL %d" % (level_index + 1), "%d OF 4" % (character_index + 1))
        draw_grid(self.canvas)
        draw_character(self.canvas, data, [WHITE] * len(data["strokes"]))
        self.canvas.text(data["pinyin"], 283, 63, YELLOW, 3)
        for line_index, line in enumerate(wrap_text(meaning, 15)[:3]):
            self.canvas.text(line, 283, 94 + line_index * 18, WHITE, 2)
        self.canvas.text("%d STROKES" % len(data["strokes"]), 283, 157, MUTED, 1)
        button(self.canvas, 278, 183, 466, 226, "WATCH", MAGENTA)
        button(self.canvas, 278, 239, 466, 290, "PRACTICE", GREEN)
        self.canvas.present()
        return char

    def watch(self, char):
        data = self.characters[char]
        for current in range(len(data["strokes"])):
            self.header("WATCH", "%d OF %d" % (current + 1, len(data["strokes"])))
            draw_grid(self.canvas)
            colors = []
            for index in range(len(data["strokes"])):
                if index < current:
                    colors.append(WHITE)
                elif index == current:
                    colors.append(CYAN)
                else:
                    colors.append(GHOST)
            draw_character(self.canvas, data, colors)
            draw_median(self.canvas, data["medians"][current], MAGENTA, 2)
            self.canvas.text(data["pinyin"], 283, 72, YELLOW, 3)
            self.canvas.text("FOLLOW THE", 283, 126, WHITE, 2)
            self.canvas.text("YELLOW DOT", 283, 146, WHITE, 2)
            self.canvas.text("THEN THE", 283, 180, MUTED, 2)
            self.canvas.text("PINK PATH", 283, 200, MUTED, 2)
            self.canvas.present()
            time.sleep(0.8)
        time.sleep(0.5)

    def practice_screen(self, char, stroke_index, message="", misses=0):
        data = self.characters[char]
        self.header("PRACTICE", "%d OF %d" % (stroke_index + 1, len(data["strokes"])))
        draw_grid(self.canvas)
        colors = []
        for index in range(len(data["strokes"])):
            colors.append(GREEN if index < stroke_index else GHOST)
        draw_character(self.canvas, data, colors)
        if stroke_index < len(data["strokes"]):
            hint_color = CYAN_DIM if misses < 2 else MAGENTA
            draw_median(self.canvas, data["medians"][stroke_index], hint_color, 2)
        self.canvas.text(data["pinyin"], 283, 61, YELLOW, 3)
        self.canvas.text("STROKE %d" % (stroke_index + 1), 283, 103, WHITE, 2)
        self.canvas.text("START AT", 283, 137, MUTED, 1)
        self.canvas.text("YELLOW DOT", 283, 151, YELLOW, 1)
        if message:
            lines = wrap_text(message, 21)
            for index, line in enumerate(lines[:3]):
                self.canvas.text(line, 283, 181 + index * 13, GREEN if message == "CORRECT" else RED, 1)
        button(self.canvas, 280, 249, 368, 290, "REPLAY", MAGENTA)
        button(self.canvas, 378, 249, 466, 290, "RESET", CYAN)
        self.canvas.present()

    def complete_screen(self, level_index, char, new_xp):
        self.canvas.fill(BG)
        self.canvas.centered_text("CHARACTER COMPLETE", 30, GREEN, 2)
        data = self.characters[char]
        draw_grid(self.canvas)
        draw_character(self.canvas, data, [GREEN] * len(data["strokes"]))
        self.canvas.text(data["pinyin"], 283, 78, YELLOW, 3)
        self.canvas.text("ALL STROKES", 283, 128, WHITE, 2)
        self.canvas.text("CORRECT", 283, 150, WHITE, 2)
        self.canvas.text("+10 XP" if new_xp else "PRACTICED", 283, 191, CYAN, 2)
        button(self.canvas, 283, 245, 466, 292, "CONTINUE", GREEN)
        self.canvas.present()

    def level_complete_screen(self, level_index):
        level = self.course[level_index]
        self.canvas.fill(BG)
        self.canvas.centered_text("LEVEL COMPLETE", 50, GREEN, 3)
        self.canvas.centered_text(level["name"], 94, CYAN, 2)
        self.canvas.centered_text("4 CHARACTERS MASTERED", 136, WHITE, 2)
        self.canvas.centered_text("TOTAL XP " + str(self.progress.data["xp"]), 174, YELLOW, 2)
        if level_index + 1 < len(self.course):
            self.canvas.centered_text("NEXT LEVEL UNLOCKED", 214, MAGENTA, 2)
        button(self.canvas, 130, 262, 350, 307, "COURSE MAP", CYAN)
        self.canvas.present()

    def run_practice(self, char):
        data = self.characters[char]
        stroke_index = 0
        misses = 0
        drawing = False
        points = []
        pending_ui = None
        self.practice_screen(char, stroke_index, "", misses)
        if self.touch is None:
            return False
        while self.running and stroke_index < len(data["strokes"]):
            for event, point in self.touch.poll(0.1):
                if point is None:
                    continue
                if event == "down":
                    pending_ui = point
                    if point_in(point, (
                        PRACTICE_X, PRACTICE_Y,
                        PRACTICE_X + PRACTICE_SIZE, PRACTICE_Y + PRACTICE_SIZE
                    )):
                        pending_ui = None
                        drawing = True
                        points = [(point[0] - PRACTICE_X - ASSET_INSET,
                                   point[1] - PRACTICE_Y - ASSET_INSET)]
                elif event == "move" and not drawing and point_in(point, (
                    PRACTICE_X, PRACTICE_Y,
                    PRACTICE_X + PRACTICE_SIZE, PRACTICE_Y + PRACTICE_SIZE
                )):
                    pending_ui = None
                    drawing = True
                    points = [(point[0] - PRACTICE_X - ASSET_INSET,
                               point[1] - PRACTICE_Y - ASSET_INSET)]
                elif event == "move" and drawing:
                    local = (point[0] - PRACTICE_X - ASSET_INSET,
                             point[1] - PRACTICE_Y - ASSET_INSET)
                    if not points or distance(local, points[-1]) >= 2:
                        previous = points[-1]
                        points.append(local)
                        x0 = previous[0] + PRACTICE_X + ASSET_INSET
                        y0 = previous[1] + PRACTICE_Y + ASSET_INSET
                        x1 = local[0] + PRACTICE_X + ASSET_INSET
                        y1 = local[1] + PRACTICE_Y + ASSET_INSET
                        self.canvas.line(x0, y0, x1, y1, MAGENTA, 5)
                        self.canvas.present_rect(
                            min(x0, x1) - 4, min(y0, y1) - 4,
                            max(x0, x1) + 5, max(y0, y1) + 5,
                        )
                elif event == "up" and drawing:
                    drawing = False
                    pending_ui = None
                    local = (point[0] - PRACTICE_X - ASSET_INSET,
                             point[1] - PRACTICE_Y - ASSET_INSET)
                    if not points or distance(local, points[-1]) >= 1:
                        points.append(local)
                    correct, message = grade_stroke(
                        points, data["medians"][stroke_index], forgiving=(misses >= 1)
                    )
                    if correct:
                        stroke_index += 1
                        misses = 0
                        if stroke_index >= len(data["strokes"]):
                            return True
                        self.practice_screen(char, stroke_index, "CORRECT", misses)
                    else:
                        misses += 1
                        self.practice_screen(char, stroke_index, message, misses)
                elif event == "up":
                    tap = point if point is not None else pending_ui
                    pending_ui = None
                    if tap is None:
                        continue
                    if point_in(tap, (0, 0, 68, 38)):
                        return False
                    if point_in(tap, (280, 249, 368, 290)):
                        self.watch(char)
                        self.practice_screen(char, stroke_index, "", misses)
                    elif point_in(tap, (378, 249, 466, 290)):
                        stroke_index, misses = 0, 0
                        self.practice_screen(char, stroke_index, "", misses)
        return False

    def run_level(self, level_index):
        level = self.course[level_index]
        completed = set(self.progress.data["completed"].get(level["id"], []))
        resume_incomplete = 0 < len(completed) < len(level["characters"])
        for character_index, (char, _) in enumerate(level["characters"]):
            if resume_incomplete and char in completed:
                continue
            while self.running:
                self.study_screen(level_index, character_index)
                if self.touch is None:
                    return
                tap = self.touch.wait_tap()
                if point_in(tap, (0, 0, 68, 38)):
                    return
                if point_in(tap, (278, 183, 466, 226)):
                    self.watch(char)
                    continue
                if point_in(tap, (278, 239, 466, 290)):
                    if self.run_practice(char):
                        new_xp = self.progress.complete_character(
                            level_index, level["id"], char
                        )
                        self.complete_screen(level_index, char, new_xp)
                        self.touch.wait_tap()
                        break
        if self.progress.level_score(level["id"]) >= 4:
            self.level_complete_screen(level_index)
            if self.touch:
                self.touch.wait_tap()

    def run(self):
        try:
            while self.running:
                zones = self.course_screen()
                if self.touch is None:
                    return
                tap = self.touch.wait_tap()
                if point_in(tap, (0, 0, 68, 38)):
                    self.running = False
                    return
                for rect, level_index in zones:
                    if point_in(tap, rect):
                        self.run_level(level_index)
                        break
        finally:
            self.close()


def render_previews(app, directory):
    os.makedirs(directory, exist_ok=True)
    app.course_screen()
    app.canvas.save_ppm(os.path.join(directory, "01-course.ppm"))
    app.study_screen(0, 0)
    app.canvas.save_ppm(os.path.join(directory, "02-study.ppm"))
    app.practice_screen("你", 2, "START AT THE YELLOW DOT", 2)
    app.canvas.save_ppm(os.path.join(directory, "03-practice.ppm"))
    app.level_complete_screen(0)
    app.canvas.save_ppm(os.path.join(directory, "04-complete.ppm"))


def default_paths():
    directory = os.path.dirname(os.path.abspath(__file__))
    return (
        os.path.join(directory, "hanzi_assets.json"),
        os.path.join(os.path.expanduser("~"), ".hanzi_quest_progress.json"),
    )


def main():
    asset_default, progress_default = default_paths()
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", default=asset_default)
    parser.add_argument("--progress", default=progress_default)
    parser.add_argument("--framebuffer", default="/dev/fb1")
    parser.add_argument("--touch", default="/dev/input/event0")
    parser.add_argument("--preview-dir")
    args = parser.parse_args()

    framebuffer = args.framebuffer
    touch = args.touch
    if args.preview_dir:
        framebuffer = "/dev/hanzi-quest-preview"
        touch = "/dev/hanzi-quest-preview-touch"
    app = HanziQuest(args.assets, args.progress, framebuffer, touch)
    if args.preview_dir:
        try:
            render_previews(app, args.preview_dir)
        finally:
            app.close()
        print("Rendered previews to " + args.preview_dir)
    else:
        if not os.path.exists(args.framebuffer):
            print("Framebuffer not found: " + args.framebuffer)
            return 1
        app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
