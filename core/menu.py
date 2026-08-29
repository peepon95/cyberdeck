import struct
import math
import os
import sys
import glob
import json
import time
import subprocess

W, H = 480, 320
BPP = 2

def c565(r, g, b):
    return struct.pack('<H', ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))

BG = c565(8, 8, 18)
CYAN = c565(0, 255, 220)
MAGENTA = c565(255, 0, 180)
GREEN = c565(0, 255, 80)
YELLOW = c565(255, 220, 0)
RED = c565(255, 50, 50)
WHITE = c565(255, 255, 255)
DARKGRAY = c565(25, 25, 40)
ORANGE = c565(255, 140, 0)
buf = bytearray(W * H * BPP)

def find_framebuffer():
    configured = os.environ.get("CYBERDECK_FB")
    if configured:
        return configured
    for candidate in ("/dev/fb1", "/dev/fb0"):
        if os.path.exists(candidate):
            return candidate
    return "/dev/fb1"


FB_PATH = find_framebuffer()
os.environ["CYBERDECK_FB"] = FB_PATH
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_APPS_DIR = (
    os.path.join(os.path.dirname(SCRIPT_DIR), "apps")
    if os.path.basename(SCRIPT_DIR) == "core"
    else os.path.join(SCRIPT_DIR, "cyberdeck", "apps")
)
APPS_DIR = os.environ.get(
    "CYBERDECK_APPS_DIR",
    DEFAULT_APPS_DIR,
)
def sp(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        p = (y * W + x) * BPP
        buf[p:p+2] = c
def fill(c):
    for i in range(0, len(buf), 2):
        buf[i:i+2] = c
def rect(x1, y1, x2, y2, c):
    for y in range(y1, min(y2, H)):
        for x in range(x1, min(x2, W)):
            sp(x, y, c)
def flush():
    with open(FB_PATH, "wb") as fb:
        fb.write(buf)
FONT = {"A":["01110","10001","10001","11111","10001","10001","10001"],"B":["11110","10001","10001","11110","10001","10001","11110"],"C":["01110","10001","10000","10000","10000","10001","01110"],"D":["11110","10001","10001","10001","10001","10001","11110"],"E":["11111","10000","10000","11110","10000","10000","11111"],"F":["11111","10000","10000","11110","10000","10000","10000"],"G":["01110","10001","10000","10111","10001","10001","01110"],"H":["10001","10001","10001","11111","10001","10001","10001"],"I":["01110","00100","00100","00100","00100","00100","01110"],"J":["00111","00010","00010","00010","00010","10010","01100"],"K":["10001","10010","10100","11000","10100","10010","10001"],"L":["10000","10000","10000","10000","10000","10000","11111"],"M":["10001","11011","10101","10101","10001","10001","10001"],"N":["10001","10001","11001","10101","10011","10001","10001"],"O":["01110","10001","10001","10001","10001","10001","01110"],"P":["11110","10001","10001","11110","10000","10000","10000"],"R":["11110","10001","10001","11110","10100","10010","10001"],"S":["01110","10001","10000","01110","00001","10001","01110"],"T":["11111","00100","00100","00100","00100","00100","00100"],"U":["10001","10001","10001","10001","10001","10001","01110"],"V":["10001","10001","10001","10001","01010","01010","00100"],"W":["10001","10001","10001","10101","10101","10101","01010"],"X":["10001","10001","01010","00100","01010","10001","10001"],"Y":["10001","10001","01010","00100","00100","00100","00100"]," ":["00000","00000","00000","00000","00000","00000","00000"],"1":["00100","01100","00100","00100","00100","00100","01110"],"2":["01110","10001","00001","00010","00100","01000","11111"],"3":["01110","10001","00001","00110","00001","10001","01110"],"4":["00010","00110","01010","10010","11111","00010","00010"],"5":["11111","10000","11110","00001","00001","10001","01110"],"6":["00110","01000","10000","11110","10001","10001","01110"],"7":["11111","00001","00010","00100","01000","01000","01000"],"8":["01110","10001","10001","01110","10001","10001","01110"],"9":["01110","10001","10001","01111","00001","00010","01100"],"0":["01110","10011","10101","10101","10101","11001","01110"],">":["01000","00100","00010","00001","00010","00100","01000"],".":["00000","00000","00000","00000","00000","01100","01100"]}
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
COLOR_NAMES = {
    "cyan": CYAN,
    "green": GREEN,
    "yellow": YELLOW,
    "orange": ORANGE,
    "magenta": MAGENTA,
    "red": RED,
    "white": WHITE,
}


def load_apps(apps_dir=APPS_DIR):
    """Load installed apps from their small, beginner-editable manifests."""
    apps = []
    for manifest_path in sorted(glob.glob(os.path.join(apps_dir, "*", "app.json"))):
        try:
            with open(manifest_path, encoding="utf-8") as handle:
                manifest = json.load(handle)
            if not manifest.get("enabled", True):
                continue
            entry = os.path.join(os.path.dirname(manifest_path), manifest["entry"])
            if not os.path.isfile(entry):
                print("Skipping app with missing entry: " + manifest_path)
                continue
            apps.append({
                "id": manifest["id"],
                "name": manifest["name"],
                "color": COLOR_NAMES.get(manifest.get("color", "cyan").lower(), CYAN),
                "script": entry,
                "order": int(manifest.get("order", 999)),
            })
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            print("Skipping invalid app manifest {}: {}".format(manifest_path, error))
    return sorted(apps, key=lambda app: (app["order"], app["name"]))


MENU = load_apps()
TOUCH_ZONES = []
scroll_offset = 0
VISIBLE = 6

def draw_menu(selected=-1):
    global TOUCH_ZONES
    TOUCH_ZONES = []
    fill(BG)
    title = "CYBERDECK 2.0"
    draw_text(title, (W - tw(title, 3)) // 2, 8, CYAN, 3)
    sub = "SELECT PROGRAM"
    draw_text(sub, (W - tw(sub, 1)) // 2, 38, MAGENTA, 1)
    rect(20, 52, W-20, 54, CYAN)
    start_y = 62
    item_h = 40
    mx = 20
    visible_items = MENU[scroll_offset:scroll_offset+VISIBLE]
    for vi, item in enumerate(visible_items):
        i = vi + scroll_offset
        y1 = start_y + vi * item_h
        y2 = y1 + item_h - 4
        TOUCH_ZONES.append((mx, y1, W - mx, y2, i))
        if i == selected:
            rect(mx, y1, W - mx, y2, DARKGRAY)
        bc = item["color"] if i == selected else DARKGRAY
        rect(mx, y1, W-mx, y1+2, bc)
        rect(mx, y2-2, W-mx, y2, bc)
        rect(mx, y1, mx+2, y2, bc)
        rect(W-mx-2, y1, W-mx, y2, bc)
        num = str(i + 1) + "."
        draw_text(num, mx + 10, y1 + 8, item["color"], 2)
        draw_text(item["name"], mx + 50, y1 + 8, WHITE, 2)
        draw_text(">", W - mx - 20, y1 + 8, item["color"], 2)
    if scroll_offset > 0:
        draw_text("UP", (W - tw("UP", 1)) // 2, 55, DARKGRAY, 1)
    if scroll_offset + VISIBLE < len(MENU):
        draw_text("DOWN", (W - tw("DOWN", 1)) // 2, H-14, DARKGRAY, 1)
    flush()
def find_touch_device():
    candidates = []
    for path in sorted(glob.glob("/dev/input/event*")):
        candidates.append(path)
        name_path = "/sys/class/input/{}/device/name".format(os.path.basename(path))
        try:
            with open(name_path, encoding="utf-8") as handle:
                name = handle.read().strip().lower()
            if "touch" in name or "ads7846" in name or "xpt2046" in name:
                return path
        except OSError:
            pass
    return candidates[0] if candidates else None
def read_touch(dev_path, timeout=0.1):
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
def map_touch(rx, ry):
    sx = int((3708 - ry) / 3300.0 * 480)
    sy = int((rx - 670) / 2918.0 * 320)
    return (max(0, min(W-1, sx)), max(0, min(H-1, sy)))
def get_sel(x, y):
    for zx1, zy1, zx2, zy2, idx in TOUCH_ZONES:
        if zx1 <= x <= zx2 and zy1 <= y <= zy2:
            return idx
    return -1
def launch_app(script):
    if os.path.exists(script):
        subprocess.run([sys.executable, script])
    else:
        fill(BG)
        draw_text("APP NOT FOUND", (W - tw("APP NOT FOUND", 2)) // 2, 140, RED, 2)
        flush()
        time.sleep(3)

K_UP = 103
K_DOWN = 108
K_ENTER = 28

def open_keyboards(fds=None, excluded_paths=None):
    """Hot-plug input devices without consuming touchscreen events."""
    if fds is None:
        fds = {}
    excluded_paths = set(excluded_paths or ())
    live_paths = set(glob.glob("/dev/input/event*")) - excluded_paths
    for path in list(fds):
        if path not in live_paths:
            try:
                os.close(fds[path])
            except OSError:
                pass
            del fds[path]
    for p in sorted(live_paths):
        if p in fds:
            continue
        try:
            fds[p] = os.open(p, os.O_RDONLY | os.O_NONBLOCK)
        except OSError:
            pass
    return fds

def poll_keys(fds):
    out = []
    for path, fd in list(fds.items()):
        while True:
            try:
                d = os.read(fd, 16)
            except BlockingIOError:
                break
            except OSError:
                try:
                    os.close(fd)
                except OSError:
                    pass
                fds.pop(path, None)
                break
            if len(d) != 16:
                break
            _, _, typ, code, val = struct.unpack("IIHHi", d)
            if typ == 1 and val == 1:
                out.append(code)
    return out

def drain_keys(fds):
    for fd in list(fds.values()):
        while True:
            try:
                d = os.read(fd, 512)
                if not d:
                    break
            except OSError:
                break

def main():
    print("CYBERDECK OS v2.0")
    if not MENU:
        print("No installed apps found in " + APPS_DIR)
        sys.exit(1)
    for i in range(60):
        if os.path.exists(FB_PATH):
            print("Display found")
            time.sleep(2)
            break
        time.sleep(2)
    else:
        print("No display")
        sys.exit(1)
    touch_dev = find_touch_device()
    print("Touch: " + str(touch_dev))
    kb_fds = open_keyboards(excluded_paths={touch_dev} if touch_dev else None)
    last_input_scan = time.time()
    kb_sel = 0
    draw_menu(kb_sel)
    print("Menu ready - arrows to navigate, enter to launch")
    global scroll_offset
    try:
        while True:
            if time.time() - last_input_scan >= 1.0:
                kb_fds = open_keyboards(
                    kb_fds,
                    excluded_paths={touch_dev} if touch_dev else None,
                )
                last_input_scan = time.time()
            keys = poll_keys(kb_fds)
            if keys:
                if K_DOWN in keys:
                    kb_sel = (kb_sel + 1) % len(MENU)
                    if kb_sel >= scroll_offset + VISIBLE:
                        scroll_offset = kb_sel - VISIBLE + 1
                    elif kb_sel < scroll_offset:
                        scroll_offset = kb_sel
                    draw_menu(kb_sel)
                    drain_keys(kb_fds)
                    continue
                if K_UP in keys:
                    kb_sel = (kb_sel - 1) % len(MENU)
                    if kb_sel < scroll_offset:
                        scroll_offset = kb_sel
                    elif kb_sel >= scroll_offset + VISIBLE:
                        scroll_offset = kb_sel - VISIBLE + 1
                    draw_menu(kb_sel)
                    drain_keys(kb_fds)
                    continue
                if K_ENTER in keys:
                    draw_menu(kb_sel)
                    time.sleep(0.2)
                    drain_keys(kb_fds)
                    launch_app(MENU[kb_sel]["script"])
                    drain_keys(kb_fds)
                    draw_menu(kb_sel)
                    continue

            if touch_dev:
                result = read_touch(touch_dev, 0.1)
                if result:
                    rx, ry = result
                    sx, sy = map_touch(rx, ry)
                    if sy < 60 and scroll_offset > 0:
                        scroll_offset -= 1
                        draw_menu(kb_sel)
                        continue
                    if sy > H-20 and scroll_offset + VISIBLE < len(MENU):
                        scroll_offset += 1
                        draw_menu(kb_sel)
                        continue
                    sel = get_sel(sx, sy)
                    if sel >= 0:
                        kb_sel = sel
                        draw_menu(sel)
                        time.sleep(0.3)
                        launch_app(MENU[sel]["script"])
                        drain_keys(kb_fds)
                        draw_menu(kb_sel)
            else:
                time.sleep(0.05)
    except KeyboardInterrupt:
        fill(c565(0, 0, 0))
        flush()
    finally:
        for fd in kb_fds.values():
            try:
                os.close(fd)
            except OSError:
                pass
if __name__ == "__main__":
    main()
