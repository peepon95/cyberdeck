#!/usr/bin/env python3
# Cyberdeck Typewriter Journal - clean rewrite
# J = new entry | S = save | Q = journal list | ESC = main menu
import struct, os, time, glob, mmap, pwd

W, H = 480, 320
BPP = 2
FBSIZE = W * H * BPP
FRAMEBUFFER = os.environ.get("CYBERDECK_FB", "/dev/fb1")
USERNAME = pwd.getpwuid(os.getuid()).pw_name
JOURNAL_DIR = os.environ.get(
    "CYBERDECK_JOURNAL_DIR",
    os.path.join(os.path.expanduser("~"), "journal"),
)

def c(r, g, b):
    return struct.pack('<H', ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))

DARK    = c(18, 16, 14)
PAPER   = c(239, 231, 214)
INK     = c(44, 38, 32)
RULE    = c(185, 172, 147)
FAINT   = c(110, 99, 83)
CREAM   = c(232, 220, 196)
MUTED   = c(122, 110, 92)
AMBER   = c(201, 162, 39)
LINE    = c(58, 52, 44)
# red typewriter
BODY    = c(255, 0, 13)
BODY_LT = c(255, 90, 98)
BODY_DK = c(170, 0, 9)
PLATE   = c(255, 220, 222)
KEYCAP  = c(250, 242, 238)
KEY_DN  = c(205, 190, 185)
BAR     = c(40, 34, 34)
ROLLER  = c(238, 228, 224)
ROLL_HI = c(255, 250, 248)
KNOB    = c(205, 0, 10)
KNOB_DK = c(135, 0, 6)

fb_fd = os.open(FRAMEBUFFER, os.O_RDWR)
fb = mmap.mmap(fb_fd, FBSIZE, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ)

def present():
    """Force mmap-rendered pixels through fb_write for fbtft displays."""
    fb.flush()
    os.lseek(fb_fd, 0, os.SEEK_SET)
    view = memoryview(fb)
    sent = 0
    try:
        while sent < FBSIZE:
            written = os.write(fb_fd, view[sent:])
            if written <= 0:
                raise OSError("framebuffer write made no progress")
            sent += written
    finally:
        view.release()

def rect(x1, y1, x2, y2, col):
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(W, x2), min(H, y2)
    if x2 <= x1 or y2 <= y1:
        return
    row = col * (x2 - x1)
    for y in range(y1, y2):
        p = (y * W + x1) * BPP
        fb[p:p + len(row)] = row

def fill(col):
    row = col * W
    for y in range(H):
        p = (y * W) * BPP
        fb[p:p + len(row)] = row

FONT = {"A":["01110","10001","10001","11111","10001","10001","10001"],"B":["11110","10001","10001","11110","10001","10001","11110"],"C":["01110","10001","10000","10000","10000","10001","01110"],"D":["11110","10001","10001","10001","10001","10001","11110"],"E":["11111","10000","10000","11110","10000","10000","11111"],"F":["11111","10000","10000","11110","10000","10000","10000"],"G":["01110","10001","10000","10111","10001","10001","01110"],"H":["10001","10001","10001","11111","10001","10001","10001"],"I":["01110","00100","00100","00100","00100","00100","01110"],"J":["00111","00010","00010","00010","00010","10010","01100"],"K":["10001","10010","10100","11000","10100","10010","10001"],"L":["10000","10000","10000","10000","10000","10000","11111"],"M":["10001","11011","10101","10101","10001","10001","10001"],"N":["10001","10001","11001","10101","10011","10001","10001"],"O":["01110","10001","10001","10001","10001","10001","01110"],"P":["11110","10001","10001","11110","10000","10000","10000"],"Q":["01110","10001","10001","10001","10101","10010","01101"],"R":["11110","10001","10001","11110","10100","10010","10001"],"S":["01110","10001","10000","01110","00001","10001","01110"],"T":["11111","00100","00100","00100","00100","00100","00100"],"U":["10001","10001","10001","10001","10001","10001","01110"],"V":["10001","10001","10001","10001","01010","01010","00100"],"W":["10001","10001","10001","10101","10101","10101","01010"],"X":["10001","10001","01010","00100","01010","10001","10001"],"Y":["10001","10001","01010","00100","00100","00100","00100"],"Z":["11111","00001","00010","00100","01000","10000","11111"]," ":["00000","00000","00000","00000","00000","00000","00000"],"0":["01110","10011","10101","10101","10101","11001","01110"],"1":["00100","01100","00100","00100","00100","00100","01110"],"2":["01110","10001","00001","00010","00100","01000","11111"],"3":["01110","10001","00001","00110","00001","10001","01110"],"4":["00010","00110","01010","10010","11111","00010","00010"],"5":["11111","10000","11110","00001","00001","10001","01110"],"6":["00110","01000","10000","11110","10001","10001","01110"],"7":["11111","00001","00010","00100","01000","01000","01000"],"8":["01110","10001","10001","01110","10001","10001","01110"],"9":["01110","10001","10001","01111","00001","00010","01100"],".":["00000","00000","00000","00000","00000","01100","01100"],",":["00000","00000","00000","00000","00100","00100","01000"],"!":["00100","00100","00100","00100","00100","00000","00100"],"?":["01110","10001","00001","00110","00100","00000","00100"],":":["00000","01100","01100","00000","01100","01100","00000"],";":["00000","01100","01100","00000","01100","00100","01000"],"-":["00000","00000","00000","11111","00000","00000","00000"],"'":["00100","00100","01000","00000","00000","00000","00000"],"(":["00010","00100","01000","01000","01000","00100","00010"],")":["01000","00100","00010","00010","00010","00100","01000"],"/":["00001","00010","00010","00100","01000","01000","10000"],"[":["01110","01000","01000","01000","01000","01000","01110"],"]":["01110","00010","00010","00010","00010","00010","01110"],"=":["00000","00000","11111","00000","11111","00000","00000"]}

def text(t, x, y, col, s=1):
    cx = x
    for ch in str(t).upper():
        if ch in FONT:
            for ri, row in enumerate(FONT[ch]):
                for ci, bit in enumerate(row):
                    if bit == "1":
                        rect(cx + ci*s, y + ri*s, cx + ci*s + s, y + ri*s + s, col)
        cx += 6 * s

def tw(t, s=1):
    return len(str(t)) * 6 * s

# ---- keycodes ----
LETTERS = {
    2:"1", 3:"2", 4:"3", 5:"4", 6:"5", 7:"6", 8:"7", 9:"8", 10:"9", 11:"0",
    12:"-", 13:"=",
    16:"Q", 17:"W", 18:"E", 19:"R", 20:"T", 21:"Y", 22:"U", 23:"I", 24:"O", 25:"P",
    26:"[", 27:"]",
    30:"A", 31:"S", 32:"D", 33:"F", 34:"G", 35:"H", 36:"J", 37:"K", 38:"L",
    39:";", 40:"'",
    44:"Z", 45:"X", 46:"C", 47:"V", 48:"B", 49:"N", 50:"M",
    51:",", 52:".", 53:"/",
    57:" ",
}
K_ESC = 1
K_BACKSPACE = 14
K_ENTER = 28
K_Q = 16
K_S = 31
K_J = 36
K_D = 32
K_UP = 103
K_DOWN = 108

TOUCH_DEV = "/dev/input/event0"

def map_touch(rx, ry):
    sx = int((3708 - ry) / 3300.0 * 480)
    sy = int((rx - 670) / 2918.0 * 320)
    return (max(0, min(W - 1, sx)), max(0, min(H - 1, sy)))

def read_touch(timeout=0.05):
    """Non-blocking check for a completed tap. Returns (sx,sy) or None."""
    try:
        fd = os.open(TOUCH_DEV, os.O_RDONLY | os.O_NONBLOCK)
    except OSError:
        return None
    tx = ty = -1
    down = False
    start = time.time()
    try:
        while time.time() - start < timeout:
            try:
                d = os.read(fd, 16)
            except OSError:
                break
            if len(d) != 16:
                break
            _, _, typ, code, val = struct.unpack("IIHHi", d)
            if typ == 3 and code == 0:
                tx = val
            elif typ == 3 and code == 1:
                ty = val
            elif typ == 1 and code == 330 and val == 1:
                down = True
            elif typ == 1 and code == 330 and val == 0:
                if down and tx >= 0 and ty >= 0:
                    os.close(fd)
                    return map_touch(tx, ty)
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
    return None

def open_inputs():
    fds = []
    for p in sorted(glob.glob("/dev/input/event*")):
        try:
            fds.append(os.open(p, os.O_RDONLY | os.O_NONBLOCK))
        except OSError:
            pass
    return fds

def close_inputs(fds):
    for fd in fds:
        try:
            os.close(fd)
        except OSError:
            pass

def poll(fds):
    """Return list of keycodes pressed since last poll."""
    keys = []
    for fd in fds:
        while True:
            try:
                d = os.read(fd, 16)
            except OSError:
                break
            if len(d) != 16:
                break
            _, _, typ, code, val = struct.unpack("IIHHi", d)
            if typ == 1 and val == 1:
                keys.append(code)
    return keys

def drain(fds):
    """Throw away any pending events."""
    for fd in fds:
        while True:
            try:
                d = os.read(fd, 512)
                if not d:
                    break
            except OSError:
                break

# ---- machine geometry ----
ROLL_Y = 190
CARR_Y = ROLL_Y - 4
BAR_N = 26
ROW1_Y = H - 50
ROW2_Y = H - 34
ROW1_N = 12
ROW2_N = 11
KEY_W = 30
KEY_H = 13

def bar_x(i):
    return 152 + (i * 176) // (BAR_N - 1)

def row1_x(i):
    return 14 + i * 38

def row2_x(i):
    return 33 + i * 38

def draw_machine():
    rect(0, ROLL_Y + 16, W, H, BODY)
    rect(6, ROLL_Y + 9, W - 6, ROLL_Y + 16, BODY_LT)
    rect(14, ROLL_Y + 6, W - 14, ROLL_Y + 10, BODY_LT)
    rect(34, ROLL_Y, W - 34, ROLL_Y + 9, ROLLER)
    rect(34, ROLL_Y, W - 34, ROLL_Y + 3, ROLL_HI)
    for kx in (22, W - 22):
        rect(kx - 12, ROLL_Y - 5, kx + 12, ROLL_Y + 15, KNOB)
        rect(kx - 6, ROLL_Y + 1, kx + 6, ROLL_Y + 9, KNOB_DK)
    text(USERNAME, (W - tw(USERNAME, 2)) // 2, ROLL_Y + 20, PLATE, 2)

def draw_bar(i, up=False):
    x = bar_x(i)
    rect(x - 1, ROLL_Y - 14, x + 3, ROLL_Y, DARK)
    if up:
        rect(x, ROLL_Y - 12, x + 2, ROLL_Y - 1, BAR)
    else:
        rect(x, ROLL_Y - 4, x + 2, ROLL_Y, BAR)

def draw_bars():
    for i in range(BAR_N):
        draw_bar(i, False)

def draw_key(row, i, down=False):
    if row == 1:
        x, y0 = row1_x(i), ROW1_Y
    else:
        x, y0 = row2_x(i), ROW2_Y
    y = y0 + (2 if down else 0)
    rect(x - 2, y0 - 3, x + KEY_W + 2, y0 + KEY_H + 5, BODY)
    rect(x, y, x + KEY_W, y + KEY_H, KEY_DN if down else KEYCAP)
    rect(x, y + KEY_H - 3, x + KEY_W, y + KEY_H, BODY_DK)

def draw_keys():
    for i in range(ROW1_N):
        draw_key(1, i, False)
    for i in range(ROW2_N):
        draw_key(2, i, False)

def draw_carriage(col, total):
    rect(34, CARR_Y, W - 34, ROLL_Y, DARK)
    x = 40 + int((col / max(1, total)) * (W - 95))
    rect(x, CARR_Y, x + 9, ROLL_Y + 12, BODY_DK)

# ---- paper ----
PX1, PY1 = 60, 6
PX2, PY2 = W - 60, ROLL_Y - 8
LINE_H = 14
COLS = 40
MAXLINES = 9

def wrap(t, cols):
    out = []
    cur = ""
    for w in t.split(" "):
        if len(cur) + len(w) + (1 if cur else 0) <= cols:
            cur = cur + " " + w if cur else w
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    return out

def draw_paper(lines, ds, ts, words):
    rect(PX1, PY1, PX2, PY2, PAPER)
    text(ds, PX1 + 10, PY1 + 7, c(74, 66, 55), 1)
    text(ts, PX2 - 10 - tw(ts, 1), PY1 + 7, c(74, 66, 55), 1)
    rect(PX1 + 10, PY1 + 19, PX2 - 10, PY1 + 20, RULE)
    show = lines[-MAXLINES:] if len(lines) > MAXLINES else lines
    ty = PY1 + 29
    for ln in show:
        text(ln, PX1 + 10, ty, INK, 1)
        ty += LINE_H
    cy = PY1 + 29 + (len(show) - 1) * LINE_H if show else PY1 + 29
    cx = PX1 + 10 + tw(show[-1] if show else "", 1)
    rect(cx, cy, cx + 5, cy + 9, INK)
    rect(PX1 + 10, PY2 - 15, PX2 - 10, PY2 - 14, RULE)
    text(str(words) + " WORDS", PX1 + 10, PY2 - 11, FAINT, 1)
    lt = "LINE " + str(len(lines))
    text(lt, PX2 - 10 - tw(lt, 1), PY2 - 11, FAINT, 1)

def draw_hints():
    rect(0, H - 13, W, H, DARK)
    text("ESC = SAVE ENTRY", 8, H - 10, AMBER, 1)
    h = "TYPE FREELY"
    text(h, W - 8 - tw(h, 1), H - 10, MUTED, 1)

# ---- screens ----
def get_entries():
    if not os.path.exists(JOURNAL_DIR):
        os.makedirs(JOURNAL_DIR)
    return sorted(glob.glob(os.path.join(JOURNAL_DIR, "*.txt")), reverse=True)

def count_words(files):
    n = 0
    for f in files:
        try:
            n += len(open(f).read().split())
        except OSError:
            pass
    return n

ROW_Y0 = 64
ROW_H = 20
MAX_ROWS = 7

def row_bounds(i):
    y = ROW_Y0 + i * ROW_H
    return (14, y - 3, W - 14, y + 13)

def screen_home(files, sel=-1):
    fill(DARK)
    text("JOURNAL", 18, 12, CREAM, 2)
    ds = time.strftime("%d %b %Y").upper()
    text(ds, W - 18 - tw(ds, 1), 18, MUTED, 1)
    rect(18, 34, W - 18, 35, LINE)
    st = str(len(files)) + " ENTRIES  -  " + str(count_words(files)) + " WORDS"
    text(st, 18, 44, MUTED, 1)
    if not files:
        text("NO ENTRIES YET", 18, 80, MUTED, 1)
        text("PRESS J TO WRITE YOUR FIRST ONE", 18, 98, MUTED, 1)
    for i, f in enumerate(files[:MAX_ROWS]):
        y = ROW_Y0 + i * ROW_H
        if i == sel:
            x1, y1, x2, y2 = row_bounds(i)
            rect(x1, y1, x2, y2, LINE)
        base = os.path.basename(f).replace(".txt", "")
        try:
            d, t = base.split("_")
            label = d[8:10] + "/" + d[5:7] + " " + t[:2] + ":" + t[2:]
        except ValueError:
            label = base
        try:
            first = open(f).read().strip().split("\n")[0][:24]
        except OSError:
            first = ""
        col = AMBER if i == sel else CREAM
        if i == sel:
            text(">", 8, y, AMBER, 1)
        text(first if first else "(EMPTY)", 20, y, col, 1)
        text(label, W - 20 - tw(label, 1), y, MUTED, 1)
        rect(18, y + 11, W - 18, y + 12, LINE)
    rect(0, H - 44, W, H - 43, LINE)
    text("J = NEW ENTRY", 18, H - 36, AMBER, 1)
    if sel >= 0:
        text("D = DELETE", 150, H - 36, c(255, 90, 90), 1)
    text("UP / DOWN = SELECT", 18, H - 20, MUTED, 1)
    text("Q = MAIN MENU", 200, H - 20, MUTED, 1)
    rect(W - 80, H - 40, W - 12, H - 14, LINE)
    text("< BACK", W - 74, H - 31, CREAM, 1)
    present()

def screen_typing(ds, ts):
    fill(DARK)
    draw_machine()
    draw_bars()
    draw_keys()
    draw_paper([""], ds, ts, 0)
    draw_carriage(0, COLS)
    draw_hints()
    present()

def screen_saved(fn, wc, lc):
    fill(DARK)
    t1 = "ENTRY SAVED"
    text(t1, (W - tw(t1, 2)) // 2, 80, AMBER, 2)
    text(fn, (W - tw(fn, 1)) // 2, 118, CREAM, 1)
    s2 = str(wc) + " WORDS  -  " + str(lc) + " LINES"
    text(s2, (W - tw(s2, 1)) // 2, 136, MUTED, 1)
    rect(140, 160, 340, 161, LINE)
    a = "J  =  WRITE ANOTHER"
    text(a, (W - tw(a, 1)) // 2, 182, AMBER, 1)
    b = "Q  =  JOURNAL LIST"
    text(b, (W - tw(b, 1)) // 2, 202, MUTED, 1)
    d = "ESC  =  MAIN MENU"
    text(d, (W - tw(d, 1)) // 2, 222, MUTED, 1)
    rect(W - 80, H - 40, W - 12, H - 14, LINE)
    text("< BACK", W - 74, H - 31, CREAM, 1)
    present()

def main():
    fds = open_inputs()
    if not os.path.exists(JOURNAL_DIR):
        os.makedirs(JOURNAL_DIR)

    state = "home"
    buf = ""
    ds = ts = ""
    bar_i = 0
    key_row = 1
    key_i = 0
    prev_bar = -1
    prev_row = 1
    prev_key = -1

    sel = -1
    files = get_entries()
    screen_home(files, sel)
    drain(fds)

    try:
        while True:
            keys = poll(fds)

            # touch handling on home / saved screens
            if state in ("home", "saved") and not keys:
                tp = read_touch(0.03)
                if tp:
                    sx, sy = tp
                    # BACK button, bottom right
                    if sx > W - 90 and sy > H - 48:
                        close_inputs(fds)
                        fb.close()
                        os.close(fb_fd)
                        return
                    # tap an entry row to select it
                    if state == "home":
                        for i in range(min(len(files), MAX_ROWS)):
                            x1, y1, x2, y2 = row_bounds(i)
                            if x1 <= sx <= x2 and y1 <= sy <= y2:
                                sel = -1 if sel == i else i
                                screen_home(files, sel)
                                break

            if not keys:
                time.sleep(0.015)
                continue

            if state == "home":
                nshow = min(len(files), MAX_ROWS)
                if K_J in keys:
                    buf = ""
                    sel = -1
                    ds = time.strftime("%d.%b.%Y").upper()
                    ts = time.strftime("%H:%M")
                    screen_typing(ds, ts)
                    state = "typing"
                    drain(fds)
                elif K_DOWN in keys and nshow > 0:
                    sel = 0 if sel < 0 else min(sel + 1, nshow - 1)
                    screen_home(files, sel)
                    drain(fds)
                elif K_UP in keys and nshow > 0:
                    sel = nshow - 1 if sel < 0 else max(sel - 1, 0)
                    screen_home(files, sel)
                    drain(fds)
                elif K_D in keys and 0 <= sel < len(files):
                    try:
                        os.remove(files[sel])
                        os.sync()
                    except OSError:
                        pass
                    files = get_entries()
                    nshow = min(len(files), MAX_ROWS)
                    if nshow == 0:
                        sel = -1
                    else:
                        sel = min(sel, nshow - 1)
                    screen_home(files, sel)
                    drain(fds)
                elif K_Q in keys or K_ESC in keys:
                    close_inputs(fds)
                    fb.close()
                    os.close(fb_fd)
                    return

            elif state == "typing":
                changed = False
                do_save = False
                for code in keys:
                    if code == K_ESC:
                        do_save = True
                        break
                    if code == K_BACKSPACE:
                        buf = buf[:-1]
                        changed = True
                    elif code == K_ENTER:
                        buf += " "
                        changed = True
                    elif code in LETTERS:
                        buf += LETTERS[code]
                        changed = True

                if do_save:
                    if buf.strip():
                        fn = time.strftime("%Y-%m-%d_%H%M") + ".txt"
                        path = os.path.join(JOURNAL_DIR, fn)
                        with open(path, "w") as f:
                            f.write(buf)
                            f.flush()
                            os.fsync(f.fileno())
                        os.sync()
                        screen_saved(fn, len(buf.split()), len(wrap(buf, COLS)))
                        state = "saved"
                    else:
                        files = get_entries()
                        screen_home(files)
                        state = "home"
                    drain(fds)
                    continue

                if changed:
                    lines = wrap(buf, COLS)
                    col = len(lines[-1])
                    if prev_bar >= 0:
                        draw_bar(prev_bar, False)
                    if prev_key >= 0:
                        draw_key(prev_row, prev_key, False)
                    bar_i = (bar_i + 7) % BAR_N
                    key_row = 2 if key_row == 1 else 1
                    key_i = (key_i + 3) % (ROW1_N if key_row == 1 else ROW2_N)
                    draw_bar(bar_i, True)
                    draw_key(key_row, key_i, True)
                    prev_bar, prev_row, prev_key = bar_i, key_row, key_i
                    draw_paper(lines, ds, ts, len(buf.split()))
                    draw_carriage(col, COLS)
                    present()

            elif state == "saved":
                if K_J in keys:
                    buf = ""
                    ds = time.strftime("%d.%b.%Y").upper()
                    ts = time.strftime("%H:%M")
                    screen_typing(ds, ts)
                    state = "typing"
                    drain(fds)
                elif K_Q in keys:
                    files = get_entries()
                    sel = -1
                    screen_home(files, sel)
                    state = "home"
                    drain(fds)
                elif K_ESC in keys:
                    close_inputs(fds)
                    fb.close()
                    os.close(fb_fd)
                    return

    except KeyboardInterrupt:
        close_inputs(fds)
        fb.close()
        os.close(fb_fd)

if __name__ == "__main__":
    main()
