#!/usr/bin/env python3
# Cyberdeck Minesweeper - FINAL v3: timeout reads + full buffer flush
import struct, os, time, random, mmap

W, H = 480, 320
BPP = 2

def c565(r, g, b):
    return struct.pack('<H', ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3))

BG=c565(8,8,18); CYAN=c565(0,255,220); MAGENTA=c565(255,0,180); GREEN=c565(0,255,80)
YELLOW=c565(255,220,0); RED=c565(255,50,50); WHITE=c565(255,255,255); DARKGRAY=c565(25,25,40)
GRAY=c565(60,60,80); LIGHTGRAY=c565(100,100,120); BLUE=c565(50,50,255); DARKBLUE=c565(0,0,180)
DARKGREEN=c565(0,150,0); MAROON=c565(128,0,0); TEAL=c565(0,128,128); BLACK=c565(0,0,0)
NUM_COLORS=[None,BLUE,DARKGREEN,RED,DARKBLUE,MAROON,TEAL,BLACK,GRAY]

FBSIZE=W*H*BPP
fb_fd=os.open("/dev/fb1",os.O_RDWR)
fb=mmap.mmap(fb_fd,FBSIZE,mmap.MAP_SHARED,mmap.PROT_WRITE|mmap.PROT_READ)

def sp(x,y,c):
    if 0<=x<W and 0<=y<H:
        p=(y*W+x)*BPP; fb[p:p+2]=c

def rect(x1,y1,x2,y2,c):
    x1,y1=max(0,x1),max(0,y1); x2,y2=min(W,x2),min(H,y2)
    if x2<=x1 or y2<=y1: return
    row=c*(x2-x1)
    for y in range(y1,y2):
        p=(y*W+x1)*BPP; fb[p:p+len(row)]=row

def fill(c):
    row=c*W
    for y in range(H):
        p=(y*W)*BPP; fb[p:p+len(row)]=row

FONT={"A":["01110","10001","10001","11111","10001","10001","10001"],"B":["11110","10001","10001","11110","10001","10001","11110"],"C":["01110","10001","10000","10000","10000","10001","01110"],"D":["11110","10001","10001","10001","10001","10001","11110"],"E":["11111","10000","10000","11110","10000","10000","11111"],"F":["11111","10000","10000","11110","10000","10000","10000"],"G":["01110","10001","10000","10111","10001","10001","01110"],"H":["10001","10001","10001","11111","10001","10001","10001"],"I":["01110","00100","00100","00100","00100","00100","01110"],"K":["10001","10010","10100","11000","10100","10010","10001"],"L":["10000","10000","10000","10000","10000","10000","11111"],"M":["10001","11011","10101","10101","10001","10001","10001"],"N":["10001","10001","11001","10101","10011","10001","10001"],"O":["01110","10001","10001","10001","10001","10001","01110"],"P":["11110","10001","10001","11110","10000","10000","10000"],"R":["11110","10001","10001","11110","10100","10010","10001"],"S":["01110","10001","10000","01110","00001","10001","01110"],"T":["11111","00100","00100","00100","00100","00100","00100"],"U":["10001","10001","10001","10001","10001","10001","01110"],"V":["10001","10001","10001","10001","01010","01010","00100"],"W":["10001","10001","10001","10101","10101","10101","01010"],"X":["10001","10001","01010","00100","01010","10001","10001"],"Y":["10001","10001","01010","00100","00100","00100","00100"],"Z":["11111","00001","00010","00100","01000","10000","11111"]," ":["00000","00000","00000","00000","00000","00000","00000"],"0":["01110","10011","10101","10101","10101","11001","01110"],"1":["00100","01100","00100","00100","00100","00100","01110"],"2":["01110","10001","00001","00010","00100","01000","11111"],"3":["01110","10001","00001","00110","00001","10001","01110"],"4":["00010","00110","01010","10010","11111","00010","00010"],"5":["11111","10000","11110","00001","00001","10001","01110"],"6":["00110","01000","10000","11110","10001","10001","01110"],"7":["11111","00001","00010","00100","01000","01000","01000"],"8":["01110","10001","10001","01110","10001","10001","01110"],"9":["01110","10001","10001","01111","00001","00010","01100"],".":["00000","00000","00000","00000","00000","01100","01100"],">":["01000","00100","00010","00001","00010","00100","01000"],"<":["00010","00100","01000","10000","01000","00100","00010"],":":["00000","01100","01100","00000","01100","01100","00000"]}

def draw_text(text,x,y,c,scale=2):
    cx=x
    for ch in text.upper():
        if ch in FONT:
            for ri,row in enumerate(FONT[ch]):
                for ci,bit in enumerate(row):
                    if bit=="1":
                        for sy in range(scale):
                            for sx in range(scale):
                                sp(cx+ci*scale+sx,y+ri*scale+sy,c)
        cx+=6*scale

def tw(text,scale=2): return len(text)*6*scale

def map_touch(rx,ry):
    sx=int((3708-ry)/3300.0*480); sy=int((rx-670)/2918.0*320)
    return (max(0,min(W-1,sx)),max(0,min(H-1,sy)))

def flush_buffer(fd):
    # drain and discard every pending event so nothing piles up
    while True:
        try:
            d=os.read(fd,512)
            if not d or len(d)<16:
                break
        except OSError:
            break

def get_tap(fd):
    # read for up to 0.25s, return a completed tap or None. Cannot hang.
    tx=-1; ty=-1; touched=False
    start=time.time()
    while time.time()-start < 0.25:
        try:
            data=os.read(fd,16)
        except OSError:
            time.sleep(0.005); continue
        if len(data)!=16:
            continue
        _,_,typ,code,value=struct.unpack("IIHHi",data)
        if typ==3 and code==0: tx=value
        elif typ==3 and code==1: ty=value
        elif typ==1 and code==330 and value==1: touched=True
        elif typ==1 and code==330 and value==0:
            if touched and tx>=0 and ty>=0:
                return map_touch(tx,ty)
    return None

COLS,ROWS=12,8; MINES=15; CELL=30
GX=(W-COLS*CELL)//2; GY=35
HIDDEN=0; REVEALED=1; FLAGGED=2

board=[[0]*COLS for _ in range(ROWS)]
state=[[HIDDEN]*COLS for _ in range(ROWS)]
mines=[[False]*COLS for _ in range(ROWS)]
flag_mode=False; game_over=False; game_won=False; start_time=0; first_click=True

def place_mines(sr,sc):
    n=0
    while n<MINES:
        r=random.randint(0,ROWS-1); c=random.randint(0,COLS-1)
        if not mines[r][c] and (abs(r-sr)>1 or abs(c-sc)>1):
            mines[r][c]=True; n+=1
    for r in range(ROWS):
        for c in range(COLS):
            if mines[r][c]: board[r][c]=-1
            else:
                k=0
                for dr in [-1,0,1]:
                    for dc in [-1,0,1]:
                        nr,nc=r+dr,c+dc
                        if 0<=nr<ROWS and 0<=nc<COLS and mines[nr][nc]: k+=1
                board[r][c]=k

def count_flags():
    return sum(1 for r in range(ROWS) for c in range(COLS) if state[r][c]==FLAGGED)

def check_win():
    for r in range(ROWS):
        for c in range(COLS):
            if not mines[r][c] and state[r][c]!=REVEALED: return False
    return True

def reveal_collect(r,c,changed):
    stack=[(r,c)]
    while stack:
        cr,cc=stack.pop()
        if state[cr][cc]!=HIDDEN: continue
        state[cr][cc]=REVEALED; changed.append((cr,cc))
        if board[cr][cc]==0:
            for dr in [-1,0,1]:
                for dc in [-1,0,1]:
                    nr,nc=cr+dr,cc+dc
                    if 0<=nr<ROWS and 0<=nc<COLS and state[nr][nc]==HIDDEN:
                        stack.append((nr,nc))

def draw_mine(cx,cy):
    rect(cx-4,cy-1,cx+5,cy+2,WHITE); rect(cx-1,cy-4,cx+2,cy+5,WHITE)
    rect(cx-3,cy-3,cx+4,cy+4,WHITE); rect(cx-2,cy-2,cx+3,cy+3,RED)

def draw_flag(cx,cy):
    rect(cx-1,cy-5,cx+4,cy-1,RED); rect(cx-1,cy-5,cx,cy+2,WHITE); rect(cx-3,cy+2,cx+4,cy+4,DARKGRAY)

def draw_cell(r,c):
    x1=GX+c*CELL; y1=GY+r*CELL; x2=x1+CELL-1; y2=y1+CELL-1
    cx=x1+CELL//2; cy=y1+CELL//2
    st=state[r][c]
    if st==HIDDEN:
        rect(x1,y1,x2,y2,GRAY); rect(x1,y1,x2,y1+1,LIGHTGRAY); rect(x1,y1,x1+1,y2,LIGHTGRAY)
        rect(x1,y2-1,x2,y2,DARKGRAY); rect(x2-1,y1,x2,y2,DARKGRAY)
    elif st==FLAGGED:
        rect(x1,y1,x2,y2,GRAY); rect(x1,y1,x2,y1+1,LIGHTGRAY); rect(x1,y1,x1+1,y2,LIGHTGRAY)
        draw_flag(cx,cy)
    else:
        rect(x1,y1,x2,y2,c565(15,15,25))
        if board[r][c]==-1: draw_mine(cx,cy)
        elif board[r][c]>0: draw_text(str(board[r][c]),cx-5,cy-6,NUM_COLORS[board[r][c]],2)

def draw_header():
    rect(0,0,W,GY-2,BG)
    draw_text("< BACK",5,5,DARKGRAY,1)
    draw_text("MINESWEEPER",(W-tw("MINESWEEPER",2))//2,3,CYAN,2)
    draw_text(str(MINES-count_flags()),GX,22,RED,1)
    if flag_mode:
        rect(W-70,2,W-5,18,RED); draw_text("FLAG",W-65,5,WHITE,1)
    else:
        rect(W-70,2,W-5,18,DARKGRAY); draw_text("FLAG",W-65,5,GRAY,1)
    elapsed=int(time.time()-start_time) if start_time>0 else 0
    draw_text(str(elapsed),GX+COLS*CELL-30,22,YELLOW,1)

def draw_all():
    fill(BG); draw_header()
    for r in range(ROWS):
        for c in range(COLS):
            draw_cell(r,c)

def draw_end(msg,color):
    rect(100,130,380,190,BG); rect(100,130,380,132,color); rect(100,188,380,190,color)
    draw_text(msg,(W-tw(msg,3))//2,145,color,3)
    draw_text("TOUCH TO RESTART",(W-tw("TOUCH TO RESTART",1))//2,300,DARKGRAY,1)

def reset_game():
    global board,state,mines,flag_mode,game_over,game_won,start_time,first_click
    board=[[0]*COLS for _ in range(ROWS)]
    state=[[HIDDEN]*COLS for _ in range(ROWS)]
    mines=[[False]*COLS for _ in range(ROWS)]
    flag_mode=False; game_over=False; game_won=False; start_time=0; first_click=True

def get_cell(sx,sy):
    c=(sx-GX)//CELL; r=(sy-GY)//CELL
    if 0<=r<ROWS and 0<=c<COLS: return (r,c)
    return None

def main():
    global flag_mode,game_over,game_won,start_time,first_click
    touch_path=None
    for i in range(10):
        p="/dev/input/event%d"%i
        if os.path.exists(p): touch_path=p; break
    fd=os.open(touch_path,os.O_RDONLY|os.O_NONBLOCK) if touch_path else None
    reset_game(); draw_all()
    if fd is not None: flush_buffer(fd)
    last_timer=time.time()
    try:
        while True:
            if start_time>0 and not game_over and not game_won:
                if time.time()-last_timer>=1:
                    draw_header(); last_timer=time.time()
            tap=get_tap(fd) if fd is not None else None
            if tap:
                sx,sy=tap
                acted=False
                if sy<20 and sx<70:
                    os.close(fd); fb.close(); os.close(fb_fd); return
                if game_over or game_won:
                    reset_game(); draw_all(); last_timer=time.time(); acted=True
                elif sy<20 and sx>W-75:
                    flag_mode=not flag_mode; draw_header(); acted=True
                else:
                    cell=get_cell(sx,sy)
                    if cell:
                        r,c=cell
                        if flag_mode:
                            if state[r][c]==HIDDEN: state[r][c]=FLAGGED; draw_cell(r,c); draw_header()
                            elif state[r][c]==FLAGGED: state[r][c]=HIDDEN; draw_cell(r,c); draw_header()
                        else:
                            if state[r][c]==HIDDEN:
                                if first_click:
                                    place_mines(r,c); first_click=False; start_time=time.time()
                                if mines[r][c]:
                                    for mr in range(ROWS):
                                        for mc in range(COLS):
                                            if mines[mr][mc]: state[mr][mc]=REVEALED; draw_cell(mr,mc)
                                    game_over=True; draw_end("GAME OVER",RED)
                                else:
                                    changed=[]; reveal_collect(r,c,changed)
                                    for (cr,cc) in changed: draw_cell(cr,cc)
                                    if check_win(): game_won=True; draw_end("YOU WIN",GREEN)
                        acted=True
                        last_timer=time.time()
                if acted:
                    # critical: after acting, throw away everything the screen queued up
                    flush_buffer(fd)
                    time.sleep(0.1)
                    flush_buffer(fd)
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        if fd is not None: os.close(fd)
        fb.close(); os.close(fb_fd)

if __name__=="__main__":
    main()
