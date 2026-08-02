#!/usr/bin/env python3
# Cyberdeck E-Reader - final clean version with corrected touch calibration
import struct, os, time, glob, json

W, H = 480, 320
BPP = 2

def c565(r, g, b):
    return struct.pack('<H', ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))

BG      = c565(8, 8, 18)
CYAN    = c565(0, 255, 220)
MAGENTA = c565(255, 0, 180)
GREEN   = c565(0, 255, 80)
YELLOW  = c565(255, 220, 0)
RED     = c565(255, 50, 50)
WHITE   = c565(255, 255, 255)
DARKGRAY= c565(25, 25, 40)
AMBER   = c565(255, 191, 0)

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

FONT = {"A":["01110","10001","10001","11111","10001","10001","10001"],"B":["11110","10001","10001","11110","10001","10001","11110"],"C":["01110","10001","10000","10000","10000","10001","01110"],"D":["11110","10001","10001","10001","10001","10001","11110"],"E":["11111","10000","10000","11110","10000","10000","11111"],"F":["11111","10000","10000","11110","10000","10000","10000"],"G":["01110","10001","10000","10111","10001","10001","01110"],"H":["10001","10001","10001","11111","10001","10001","10001"],"I":["01110","00100","00100","00100","00100","00100","01110"],"J":["00111","00010","00010","00010","00010","10010","01100"],"K":["10001","10010","10100","11000","10100","10010","10001"],"L":["10000","10000","10000","10000","10000","10000","11111"],"M":["10001","11011","10101","10101","10001","10001","10001"],"N":["10001","10001","11001","10101","10011","10001","10001"],"O":["01110","10001","10001","10001","10001","10001","01110"],"P":["11110","10001","10001","11110","10000","10000","10000"],"Q":["01110","10001","10001","10001","10101","10010","01101"],"R":["11110","10001","10001","11110","10100","10010","10001"],"S":["01110","10001","10000","01110","00001","10001","01110"],"T":["11111","00100","00100","00100","00100","00100","00100"],"U":["10001","10001","10001","10001","10001","10001","01110"],"V":["10001","10001","10001","10001","01010","01010","00100"],"W":["10001","10001","10001","10101","10101","10101","01010"],"X":["10001","10001","01010","00100","01010","10001","10001"],"Y":["10001","10001","01010","00100","00100","00100","00100"],"Z":["11111","00001","00010","00100","01000","10000","11111"]," ":["00000","00000","00000","00000","00000","00000","00000"],"0":["01110","10011","10101","10101","10101","11001","01110"],"1":["00100","01100","00100","00100","00100","00100","01110"],"2":["01110","10001","00001","00010","00100","01000","11111"],"3":["01110","10001","00001","00110","00001","10001","01110"],"4":["00010","00110","01010","10010","11111","00010","00010"],"5":["11111","10000","11110","00001","00001","10001","01110"],"6":["00110","01000","10000","11110","10001","10001","01110"],"7":["11111","00001","00010","00100","01000","01000","01000"],"8":["01110","10001","10001","01110","10001","10001","01110"],"9":["01110","10001","10001","01111","00001","00010","01100"],".":["00000","00000","00000","00000","00000","01100","01100"],",":["00000","00000","00000","00000","00100","00100","01000"],"!":["00100","00100","00100","00100","00100","00000","00100"],"?":["01110","10001","00001","00110","00100","00000","00100"],":":["00000","01100","01100","00000","01100","01100","00000"],";":["00000","01100","01100","00000","01100","00100","01000"],"-":["00000","00000","00000","11111","00000","00000","00000"],"'":["00100","00100","01000","00000","00000","00000","00000"],">":["01000","00100","00010","00001","00010","00100","01000"],"<":["00010","00100","01000","10000","01000","00100","00010"],"/":["00001","00010","00010","00100","01000","01000","10000"],"(":["00010","00100","01000","01000","01000","00100","00010"],")":["01000","00100","00010","00010","00010","00100","01000"],"%":["11001","11010","00100","00100","00100","01011","10011"]}

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

def read_touch(dev_path, timeout=0.2):
    touch_x = -1
    touch_y = -1
    touched = False
    try:
        fd = os.open(dev_path, os.O_RDONLY | os.O_NONBLOCK)
    except:
        return None
    try:
        start = time.time()
        while time.time() - start < timeout:
            try:
                data = os.read(fd, 16)
                if len(data) == 16:
                    ts, tsu, typ, code, value = struct.unpack("IIHHi", data)
                    if typ == 3 and code == 0:
                        touch_x = value
                    elif typ == 3 and code == 1:
                        touch_y = value
                    elif typ == 1 and code == 330 and value == 1:
                        touched = True
                    elif typ == 0 and touched and touch_x >= 0:
                        os.close(fd)
                        return (touch_x, touch_y)
            except OSError:
                time.sleep(0.01)
    except:
        pass
    os.close(fd)
    return None

# ---- CORRECTED CALIBRATION (from 4-corner calibration) ----
def map_touch(rx, ry):
    sx = int((3708 - ry) / 3300.0 * 480)
    sy = int((rx - 670) / 2918.0 * 320)
    return (max(0, min(W-1, sx)), max(0, min(H-1, sy)))

BOOKS_DIR = "/home/ee/books"
PROGRESS_FILE = "/home/ee/books/.progress.json"
CHARS_PER_LINE = 76
LINES_PER_PAGE = 18
LINE_H = 16
TEXT_X = 5
TEXT_Y = 3

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)
        f.flush()
        os.fsync(f.fileno())

def wrap_text(text):
    words = text.replace('\n', ' ').split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= CHARS_PER_LINE:
            current = current + " " + word if current else word
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def load_book(filepath):
    with open(filepath, 'r', errors='replace') as f:
        text = f.read()
    lines = wrap_text(text)
    pages = [lines[i:i+LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)]
    if not pages:
        pages = [["EMPTY FILE"]]
    return pages

def draw_reader(pages, page_num):
    fill(BG)
    for i, line in enumerate(pages[page_num]):
        draw_text(line, TEXT_X, TEXT_Y + i * LINE_H, AMBER, 1)
    rect(0, H-18, W, H, c565(5, 5, 12))
    rect(0, H-18, W, H-17, DARKGRAY)
    draw_text("< BACK", 5, H-14, DARKGRAY, 1)
    if page_num > 0:
        draw_text("PREV", 120, H-14, CYAN, 1)
    pg = str(page_num + 1) + "/" + str(len(pages))
    draw_text(pg, (W - tw(pg, 1)) // 2, H-14, WHITE, 1)
    if page_num < len(pages) - 1:
        draw_text("NEXT", W - 80, H-14, CYAN, 1)
    pct = (page_num + 1) / len(pages)
    rect(0, H-2, int(W * pct), H, CYAN)
    flush()

def draw_progress_bar(x, y, w, h, pct, color):
    rect(x, y, x+w, y+h, DARKGRAY)
    filled = int(w * pct)
    if filled > 0:
        rect(x, y, x+filled, y+h, color)

def draw_dashboard(books, progress, today_stats):
    fill(BG)
    draw_text("E READER", (W - tw("E READER", 2)) // 2, 5, CYAN, 2)
    draw_text("< BACK", 10, 8, DARKGRAY, 1)
    rect(10, 28, W-10, 29, CYAN)
    mins = today_stats.get("minutes", 0)
    pgs = today_stats.get("pages", 0)
    stat_text = "TODAY: " + str(mins) + " MIN  " + str(pgs) + " PAGES"
    draw_text(stat_text, (W - tw(stat_text, 1)) // 2, 33, MAGENTA, 1)
    if not books:
        draw_text("NO BOOKS FOUND", 100, 120, RED, 2)
        draw_text("ADD TXT FILES TO", (W - tw("ADD TXT FILES TO", 1)) // 2, 160, WHITE, 1)
        draw_text("/HOME/EE/BOOKS/", (W - tw("/HOME/EE/BOOKS/", 1)) // 2, 180, YELLOW, 1)
        flush()
        return []
    zones = []
    start_y = 48
    item_h = 52
    mx = 10
    for i, book in enumerate(books):
        if i >= 5:
            break
        y1 = start_y + i * item_h
        y2 = y1 + item_h - 2
        zones.append((mx, y1, W-mx, y2, i))
        rect(mx, y1, W-mx, y1+1, DARKGRAY)
        rect(mx, y2-1, W-mx, y2, DARKGRAY)
        rect(mx, y1, mx+1, y2, DARKGRAY)
        rect(W-mx-1, y1, W-mx, y2, DARKGRAY)
        name = os.path.basename(book).replace('.txt', '')
        bkey = os.path.basename(book)
        bp = progress.get(bkey, {})
        cur_page = bp.get("page", 0)
        total = bp.get("total", 1)
        pct = (cur_page + 1) / total if total > 0 else 0
        draw_text(str(i+1) + ".", mx+5, y1+5, CYAN, 1)
        draw_text(name[:22], mx+25, y1+5, WHITE, 1)
        pct_text = str(int(pct * 100)) + "%"
        draw_text(pct_text, W - mx - tw(pct_text, 1) - 5, y1+5, GREEN, 1)
        draw_progress_bar(mx+5, y1+22, W-mx*2-10, 6, pct, GREEN)
        if cur_page > 0:
            draw_text("CONTINUE P" + str(cur_page + 1), mx+25, y1+32, DARKGRAY, 1)
        else:
            draw_text("NEW", mx+25, y1+32, DARKGRAY, 1)
    flush()
    return zones

def get_today_key():
    t = time.localtime()
    return "%04d%02d%02d" % (t.tm_year, t.tm_mon, t.tm_mday)

def main():
    touch_dev = find_touch_device()
    if not os.path.exists(BOOKS_DIR):
        os.makedirs(BOOKS_DIR)
    progress = load_progress()
    today_key = get_today_key()
    if "daily" not in progress:
        progress["daily"] = {}
    if today_key not in progress["daily"]:
        progress["daily"][today_key] = {"minutes": 0, "pages": 0}

    while True:
        books = sorted(glob.glob(os.path.join(BOOKS_DIR, "*.txt")))
        today_stats = progress.get("daily", {}).get(today_key, {"minutes": 0, "pages": 0})
        zones = draw_dashboard(books, progress, today_stats)
        in_library = True
        while in_library:
            if touch_dev:
                result = read_touch(touch_dev, 0.2)
                if result:
                    rx, ry = result
                    sx, sy = map_touch(rx, ry)
                    if sy < 25 and sx < 80:
                        save_progress(progress)
                        return
                    for zx1, zy1, zx2, zy2, idx in zones:
                        if zx1 <= sx <= zx2 and zy1 <= sy <= zy2:
                            filepath = books[idx]
                            bkey = os.path.basename(filepath)
                            pages = load_book(filepath)
                            bp = progress.get(bkey, {})
                            page_num = bp.get("page", 0)
                            if page_num >= len(pages):
                                page_num = 0
                            progress[bkey] = {"page": page_num, "total": len(pages)}
                            draw_reader(pages, page_num)
                            read_start = time.time()
                            reading = True
                            while reading:
                                r2 = read_touch(touch_dev, 0.2)
                                if r2:
                                    rx2, ry2 = r2
                                    sx2, sy2 = map_touch(rx2, ry2)
                                    if sy2 > H-20 and sx2 < 70:
                                        elapsed = int((time.time() - read_start) / 60)
                                        progress["daily"][today_key]["minutes"] += max(1, elapsed)
                                        save_progress(progress)
                                        reading = False
                                    elif sy2 > H-20 and sx2 < 160:
                                        if page_num > 0:
                                            page_num -= 1
                                            progress[bkey]["page"] = page_num
                                            progress["daily"][today_key]["pages"] += 1
                                            draw_reader(pages, page_num)
                                    elif sy2 > H-20 and sx2 > W - 100:
                                        if page_num < len(pages) - 1:
                                            page_num += 1
                                            progress[bkey]["page"] = page_num
                                            progress["daily"][today_key]["pages"] += 1
                                            draw_reader(pages, page_num)
                                    elif sx2 > W // 2:
                                        if page_num < len(pages) - 1:
                                            page_num += 1
                                            progress[bkey]["page"] = page_num
                                            progress["daily"][today_key]["pages"] += 1
                                            draw_reader(pages, page_num)
                                    elif sx2 <= W // 2:
                                        if page_num > 0:
                                            page_num -= 1
                                            progress[bkey]["page"] = page_num
                                            progress["daily"][today_key]["pages"] += 1
                                            draw_reader(pages, page_num)
                            in_library = False
                            break
            else:
                time.sleep(0.1)

if __name__ == "__main__":
    main()
