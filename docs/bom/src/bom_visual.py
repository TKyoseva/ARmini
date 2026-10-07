# Generated the PNG/PDF next to this folder. Product photos are extracted from docs/bom/AR_BOM_2026-10-06.xlsx
# (column Picture) into an image folder first; the paths below are the ones used on the build machine.
#!/usr/bin/env python3
"""AR-Mini visual BOM poster — A3 landscape, 300 dpi (PIL)."""
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageOps
import math, os, sys

IMG = '/home/claude/bom_img'
OUT = '/mnt/user-data/outputs'
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
        for (y0r, lab) in ((Hd*0.17, "100 k"), (Hd*0.59, "33 k")):
            d.rectangle([x-Wd*0.07, y0r, x+Wd*0.07, y0r+Hd*0.24], fill=(245, 225, 190), outline=OUT, width=5)
            for j, col in enumerate([(120, 70, 20), (30, 30, 30), (230, 180, 30)] if lab == "100 k" else [(230, 120, 30), (230, 120, 30), (30, 30, 30)]):
                yy = y0r + Hd*0.05 + j*Hd*0.055
                d.rectangle([x-Wd*0.07+5, yy, x+Wd*0.07-5, yy+Hd*0.03], fill=col)
            d.text((x+Wd*0.10, y0r+Hd*0.06), lab, font=F('Inter-Bold.otf', 44), fill=OUT)
        d.line([(x, yb), (x+Wd*0.30, yb)], fill=(200, 30, 30), width=6)
        d.text((x+Wd*0.31, yb-Hd*0.11), "A0", font=F('Inter-Bold.otf', 44), fill=(200, 30, 30))
        d.text((x-Wd*0.30, ya-Hd*0.02), "VBAT", font=F('Inter-Bold.otf', 40), fill=OUT)
        d.text((x-Wd*0.30, yc-Hd*0.16), "GND", font=F('Inter-Bold.otf', 40), fill=OUT)
    elif kind == 'pcb':
        d.rounded_rectangle([Wd*0.08, Hd*0.12, Wd*0.92, Hd*0.88], radius=20, fill=(30, 110, 60), outline=OUT, width=4)
    else:
        d.rectangle([10, 10, Wd-10, Hd-10], outline=OUT, width=4)
    return im.resize((bw, bh), Image.LANCZOS)

# ---------- catalogue ----------
from PIL import Image as _I
OLD = {17:21,18:24,19:25,34:5,35:6,36:27,37:55,38:56,39:54,44:30,45:34,46:35,47:46,53:50,
       100:14,101:47,102:58,103:31,118:59,119:60,120:61,55:39,48:45,51:9}
def Q(r, crop=None):
    p = f'/home/claude/bom_img3/r{r:03d}.png'
    if r in OLD:
        o = f'{IMG}/row{OLD[r]:02d}.png'
        if _I.open(o).size[0]*_I.open(o).size[1] > _I.open(p).size[0]*_I.open(p).size[1]: p = o
    return dict(img=p, crop=crop)
def I(kind): return dict(icon=kind)
def it(src, name, spec='', qty=None):
    d = dict(src); d.update(name=name, spec=spec, qty=qty); return d

PCB_IMG = f'{OUT}/AR-Mini_xiao_breakout_rev0_assembled.png'
PCB_CROP = (190, 180, 2200, 1810)

COLUMNS = [
    ("Compute & Control", [
        ("Controller v1 (autumn 2026)", [
            it(Q(61), "Seeed XIAO ESP32-S3 Sense", "Wi-Fi/BLE · camera · microSD"),
            it(dict(img=PCB_IMG, crop=PCB_CROP), "XIAO breakout rev 0 (own PCB)", "KiCad 9 · AISLER · 50×40"),
            it(Q(69), "PCA9685 16-ch PWM driver", "I²C · ESC + H-bridge PWM"),
            it(Q(71), "BTS7960 43 A H-bridge", "track motors, left / right", qty=2),
            it(Q(72), "Waveshare serial bus servo driver", "UART → ST3215 bus", qty=2),
        ]),
        ("Carrier rev A (next)", [
            it(Q(59), "Olimex ESP32-S3-DevKit-Lipo", "firmware test board", qty=3),
            it(Q(60), "ESP32-S3-WROOM-1 N16R8", "16 MB flash · 8 MB PSRAM", qty=3),
        ]),
        ("Controller v2 · ROS 2 (2027)", [
            it(Q(62), "Raspberry Pi 5 · 8 GB", "ROS 2 Jazzy · USB to XIAO"),
            it(Q(63), "Active cooler for Pi 5", "fan + heatsink"),
        ]),
    ]),
    ("Sensing", [
        ("Thermal", [
            it(Q(73), "MLX90642-D45 thermal camera", "forward search · I²C-0"),
            it(Q(74), "MLX90640 110° thermal camera", "32×24 px · cradle · I²C-1"),
        ]),
        ("Vision", [
            it(Q(61, crop=(60, 0, 520, 300)), "OV3660 2 MP camera (XIAO Sense)", "pan mount on the arch"),
        ]),
        ("Inertial", [
            it(Q(75), "BNO055 9-DOF IMU", "heading / roll · I²C-0"),
        ]),
        ("Safety inputs", [
            it(I('leak'), "Leak probe — two bare wires", "ADC ladder on A1"),
            it(Q(57), "Battery monitor 100 k / 33 k", "VBAT ÷ 4 → A0"),
        ]),
    ]),
    ("Propulsion & Actuation", [
        ("Water", [
            it(Q(29), "Cuifati 560 KV deep-water thruster", "bidirectional ESC · 12 V", qty=2),
        ]),
        ("Land", [
            it(Q(28), "DFRobot ROB0154 tracked chassis", "2 DC motors · 152×135 plate"),
        ]),
        ("Rescue arm (parallelogram lift)", [
            it(Q(30), "Waveshare ST3215 30 kg bus servo", "magnetic encoder · 12 V bus", qty=4),
            it(Q(31), "TD-8120MG 20 kg servo", "fallback option", qty=2),
        ]),
        ("Camera pan & servo cabling", [
            it(Q(32), "MG90S 9 g micro servo", "camera pan · test rigs", qty=8),
            it(Q(52), "Waveshare 5264 servo cables", "ST3215 daisy-chain", qty=2),
        ]),
    ]),
    ("Power", [
        ("Energy", [
            it(Q(54), "Turnigy 2200 mAh 3S 40 C LiPo", "XT60 · 11.1 V", qty=2),
            it(Q(53), "SkyRC iMAX B6 V2 charger", "balance charge / storage"),
        ]),
        ("Protection & switching", [
            it(Q(78), "50 A toggle switch (main)", "R13-401A2A · OFF-ON"),
            it(Q(79), "20 A rocker ON-ON (logic kill)", "→ PCA9685 OE + ADC"),
            it(Q(80), "Inline fuse holder GT4652", "30 A main fuse"),
            it(Q(81), "6-slot blade fuse block", "20/15/10/5/5 A branches"),
            it(Q(82), "Blade fuse kit · 250 pcs", "spares"),
        ]),
        ("Conversion", [
            it(Q(76), "MZHOU 12 → 5 V USB-C buck", "logic rail (XIAO, sensors)"),
            it(Q(77), "QIQIAZI 10–90 V → 5 V 5 A buck", "Raspberry Pi 5 rail"),
        ]),
    ]),
    ("Wiring & Connectors", [
        ("Battery side", [
            it(Q(51), "XT60 pigtails · 10 pcs", "12 AWG silicone"),
            it(Q(49), "14 AWG silicone wire", "black + red · 2 m each", qty=4),
            it(Q(48), "Insulated spade connectors", "switches & fuse block"),
        ]),
        ("Logic side", [
            it(Q(50), "18 AWG silicone wire", "black + red · 2 m each", qty=4),
            it(Q(56), "JST-XH 2.54 kit + crimped leads", "2–6 pin · 22 AWG"),
            it(Q(46), "Alkan wire ferrules · 800 pcs", "0.5–10 mm² terminals"),
            it(Q(47), "Heat-shrink tubing box", "Ø1.5–13 mm"),
        ]),
    ]),
    ("Structure & Materials", [
        ("3D printing (Creality K2 Pro)", [
            it(Q(24), "Creality Hyper PLA 1 kg", "6 colours, colour-coded", qty=7),
            it(Q(25), "Creality Hyper PETG 1 kg", "hulls & all wet parts", qty=4),
            it(I('hulls'), "Printed hulls, beams & brackets", "own CAD, OpenSCAD + F360"),
            it(I('dummy'), "Rescue dummy “Pesho” (red PLA)", "thermal target"),
        ]),
        ("Frame & enclosure", [
            it(Q(2), "Kantoflex Al profile 15 × 15 × 1", "cross-beams · 304 mm", qty=2),
            it(Q(3), "Aluminium rod Ø5 mm", "cradle 220 × 123 mm"),
            it(Q(27), "LANUCN IP65 box 150 × 110 × 70", "logic enclosure"),
            it(Q(23), "WEDZE hand warmers", "dummy heat source", qty=10),
        ]),
        ("Fasteners & bonding", [
            it(Q(19), "ruthex threaded inserts M2–M5", "+ 100 × M3S short"),
            it(Q(17), "DSM DIN 912 screw set · 640 pcs", "M3–M6 · + M2 set · nyloc"),
        ]),
    ]),
]

BAND_A = ("Tools & Workshop", [
    ("Fabrication", [
        it(Q(121), "Creality K2 Pro Combo", "300³ mm build"),
        it(Q(101), "Digital caliper", "0–150 mm"),
    ]),
    ("Soldering & crimping", [
        it(Q(36), "FNIRSI HS-03 iron", "2600 mAh"),
        it(Q(39), "Third hand ZD-126-4", "LED + iron stand"),
        it(Q(43), "Toolour third hand", "magnetic base"),
        it(Q(115), "YIHUA 948DQ-I", "fume extractor"),
        it(Q(37), "Solder Sn60Pb40", "0.8 mm · 100 g"),
        it(Q(38), "TOPNIK-ZEL flux", "RMA gel", qty=3),
        it(Q(44), "KNIPEX NexStrip", "strip · cut · crimp"),
        it(Q(45), "Preciva crimp set", "Dupont · JST-XH"),
    ]),
    ("Measurement & debug", [
        it(Q(102), "UNI-T UT61E+", "multimeter"),
        it(Q(103), "Logic analyzer", "24 MHz · 8 ch"),
        it(Q(100), "Jesverty lab PSU", "60 V / 5 A"),
        it(Q(55), "FT232RL USB-TTL", "servo config"),
    ]),
    ("Prototyping", [
        it(Q(58), "VooGenzek PCB kit", "perfboards", qty=2),
        it(Q(66), "Hailege jumper kit", "2 × 140 U-wires"),
        it(Q(64), "Alligator clips", "10 pcs"),
        it(Q(65), "Cleqee clip leads", "clip → Dupont"),
    ]),
    ("Documentation", [
        it(Q(118), "NEEWER magic arm", "table clamp"),
        it(Q(119), "ULANZI MT-79", "tripod 204 cm"),
        it(Q(120), "ULANZI VL49", "LED light"),
    ]),
])

BAND_B = ("Software & Services", [
    ("Design", [(83, "Fusion 360"), (84, "OpenSCAD"), (85, "KiCad 9"), (86, "Creality Print")]),
    ("Firmware & software", [(87, "PlatformIO"), (88, "Arduino IDE"), (91, "Python"), (92, "Git + GitHub"), (93, "Pi OS + ROS 2"), (90, "PulseView")]),
    ("Services & media", [(95, "AISLER"), (94, "Eurocircuits"), (96, "Printables"), (97, "SlideRoom"), (98, "DaVinci Resolve")]),
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
sub = "1:9 physical demonstrator of the AmphiReach amphibious rescue robot  ·  what goes into the robot (top) and what builds it (bottom)  ·  status 06.10.2026 (v2)"
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
IMG_W, IMG_H = CELLW - 26, 250
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
        pic = fit(load_photo(f'/home/claude/bom_img3/r{r:03d}.png'), lw_ - 24, 110, max_up=3)
        img.paste(pic, (int(x + (lw_ - pic.width)/2), int(BB_TOP + 66 + (110 - pic.height)/2)))
        tl = f_spec_s.getlength(label)
        d.text((x + (lw_ - tl)/2, BB_TOP + 186), label, font=f_spec_s, fill=GREY)
        x += lw_ + LGAP
    x += SGAP - LGAP

# ----- Footer -----
fy = BB_BOT + BGAP
d.text((M, fy), "Sources:", font=f_foot_b, fill=INK)
d.text((M + f_foot_b.getlength("Sources:  "), fy),
       "AR_BOM_06_10_2026_v3.xlsx · product photos and logos from the shop listings / vendors (Amazon.de, Comet.bg, Elimex, Vikiwat, NenovTechnic, Ardboard) · "
       "items without a photo are drawn schematically.  ×N = quantity ordered.", font=f_foot, fill=GREY)
d.text((M, fy + 34), "Notes:", font=f_foot_b, fill=INK)
d.text((M + f_foot_b.getlength("Sources:  "), fy + 34),
       "v1 = XIAO-only controller (autumn 2026) · v2 = Raspberry Pi 5 + ROS 2 (2027).  Printed parts: PETG for everything wet, PLA for dry parts (orange = moving, black = structure, red = dummy, blue = enclosures).  "
       "AmphiReach · AR-Mini · T. Kyoseva, Sofia, 2026", font=f_foot, fill=GREY)

img.save(f'{OUT}/AR-Mini_BOM_visual_v2.png', dpi=(300, 300))
img.save(f'{OUT}/AR-Mini_BOM_visual_v2.pdf', resolution=300.0)
img.resize((W//3, H//3), Image.LANCZOS).save('/home/claude/vbom/preview.png')
print("done", COL_BOTTOM, BA_BOT, BB_BOT, fy)
