# v4, 31.10.2026, from v3. Generated in the container. Photos: docs/bom/AR_BOM_2026-10-09.xlsx column Picture extracted as rNNN.* (NNN = BOM row), docs/bom/src/photos/, pcb/*/..._assembled.png and ★ build photos from AR-Mini-Media/06_Edit/web-log/. Paths at the top are the build machine's.
OUT='/tmp/claude-0/-home-user/02c07dea-0385-5b8f-8c0e-5cbda7f6036b/scratchpad/arch4/out'; BOMIMG='/tmp/claude-0/-home-user/02c07dea-0385-5b8f-8c0e-5cbda7f6036b/scratchpad/arch4/img'; PH='/tmp/claude-0/-home-user/02c07dea-0385-5b8f-8c0e-5cbda7f6036b/scratchpad/arch4/ph'
#!/usr/bin/env python3
"""AR-Mini — system architecture v4 (as wired 31.10.2026), A3 landscape 300 dpi."""
from PIL import Image, ImageDraw, ImageFont, ImageOps
import math




W, H = 4961, 3508

RED = (181, 18, 27); RED_DK = (143, 14, 21); RED_LT = (225, 90, 95)
INK = (26, 26, 26); GREY = (105, 105, 105); LINE = (70, 70, 70); WHITE = (255, 255, 255)
CARD_B = (200, 200, 200)
# wire colours
C12 = (210, 35, 35); C5 = (240, 140, 0); C33 = (196, 30, 120)
CI2C0 = (40, 140, 60); CI2C1 = (120, 175, 40); CUART = (0, 140, 140)
CPWM = (35, 85, 200); CAN = (130, 70, 180); CMOT = (215, 170, 0); CUSB = (90, 90, 90)

FD = '/usr/share/fonts/opentype/inter/'
def F(n, s): return ImageFont.truetype(FD + n, s)
f_title = F('InterDisplay-Bold.otf', 100); f_sub = F('Inter-Regular.otf', 38)
f_hdr = F('Inter-Bold.otf', 44); f_name = F('Inter-Bold.otf', 30); f_spec = F('Inter-Regular.otf', 24)
f_lab = F('Inter-SemiBold.otf', 25); f_flag = F('Inter-Bold.otf', 23); f_pin = F('Inter-Bold.otf', 27)
f_small = F('Inter-Regular.otf', 24); f_leg = F('Inter-Regular.otf', 27); f_legb = F('Inter-Bold.otf', 30)
f_grp = F('Inter-SemiBoldItalic.otf', 31)

img = Image.new('RGB', (W, H), WHITE)
d = ImageDraw.Draw(img)

def load(path, crop=None):
    im = Image.open(path).convert('RGBA')
    if crop: im = im.crop(crop)
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
    m = ImageOps.grayscale(im).point(lambda p: 255 if p < 240 else 0); bb = m.getbbox()
    if bb: im = im.crop((max(0, bb[0]-4), max(0, bb[1]-4), min(im.width, bb[2]+4), min(im.height, bb[3]+4)))
    return im
def fit(im, bw, bh, up=3.0):
    sc = min(bw/im.width, bh/im.height, up)
    return im.resize((max(1, int(im.width*sc)), max(1, int(im.height*sc))), Image.LANCZOS)

def dashed_rect(box, col=RED_LT, w=4, dash=22, gap=14, r=26):
    x0, y0, x1, y1 = box
    d.arc([x0, y0, x0+2*r, y0+2*r], 180, 270, fill=col, width=w); d.arc([x1-2*r, y0, x1, y0+2*r], 270, 360, fill=col, width=w)
    d.arc([x1-2*r, y1-2*r, x1, y1], 0, 90, fill=col, width=w); d.arc([x0, y1-2*r, x0+2*r, y1], 90, 180, fill=col, width=w)
    def dl(a, b):
        L = math.dist(a, b); n = max(1, int(L//(dash+gap))); ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L
        off = (L - (n*(dash+gap)-gap))/2
        for i in range(n):
            s = off + i*(dash+gap); d.line([(a[0]+ux*s, a[1]+uy*s), (a[0]+ux*(s+dash), a[1]+uy*(s+dash))], fill=col, width=w)
    dl((x0+r, y0), (x1-r, y0)); dl((x1, y0+r), (x1, y1-r)); dl((x0+r, y1), (x1-r, y1)); dl((x0, y0+r), (x0, y1-r))

def section(box, title, dashed=False):
    x0, y0, x1, y1 = box
    if dashed:
        dashed_rect((x0, y0, x1, y1), col=(150, 150, 150), r=10)
        d.rectangle([x0, y0, x1, y0+76], fill=(120, 120, 120))
    else:
        d.rectangle([x0, y0, x1, y1], outline=LINE, width=3)
        d.rectangle([x0, y0, x1, y0+76], fill=RED)
    tw = f_hdr.getlength(title); d.text(((x0+x1)/2 - tw/2, y0+12), title, font=f_hdr, fill=WHITE)

class Card:
    def __init__(s, x, y, w, h, src, name, spec='', qty=None, icon=None, crop=None, ih=None, dashed=False):
        s.x, s.y, s.w, s.h = x, y, w, h
        if dashed: dashed_rect((x, y, x+w, y+h), col=(170, 170, 170), r=18, w=3)
        else: d.rounded_rectangle([x, y, x+w, y+h], radius=18, fill=WHITE, outline=CARD_B, width=3)
        ih = ih or h - 110
        if icon: pic = icon(w-40, ih)
        else: pic = fit(load(src, crop), w-40, ih)
        img.paste(pic, (int(x + (w-pic.width)/2), int(y + 14 + (ih-pic.height)/2)))
        ty = y + 14 + ih + 8
        for ln in wrap(name, f_name, w-20)[:2]:
            d.text((x + (w - f_name.getlength(ln))/2, ty), ln, font=f_name, fill=INK); ty += 34
        if spec:
            sp = wrap(spec, f_spec, w-16)[0]
            d.text((x + (w - f_spec.getlength(sp))/2, ty), sp, font=f_spec, fill=GREY)
        if qty:
            q = f'×{qty}'; qw = f_flag.getlength(q) + 22
            d.rounded_rectangle([x+w-qw-10, y+10, x+w-10, y+46], radius=12, fill=RED); d.text((x+w-qw+1, y+14), q, font=f_flag, fill=WHITE)
    def L(s, f=0.5): return (s.x, s.y + s.h*f)
    def R(s, f=0.5): return (s.x + s.w, s.y + s.h*f)
    def T(s, f=0.5): return (s.x + s.w*f, s.y)
    def B(s, f=0.5): return (s.x + s.w*f, s.y + s.h)

def wrap(t, font, w):
    out, cur = [], ''
    for wd in t.split():
        tt = (cur + ' ' + wd).strip()
        if font.getlength(tt) <= w or not cur: cur = tt
        else: out.append(cur); cur = wd
    if cur: out.append(cur)
    return out

def wire(pts, col, w=7, dot_end=True, dot_start=False, dash=False):
    pts = [(int(a), int(b)) for a, b in pts]
    if dash:
        for a, b in zip(pts, pts[1:]):
            L = math.dist(a, b)
            if L == 0: continue
            n = int(L // 30)
            for i in range(n):
                s0, s1 = i*30, min(i*30+18, L)
                d.line([(a[0]+(b[0]-a[0])*s0/L, a[1]+(b[1]-a[1])*s0/L), (a[0]+(b[0]-a[0])*s1/L, a[1]+(b[1]-a[1])*s1/L)], fill=col, width=w)
    else:
        d.line(pts, fill=col, width=w, joint='curve')
    r = w + 4
    if dot_end: x, y = pts[-1]; d.ellipse([x-r, y-r, x+r, y+r], fill=col)
    if dot_start: x, y = pts[0]; d.ellipse([x-r, y-r, x+r, y+r], fill=col)

def tag(x, y, text, col, anchor='c', font=f_lab, fg=None):
    tw = font.getlength(text); th = 34
    if anchor == 'c': x0 = x - tw/2 - 12
    elif anchor == 'l': x0 = x
    else: x0 = x - tw - 24
    d.rounded_rectangle([x0, y - th/2, x0 + tw + 24, y + th/2], radius=10, fill=WHITE, outline=col, width=3)
    d.text((x0 + 12, y - th/2 + 3), text, font=font, fill=fg or col)

def flag(x, y, text, col, side='r'):
    """power net flag: filled pill"""
    tw = f_flag.getlength(text); h = 36
    if side == 'r': x0 = x
    else: x0 = x - tw - 26
    d.rounded_rectangle([x0, y - h/2, x0 + tw + 26, y + h/2], radius=18, fill=col)
    d.text((x0 + 13, y - h/2 + 5), text, font=f_flag, fill=WHITE)

# ---------- icons ----------
def icon_leak(bw, bh):
    k = 2; im = Image.new('RGB', (bw*k, bh*k), WHITE); g = ImageDraw.Draw(im); Wd, Hd = bw*k, bh*k
    for col, yy in (((200, 30, 30), .40), ((40, 40, 40), .60)):
        g.line([(Wd*.08, Hd*yy), (Wd*.70, Hd*yy)], fill=col, width=18); g.line([(Wd*.70, Hd*yy), (Wd*.92, Hd*yy)], fill=(205, 140, 70), width=10)
    g.rounded_rectangle([Wd*.02, Hd*.30, Wd*.12, Hd*.70], radius=8, fill=(240, 240, 235), outline=(80, 80, 80), width=4)
    for cx, cy in ((.80, .22), (.88, .78)): g.ellipse([Wd*cx-14, Hd*cy-14, Wd*cx+14, Hd*cy+14], fill=(90, 160, 230))
    return im.resize((bw, bh), Image.LANCZOS)
def icon_ind(bw, bh):
    k = 2; im = Image.new('RGB', (bw*k, bh*k), WHITE); g = ImageDraw.Draw(im); Wd, Hd = bw*k, bh*k
    g.ellipse([Wd*.05, Hd*.25, Wd*.35, Hd*.75], fill=(30, 30, 30)); g.ellipse([Wd*.15, Hd*.42, Wd*.25, Hd*.58], fill=(90, 90, 90))
    for i, c in enumerate([(40, 180, 70), (240, 190, 20), (220, 40, 40)]):
        cx = Wd*(.50 + i*.17); g.rounded_rectangle([cx-Wd*.05, Hd*.30, cx+Wd*.05, Hd*.62], radius=int(Wd*.05), fill=c, outline=(80, 80, 80), width=3)
        g.line([(cx-Wd*.02, Hd*.62), (cx-Wd*.02, Hd*.85)], fill=(150, 150, 150), width=5); g.line([(cx+Wd*.02, Hd*.62), (cx+Wd*.02, Hd*.80)], fill=(150, 150, 150), width=5)
    return im.resize((bw, bh), Image.LANCZOS)

# ================= LAYOUT v3 =================
import glob as _g
IMG = BOMIMG
def Q(r): return _g.glob(f'{IMG}/r{r:03d}.*')[0]
def P(n): return f'{PH}/{n}'
C6 = (190, 120, 0)
M = 60
title = 'AR-Mini  ·  System Architecture v4'
tw = f_title.getlength(title); d.text(((W-tw)/2, 40), title, font=f_title, fill=INK)
d.rectangle([(W-tw)/2, 160, (W+tw)/2, 168], fill=RED)
sub = 'As wired on 31.10.2026 for the water runs: one Olimex ESP32-S3-DevKit-Lipo on the 3S LiPo, the XIAO is the camera node  ·  tracks off for the water  ·  power fused per branch  ·  dashed = idle, designed or on order'
d.text(((W - f_sub.getlength(sub))/2, 186), sub, font=f_sub, fill=GREY)

TOP = 270
PX0, PX1 = M, 1120
CX0, CX1 = 1200, 3060
AX0, AX1 = 3140, W - M
BOT = 3130
section((PX0, TOP, PX1, BOT), 'Power')
section((CX0, TOP, CX1, 900), 'Sensing')
section((CX0, 1000, CX1, 2560), 'Control')
section((CX0, 2650, CX1, BOT), 'Next · own PCBs, level shifter, v2 (2027)', dashed=True)
section((AX0, TOP, AX1, BOT), 'Actuation & rescue')

# ---------- POWER ----------
cw, ch = 400, 330
px = PX0 + 50
lipo = Card(px, 380, cw, ch, Q(53), 'Turnigy 3S 2200 mAh', '12.60 V full · 4.20 V/cell · C058', qty=2)
fuse = Card(px, 790, cw, ch, Q(83), 'Inline fuse 30 A', 'GT4652 · on the XT60 lead')
sw = Card(px, 1200, cw, ch, Q(81), 'Main switch 50 A', 'R13-401A2A · cuts everything')
fb = Card(px, 1610, cw, 360, Q(84), '6-slot fuse block', 'branches below · card C026')
for a, b in ((lipo, fuse), (fuse, sw), (sw, fb)):
    wire([a.B(0.5), b.T(0.5)], C12, w=10, dot_end=False, dash=True)
tag(px + cw/2 + 20, 760, '12 V', C12, 'l'); tag(px + cw/2 + 20, 1170, '12 V', C12, 'l'); tag(px + cw/2 + 20, 1580, '12 V', C12, 'l')
bx = PX0 + 40; by = 2010
d.text((bx, by), 'Fused branches (12 V)', font=f_legb, fill=INK); by += 50
for fl, txt in (('F1 20 A', 'thruster (ESC inside the lead)'), ('F2 15 A', 'QIQIAZI 5 V / 5 A → lift servos'), ('F3 —', 'empty: tracks off for water'), ('F4 5 A', 'MZHOU 5 V → DevKit + VBAT sense')):
    flag(bx, by + 16, fl, C12); d.text((bx + 150, by), txt, font=f_leg, fill=INK); by += 46
buck = Card(px, 2300, 300, 300, Q(79), 'MZHOU buck', '12 → 5 V 3 A · USB-C', ih=160)
flag(px + 320, 2330, 'F4 5 A', C12); d.text((px + 320, 2360), 'into the', font=f_small, fill=GREY); d.text((px + 320, 2390), 'DevKit OTG', font=f_small, fill=GREY)
bench = Card(px, 2650, 300, 300, Q(80), 'QIQIAZI buck', '12 → 5 V 5 A · lift', ih=160)
flag(px + 320, 2680, 'F2 15 A', C12); d.text((px + 320, 2710), '→ PCA9685 V+', font=f_small, fill=GREY); d.text((px + 320, 2740), '(never 12 V', font=f_small, fill=GREY); d.text((px + 320, 2770), 'into V+)', font=f_small, fill=GREY)
d.text((PX0 + 40, 2985), 'On the LiPo since 31.10 (C059); balance', font=f_small, fill=GREY)
d.text((PX0 + 40, 3017), 'charged in a bag on SkyRC iMAX B6 V2.', font=f_small, fill=GREY)
d.text((PX0 + 40, 3049), 'Stop the run at VBAT ≤ 10.5 V.', font=f_small, fill=GREY)

# ---------- SENSING ----------
sy = 380; sh = 420
head = Card(CX0 + 30, sy, 400, sh, P('C047_13.jpg'), 'Camera head on the arch', 'printed mount · 3 cameras · C047', ih=300)
scw = 220; sx = CX0 + 455; sp = 232
d45 = Card(sx, sy, scw, sh, Q(76), 'MLX90642-D45', '45° · wired, idle', ih=300)
m110 = Card(sx + sp, sy, scw, sh, Q(77), 'MLX90640 110°', 'wired, idle · C029', ih=300)
ov = Card(sx + 2*sp, sy, scw, sh, Q(63), 'OV3660 2 MP', 'XIAO · own Wi-Fi', ih=300)
bno = Card(sx + 3*sp, sy, scw, sh, Q(78), 'BNO055 IMU', 'not wired yet', ih=300, dashed=True)
leak = Card(sx + 4*sp, sy, scw, sh, None, 'Leak probe', 'GPIO7 · in box floor', icon=icon_leak, ih=300)
vb = Card(sx + 5*sp, sy, scw, sh, Q(56), 'VBAT divider', '100k / 30k · F4', ih=300)

# ---------- CONTROL ----------
dk = Card(1930, 1130, 520, 430, Q(61), 'Olimex ESP32-S3-DevKit-Lipo', 'two breadboards in the food box', ih=300)
# buses between sensing and control
# I2C-0: D45 + BNO -> GPIO48/47 (and on to PCA9685 in actuation)
yb0 = 935; yb1 = 960; yba = 985
wire([d45.B(0.5), (d45.x + scw/2, yb0)], CI2C0, w=6, dot_end=False); wire([bno.B(0.5), (bno.x + scw/2, yb0)], CI2C0, w=6, dot_end=False, dash=True)
wire([(d45.x + scw/2, yb0), (1300, yb0), (1300, 1400), (1700, 1400)], CI2C0, w=6, dot_end=False)
wire([(d45.x + scw/2, yb0), (bno.x + scw/2, yb0)], CI2C0, w=6, dot_end=False); wire([(bno.x + scw/2, yb0), (3140, yb0)], CI2C0, w=6, dot_end=False)
tag(2980, yb0, 'I²C-0 → PCA9685', CI2C0, 'r')
wire([m110.B(0.5), (m110.x + scw/2, yb1), (1270, yb1), (1270, 1340), (1700, 1340)], CI2C1, w=6, dot_end=False)
tag(1395, 905, 'I²C-1', CI2C1); tag(1395, 960, 'I²C-0', CI2C0, 'r'); tag(1230, 1050, 'VBAT · LEAK', CAN, 'l')
wire([vb.B(0.5), (vb.x + 130, yba), (1240, yba), (1240, 1180), (1700, 1180)], CAN, w=6, dot_end=False)
wire([leak.B(0.5), (leak.x + scw/2, yba)], CAN, w=6, dot_end=False)
wire([(1240, 1230), (1700, 1230)], CAN, w=6, dot_end=False)
# left pins
pins_l = [(1180, 'GPIO4  VBAT', CAN), (1230, 'GPIO7  LEAK', CAN), (1280, 'GPIO14  KILL rocker', CAN), (1340, 'GPIO8 / 9  I²C-1', CI2C1), (1400, 'GPIO48 / 47  I²C-0', CI2C0), (1470, 'USB-C OTG  5 V in', C5), (1520, 'USB-C UART  laptop', CUSB)]
for y, t, c in pins_l:
    wire([(1700, y), (dk.x, y)], c, w=5, dot_end=False); tag(1700, y, t, c, 'r')
pins_r = [(1180, 'GPIO1 / 2  ESC / rudder', CPWM), (1240, 'GPIO39–42  tracks (off)', CPWM), (1300, 'Wi-Fi AP "AR-Mini"  phone', CUSB)]
for y, t, c in pins_r:
    wire([(dk.x + dk.w, y), (2680, y), ], c, w=5, dot_end=False); tag(2680, y, t, c, 'l')
# below the DevKit
ph1 = Card(1250, 1650, 460, 420, P('C059_44.png'), 'Phone remote', 'thrust · turn · lift · VBAT on screen', ih=300)
xi = Card(1760, 1650, 460, 420, Q(63), 'XIAO ESP32-S3 Sense', 'camera node · own AP "AR-Mini-cam"', ih=300)
fw = Card(2270, 1650, 460, 420, Q(90), 'Firmware · PlatformIO', 'env remote_pool · C059', ih=300)
s80 = Card(2780, 1650, 250, 420, P('sn74ahct125n.png'), '74HCT125', '3.3 → 5 V', ih=300)
wire([dk.B(0.2), (dk.x + dk.w*0.2, 1610), (ph1.x + 230, 1610), ph1.T(0.5)], CUSB, w=5, dot_end=False)
wire([dk.B(0.5), (dk.x + dk.w*0.5, 1610), (fw.x + 230, 1610), fw.T(0.5)], CUSB, w=5, dot_end=False)
wire([(3005, 1180), (3100, 1180), (3100, 1050), (AX0 + 40, 1050)], CPWM, w=5, dot_end=False)
wire([s80.R(0.5), (3100, s80.y + 210), (3100, 1180)], CPWM, w=5, dot_end=False)
# state machine
smy = 2160
d.text((1250, smy - 60), 'Mission state machine (firmware)', font=f_grp, fill=RED_DK)
states = ['SEARCH', 'APPROACH', 'ALIGN', 'LIFT', 'RETURN']
sx0 = 1250; sw_ = 300; gap = (CX1 - 30 - sx0 - 5*sw_)/4
for i, st in enumerate(states):
    x = sx0 + i*(sw_ + gap)
    d.rounded_rectangle([x, smy, x + sw_, smy + 80], radius=14, fill=(252, 236, 236), outline=RED, width=4)
    d.text((x + (sw_ - f_pin.getlength(st))/2, smy + 24), st, font=f_pin, fill=RED_DK)
    if i < 4: wire([(x + sw_, smy + 40), (x + sw_ + gap - 6, smy + 40)], RED, w=6, dot_end=False); d.polygon([(x + sw_ + gap, smy + 40), (x + sw_ + gap - 22, smy + 26), (x + sw_ + gap - 22, smy + 54)], fill=RED)
d.rounded_rectangle([1250, smy + 110, CX1 - 30, smy + 170], radius=14, fill=(50, 50, 50))
d.text((1280, smy + 124), 'any state → SAFE on  KILL · LEAK · LOW BATTERY · lost heartbeat · 2 s dead-man   (thruster 1500 µs, rudder centred, cradle holds)', font=f_lab, fill=WHITE)
d.text((1250, smy + 200), 'Stops in series: the KILL rocker puts the firmware in SAFE (1500 µs, rudder centred), S1 cuts the battery, every branch has its own fuse,', font=f_small, fill=INK)
d.text((1250, smy + 234), 'and a 10 k pull-down holds the ESC signal low through boot. Tested: KILL stops the thruster within 40 ms (C025), and on the battery (C059).', font=f_small, fill=INK)
d.text((1250, smy + 290), 'Logs: CSV over USB on the bench (C027 calibration, C050 currents) · 59 loop cards in docs/LOG.md · FAILS_AND_FIXES.md 180 entries', font=f_small, fill=GREY)

# ---------- ACTUATION ----------
ay = 380; acw = 380; ach = 330
kill = Card(AX0 + 40, ay, 360, ach, Q(82), 'KILL rocker · SPDT', 'C → GPIO14 · RUN 3V3 · KILL GND')
btsL = Card(AX0 + 480, ay, acw, ach, Q(74), 'BTS7960 L', 'C050 PASS · off for water', dashed=True)
btsR = Card(AX0 + 920, ay, acw, ach, Q(74), 'BTS7960 R', 'C051 PASS · off for water', dashed=True)
rob = Card(AX0 + 1360, ay, acw, ach, P('C050_11.jpg'), 'ROB0154 tracks', 'built 25.10 · off the boat', dashed=True)
wire([kill.R(0.35), btsL.L(0.35)], CAN, w=7, dot_end=False, dash=True); wire([btsL.R(0.35), btsR.L(0.35)], CAN, w=7, dot_end=False, dash=True)
tag(AX0 + 440, ay + 80, 'EN', CAN); tag(AX0 + 880, ay + 80, 'EN', CAN)
wire([btsR.R(0.65), rob.L(0.65)], CMOT, w=8, dot_end=False); wire([btsL.B(0.5), (btsL.x + acw/2, ay + ach + 30), (rob.x + 60, ay + ach + 30), (rob.x + 60, ay + ach)], CMOT, w=8, dot_end=False)
tag(AX0 + 1320, ay + 200, 'M+ M−', CMOT)
flag(btsL.x + 10, ay - 20, 'F3 empty', C12); flag(btsR.x + 10, ay - 20, 'F3 empty', C12)
d.text((AX0 + 40, ay + ach + 78), 'Tracks: 0.08 A at 20 %, 0.34 A at 80 % on the bench (12 V, free-running) · for the water runs the chassis is off and F3 is empty', font=f_small, fill=GREY)
# thrusters row
ty = 850
cuL = Card(AX0 + 40, ty, acw, ach, Q(28), 'Cuifati 560 KV · centre', 'works · 0.58 A · C025/C059')
cuR = Card(AX0 + 460, ty, acw, ach, Q(28), 'Cuifati · right', 'faulty · FAILS 173', dashed=True)
t200 = Card(AX0 + 880, ty, acw, ach, P('t200.png'), 'Blue Robotics T200', 'planned replacement', qty=2, dashed=True)
besc = Card(AX0 + 1300, ty, acw, ach, P('basic_esc.png'), 'Basic ESC R3', '1500 µs stop · 3.3 V signal', qty=2, dashed=True)
flag(cuL.x + 10, ty - 20, 'F1 20 A', C12); flag(t200.x + 10, ty - 20, 'F1 20 A', C12)
tag(AX0 + 40, ty + ach + 30, 'GPIO1 → 74HCT125 1A → 1Y → ESC signal (5 V, not inverted)', CPWM, 'l')
wire([besc.L(0.5), t200.R(0.5)], CMOT, w=7, dot_end=False, dash=True)
# row 3: mounts + rudder
ry = 1320
kick = Card(AX0 + 40, ry, acw, ach, P('C057_20.jpg'), 'beam_leg mount', 'centre, under beams · C056')
rud = Card(AX0 + 460, ry, acw, ach, P('C057_21.jpg'), 'MG90S rudder', 'NACA 0015 · 2Y · C057')
flt = Card(AX0 + 880, ry, acw, ach, P('C059_50.jpg'), 'Water test · 31.10', 'on the battery · C059')
pesho = Card(AX0 + 1300, ry, acw, ach, P('C021_37.jpg'), 'Pesho · thermal dummy', 'red PLA · 37 °C · C021')
# rescue row
rsy = 1790
pca = Card(AX0 + 40, rsy, acw, ach, Q(72), 'PCA9685', '0x40 · CH12/13 · V+ 5 V')
td = Card(AX0 + 460, rsy, acw, ach, Q(30), 'TD-8120MG', 'lift slider 50–130°', qty=2)
arms = Card(AX0 + 880, rsy, acw, ach, P('C023_07.jpg'), 'Parallelogram arms', 'Ø5 cradle U · C023')
st = Card(AX0 + 1300, rsy, acw, ach, Q(29), 'ST3215 bus servo', 'option B · spare', qty=4, dashed=True)
wire([pca.R(0.5), td.L(0.5)], CPWM, w=6, dot_end=False); tag(AX0 + 440, rsy + 130, 'CH12/13', CPWM)
flag(pca.x + 10, rsy - 20, 'F2 15 A → QIQIAZI 5 V', C5)
d.text((AX0 + 40, rsy + ach + 18), 'OPEN (FAILS 180): only the higher PCA channel drives a servo; the next run lifts with one servo on CH13.', font=f_small, fill=RED_DK)
wire([(AX0, yb0), (AX0 + 18, yb0), (AX0 + 18, rsy + 165), (pca.x, rsy + 165)], CI2C0, w=6, dot_end=False)
wire([kill.B(0.5), (kill.x + 180, ay + ach + 20)], CAN, w=5, dot_end=False, dash=True); tag(kill.x + 180, ay + ach + 36, '→ GPIO14 → SAFE', CAN)
# hero
hero = Card(AX0 + 40, 2260, 820, 820, P('C059_37.jpg'), 'The robot as wired · 31.10 (C059)', 'hulls, beams, food box, beam_leg, thruster, rudder, cradle', ih=690)
d.text((AX0 + 900, 2290), 'What is tested (card → PASS):', font=f_legb, fill=INK)
for i, t in enumerate(['C023  cradle lifts Pesho (mirrored servo pair)', 'C025  thruster at 12 V, KILL → 1500 µs in 40 ms', 'C027  VBAT reading ±0.02 V from 10 to 12.6 V', 'C028  whole robot floats, phone drive over Wi-Fi', 'C047–C049  camera head: D45 sees a 39.8 °C head at 1.3 m', 'C050 / C051  both tracks run from the BTS7960s', 'C055  right thruster faulty, confirmed on a Mega', 'C058  LiPo balance charge to 12.60 V', 'C059  thruster + rudder in water, on battery, from the phone']):
    d.text((AX0 + 900, 2345 + i*44), t, font=f_leg, fill=INK)
d.text((AX0 + 900, 2760), 'Open:', font=f_legb, fill=INK)
for i, t in enumerate(['lift on one PCA channel only (FAILS 180)', 'lake test and full rescue cycle in water (P22)', 'replace the faulty right thruster', 'own PCB: carrier rev B (C032)']):
    d.text((AX0 + 900, 2815 + i*44), t, font=f_leg, fill=GREY)

# ---------- NEXT ----------
ny = 2745; ncw = 270; nch = 340
bo = Card(CX0 + 40, ny, ncw, nch, P('AR-Mini_xiao_breakout_rev0_assembled.png'), 'XIAO breakout rev 0', 'built · AISLER', ih=200)
cb = Card(CX0 + 340, ny, ncw, nch, P('AR-Mini_carrier_revB_assembled.png'), 'Carrier rev B', 'designed · C032', ih=200, dashed=True)
ls = Card(CX0 + 640, ny, ncw, nch, Q(78), 'BNO055 IMU', 'heading hold', ih=200, dashed=True)
wr = Card(CX0 + 940, ny, ncw, nch, Q(62), 'WROOM-1 N16R8', 'on the carrier', ih=200, qty=3, dashed=True)
pi = Card(CX0 + 1240, ny, ncw, nch, Q(64), 'Raspberry Pi 5', 'v2 2027 · ROS 2', ih=200, dashed=True)
co = Card(CX0 + 1540, ny, ncw, nch, Q(65), 'Active cooler', 'v2 2027', ih=200, dashed=True)

# ---------- LEGEND ----------
ly = 3180; lx = M
d.text((lx, ly), 'Wires:', font=f_legb, fill=INK); lx += 110
for col, t in ((C12, '12 V (fused branch)'), (C5, '5 V'), (CI2C0, 'I²C-0 (Wire)'), (CI2C1, 'I²C-1 (Wire1)'), (CPWM, 'PWM / ESC signal'), (CAN, 'analog · KILL / EN'), (CMOT, 'motor power'), (CUSB, 'USB · Wi-Fi')):
    d.line([(lx, ly + 18), (lx + 60, ly + 18)], fill=col, width=8); d.text((lx + 72, ly), t, font=f_leg, fill=INK); lx += 72 + f_leg.getlength(t) + 50
d.text((M, ly + 50), 'Dashed card = idle, designed or on order.  Solid wire = wired and tested (card numbers = tests in docs/LOG.md).  Common GND everywhere; 12 V reaches the breadboard only on the thin VBAT sense wire (F4, ≈100 µA).', font=f_leg, fill=INK)
d.text((M, ly + 95), 'AmphiReach · AR-Mini 1:9 demonstrator · architecture v4 (as wired 31.10.2026; v1 06.10, v2 27.10, v3 28.10 in docs/diagrams/) · photos: BOM listings + build cards · T. Kyoseva, Sofia', font=f_small, fill=GREY)

img.save(f'{OUT}/AR-Mini_architecture_v4.png', dpi=(300, 300))
img.save(f'{OUT}/AR-Mini_architecture_v4.pdf', resolution=300.0)
img.resize((2000, int(H*2000/W)), Image.LANCZOS).save(f'{OUT}/v4_view.jpg', quality=82)
print('done')
