import struct
import os
import sys
import time
import random
import math

W, H = 480, 320
BPP = 2
FRAMEBUFFER = os.environ.get("CYBERDECK_FB", "/dev/fb1")

def c565(r, g, b):
    return struct.pack('<H', ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))

BG = c565(8, 8, 18)
CYAN = c565(0, 255, 220)
MAGENTA = c565(255, 0, 180)
GREEN = c565(0, 255, 80)
RED = c565(255, 50, 50)
WHITE = c565(255, 255, 255)
DARKGRAY = c565(25, 25, 40)
YELLOW = c565(255, 220, 0)

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
    with open(FRAMEBUFFER, "wb") as fb:
        fb.write(buf)

FONT = {"A":["01110","10001","10001","11111","10001","10001","10001"],"B":["11110","10001","10001","11110","10001","10001","11110"],"C":["01110","10001","10000","10000","10000","10001","01110"],"D":["11110","10001","10001","10001","10001","10001","11110"],"E":["11111","10000","10000","11110","10000","10000","11111"],"F":["11111","10000","10000","11110","10000","10000","10000"],"G":["01110","10001","10000","10111","10001","10001","01110"],"H":["10001","10001","10001","11111","10001","10001","10001"],"I":["01110","00100","00100","00100","00100","00100","01110"],"K":["10001","10010","10100","11000","10100","10010","10001"],"L":["10000","10000","10000","10000","10000","10000","11111"],"M":["10001","11011","10101","10101","10001","10001","10001"],"N":["10001","10001","11001","10101","10011","10001","10001"],"O":["01110","10001","10001","10001","10001","10001","01110"],"P":["11110","10001","10001","11110","10000","10000","10000"],"R":["11110","10001","10001","11110","10100","10010","10001"],"S":["01110","10001","10000","01110","00001","10001","01110"],"T":["11111","00100","00100","00100","00100","00100","00100"],"U":["10001","10001","10001","10001","10001","10001","01110"],"V":["10001","10001","10001","10001","01010","01010","00100"],"W":["10001","10001","10001","10101","10101","10101","01010"],"X":["10001","10001","01010","00100","01010","10001","10001"],"Y":["10001","10001","01010","00100","00100","00100","00100"]," ":["00000","00000","00000","00000","00000","00000","00000"],"1":["00100","01100","00100","00100","00100","00100","01110"],"2":["01110","10001","00001","00010","00100","01000","11111"],"3":["01110","10001","00001","00110","00001","10001","01110"],">":["01000","00100","00010","00001","00010","00100","01000"],".":["00000","00000","00000","00000","00000","01100","01100"],"<":["00010","00100","01000","10000","01000","00100","00010"]}

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

OX, OY = 90, 50
SZ = 80
board = [[" "]*3 for _ in range(3)]
turn = "X"
game_over = False
winner = None

def draw_x(cx, cy, s, c):
    for i in range(-s, s+1):
        for t in range(-2, 3):
            sp(cx+i+t, cy+i, c)
            sp(cx-i+t, cy+i, c)

def draw_o(cx, cy, r, c):
    for a in range(360):
        x = int(cx + r * math.cos(math.radians(a)))
        y = int(cy + r * math.sin(math.radians(a)))
        for t in range(-2, 3):
            sp(x+t, y, c)
            sp(x, y+t, c)

def check_winner():
    for r in range(3):
        if board[r][0] == board[r][1] == board[r][2] != " ":
            return board[r][0]
    for c in range(3):
        if board[0][c] == board[1][c] == board[2][c] != " ":
            return board[0][c]
    if board[0][0] == board[1][1] == board[2][2] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != " ":
        return board[0][2]
    return None

def board_full():
    for r in range(3):
        for c in range(3):
            if board[r][c] == " ":
                return False
    return True

def ai_move():
    empty = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == " ":
                empty.append((r, c))
    if empty:
        return random.choice(empty)
    return None

def draw_board():
    fill(BG)
    draw_text("TIC TAC TOE", (W - tw("TIC TAC TOE", 2)) // 2, 5, CYAN, 2)
    draw_text("< BACK", 10, 5, DARKGRAY, 1)
    for i in range(1, 3):
        rect(OX + i*SZ - 1, OY, OX + i*SZ + 2, OY + 3*SZ, CYAN)
        rect(OX, OY + i*SZ - 1, OX + 3*SZ, OY + i*SZ + 2, CYAN)
    for r in range(3):
        for c in range(3):
            cx = OX + c*SZ + SZ//2
            cy = OY + r*SZ + SZ//2
            if board[r][c] == "X":
                draw_x(cx, cy, 25, RED)
            elif board[r][c] == "O":
                draw_o(cx, cy, 25, GREEN)
    if game_over:
        if winner:
            msg = winner + " WINS"
            color = RED if winner == "X" else GREEN
        else:
            msg = "DRAW"
            color = YELLOW
        rect(80, 135, 400, 185, BG)
        rect(80, 135, 400, 137, color)
        rect(80, 183, 400, 185, color)
        draw_text(msg, (W - tw(msg, 3)) // 2, 145, color, 3)
        draw_text("TOUCH TO RESTART", (W - tw("TOUCH TO RESTART", 1)) // 2, 300, DARKGRAY, 1)
    else:
        msg = turn + " TURN"
        color = RED if turn == "X" else GREEN
        draw_text(msg, (W - tw(msg, 2)) // 2, 300, color, 2)
    flush()

def find_touch_device():
    for i in range(10):
        path = "/dev/input/event%d" % i
        if os.path.exists(path):
            return path
    return None

def read_touch(dev_path, timeout=0.5):
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
    sx = int((3488 - ry) / 2818.0 * 360 + 60)
    sy = int((rx - 690) / 2766.0 * 240 + 40)
    sx = max(0, min(W-1, sx))
    sy = max(0, min(H-1, sy))
    return (sx, sy)

def get_cell(x, y):
    if x < OX or x > OX + 3*SZ or y < OY or y > OY + 3*SZ:
        return None
    col = (x - OX) // SZ
    row = (y - OY) // SZ
    if 0 <= row < 3 and 0 <= col < 3:
        return (row, col)
    return None

def reset_game():
    global board, turn, game_over, winner
    board = [[" "]*3 for _ in range(3)]
    turn = "X"
    game_over = False
    winner = None

def main():
    global turn, game_over, winner
    print("Tic Tac Toe started")
    touch_dev = find_touch_device()
    draw_board()
    try:
        while True:
            if touch_dev:
                result = read_touch(touch_dev, 0.2)
                if result:
                    rx, ry = result
                    sx, sy = map_touch(rx, ry)
                    if sy < 20 and sx < 80:
                        print("Back to menu")
                        return
                    if game_over:
                        reset_game()
                        draw_board()
                        continue
                    cell = get_cell(sx, sy)
                    if cell:
                        r, c = cell
                        if board[r][c] == " ":
                            board[r][c] = turn
                            winner = check_winner()
                            if winner or board_full():
                                game_over = True
                            else:
                                turn = "O" if turn == "X" else "X"
                                if turn == "O":
                                    draw_board()
                                    time.sleep(0.5)
                                    move = ai_move()
                                    if move:
                                        board[move[0]][move[1]] = "O"
                                        winner = check_winner()
                                        if winner or board_full():
                                            game_over = True
                                        else:
                                            turn = "X"
                            draw_board()
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
