import struct
import os
import time
import math

W, H = 480, 320
BPP = 2

def c565(r, g, b):
    return struct.pack('<H', ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))

WHITE = c565(255, 255, 255)
BLACK = c565(0, 0, 0)
RED = c565(255, 0, 0)
GREEN = c565(0, 255, 0)
BLUE = c565(0, 0, 255)
YELLOW = c565(255, 255, 0)
CYAN = c565(0, 255, 255)
MAGENTA = c565(255, 0, 255)
ORANGE = c565(255, 140, 0)
PURPLE = c565(128, 0, 255)
PINK = c565(255, 100, 200)
BROWN = c565(139, 69, 19)
GRAY = c565(128, 128, 128)
DARKGRAY = c565(25, 25, 40)
BG = c565(8, 8, 18)
CANVAS_BG = c565(255, 255, 255)

PALETTE = [
    BLACK, WHITE, RED, GREEN, BLUE, YELLOW,
    CYAN, MAGENTA, ORANGE, PURPLE, PINK, BROWN,
    GRAY, c565(0, 100, 0), c565(0, 0, 128), c565(255, 200, 200),
]

BRUSH_SIZES = [1, 3, 5, 8]

buf = bytearray(W * H * BPP)

def sp(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        p = (y * W + x) * BPP
        buf[p:p+2] = c

def fill(c):
    for i in range(0, len(buf), 2):
        buf[i:i+2] = c

def rect(x1, y1, x2, y2, c):
    for y in range(max(0,y1), min(y2, H)):
        for x in range(max(0,x1), min(x2, W)):
            sp(x, y, c)

def flush():
    with open("/dev/fb1", "wb") as fb:
        fb.write(buf)

FONT = {"A":["01110","10001","10001","11111","10001","10001","10001"],"B":["11110","10001","10001","11110","10001","10001","11110"],"C":["01110","10001","10000","10000","10000","10001","01110"],"D":["11110","10001","10001","10001","10001","10001","11110"],"E":["11111","10000","10000","11110","10000","10000","11111"],"I":["01110","00100","00100","00100","00100","00100","01110"],"K":["10001","10010","10100","11000","10100","10010","10001"],"L":["10000","10000","10000","10000","10000","10000","11111"],"N":["10001","10001","11001","10101","10011","10001","10001"],"P":["11110","10001","10001","11110","10000","10000","10000"],"R":["11110","10001","10001","11110","10100","10010","10001"],"S":["01110","10001","10000","01110","00001","10001","01110"],"T":["11111","00100","00100","00100","00100","00100","00100"]," ":["00000","00000","00000","00000","00000","00000","00000"],"<":["00010","00100","01000","10000","01000","00100","00010"]}

def draw_text(text, x, y, c, scale=2):
    cx = x
    for ch in text.upper():
        if ch in FONT:
            for ri, row in enumerate(FONT[ch]):
                for ci, bit in enumerate(row):
                    if bit == "1":
                        for sy in range(scale):
                            for sx in range(scale):
                                sp(cx + ci*scale + sx, y + ri*scale + sy, c)
        cx += 6 * scale

def tw(text, scale=2):
    return len(text) * 6 * scale

def find_touch_device():
    for i in range(10):
        path = "/dev/input/event%d" % i
        if os.path.exists(path):
            return path
    return None

def map_touch(rx, ry):
    sx = int((3488 - ry) / 2818.0 * 360 + 60)
    sy = int((rx - 690) / 2766.0 * 240 + 40)
    sx = max(0, min(W-1, sx))
    sy = max(0, min(H-1, sy))
    return (sx, sy)

TOOLBAR_H = 30
CANVAS_H = H - TOOLBAR_H
current_color = BLACK
current_size = 3
eraser_mode = False

def draw_brush(cx, cy, size, color):
    for dy in range(-size, size+1):
        for dx in range(-size, size+1):
            if dx*dx + dy*dy <= size*size:
                sp(cx+dx, cy+dy, color)

def draw_line(x0, y0, x1, y1, size, color):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    steps = max(dx, dy, 1)
    for i in range(steps + 1):
        t = i / steps if steps > 0 else 0
        x = int(x0 + (x1 - x0) * t)
        y = int(y0 + (y1 - y0) * t)
        draw_brush(x, y, size, color)

def draw_toolbar():
    rect(0, CANVAS_H, W, H, c565(30, 30, 45))
    rect(0, CANVAS_H, W, CANVAS_H+1, GRAY)
    draw_text("< BACK", 3, CANVAS_H + 8, DARKGRAY, 1)
    px = 55
    for i, color in enumerate(PALETTE):
        x1 = px + i * 18
        y1 = CANVAS_H + 3
        rect(x1, y1, x1+16, y1+12, color)
        if color == current_color and not eraser_mode:
            rect(x1-1, y1-1, x1+17, y1, CYAN)
            rect(x1-1, y1+12, x1+17, y1+13, CYAN)
            rect(x1-1, y1, x1, y1+12, CYAN)
            rect(x1+16, y1, x1+17, y1+12, CYAN)
    bx = 55
    for i, size in enumerate(BRUSH_SIZES):
        x1 = bx + i * 22
        y1 = CANVAS_H + 18
        if size == current_size:
            rect(x1-1, y1-1, x1+16, y1+11, CYAN)
        rect(x1, y1, x1+15, y1+10, c565(20, 20, 35))
        ccx = x1 + 7
        ccy = y1 + 5
        ds = min(size, 4)
        for dy in range(-ds, ds+1):
            for dx in range(-ds, ds+1):
                if dx*dx + dy*dy <= ds*ds:
                    sp(ccx+dx, ccy+dy, WHITE)
    ex = bx + len(BRUSH_SIZES) * 22 + 5
    if eraser_mode:
        rect(ex-1, CANVAS_H+17, ex+31, CANVAS_H+30, CYAN)
    rect(ex, CANVAS_H+18, ex+30, CANVAS_H+29, c565(20, 20, 35))
    draw_text("E", ex+10, CANVAS_H+19, PINK, 1)
    cx = W - 40
    rect(cx, CANVAS_H+5, cx+35, CANVAS_H+25, c565(40, 20, 20))
    draw_text("CLR", cx+3, CANVAS_H+9, RED, 1)

def init_canvas():
    fill(BG)
    rect(0, 0, W, CANVAS_H, CANVAS_BG)
    draw_toolbar()
    flush()

def read_all_events(fd):
    events = []
    while True:
        try:
            data = os.read(fd, 16)
            if len(data) == 16:
                ts, tsu, typ, code, value = struct.unpack("IIHHi", data)
                events.append((typ, code, value))
            else:
                break
        except OSError:
            break
    return events

def main():
    global current_color, current_size, eraser_mode
    touch_dev = find_touch_device()
    if not touch_dev:
        print("No touch device")
        return
    init_canvas()
    fd = os.open(touch_dev, os.O_RDONLY | os.O_NONBLOCK)
    touch_x = -1
    touch_y = -1
    touching = False
    prev_sx = -1
    prev_sy = -1
    dirty = False
    last_flush = time.time()
    toolbar_tap = False
    try:
        while True:
            events = read_all_events(fd)
            for typ, code, value in events:
                if typ == 3 and code == 0:
                    touch_x = value
                elif typ == 3 and code == 1:
                    touch_y = value
                elif typ == 1 and code == 330:
                    if value == 1:
                        touching = True
                        toolbar_tap = False
                    elif value == 0:
                        touching = False
                        prev_sx = -1
                        prev_sy = -1
                        if dirty:
                            draw_toolbar()
                            flush()
                            dirty = False
                elif typ == 0 and touching and touch_x >= 0 and touch_y >= 0:
                    sx, sy = map_touch(touch_x, touch_y)
                    if sy >= CANVAS_H:
                        if not toolbar_tap:
                            toolbar_tap = True
                            if sx < 50:
                                os.close(fd)
                                return
                            px = 55
                            for i, color in enumerate(PALETTE):
                                x1 = px + i * 18
                                if x1 <= sx <= x1+16 and CANVAS_H+3 <= sy <= CANVAS_H+15:
                                    current_color = color
                                    eraser_mode = False
                                    draw_toolbar()
                                    flush()
                                    break
                            bx = 55
                            for i, size in enumerate(BRUSH_SIZES):
                                x1 = bx + i * 22
                                if x1 <= sx <= x1+15 and CANVAS_H+18 <= sy <= CANVAS_H+28:
                                    current_size = size
                                    draw_toolbar()
                                    flush()
                                    break
                            ex = bx + len(BRUSH_SIZES) * 22 + 5
                            if ex <= sx <= ex+30 and CANVAS_H+18 <= sy <= CANVAS_H+29:
                                eraser_mode = not eraser_mode
                                draw_toolbar()
                                flush()
                            if sx > W - 45 and CANVAS_H+5 <= sy <= CANVAS_H+25:
                                rect(0, 0, W, CANVAS_H, CANVAS_BG)
                                draw_toolbar()
                                flush()
                        prev_sx = -1
                        prev_sy = -1
                    elif sy < CANVAS_H:
                        if eraser_mode:
                            bc = CANVAS_BG
                            bs = current_size + 3
                        else:
                            bc = current_color
                            bs = current_size
                        if prev_sx >= 0 and prev_sy >= 0:
                            draw_line(prev_sx, prev_sy, sx, sy, bs, bc)
                        else:
                            draw_brush(sx, sy, bs, bc)
                        prev_sx = sx
                        prev_sy = sy
                        dirty = True
            now = time.time()
            if dirty and now - last_flush > 0.03:
                flush()
                last_flush = now
                dirty = False
            if not events:
                time.sleep(0.005)
    except KeyboardInterrupt:
        os.close(fd)

if __name__ == "__main__":
    main()
