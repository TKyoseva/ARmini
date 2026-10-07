# Generated the PNG/PDF next to this folder. Product photos are extracted from docs/bom/AR_BOM_2026-10-06.xlsx
# (column Picture) into an image folder first; the paths below are the ones used on the build machine.
#!/usr/bin/env python3
"""AR-Mini — system architecture v1 (XIAO controller), A3 landscape 300 dpi."""
from PIL import Image, ImageDraw, ImageFont, ImageOps
import math

OUT = '/mnt/user-data/outputs'
I3 = '/home/claude/bom_img3'
OLDI = '/home/claude/bom_img'
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
def Q(r): return f'{I3}/r{r:03d}.png'

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

# ================= LAYOUT =================
M = 60
title = 'AR-Mini  ·  System Architecture v1'
tw = f_title.getlength(title); d.text(((W-tw)/2, 40), title, font=f_title, fill=INK)
d.rectangle([(W-tw)/2, 160, (W+tw)/2, 168], fill=RED)
sub = 'Controller v1: one XIAO ESP32-S3 Sense runs the whole robot  ·  power is fused per branch, signals only pass through the XIAO and the PCA9685  ·  06.10.2026'
d.text(((W - f_sub.getlength(sub))/2, 186), sub, font=f_sub, fill=GREY)

TOP = 270
PX0, PX1 = M, 1120                     # power
CX0, CX1 = 1200, 3060                  # sensing / control / v2
AX0, AX1 = 3140, W - M                 # actuation
BOT = 3130
section((PX0, TOP, PX1, BOT), 'Power')
section((CX0, TOP, CX1, 860), 'Sensing')
section((CX0, 1010, CX1, 2560), 'Control')
section((CX0, 2650, CX1, BOT), 'v2 · 2027 (not in v1)', dashed=True)
section((AX0, TOP, AX1, BOT), 'Actuation')

# ---------- POWER ----------
cw, ch = 400, 330
px = PX0 + 50
lipo = Card(px, 380, cw, ch, Q(54), 'Turnigy 3S 2200 mAh', '11.1 V · 40 C · XT60', qty=2)
fuse = Card(px, 790, cw, ch, Q(80), 'Inline fuse 30 A', 'GT4652 · on the XT60 lead')
sw = Card(px, 1200, cw, ch, Q(78), 'Main switch 50 A', 'R13-401A2A · cuts everything')
fb = Card(px, 1610, cw, 360, Q(81), '6-slot fuse block', 'branches below')
for a, b in ((lipo, fuse), (fuse, sw), (sw, fb)):
    wire([a.B(0.5), b.T(0.5)], C12, w=10, dot_end=False)
tag(px + cw/2 + 20, 760, '12 V', C12, 'l'); tag(px + cw/2 + 20, 1170, '12 V', C12, 'l'); tag(px + cw/2 + 20, 1580, '12 V', C12, 'l')
# branch list
bx = PX0 + 40; by = 2010
d.text((bx + 10, by), 'Fused branches (12 V)', font=f_legb, fill=INK)
branches = [('F1 20 A', 'ESC + thrusters ×2'), ('F2 15 A', 'servo bus driver'), ('F3 10 A', 'BTS7960 ×2 → tracks'),
            ('F4 5 A', 'logic buck → 5 V'), ('F5 5 A', 'Pi buck (v2)')]
for i, (f, t) in enumerate(branches):
    yy = by + 70 + i*52
    flag(bx + 10, yy, f, C12); d.text((bx + 160, yy - 15), t, font=f_small, fill=INK)
# bucks
bw_ = 470
mz = Card(PX0 + 40, 2340, 300, 330, Q(76), 'MZHOU buck', '12 → 5 V · 3 A')
qq = Card(PX0 + 40, 2730, 300, 330, Q(77), 'QIQIAZI buck', '12 → 5 V · 5 A')
flag(mz.x + mz.w + 14, mz.y + 50, 'F4 5 A', C12)
flag(qq.x + qq.w + 14, qq.y + 50, 'F5 5 A', C12)
d.text((mz.x + mz.w + 14, mz.y + 90), 'logic rail', font=f_small, fill=GREY)
d.text((qq.x + qq.w + 14, qq.y + 90), 'Pi 5 rail', font=f_small, fill=GREY)
# charger note
d.text((PX0 + 40, BOT - 60), 'Charged off-robot on SkyRC iMAX B6 V2', font=f_small, fill=GREY)

# ---------- SENSING ----------
sw_ = 330; sg = (CX1 - CX0 - 60 - 5*sw_) / 4
sx = [CX0 + 30 + i*(sw_ + sg) for i in range(5)]
sy, sh = 370, 400
s_d45 = Card(sx[0], sy, sw_, sh, Q(73), 'MLX90642-D45', 'thermal · forward 45°')
s_bno = Card(sx[1], sy, sw_, sh, Q(75), 'BNO055 IMU', '9-DOF · heading / roll')
s_110 = Card(sx[2], sy, sw_, sh, Q(74), 'MLX90640 110°', 'thermal · on the cradle')
s_leak = Card(sx[3], sy, sw_, sh, None, 'Leak probe', '2 bare wires · hull floor', icon=icon_leak)
s_vb = Card(sx[4], sy, sw_, sh, Q(57), 'VBAT divider', '100 k / 33 k → ÷ 4')

# buses in the gap between sensing (860) and control (1010)
Y_I2C0, Y_I2C1, Y_A1, Y_A0 = 885, 915, 945, 975

# ---------- CONTROL ----------
pcb = Card(1830, 1180, 600, 560, f'{OUT}/AR-Mini_xiao_breakout_rev0_assembled.png', 'XIAO ESP32-S3 Sense', 'on breakout rev 0 (own PCB, 50 × 40 mm)', crop=(190, 180, 2200, 1810), ih=440)
# pin labels left / right
lp = [('A0  VBAT', CAN), ('A1  LEAK + KILL', CAN), ('D2 / D3  I²C-1', CI2C1), ('D4 / D5  I²C-0', CI2C0)]
rp = [('5 V in', C5), ('D6 / D7  UART1', CUART), ('USB-C  → Pi (v2)', CUSB)]
LPX = pcb.x; RPX = pcb.x + pcb.w
lpy = [1260, 1340, 1420, 1500]
for (t, c), yy in zip(lp, lpy):
    d.line([(LPX - 40, yy), (LPX, yy)], fill=c, width=7); tag(LPX - 50, yy, t, c, 'r', font=f_pin)
rpy = [1260, 1420, 1580]
for (t, c), yy in zip(rp, rpy):
    d.line([(RPX, yy), (RPX + 40, yy)], fill=c, width=7); tag(RPX + 50, yy, t, c, 'l', font=f_pin)

# sensors -> buses
def drop(card, ybus, col):
    x = card.B(0.5)[0]; wire([card.B(0.5), (x, ybus)], col, w=6)
drop(s_d45, Y_I2C0, CI2C0); drop(s_bno, Y_I2C0, CI2C0); drop(s_110, Y_I2C1, CI2C1)
drop(s_leak, Y_A1, CAN); drop(s_vb, Y_A0, CAN)
# buses horizontal
xL = lambda yy: LPX - 330 - (yy - 1260)/80*40
# I2C-0 bus: from D45 x to PCA in actuation (extends right)
pins_x = {'A0': 1360, 'A1': 1410, 'I2C1': 1460, 'I2C0': 1510}
d.line([(s_d45.B()[0], Y_I2C0), (AX0 + 40, Y_I2C0)], fill=CI2C0, width=6)
d.line([(s_110.B()[0], Y_I2C1), (pins_x['I2C1'], Y_I2C1)], fill=CI2C1, width=6)
d.line([(s_leak.B()[0], Y_A1), (pins_x['A1'], Y_A1)], fill=CAN, width=6)
d.line([(s_vb.B()[0], Y_A0), (pins_x['A0'], Y_A0)], fill=CAN, width=6)
# down into pins
for key, yb, yp, col in (('A0', Y_A0, lpy[0], CAN), ('A1', Y_A1, lpy[1], CAN), ('I2C1', Y_I2C1, lpy[2], CI2C1), ('I2C0', Y_I2C0, lpy[3], CI2C0)):
    xx = pins_x[key]
    tagw = f_pin.getlength(dict(A0=lp[0][0], A1=lp[1][0], I2C1=lp[2][0], I2C0=lp[3][0])[key]) + 24
    xend = LPX - 50 - tagw
    wire([(xx, yb), (xx, yp), (xend, yp)], col, w=6, dot_end=False)
d.ellipse([s_d45.B()[0]-10, Y_I2C0-10, s_d45.B()[0]+10, Y_I2C0+10], fill=CI2C0)
tag(CX0 + 160, Y_I2C0 + 2, 'I²C-0 · Wire · 0x33 / 0x28 / 0x40', CI2C0, 'l', font=f_small) if False else None
# bus labels in the gap
d.text((CX1 - 640, Y_I2C0 - 32), 'I²C-0  (D45 · BNO055 · PCA9685)', font=f_small, fill=CI2C0)
# 3V3 note
d.text((CX0 + 30, 2480), 'XIAO 3V3 → sensors + PCA9685 VCC · 4.7 k pull-ups · common GND everywhere', font=f_small, fill=C33)

# on-board blocks under the XIAO
ob_y = 1820
ob = [('OV3660 camera', 'on XIAO Sense · arch pan', Q(61), (60, 0, 520, 300)),
      ('microSD log', 'CSV 10 Hz + snapshots', Q(68), None),
      ('Firmware (FreeRTOS)', 'core 0 perception · core 1 control', Q(87), None)]
obw = 470; obg = (CX1 - CX0 - 60 - 3*obw) / 2
for i, (n, sp, src, cr) in enumerate(ob):
    Card(CX0 + 30 + i*(obw + obg), ob_y, obw, 330, src, n, sp, crop=cr, ih=200)
    cx = CX0 + 30 + i*(obw + obg) + obw/2
d.line([(pcb.B()[0], pcb.y + pcb.h), (pcb.B()[0], ob_y)], fill=LINE, width=4)
d.text((pcb.B()[0] + 14, pcb.y + pcb.h + 14), 'on board', font=f_small, fill=GREY)
# controller states
d.text((CX0 + 30, 2205), 'Mission state machine (core 1)', font=f_grp, fill=RED_DK)
states = ['SEARCH', 'APPROACH', 'ALIGN', 'LIFT', 'RETURN']
bwS = 270; gS = (CX1 - CX0 - 60 - 5*bwS) / 4
for i, t in enumerate(states):
    x0 = CX0 + 30 + i*(bwS + gS)
    d.rounded_rectangle([x0, 2260, x0 + bwS, 2340], radius=16, fill=(250, 235, 235), outline=RED, width=3)
    d.text((x0 + bwS/2 - f_name.getlength(t)/2, 2280), t, font=f_name, fill=RED_DK)
    if i < 4:
        ax = x0 + bwS + 8; d.line([(ax, 2300), (ax + gS - 16, 2300)], fill=RED, width=5)
        d.polygon([(ax + gS - 16, 2290), (ax + gS - 4, 2300), (ax + gS - 16, 2310)], fill=RED)
t = 'any state  →  SAFE  on  KILL  ·  LEAK  ·  LOW BATTERY  ·  lost target'
d.rounded_rectangle([CX0 + 30, 2370, CX1 - 30, 2430], radius=16, fill=(60, 60, 60))
d.text(((CX0 + CX1)/2 - f_lab.getlength(t)/2, 2384), t, font=f_lab, fill=WHITE)

# 5 V from MZHOU into XIAO
y5 = rpy[0]
wire([(mz.R(0.75)[0], mz.y + mz.h*0.75), (1160, mz.y + mz.h*0.75), (1160, 1110), (RPX + 330, 1110), (RPX + 330, y5), (RPX + 50 + f_pin.getlength('5 V in') + 24, y5)], C5, w=7)
tag(1160, 1700, '5 V logic', C5)

# ---------- ACTUATION ----------
aw, ah = 380, 360
c1, c2, c3, c4 = AX0 + 40, AX0 + 470, AX0 + 900, AX0 + 1330
pca = Card(c1, 400, aw, 400, Q(69), 'PCA9685', '16-ch PWM · I²C 0x40')
thL = Card(c3, 400, aw, ah, Q(29), 'Thruster L + ESC', 'Cuifati 560 KV · CCW')
thR = Card(c4, 400, aw, ah, Q(29), 'Thruster R + ESC', 'Cuifati 560 KV · CW')
btL = Card(c3, 880, aw, ah, Q(71), 'BTS7960 L', '43 A H-bridge')
btR = Card(c4, 880, aw, ah, Q(71), 'BTS7960 R', '43 A H-bridge')
rob = Card(c3, 1340, c4 + aw - c3, 400, Q(28), 'DFRobot ROB0154 tracks', '2 DC motors · axis 62 mm above the hull floor', ih=280)
kill = Card(c1, 900, aw, 360, Q(79), 'Logic kill (rocker)', 'ON-ON 20 A')
ind = Card(c1, 1340, aw, 330, None, 'Buzzer + 3 LEDs', 'CH6 · CH7–9', icon=icon_ind)
# I2C-0 into PCA
wire([(AX0 + 40, Y_I2C0), (AX0 + 20, Y_I2C0), (AX0 + 20, pca.y + 300), pca.L(0.75)], CI2C0, w=6)
d.line([(AX0 - 80, Y_I2C0), (AX0 + 20, Y_I2C0)], fill=CI2C0, width=6)
# PWM to thrusters
yP = 365
wire([pca.R(0.3), (c2 + 200, pca.y + 120), (c2 + 200, yP), (thL.T()[0], yP), thL.T()], CPWM, w=6)
wire([(c2 + 200, yP), (thR.T()[0], yP), thR.T()], CPWM, w=6, dot_end=True)
tag(c2 + 200, 600, 'CH0 / CH1', CPWM)
# PWM to BTS
wire([pca.R(0.8), (c2 + 140, pca.y + 320), (c2 + 140, btL.y + 120), btL.L(120/ah)], CPWM, w=6)
wire([(c2 + 140, btL.y + 120), (c2 + 140, btL.y + ah + 30), (btR.B()[0] - 120, btL.y + ah + 30), (btR.B()[0] - 120, btR.y + ah)], CPWM, w=6)
tag(c2 + 140, 1080, 'CH2–5', CPWM)
# motors
wire([btL.B(), (btL.B()[0], rob.y)], CMOT, w=8); wire([(btR.B()[0] + 60, btR.y + ah), (btR.B()[0] + 60, rob.y)], CMOT, w=8)
tag(btL.B()[0] + 4, 1295, 'M+ / M−', (160, 120, 0), 'l')
# kill -> OE ; indicators
wire([kill.T(), pca.B()], CAN, w=6)
tag(kill.T()[0] + 6, 850, 'OE', CAN, 'l')
wire([ind.T(0.7), (ind.T(0.7)[0], kill.y + kill.h)], CPWM, w=5, dot_end=False)
d.text((ind.x + ind.w*0.7 + 12, kill.y + kill.h + 12), 'CH6–9', font=f_small, fill=CPWM)
# kill -> A1 ladder (route left into gap bus)
wire([kill.L(0.5), (AX0 + 20 - 10, kill.y + kill.h*0.5)], CAN, w=6, dot_end=False)
d.line([(AX0 + 10, kill.y + kill.h*0.5), (AX0 + 10, Y_A1 + 0)], fill=CAN, width=6)
d.line([(pins_x['A1'], Y_A1), (AX0 + 10, Y_A1)], fill=CAN, width=6)
d.ellipse([pins_x['A1']-10, Y_A1-10, pins_x['A1']+10, Y_A1+10], fill=CAN)
# power flags on actuation
flag(thL.x + 12, thL.y + 30, 'F1 20 A', C12); flag(thR.x + 12, thR.y + 30, 'F1 20 A', C12)
flag(btL.x + 12, btL.y + 30, 'F3 10 A', C12); flag(btR.x + 12, btR.y + 30, 'F3 10 A', C12)
# servo bus
sv = Card(c1, 1880, aw, 380, Q(72), 'Serial bus servo driver', 'Waveshare · 1 Mbps')
flag(sv.x + 12, sv.y + 30, 'F2 15 A', C12)
sw4 = 330; sg4 = (AX1 - 30 - (c1 + aw + 60) - 4*sw4) / 3
sxs = [c1 + aw + 60 + i*(sw4 + sg4) for i in range(4)]
ids = [('ST3215 · ID 1', 'arm left'), ('ST3215 · ID 2', 'arm right'), ('ST3215 · ID 3', 'camera pan'), ('ST3215 · ID 4', 'spare / v2')]
sv_cards = [Card(x, 1880, sw4, 380, Q(30), n, s) for x, (n, s) in zip(sxs, ids)]
prev = sv
for c in sv_cards:
    wire([prev.R(0.82), c.L(0.82)], CUART, w=7, dot_end=False)
    prev = c
tag((sxs[0] + sxs[-1] + sw4)/2, 1840, 'ID 1–4 on one 5264 daisy-chain (half-duplex, 1 Mbps)', CUART)
d.text((sxs[0], 2290), '30 kg·cm @ 12 V · magnetic encoder · position / load / temperature feedback', font=f_small, fill=GREY)
# UART from XIAO
yU = rpy[1]
wire([(RPX + 50 + f_pin.getlength('D6 / D7  UART1') + 24, yU), (CX1 + 40, yU), (CX1 + 40, sv.y + 120), sv.L(120/380)], CUART, w=7)
tag(CX1 + 40, 1800, 'UART1', CUART)

# arm note
d.text((c1, 2420), 'Parallelogram lift: arm 110 mm · deploy 215° / stow 45° · cradle Ø5 rod 220 × 123 mm', font=f_small, fill=INK)
d.text((c1, 2470), 'Thrusters: differential steering on water · tracks: ROB0154 on land, motor axis above the waterline', font=f_small, fill=INK)

# ---------- v2 ----------
pi = Card(CX0 + 40, 2750, 380, 330, Q(62), 'Raspberry Pi 5 · 8 GB', 'ROS 2 Jazzy · rosbag', dashed=True)
cool = Card(CX0 + 450, 2750, 300, 330, Q(63), 'Active cooler', 'fan + heatsink', dashed=True)
wro = Card(CX0 + 1100, 2750, 340, 330, Q(60), 'ESP32-S3-WROOM-1', 'carrier rev A · N16R8', dashed=True, qty=3)
dkl = Card(CX0 + 1470, 2750, 340, 330, Q(59), 'ESP32-S3-DevKit-Lipo', 'firmware test board', dashed=True, qty=3)
d.text((CX0 + 820, 2810), 'next:', font=f_legb, fill=GREY)
d.text((CX0 + 790, 2860), 'replaces', font=f_small, fill=GREY); d.text((CX0 + 790, 2892), 'the XIAO', font=f_small, fill=GREY)
# USB XIAO -> Pi (dashed)
yUS = rpy[2]
wire([(RPX + 50 + f_pin.getlength('USB-C  → Pi (v2)') + 24, yUS), (CX1 - 60, yUS), (CX1 - 60, 2620), (pi.T()[0], 2620), pi.T()], CUSB, w=6, dash=True)
# Pi 5 V from QIQIAZI
wire([qq.R(0.75), (CX0 - 10, qq.y + qq.h*0.75), (CX0 - 10, pi.y + pi.h*0.5), pi.L()], C5, w=7, dash=True)

# ---------- LEGEND ----------
ly = BOT + 40
d.text((M, ly), 'Wires:', font=f_legb, fill=INK)
leg = [(C12, '12 V (fused branch)'), (C5, '5 V'), (C33, '3V3'), (CI2C0, 'I²C-0'), (CI2C1, 'I²C-1'), (CUART, 'UART / servo bus'),
       (CPWM, 'PWM'), (CAN, 'analog / kill'), (CMOT, 'motor power'), (CUSB, 'USB (v2, dashed)')]
x = M + 120
for col, t in leg:
    d.line([(x, ly + 20), (x + 70, ly + 20)], fill=col, width=9); d.text((x + 82, ly + 3), t, font=f_leg, fill=INK)
    x += 82 + f_leg.getlength(t) + 50
ly2 = ly + 60
flag(M + 120, ly2 + 18, 'F1 20 A', C12)
d.text((M + 270, ly2 + 2), '= fed from that fuse-block slot (12 V).   Common GND for every module.   Kill: 50 A main switch (hardware) + logic rocker → PCA9685 OE + ADC ladder on A1.', font=f_leg, fill=INK)
ly3 = ly2 + 56
d.text((M, ly3), 'AmphiReach · AR-Mini 1:9 demonstrator · architecture v1 (XIAO only, autumn 2026) · photos from AR_BOM_06_10_2026_v3.xlsx · T. Kyoseva, Sofia', font=f_small, fill=GREY)

img.save(f'{OUT}/AR-Mini_architecture_v1.png', dpi=(300, 300))
img.save(f'{OUT}/AR-Mini_architecture_v1.pdf', resolution=300.0)
img.resize((W//3, H//3), Image.LANCZOS).save('/home/claude/vbom/arch_prev.png')
print('ok')
