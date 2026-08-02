#!/usr/bin/env python3
# Flappy KL - clean version, no background glitch, touch + keyboard control
import struct, os, time, random, mmap, glob

W, H = 480, 320
BPP = 2
FBSIZE = W * H * BPP

def c565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

C_WHITE = c565(255,255,255)
C_BLACK = c565(0,0,0)
C_RED   = c565(255,50,50)
C_GREEN = c565(0,200,100)
C_GREDGE= c565(0,150,70)
C_YELLOW= c565(255,220,0)
C_CYAN  = c565(0,255,220)
C_MAG   = c565(255,0,180)
C_DARK  = c565(25,25,40)
C_BIRD  = c565(255,220,50)
C_WING  = c565(255,180,0)
C_EYE   = c565(255,255,255)
C_PUPIL = c565(0,0,0)
C_BEAK  = c565(255,100,0)
C_OVER  = c565(10,5,20)

# ---------- framebuffer ----------
buf = bytearray(FBSIZE)
fb_fd = os.open("/dev/fb1", os.O_RDWR)
fb_mm = mmap.mmap(fb_fd, FBSIZE, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ)

def sp(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        p = (y*W+x)*BPP
        buf[p:p+2] = struct.pack('<H', c)

def rect_fast(x1, y1, x2, y2, c):
    pc = struct.pack('<H', c)
    x1,y1 = max(0,x1), max(0,y1)
    x2,y2 = min(W,x2), min(H,y2)
    if x2<=x1 or y2<=y1: return
    row = pc*(x2-x1)
    for y in range(y1,y2):
        p=(y*W+x1)*BPP
        buf[p:p+len(row)] = row

def flush():
    fb_mm.seek(0); fb_mm.write(buf)

# ---------- cyberpunk KL background, built once ----------
def build_bg():
    bg = bytearray(FBSIZE)
    random.seed(42)
    for y in range(H):
        r = 10+int(y*0.05); g = 2+int(y*0.03); b = 25+int(y*0.1)
        pc = struct.pack('<H', c565(r,g,b))
        for x in range(W):
            p=(y*W+x)*BPP; bg[p:p+2]=pc
    def bs(x,y,c):
        if 0<=x<W and 0<=y<H:
            p=(y*W+x)*BPP; bg[p:p+2]=struct.pack('<H',c)
    def br(x1,y1,x2,y2,c):
        pc=struct.pack('<H',c)
        for y in range(max(0,y1),min(y2,H)):
            for x in range(max(0,x1),min(x2,W)):
                p=(y*W+x)*BPP; bg[p:p+2]=pc
    # stars
    for _ in range(60):
        bs(random.randint(0,W-1), random.randint(0,140), random.choice([C_WHITE, c565(180,180,255), c565(255,200,255)]))
    # skyline buildings
    bx = 0
    while bx < W:
        bw = random.randint(15,35); bh = random.randint(30,90)
        br(bx, H-30-bh, bx+bw, H-30, c565(15,8,30))
        for wy in range(H-30-bh+4, H-34, 8):
            for wx in range(bx+3, bx+bw-3, 6):
                if random.random() > 0.45:
                    bs(wx, wy, random.choice([c565(255,200,50), c565(0,200,255), c565(255,0,150)]))
                    bs(wx+1, wy, c565(0,200,255))
        bx += bw + random.randint(2,6)
    # Petronas
    px = 120
    br(px, 90, px+14, H-30, c565(25,12,45)); br(px+24, 90, px+38, H-30, c565(25,12,45))
    br(px+14, 140, px+24, 148, c565(40,20,60))
    bs(px+7, 85, C_MAG); bs(px+31, 85, C_MAG)
    for wy in range(95, H-32, 6):
        for wx in [px+3, px+8, px+27, px+32]:
            bs(wx, wy, c565(0,200,255))
    # KL Tower
    tx = 330
    br(tx+2, 80, tx+6, H-30, c565(40,20,60)); br(tx-4, 75, tx+12, 82, c565(60,30,80))
    bs(tx+4, 70, C_MAG)
    # ground
    br(0, H-30, W, H-28, C_CYAN); br(0, H-28, W, H, c565(10,8,20))
    for gx in range(0, W, 30):
        br(gx, H-28, gx+15, H-26, C_MAG)
    random.seed()
    return bg

game_bg = build_bg()

# ---------- font ----------
FONT={"A":["01110","10001","10001","11111","10001","10001","10001"],"B":["11110","10001","10001","11110","10001","10001","11110"],"C":["01110","10001","10000","10000","10000","10001","01110"],"D":["11110","10001","10001","10001","10001","10001","11110"],"E":["11111","10000","10000","11110","10000","10000","11111"],"F":["11111","10000","10000","11110","10000","10000","10000"],"G":["01110","10001","10000","10111","10001","10001","01110"],"H":["10001","10001","10001","11111","10001","10001","10001"],"I":["01110","00100","00100","00100","00100","00100","01110"],"K":["10001","10010","10100","11000","10100","10010","10001"],"L":["10000","10000","10000","10000","10000","10000","11111"],"M":["10001","11011","10101","10101","10001","10001","10001"],"N":["10001","10001","11001","10101","10011","10001","10001"],"O":["01110","10001","10001","10001","10001","10001","01110"],"P":["11110","10001","10001","11110","10000","10000","10000"],"R":["11110","10001","10001","11110","10100","10010","10001"],"S":["01110","10001","10000","01110","00001","10001","01110"],"T":["11111","00100","00100","00100","00100","00100","00100"],"U":["10001","10001","10001","10001","10001","10001","01110"],"V":["10001","10001","10001","10001","01010","01010","00100"],"W":["10001","10001","10001","10101","10101","10101","01010"],"X":["10001","10001","01010","00100","01010","10001","10001"],"Y":["10001","10001","01010","00100","00100","00100","00100"]," ":["00000","00000","00000","00000","00000","00000","00000"],"0":["01110","10011","10101","10101","10101","11001","01110"],"1":["00100","01100","00100","00100","00100","00100","01110"],"2":["01110","10001","00001","00010","00100","01000","11111"],"3":["01110","10001","00001","00110","00001","10001","01110"],"4":["00010","00110","01010","10010","11111","00010","00010"],"5":["11111","10000","11110","00001","00001","10001","01110"],"6":["00110","01000","10000","11110","10001","10001","01110"],"7":["11111","00001","00010","00100","01000","01000","01000"],"8":["01110","10001","10001","01110","10001","10001","01110"],"9":["01110","10001","10001","01111","00001","00010","01100"],":":["00000","01100","01100","00000","01100","01100","00000"],"-":["00000","00000","00000","11111","00000","00000","00000"],".":["00000","00000","00000","00000","00000","01100","01100"],"<":["00010","00100","01000","10000","01000","00100","00010"],">":["01000","00100","00010","00001","00010","00100","01000"]}

def draw_text(t, x, y, c, s=2):
    cx = x
    for ch in t.upper():
        if ch in FONT:
            for ri,row in enumerate(FONT[ch]):
                for ci,bit in enumerate(row):
                    if bit=="1":
                        rect_fast(cx+ci*s, y+ri*s, cx+ci*s+s, y+ri*s+s, c)
        cx += 6*s

def tw(t, s=2): return len(t)*6*s

def dout(t, x, y, c, s=2):
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            if dx or dy: draw_text(t, x+dx, y+dy, C_BLACK, s)
    draw_text(t, x, y, c, s)

# ---------- input: touch + keyboard ----------
def find_touch():
    for i in range(10):
        p="/dev/input/event%d"%i
        if os.path.exists(p): return p
    return None

def open_keyboards():
    # open every event device that isn't the touchscreen; keyboard will be among them
    fds = []
    for path in glob.glob("/dev/input/event*"):
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            fds.append(fd)
        except OSError:
            pass
    return fds

def map_touch(rx, ry):
    sx = int((rx-565)/(3524-565)*480)
    sy = int((3406-ry)/(3406-708)*320)
    return (max(0,min(W-1,sx)), max(0,min(H-1,sy)))

# Linux key codes
KEY_UP = 103
KEY_SPACE = 57

GRAVITY = 0.35
FLAP = -4.5
PIPE_W = 35
PIPE_GAP = 95
PIPE_SPEED = 3
BIRD_X = 80

def draw_bird(by, flapping):
    iy = int(by)
    for dy in range(-7,8):
        for dx in range(-9,10):
            if dx*dx + dy*dy*1.3 <= 70:
                sp(BIRD_X+dx, iy+dy, C_BIRD)
    if flapping:
        for dy in range(-5,0):
            for dx in range(-5,2):
                if dx*dx+(dy+2)*(dy+2)<=12: sp(BIRD_X+dx, iy+dy, C_WING)
    else:
        for dy in range(1,6):
            for dx in range(-5,2):
                if dx*dx+(dy-3)*(dy-3)<=12: sp(BIRD_X+dx, iy+dy, C_WING)
    sp(BIRD_X+4, iy-3, C_EYE); sp(BIRD_X+5, iy-3, C_EYE)
    sp(BIRD_X+4, iy-2, C_EYE); sp(BIRD_X+5, iy-2, C_PUPIL)
    for dx in range(7,12):
        sp(BIRD_X+dx, iy, C_BEAK); sp(BIRD_X+dx, iy+1, C_BEAK)

def draw_pipe(px, gap_y):
    ipx = int(px)
    rect_fast(ipx, 0, ipx+PIPE_W, gap_y-8, C_GREEN)
    rect_fast(ipx-2, gap_y-14, ipx+PIPE_W+2, gap_y-6, C_GREDGE)
    rect_fast(ipx, gap_y+PIPE_GAP+8, ipx+PIPE_W, H-30, C_GREEN)
    rect_fast(ipx-2, gap_y+PIPE_GAP+6, ipx+PIPE_W+2, gap_y+PIPE_GAP+14, C_GREDGE)

def main():
    touch_dev = find_touch()
    tfd = os.open(touch_dev, os.O_RDONLY | os.O_NONBLOCK) if touch_dev else None
    kfds = open_keyboards()

    bird_y = 160.0; bird_vel = 0.0
    pipes = []; score = 0; high_score = 0
    state = "menu"; frame = 0; grace = 0
    tx, ty = -1, -1

    def reset():
        nonlocal bird_y, bird_vel, pipes, score, frame, grace
        bird_y=160.0; bird_vel=0.0
        pipes=[[W+100, random.randint(60, H-PIPE_GAP-60)]]
        score=0; frame=0; grace=40

    def draw_menu():
        buf[:] = game_bg[:]
        draw_bird(120, True)
        dout("FLAPPY KL", (W-tw("FLAPPY KL",3))//2, 20, C_CYAN, 3)
        dout("TAP OR SPACE", (W-tw("TAP OR SPACE",2))//2, 135, C_WHITE, 2)
        dout("TO PLAY", (W-tw("TO PLAY",2))//2, 160, C_WHITE, 2)
        if high_score>0:
            dout("BEST: "+str(high_score), (W-tw("BEST: "+str(high_score),2))//2, 195, C_YELLOW, 2)
        draw_text("< BACK", 10, 5, C_DARK, 1)
        flush()

    def draw_game():
        buf[:] = game_bg[:]
        for px,gy in pipes: draw_pipe(px, gy)
        draw_bird(bird_y, frame%6<3)
        dout(str(score), (W-tw(str(score),3))//2, 8, C_CYAN, 3)
        flush()

    def draw_over():
        rect_fast(90,85,390,225,C_OVER)
        rect_fast(90,85,390,88,C_MAG); rect_fast(90,222,390,225,C_MAG)
        dout("GAME OVER", (W-tw("GAME OVER",3))//2, 100, C_RED, 3)
        draw_text("SCORE: "+str(score), (W-tw("SCORE: "+str(score),2))//2, 140, C_CYAN, 2)
        draw_text("BEST: "+str(high_score), (W-tw("BEST: "+str(high_score),2))//2, 170, C_YELLOW, 2)
        draw_text("TAP OR SPACE TO RETRY", (W-tw("TAP OR SPACE TO RETRY",1))//2, 205, C_DARK, 1)
        flush()

    draw_menu()

    try:
        while True:
            tapped = False
            flap_key = False
            # read touch
            if tfd:
                while True:
                    try:
                        d = os.read(tfd, 16)
                        if len(d)==16:
                            _,_,typ,code,val = struct.unpack("IIHHi", d)
                            if typ==1 and code==330 and val==1: tapped=True
                            if typ==3 and code==0: tx=val
                            if typ==3 and code==1: ty=val
                    except OSError:
                        break
            # read keyboards
            for kfd in kfds:
                while True:
                    try:
                        d = os.read(kfd, 16)
                        if len(d)==16:
                            _,_,typ,code,val = struct.unpack("IIHHi", d)
                            if typ==1 and val==1 and code in (KEY_UP, KEY_SPACE):
                                flap_key = True
                                tapped = True
                    except OSError:
                        break

            if state=="menu":
                if tapped:
                    if tx>0 and ty>0:
                        sx,sy = map_touch(tx,ty)
                        if sy<20 and sx<70:
                            if tfd: os.close(tfd)
                            for k in kfds: os.close(k)
                            fb_mm.close(); os.close(fb_fd)
                            return
                    reset(); state="playing"
                time.sleep(0.02)

            elif state=="playing":
                if tapped or flap_key:
                    bird_vel = FLAP; grace = 0
                if grace>0:
                    grace-=1; bird_vel=0
                else:
                    bird_vel += GRAVITY
                bird_y += bird_vel
                for i in range(len(pipes)): pipes[i][0] -= PIPE_SPEED
                if pipes and pipes[0][0] < -PIPE_W-5: pipes.pop(0)
                if not pipes or pipes[-1][0] < W-160:
                    pipes.append([W, random.randint(60, H-PIPE_GAP-60)])
                for px,gy in pipes:
                    if int(px)==BIRD_X-PIPE_SPEED or int(px)==BIRD_X-PIPE_SPEED-1:
                        score += 1
                hit = bird_y<3 or bird_y>H-33
                for px,gy in pipes:
                    if BIRD_X+8>px-2 and BIRD_X-8<px+PIPE_W+2:
                        if bird_y-6<gy-6 or bird_y+6>gy+PIPE_GAP+6: hit=True
                if hit:
                    if score>high_score: high_score=score
                    state="dead"; draw_game(); time.sleep(0.5); draw_over(); time.sleep(0.3)
                else:
                    frame+=1; draw_game()

            elif state=="dead":
                if tapped:
                    state="menu"; draw_menu()
                time.sleep(0.02)

    except KeyboardInterrupt:
        if tfd: os.close(tfd)
        for k in kfds: os.close(k)
        fb_mm.close(); os.close(fb_fd)

if __name__ == "__main__":
    main()
