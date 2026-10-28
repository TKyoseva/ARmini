# Generated the PNG/PDF next to this folder. Product photos are extracted from docs/bom/AR_BOM_2026-10-06.xlsx
# (column Picture) into an image folder first; the paths below are the ones used on the build machine.
#!/usr/bin/env python3
"""AR-Mini visual BOM poster v3 (28.10.2026) — A3 landscape, 300 dpi (PIL). Photos: docs/bom/AR_BOM_2026-10-09.xlsx (column Picture, file = BOM row) + 01_Loops ★ photos."""
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageOps
import math, os, sys

IMG = '/tmp/claude-0/-home-user/5fc25332-8a11-540b-8d8b-b4939c32d95d/scratchpad/bom/img'
PH = '/tmp/claude-0/-home-user/5fc25332-8a11-540b-8d8b-b4939c32d95d/scratchpad/bom/ph'
OUT = '/tmp/claude-0/-home-user/5fc25332-8a11-540b-8d8b-b4939c32d95d/scratchpad/bom/out'
W, H = 4961, 3508          # A3 landscape @ 300 dpi
S = 1.0                    # global scale (unused)

# ---------- palette ----------
RED = (181, 18, 27)
RED_DK = (143, 14, 21)
RED_LT = (225, 90, 95)
INK = (26, 26, 26)
GREY = (105, 105, 105)
LINE = (70, 70, 70)
PILL = (242, 242, 242)
PILL_B = (190, 190, 190)
WHITE = (255, 255, 255)

# ---------- fonts ----------
FD = '/usr/share/fonts/opentype/inter/'
def F(name, size): return ImageFont.truetype(FD + name, size)
f_title = F('InterDisplay-Bold.otf', 104)
f_sub = F('Inter-Regular.otf', 38)
f_colhdr = F('Inter-Bold.otf', 42)
f_grp = F('Inter-SemiBoldItalic.otf', 31)
f_name = F('Inter-Bold.otf', 30)
f_spec = F('Inter-Regular.otf', 25)
f_name_s = F('Inter-Bold.otf', 24)
f_spec_s = F('Inter-Regular.otf', 21)
f_band = F('Inter-Bold.otf', 40)
f_pill = F('Inter-Bold.otf', 31)
f_pill_s = F('Inter-Regular.otf', 23)
f_foot = F('Inter-Regular.otf', 26)
f_foot_b = F('Inter-Bold.otf', 26)
f_qty = F('Inter-Bold.otf', 26)

# ---------- image helpers ----------
def load_photo(path, crop=None):
    im = Image.open(path).convert('RGBA')
    if crop: im = im.crop(crop)
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert('RGB')
    # auto-trim near-white border
    g = ImageOps.grayscale(im)
    mask = g.point(lambda p: 255 if p < 240 else 0)
    bb = mask.getbbox()
    if bb:
        pad = 4
        bb = (max(0, bb[0]-pad), max(0, bb[1]-pad), min(im.width, bb[2]+pad), min(im.height, bb[3]+pad))
        im = im.crop(bb)
    return im

def fit(im, bw, bh, max_up=2.6):
    sc = min(bw / im.width, bh / im.height, max_up)
    nw, nh = max(1, int(im.width * sc)), max(1, int(im.height * sc))
    return im.resize((nw, nh), Image.LANCZOS)

def wrap(text, font, width):
    words = text.split()
    lines, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if font.getlength(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def rounded_dashed(d, box, r=28, dash=22, gap=14, width=4, fill=RED_LT):
    """Dashed rounded rectangle (approximate: dashes along straight edges, solid arcs)."""
    x0, y0, x1, y1 = box
    # arcs
    d.arc([x0, y0, x0+2*r, y0+2*r], 180, 270, fill=fill, width=width)
    d.arc([x1-2*r, y0, x1, y0+2*r], 270, 360, fill=fill, width=width)
    d.arc([x1-2*r, y1-2*r, x1, y1], 0, 90, fill=fill, width=width)
    d.arc([x0, y1-2*r, x0+2*r, y1], 90, 180, fill=fill, width=width)
    def dline(a, b):
        ax, ay = a; bx, by = b
        L = math.hypot(bx-ax, by-ay); n = max(1, int(L // (dash+gap)))
        ux, uy = (bx-ax)/L, (by-ay)/L
        # centre the dash pattern
        total = n*(dash+gap) - gap
        off = (L - total) / 2
        for i in range(n):
            s = off + i*(dash+gap)
            d.line([(ax+ux*s, ay+uy*s), (ax+ux*(s+dash), ay+uy*(s+dash))], fill=fill, width=width)
    dline((x0+r, y0), (x1-r, y0))
    dline((x1, y0+r), (x1, y1-r))
    dline((x0+r, y1), (x1-r, y1))
    dline((x0, y0+r), (x0, y1-r))

# ---------- schematic icons for items without product photos ----------
def icon(kind, bw, bh):
    """Return RGB image bw×bh drawn at 2× and downsampled."""
    k = 2
    im = Image.new('RGB', (bw*k, bh*k), WHITE)
    d = ImageDraw.Draw(im)
    Wd, Hd = bw*k, bh*k
    AL = (200, 203, 208); AL_D = (150, 153, 158); OUT = (80, 80, 80)
    if kind == 'altube':
        # isometric square tube
        L = Wd*0.78; s = Hd*0.30; dx, dy = s*0.55, -s*0.32
        x0, y0 = Wd*0.08, Hd*0.70
        # front face
        d.polygon([(x0, y0), (x0+L, y0), (x0+L, y0-s), (x0, y0-s)], fill=AL, outline=OUT, width=4)
        # top face
        d.polygon([(x0, y0-s), (x0+L, y0-s), (x0+L+dx, y0-s+dy), (x0+dx, y0-s+dy)], fill=(225, 227, 230), outline=OUT, width=4)
        # end face with hollow square
        d.polygon([(x0+L, y0), (x0+L+dx, y0+dy), (x0+L+dx, y0-s+dy), (x0+L, y0-s)], fill=AL_D, outline=OUT, width=4)
        t = s*0.14
        d.polygon([(x0+L+t*0.6, y0-t), (x0+L+dx-t*0.6, y0+dy-t), (x0+L+dx-t*0.6, y0-s+dy+t), (x0+L+t*0.6, y0-s+t)], fill=(60, 60, 60), outline=OUT, width=3)
    elif kind == 'rod':
        r = Hd*0.11; L = Wd*0.80; x0, y0 = Wd*0.08, Hd*0.5
        d.rectangle([x0, y0-r, x0+L, y0+r], fill=AL, outline=OUT, width=4)
        d.ellipse([x0+L-r*0.45, y0-r, x0+L+r*0.45, y0+r], fill=AL_D, outline=OUT, width=4)
        d.ellipse([x0-r*0.45, y0-r, x0+r*0.45, y0+r], fill=AL, outline=OUT, width=4)
        d.line([x0+r*0.3, y0-r*0.45, x0+L-r*0.5, y0-r*0.45], fill=(240, 240, 242), width=6)
    elif kind == 'foam':
        # thin grey sheet in perspective
        x0, y0 = Wd*0.12, Hd*0.74; L = Wd*0.62; dx, dy = Wd*0.22, -Hd*0.40; t = Hd*0.06
        d.polygon([(x0, y0), (x0+L, y0), (x0+L+dx, y0+dy), (x0+dx, y0+dy)], fill=(120, 120, 125), outline=OUT, width=4)
        d.polygon([(x0, y0), (x0+L, y0), (x0+L, y0+t), (x0, y0+t)], fill=(70, 70, 75), outline=OUT, width=4)
        d.polygon([(x0+L, y0), (x0+L+dx, y0+dy), (x0+L+dx, y0+dy+t), (x0+L, y0+t)], fill=(50, 50, 55), outline=OUT, width=4)
    elif kind == 'warmer':
        # rounded pouch with heat waves
        x0, y0, x1, y1 = Wd*0.18, Hd*0.30, Wd*0.82, Hd*0.92
        d.rounded_rectangle([x0, y0, x1, y1], radius=int(Hd*0.16), fill=(255, 190, 110), outline=(200, 120, 40), width=5)
        d.rounded_rectangle([x0+Wd*0.07, y0+Hd*0.1, x1-Wd*0.07, y1-Hd*0.1], radius=int(Hd*0.1), fill=(255, 215, 150), outline=None)
        for i, cx in enumerate([0.38, 0.5, 0.62]):
            pts = []
            for j in range(0, 21):
                yy = Hd*0.26 - j*(Hd*0.011)
                xx = Wd*cx + math.sin(j/20*math.pi*2)*Wd*0.025
                pts.append((xx, yy))
            d.line(pts, fill=(220, 90, 40), width=6, joint='curve')
    elif kind == 'leak':
        # two bare wires with stripped copper tips
        for i, (col, yy) in enumerate([((200, 30, 30), 0.40), ((40, 40, 40), 0.60)]):
            d.line([(Wd*0.08, Hd*yy), (Wd*0.70, Hd*yy)], fill=col, width=18)
            d.line([(Wd*0.70, Hd*yy), (Wd*0.92, Hd*yy)], fill=(205, 140, 70), width=10)
        d.rounded_rectangle([Wd*0.02, Hd*0.30, Wd*0.12, Hd*0.70], radius=8, fill=(240, 240, 235), outline=OUT, width=4)
        # water drops
        for cx, cy in [(0.80, 0.22), (0.88, 0.78)]:
            d.ellipse([Wd*cx-14, Hd*cy-14, Wd*cx+14, Hd*cy+14], fill=(90, 160, 230))
    elif kind == 'hulls':
        # top view: two catamaran hulls + two cross beams + arch (printed parts)
        hull = (70, 70, 72)
        for yy in (0.27, 0.73):
            L = Wd*0.86; x0 = Wd*0.07; h = Hd*0.16
            pts = [(x0+L*0.18, Hd*yy-h), (x0+L, Hd*yy-h), (x0+L, Hd*yy+h), (x0+L*0.18, Hd*yy+h), (x0, Hd*yy)]
            d.polygon(pts, fill=hull, outline=OUT, width=3)
        for xx in (0.60, 0.78):
            d.rectangle([Wd*xx-9, Hd*0.14, Wd*xx+9, Hd*0.86], fill=AL, outline=OUT, width=3)
        d.rectangle([Wd*0.30-7, Hd*0.14, Wd*0.30+7, Hd*0.86], fill=(255, 140, 0), outline=OUT, width=3)
        d.rectangle([Wd*0.34, Hd*0.40, Wd*0.52, Hd*0.60], fill=(255, 140, 0), outline=OUT, width=3)
    elif kind == 'dummy':
        red = (210, 40, 40)
        d.ellipse([Wd*0.08, Hd*0.30, Wd*0.30, Hd*0.70], fill=red, outline=OUT, width=4)
        d.rounded_rectangle([Wd*0.30, Hd*0.34, Wd*0.74, Hd*0.66], radius=int(Hd*0.14), fill=red, outline=OUT, width=4)
        d.rounded_rectangle([Wd*0.72, Hd*0.38, Wd*0.92, Hd*0.50], radius=16, fill=red, outline=OUT, width=4)
        d.rounded_rectangle([Wd*0.72, Hd*0.52, Wd*0.92, Hd*0.64], radius=16, fill=red, outline=OUT, width=4)
        d.ellipse([Wd*0.44, Hd*0.40, Wd*0.60, Hd*0.60], fill=(255, 200, 120), outline=(200, 120, 40), width=3)
    elif kind == 'jst':
        # JST-XH housing + crimped wires
        d.rectangle([Wd*0.50, Hd*0.30, Wd*0.92, Hd*0.70], fill=(245, 243, 230), outline=OUT, width=4)
        for i in range(4):
            yy = Hd*(0.36 + i*0.093)
            d.rectangle([Wd*0.56, yy, Wd*0.62, yy+Hd*0.05], fill=(60, 60, 60))
            col = [(200, 30, 30), (40, 40, 40), (230, 200, 30), (40, 120, 220)][i]
            d.line([(Wd*0.06, yy+Hd*0.025), (Wd*0.50, yy+Hd*0.025)], fill=col, width=10)
    elif kind == 'divider':
        # two resistors in series between VBAT and GND with a tap to A0
        x = Wd*0.5; ya, yb, yc = Hd*0.08, Hd*0.5, Hd*0.92
        d.line([(x, ya), (x, yc)], fill=OUT, width=6)
        for (y0r, lab) in ((Hd*0.17, "100 k"), (Hd*0.59, "30 k")):
            d.rectangle([x-Wd*0.07, y0r, x+Wd*0.07, y0r+Hd*0.24], fill=(245, 225, 190), outline=OUT, width=5)
            for j, col in enumerate([(120, 70, 20), (30, 30, 30), (230, 180, 30)] if lab == "100 k" else [(230, 120, 30), (230, 120, 30), (30, 30, 30)]):
                yy = y0r + Hd*0.05 + j*Hd*0.055
                d.rectangle([x-Wd*0.07+5, yy, x+Wd*0.07-5, yy+Hd*0.03], fill=col)
            d.text((x+Wd*0.10, y0r+Hd*0.06), lab, font=F('Inter-Bold.otf', 44), fill=OUT)
        d.line([(x, yb), (x+Wd*0.30, yb)], fill=(200, 30, 30), width=6)
        d.text((x+Wd*0.12, yb-Hd*0.16), "GPIO4", font=F('Inter-Bold.otf', 40), fill=(200, 30, 30))
        d.text((x-Wd*0.30, ya-Hd*0.02), "VBAT", font=F('Inter-Bold.otf', 40), fill=OUT)
        d.text((x-Wd*0.30, yc-Hd*0.16), "GND", font=F('Inter-Bold.otf', 40), fill=OUT)
    elif kind == 't200':
        # ducted thruster, side view: nozzle ring + hub + 3 blades, cable to the left
        cx, cy = Wd*0.58, Hd*0.5; R = Hd*0.40
        d.ellipse([cx-R, cy-R, cx+R, cy+R], fill=(40, 70, 110), outline=OUT, width=5)
        d.ellipse([cx-R*0.82, cy-R*0.82, cx+R*0.82, cy+R*0.82], fill=(225, 232, 240), outline=OUT, width=3)
        for k in range(3):
            a = math.radians(90 + k*120)
            d.polygon([(cx, cy), (cx+R*0.75*math.cos(a-0.35), cy-R*0.75*math.sin(a-0.35)), (cx+R*0.78*math.cos(a), cy-R*0.78*math.sin(a)), (cx+R*0.6*math.cos(a+0.45), cy-R*0.6*math.sin(a+0.45))], fill=(40, 70, 110), outline=OUT, width=3)
        d.ellipse([cx-R*0.2, cy-R*0.2, cx+R*0.2, cy+R*0.2], fill=(60, 90, 130), outline=OUT, width=3)
        d.line([(Wd*0.04, cy+R*0.1), (cx-R, cy+R*0.1)], fill=(30, 30, 30), width=14)
        d.text((Wd*0.03, Hd*0.06), "T200", font=F('Inter-Bold.otf', 54), fill=(40, 70, 110))
    elif kind == 'esc':
        # small ESC: heat-shrunk brick, 3 motor wires right, 2 power wires + signal lead left
        x0, y0, x1, y1 = Wd*0.30, Hd*0.30, Wd*0.72, Hd*0.72
        d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=(45, 45, 50), outline=OUT, width=4)
        d.text((x0+Wd*0.05, y0+Hd*0.09), "Basic\nESC", font=F('Inter-Bold.otf', 40), fill=WHITE, spacing=4)
        for i, col in enumerate([(40, 40, 40), (40, 40, 40), (40, 40, 40)]):
            yy = y0 + Hd*0.08 + i*Hd*0.13
            d.line([(x1, yy), (Wd*0.94, yy)], fill=col, width=10)
        d.line([(x0, y0+Hd*0.08), (Wd*0.06, y0+Hd*0.08)], fill=(200, 30, 30), width=12)
        d.line([(x0, y0+Hd*0.21), (Wd*0.06, y0+Hd*0.21)], fill=(30, 30, 30), width=12)
        for i, col in enumerate([(230, 230, 230), (200, 30, 30), (40, 40, 40)]):
            d.line([(x0, y0+Hd*0.33+i*Hd*0.025), (Wd*0.06, y0+Hd*0.33+i*Hd*0.025)], fill=col, width=5)
    elif kind == 'dip':
        # DIP-14 package
        x0, y0, x1, y1 = Wd*0.14, Hd*0.30, Wd*0.86, Hd*0.70
        for i in range(7):
            xx = x0 + Wd*0.06 + i*Wd*0.1
            d.rectangle([xx-7, y0-Hd*0.12, xx+7, y0], fill=(190, 190, 195), outline=OUT, width=2)
            d.rectangle([xx-7, y1, xx+7, y1+Hd*0.12], fill=(190, 190, 195), outline=OUT, width=2)
        d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=(35, 35, 38), outline=OUT, width=4)
        d.ellipse([x0+10, (y0+y1)/2-16, x0+42, (y0+y1)/2+16], fill=(90, 90, 95))
        d.text((x0+Wd*0.12, y0+Hd*0.1), "SN74AHCT125N", font=F('Inter-Bold.otf', 36), fill=(220, 220, 220))
    elif kind == 'pcb':
        d.rounded_rectangle([Wd*0.08, Hd*0.12, Wd*0.92, Hd*0.88], radius=20, fill=(30, 110, 60), outline=OUT, width=4)
    else:
        d.rectangle([10, 10, Wd-10, Hd-10], outline=OUT, width=4)
    return im.resize((bw, bh), Image.LANCZOS)

# ---------- catalogue ----------
import glob as _g
def Q(r, crop=None):
    p = _g.glob(f'{IMG}/r{r:03d}.*')[0]
    return dict(img=p, crop=crop)
def P(name, crop=None): return dict(img=f'{PH}/{name}', crop=crop)
def I(kind): return dict(icon=kind)
def it(src, name, spec='', qty=None):
    d = dict(src); d.update(name=name, spec=spec, qty=qty); return d

_w, _h = _I.open(f'{PH}/C053_01.jpg').size if False else (0, 0)
from PIL import Image as _I
_w, _h = _I.open(f'{PH}/C053_01.jpg').size
C053_CROP = (0, int(_h*0.12), _w, int(_h*0.80))

COLUMNS = [
    ("Compute & Control", [
        ("Controller v1 · bench (autumn 2026)", [
            it(Q(61), "Olimex ESP32-S3-DevKit-Lipo", "main controller · Wi-Fi AP"),
            it(Q(63), "Seeed XIAO ESP32-S3 Sense", "camera node · OV3660"),
            it(Q(72), "PCA9685 16-ch PWM driver", "I²C 0x40 · cradle CH10/11"),
            it(Q(74), "BTS7960 43 A H-bridge", "tracks L/R · C050, C051", qty=2),
        ]),
        ("Own PCBs · rev 0 built, rev B designed", [
            it(P('AR-Mini_xiao_breakout_rev0_assembled.png', (190, 180, 2200, 1810)), "XIAO breakout rev 0", "KiCad · AISLER · 50 × 40"),
            it(P('AR-Mini_carrier_revB_assembled.png'), "Carrier rev B · 100 × 80", "KiCad 10 · DevKit + modules"),
            it(Q(62), "ESP32-S3-WROOM-1 N16R8", "16 MB flash · 8 MB PSRAM", qty=3),
            it(P('sn74ahct125n.png'), "SN74AHCT125N level shifter", "ESC signal 3.3 → 5 V · to buy", qty=5),
        ]),
        ("Controller v2 · ROS 2 (2027)", [
            it(Q(64), "Raspberry Pi 5 · 8 GB", "ROS 2 Jazzy · USB to DevKit"),
            it(Q(65), "Active cooler for Pi 5", "fan + heatsink"),
        ]),
    ]),
    ("Sensing", [
        ("Thermal", [
            it(Q(76), "MLX90642-D45 thermal camera", "forward search · Wire · C048"),
            it(Q(77), "MLX90640 110° thermal camera", "32 × 24 px · Wire1 · C029"),
        ]),
        ("Vision & camera head", [
            it(Q(63, crop=(60, 0, 520, 300)), "OV3660 2 MP camera (XIAO Sense)", "Wi-Fi stream · C049"),
            it(P('C047_13.jpg'), "Fixed camera head on the arch", "3 cameras · printed · C047"),
        ]),
        ("Inertial", [
            it(Q(78), "BNO055 9-DOF IMU", "heading · not wired yet"),
        ]),
        ("Safety inputs", [
            it(I('leak'), "Leak probe — two bare wires", "GPIO7 · 10 k / 4.7 k · wired"),
            it(I('divider'), "Battery monitor 100 k / 30 k", "VBAT → GPIO4 · C027"),
        ]),
    ]),
    ("Propulsion & Actuation", [
        ("Water", [
            it(Q(28), "Cuifati 560 KV thruster", "L runs · R faulty (FAILS 173)", qty=2),
            it(P('C042_10.jpg'), "Kick-up transom mount (printed)", "Ø5 hinge · C041/C042"),
            it(P('t200.png'), "Blue Robotics T200 thruster", "replacement · ordered 26.10", qty=2),
            it(P('basic_esc.png'), "Blue Robotics Basic ESC R3", "1500 µs stop · 3.3 V signal", qty=2),
        ]),
        ("Land", [
            it(Q(27), "DFRobot ROB0154 tracked chassis", "built 25.10 · both tracks run"),
            it(P('C050_11.jpg'), "ROB0154 assembled", "2 × DC 12 V · C050"),
        ]),
        ("Rescue arm (parallelogram lift)", [
            it(Q(30), "TD-8120MG 20 kg servo", "cradle lift · PCA9685 · C023", qty=2),
            it(Q(29), "Waveshare ST3215 30 kg bus servo", "option B · spare", qty=4),
        ]),
        ("Rudder & test rigs", [
            it(Q(31), "MG90S 9 g micro servo", "interim rudder (GPIO2) · rigs", qty=8),
            it(Q(51), "Waveshare 5264 servo cables", "ST3215 daisy-chain", qty=2),
        ]),
    ]),
    ("Power", [
        ("Energy", [
            it(Q(53), "Turnigy 2200 mAh 3S 40 C LiPo", "XT60 · 11.1 V", qty=2),
            it(Q(52), "SkyRC iMAX B6 V2 charger", "balance charge / storage"),
        ]),
        ("Protection & switching", [
            it(Q(81), "50 A toggle switch (main)", "R13-401A2A · OFF-ON"),
            it(Q(82), "20 A rocker SPDT (KILL)", "EN of both BTS7960 · GPIO14"),
            it(Q(83), "Inline fuse holder GT4652", "30 A main fuse"),
            it(Q(84), "6-slot blade fuse block", "20/15/10/5 A · C026"),
            it(Q(85), "Blade fuse kit · 250 pcs", "spares"),
        ]),
        ("Conversion", [
            it(Q(79), "MZHOU 12 → 5 V USB-C buck", "into the DevKit OTG USB-C"),
            it(Q(80), "QIQIAZI 10–90 V → 5 V 5 A buck", "Raspberry Pi 5 rail (v2)"),
        ]),
    ]),
    ("Wiring & Connectors", [
        ("Battery side", [
            it(Q(50), "XT60 pigtails · 10 pcs", "12 AWG silicone"),
            it(Q(48), "14 AWG silicone wire", "black + red · 2 m each", qty=4),
            it(Q(47), "Insulated spade connectors", "switches & fuse block"),
        ]),
        ("Logic side", [
            it(Q(49), "18 AWG silicone wire", "black + red · 2 m each", qty=4),
            it(Q(55), "JST-XH 2.54 kit + crimped leads", "2–6 pin · 22 AWG"),
            it(Q(59), "MOGAOPI component kit", "S8050 · 1 k / 10 k · divider"),
            it(Q(45), "Alkan wire ferrules · 800 pcs", "0.5–10 mm² terminals"),
            it(Q(46), "Heat-shrink tubing box", "Ø1.5–13 mm"),
        ]),
    ]),
    ("Structure & Materials", [
        ("3D printing (Creality K2 Pro)", [
            it(Q(23), "Creality Hyper PLA 1 kg", "6 colours, colour-coded", qty=7),
            it(Q(24), "Creality Hyper PETG 1 kg", "wet parts (hulls v2)", qty=4),
            it(P('C053_01.jpg', C053_CROP), "First dry assembly · 28.10", "all subsystems · C053"),
            it(P('C021_37.jpg'), "Rescue dummy “Pesho”", "red PLA · 37 °C bottle"),
        ]),
        ("Frame & enclosure", [
            it(Q(1), "Kantoflex Al profile 15 × 15 × 1", "cross-beams · 304 mm", qty=2),
            it(Q(2), "Aluminium rod Ø5 mm", "cradle U 220 × 123 · C020"),
            it(Q(12), "M12 nuts DIN 934 · ballast", "~240 g · trim and heel", qty=12),
            it(Q(26), "LANUCN IP65 box 150 × 110 × 70", "logic enclosure"),
        ]),
        ("Fasteners & bonding", [
            it(Q(18), "ruthex threaded inserts M2–M5", "+ 100 × M3S short"),
            it(Q(16), "DSM DIN 912 screw set · 640 pcs", "M3–M6 · + M2 set · nyloc"),
        ]),
    ]),
]

BAND_A = ("Tools & Workshop", [
    ("Fabrication", [
        it(Q(133), "Creality K2 Pro Combo", "300³ mm build"),
        it(Q(109), "Digital caliper", "0–150 mm"),
        it(P('dremel4000.png'), "Dremel 4000", "rotary tool"),
    ]),
    ("Soldering & crimping", [
        it(Q(35), "FNIRSI HS-03 iron", "2600 mAh"),
        it(Q(38), "Third hand ZD-126-4", "LED + iron stand"),
        it(Q(42), "Toolour third hand", "magnetic base"),
        it(Q(124), "YIHUA 948DQ-I", "fume extractor"),
        it(Q(36), "Solder Sn60Pb40", "0.8 mm · 100 g"),
        it(Q(37), "TOPNIK-ZEL flux", "RMA gel", qty=3),
        it(Q(43), "KNIPEX NexStrip", "strip · cut · crimp"),
        it(Q(44), "Preciva crimp set", "Dupont · JST-XH"),
    ]),
    ("Measurement & debug", [
        it(Q(110), "UNI-T UT61E+", "multimeter"),
        it(Q(111), "Logic analyzer", "24 MHz · 8 ch"),
        it(Q(108), "Jesverty SPS-3010N", "30 V · 10 A"),
        it(Q(107), "Laserliner ThermoSpot", "IR thermometer"),
        it(Q(54), "FT232RL USB-TTL", "servo config"),
    ]),
    ("Prototyping", [
        it(Q(57), "VooGenzek PCB kit", "perfboards", qty=2),
        it(Q(68), "Hailege jumper kit", "2 × 140 U-wires"),
        it(Q(66), "Alligator clips", "10 pcs"),
        it(Q(67), "Cleqee clip leads", "clip → Dupont"),
    ]),
    ("Computers", [
        it(P('macbook.png'), "MacBook Pro", "repo · CAD"),
        it(P('lenovo.png'), "Lenovo laptop", "ROS 2 sim"),
    ]),
    ("Documentation", [
        it(Q(127), "NEEWER magic arm", "table clamp"),
        it(Q(128), "ULANZI MT-79", "tripod 204 cm"),
        it(Q(129), "ULANZI VL49", "LED light"),
    ]),
])

BAND_B = ("Software & Services", [
    ("Design", [(86, "Fusion 360"), (87, "OpenSCAD"), (88, "KiCad 10"), (89, "Creality Print")]),
    ("Firmware & software", [(90, "PlatformIO"), (91, "Arduino IDE"), (94, "Python"), (95, "Git + GitHub"), (96, "Pi OS + ROS 2"), (93, "PulseView")]),
    ("AI collaborators", [(102, "Claude"), (103, "Cursor"), (104, "ChatGPT"), (105, "Gemini")]),
    ("Services & media", [(98, "AISLER"), (97, "Eurocircuits"), (99, "Printables"), (100, "SlideRoom"), (101, "DaVinci Resolve")]),
])

# ---------- drawing ----------
img = Image.new('RGB', (W, H), WHITE)
d = ImageDraw.Draw(img)

M = 70
# Title
title = "AR-Mini  ·  Bill of Materials"
tw = f_title.getlength(title)
d.text(((W - tw)/2, 48), title, font=f_title, fill=INK)
# underline accent under "Bill of Materials" — simple red rule
d.rectangle([(W - tw)/2, 170, (W + tw)/2, 178], fill=RED)
sub = "1:9 physical demonstrator of the AmphiReach amphibious rescue robot  ·  what goes into the robot (top) and what builds it (bottom)  ·  status 28.10.2026 (v3) · first dry assembly"
sw = f_sub.getlength(sub)
d.text(((W - sw)/2, 196), sub, font=f_sub, fill=GREY)

# ----- column geometry -----
COL_TOP = 290
NCOL = len(COLUMNS)
CGAP = 30
COLW = (W - 2*M - (NCOL-1)*CGAP) // NCOL
HDR_H = 82
PAD = 18
GPAD = 16          # padding inside a subgroup box
CELLS = 2
CELLW = (COLW - 2*PAD - 2*GPAD) // CELLS
IMG_W, IMG_H = CELLW - 26, 236
NAME_LH = 34
SPEC_LH = 28
GRP_TITLE_H = 44   # vertical space reserved for the subgroup title (sits on the border)
GRP_GAP = 34       # min gap between subgroups

def cell_height(item):
    lines = wrap(item['name'], f_name, IMG_W + 18)
    n = min(len(lines), 2)
    h = IMG_H + 12 + n*NAME_LH
    if item.get('spec'): h += SPEC_LH
    return h + 14

def group_height(items):
    rows = [items[i:i+CELLS] for i in range(0, len(items), CELLS)]
    h = GRP_TITLE_H//2 + GPAD
    for r in rows: h += max(cell_height(x) for x in r)
    return h + GPAD

def column_needed(groups):
    h = HDR_H + PAD + GRP_TITLE_H//2
    for g in groups: h += group_height(g[1]) + GRP_GAP
    return h - GRP_GAP + PAD

# bottom-area heights (fixed), used to find the column bottom
BAND_A_H = 400
BAND_B_H = 250
FOOT_H = 70
BGAP = 34
col_bottom_max = H - M - FOOT_H - BGAP - BAND_B_H - BGAP - BAND_A_H - BGAP
needed = max(column_needed(g) for _, g in COLUMNS)
COL_BOTTOM = col_bottom_max
print("needed", needed, "available", col_bottom_max - COL_TOP, "col_bottom", COL_BOTTOM)

def draw_item(x, y, item, cw, iw, ih, fn, fs, name_lh, spec_lh):
    """Draw one item cell with top-left (x,y), cell width cw; returns height used."""
    # image
    if 'icon' in item:
        pic = icon(item['icon'], iw, ih)
    else:
        pic = fit(load_photo(item['img'], item.get('crop')), iw, ih)
    px = x + (cw - pic.width)//2
    py = y + (ih - pic.height)//2
    img.paste(pic, (px, py))
    # qty badge
    if item.get('qty'):
        q = f"×{item['qty']}"
        qw = f_qty.getlength(q) + 22
        bx1 = x + cw - 4; bx0 = bx1 - qw; by0 = y + 16; by1 = by0 + 38
        d.rounded_rectangle([bx0, by0, bx1, by1], radius=12, fill=RED)
        d.text((bx0 + 11, by0 + 5), q, font=f_qty, fill=WHITE)
    # name
    ty = y + ih + 12
    lines_all = wrap(item['name'], fn, cw - 8)
    if len(lines_all) > 2: print("NAME TRUNCATED:", item['name'])
    lines = lines_all[:2]
    for ln in lines:
        lw = fn.getlength(ln)
        d.text((x + (cw - lw)/2, ty), ln, font=fn, fill=INK)
        ty += name_lh
    if item.get('spec'):
        spl = wrap(item['spec'], fs, cw - 4)
        if len(spl) > 1: print("SPEC TRUNCATED:", item['name'], '|', item['spec'])
        sp = spl[0]
        lw = fs.getlength(sp)
        d.text((x + (cw - lw)/2, ty), sp, font=fs, fill=GREY)
        ty += spec_lh
    return ty - y + 14

def draw_group(x0, y0, x1, title, items, cells, cellw, iw, ih, fn, fs, name_lh, spec_lh, title_h):
    """Dashed subgroup box with title on the top edge. Returns bottom y."""
    rows = [items[i:i+cells] for i in range(0, len(items), cells)]
    # layout rows first to know height
    y = y0 + title_h//2 + GPAD
    row_h = []
    for r in rows:
        row_h.append(max(cell_height_generic(x, iw, fn, fs, name_lh, spec_lh, ih) for x in r))
    hbox = title_h//2 + GPAD + sum(row_h) + GPAD
    box = (x0, y0 + title_h//2, x1, y0 + hbox)
    rounded_dashed(d, box)
    # title with white backing
    tw = f_grp.getlength(title)
    cx = (x0 + x1)/2
    d.rectangle([cx - tw/2 - 14, y0 + 2, cx + tw/2 + 14, y0 + title_h - 2], fill=WHITE)
    d.text((cx - tw/2, y0 + 4), title, font=f_grp, fill=RED_DK)
    # cells
    inner_w = (x1 - x0) - 2*GPAD
    for r, rh in zip(rows, row_h):
        n = len(r)
        total = n*cellw
        sx = x0 + GPAD + (inner_w - total)//2
        for i, item in enumerate(r):
            draw_item(sx + i*cellw, y, item, cellw, iw, ih, fn, fs, name_lh, spec_lh)
        y += rh
    return y0 + hbox

def cell_height_generic(item, iw, fn, fs, name_lh, spec_lh, ih):
    lines = wrap(item['name'], fn, iw + 18)
    n = min(len(lines), 2)
    h = ih + 12 + n*name_lh
    if item.get('spec'): h += spec_lh
    return h + 14

# ----- draw columns -----
for ci, (ctitle, groups) in enumerate(COLUMNS):
    x0 = M + ci*(COLW + CGAP); x1 = x0 + COLW
    # header bar
    d.rectangle([x0, COL_TOP, x1, COL_TOP + HDR_H], fill=RED)
    tw = f_colhdr.getlength(ctitle)
    d.text((x0 + (COLW - tw)/2, COL_TOP + (HDR_H - 50)/2), ctitle, font=f_colhdr, fill=WHITE)
    # body outline
    d.rectangle([x0, COL_TOP + HDR_H, x1, COL_BOTTOM], outline=LINE, width=3)
    # distribute groups vertically (justify: first at top, last at bottom)
    gh = [group_height(g[1]) for g in groups]
    avail = (COL_BOTTOM - PAD) - (COL_TOP + HDR_H + PAD + GRP_TITLE_H//2)
    slack = avail - sum(gh)
    gap = GRP_GAP if len(groups) == 1 else max(GRP_GAP, slack // (len(groups) - 1))
    gap = min(gap, 260)
    # if gap is capped, centre the block
    used = sum(gh) + gap*(len(groups)-1)
    y = COL_TOP + HDR_H + PAD + GRP_TITLE_H//2 + max(0, (avail - used)//2)
    y = y - GRP_TITLE_H//2
    for (gtitle, items), h in zip(groups, gh):
        yb = draw_group(x0 + PAD, y, x1 - PAD, gtitle, items, CELLS, CELLW, IMG_W, IMG_H,
                        f_name, f_spec, NAME_LH, SPEC_LH, GRP_TITLE_H)
        y = yb + gap

# ----- Band A: tools & workshop -----
BA_TOP = COL_BOTTOM + BGAP
BA_BOT = BA_TOP + BAND_A_H
LBL_W = 74
d.rectangle([M, BA_TOP, M + LBL_W, BA_BOT], fill=RED)
d.rectangle([M + LBL_W, BA_TOP, W - M, BA_BOT], outline=LINE, width=3)
def vlabel(text, x0, y0, x1, y1, font):
    tw = int(font.getlength(text)); th = 52
    t = Image.new('RGBA', (tw + 10, th), (0, 0, 0, 0))
    ImageDraw.Draw(t).text((5, 0), text, font=font, fill=WHITE)
    t = t.rotate(90, expand=True)
    img.paste(t, (int((x0 + x1)/2 - t.width/2), int((y0 + y1)/2 - t.height/2)), t)
vlabel(BAND_A[0], M, BA_TOP, M + LBL_W, BA_BOT, f_band)

# sub-boxes proportional to item count
groupsA = BAND_A[1]
S_IW, S_IH = 160, 160
S_CELLW = 182
S_NAME_LH, S_SPEC_LH = 28, 25
S_TITLE_H = 42
ax0 = M + LBL_W + 24; ax1 = W - M - 24
SGAP = 26
widths = [len(items)*S_CELLW + 2*GPAD for _, items in groupsA]
extra = (ax1 - ax0 - (len(groupsA)-1)*SGAP - sum(widths))
widths = [w + extra*w//sum(widths) for w in widths]
x = ax0
by = BA_TOP + 26
for (gtitle, items), w in zip(groupsA, widths):
    draw_group(x, by, x + w, gtitle, items, len(items), S_CELLW, S_IW, S_IH,
               f_name_s, f_spec_s, S_NAME_LH, S_SPEC_LH, S_TITLE_H)
    x += w + SGAP

# ----- Band B: software & services -----
BB_TOP = BA_BOT + BGAP
BB_BOT = BB_TOP + BAND_B_H
d.rectangle([M, BB_TOP, M + LBL_W, BB_BOT], fill=RED)
d.rectangle([M + LBL_W, BB_TOP, W - M, BB_BOT], outline=LINE, width=3)
vlabel("Software", M, BB_TOP, M + LBL_W, BB_BOT, f_band)
bx0 = M + LBL_W + 24; bx1 = W - M - 24
groupsB = BAND_B[1]
nb = sum(len(p) for _, p in groupsB)
LGAP = 18
lw_ = (bx1 - bx0 - (len(groupsB)-1)*SGAP - nb*LGAP) // nb
x = bx0
for gtitle, logos in groupsB:
    gw = len(logos)*(lw_ + LGAP) - LGAP
    rounded_dashed(d, (x - 8, BB_TOP + 34, x + gw + 8, BB_BOT - 16), r=24)
    tw = f_grp.getlength(gtitle)
    d.rectangle([x + gw/2 - tw/2 - 14, BB_TOP + 14, x + gw/2 + tw/2 + 14, BB_TOP + 54], fill=WHITE)
    d.text((x + gw/2 - tw/2, BB_TOP + 14), gtitle, font=f_grp, fill=RED_DK)
    for r, label in logos:
        pic = fit(load_photo(Q(r)['img']), lw_ - 24, 110, max_up=3)
        img.paste(pic, (int(x + (lw_ - pic.width)/2), int(BB_TOP + 66 + (110 - pic.height)/2)))
        tl = f_spec_s.getlength(label)
        d.text((x + (lw_ - tl)/2, BB_TOP + 186), label, font=f_spec_s, fill=GREY)
        x += lw_ + LGAP
    x += SGAP - LGAP

# ----- Footer -----
fy = BB_BOT + BGAP
d.text((M, fy), "Sources:", font=f_foot_b, fill=INK)
d.text((M + f_foot_b.getlength("Sources:  "), fy),
       "docs/bom/bom.csv (152 rows, 23.10) + AR_BOM_2026-10-09.xlsx photos · build photos from the loop cards (C0xx) · shop listings / vendors (Amazon.de, Comet.bg, Elimex, Vikiwat, NenovTechnic, Ardboard) · "
       "items without a photo are drawn schematically.  ×N = quantity.  Card numbers = tests in docs/LOG.md.", font=f_foot, fill=GREY)
d.text((M, fy + 34), "Notes:", font=f_foot_b, fill=INK)
d.text((M + f_foot_b.getlength("Sources:  "), fy + 34),
       "v1 = Olimex DevKit-Lipo on two breadboards, XIAO = camera node (autumn 2026) · carrier rev B designed · v2 = Raspberry Pi 5 + ROS 2 (2027).  PLA colour code: white = hulls, orange = moving, black = structure, red = dummy.  "
       "AmphiReach · AR-Mini · T. Kyoseva, Sofia, 2026", font=f_foot, fill=GREY)

img.save(f'{OUT}/AR-Mini_BOM_visual_v3.png', dpi=(300, 300))
img.save(f'{OUT}/AR-Mini_BOM_visual_v3.pdf', resolution=300.0)
img.resize((W//3, H//3), Image.LANCZOS).save(f'{OUT}/preview.png')
print("done", COL_BOTTOM, BA_BOT, BB_BOT, fy)
