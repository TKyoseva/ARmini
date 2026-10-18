"""Breadboard-view drawing primitives (PIL). A3 landscape, 300 dpi."""
from PIL import Image, ImageDraw, ImageFont, ImageOps
import math

W, H = 4961, 3508
FD = '/usr/share/fonts/opentype/inter/'
def F(n, s): return ImageFont.truetype(FD + n, s)
f_title = F('InterDisplay-Bold.otf', 96); f_sub = F('Inter-Regular.otf', 36)
f_hdr = F('Inter-Bold.otf', 40); f_mod = F('Inter-Bold.otf', 34); f_pin = F('Inter-SemiBold.otf', 24); f_pin_s = F('Inter-SemiBold.otf', 20)
f_txt = F('Inter-Regular.otf', 29); f_txt_b = F('Inter-Bold.otf', 29); f_small = F('Inter-Regular.otf', 24); f_tag = F('Inter-Bold.otf', 25)
f_grp = F('Inter-SemiBoldItalic.otf', 30); f_num = F('Inter-Bold.otf', 34)

RED = (181, 18, 27); RED_DK = (143, 14, 21); INK = (26, 26, 26); GREY = (105, 105, 105); LINE = (70, 70, 70); WHITE = (255, 255, 255)
# wire colours (Fritzing-like)
W_RED = (214, 40, 40); W_BLK = (30, 30, 30); W_ORG = (240, 140, 20); W_YEL = (230, 200, 30); W_GRN = (40, 150, 70); W_BLU = (40, 100, 210)
W_PUR = (130, 70, 180); W_CYN = (0, 150, 150); W_WHT = (235, 235, 235); W_BRN = (120, 75, 30); W_GRY = (140, 140, 140)
BB_BODY = (236, 236, 230); BB_LINE = (170, 170, 160); HOLE = (90, 90, 85); PCB_BLUE = (30, 70, 160); PCB_GREEN = (30, 110, 60); PCB_RED = (160, 40, 50); PCB_BLACK = (45, 45, 48)

img = None; d = None
def new():
    global img, d
    img = Image.new('RGB', (W, H), WHITE); d = ImageDraw.Draw(img); return img, d

def text(x, y, t, font=f_txt, fill=INK, anchor='la'):
    d.text((x, y), t, font=font, fill=fill, anchor=anchor)

def wrap(t, font, width):
    out, cur = [], ''
    for wd in t.split():
        tt = (cur + ' ' + wd).strip()
        if font.getlength(tt) <= width or not cur: cur = tt
        else: out.append(cur); cur = wd
    if cur: out.append(cur)
    return out

def para(x, y, t, font=f_txt, width=1100, fill=INK, lh=None):
    lh = lh or int(font.size * 1.35)
    for ln in wrap(t, font, width): d.text((x, y), ln, font=font, fill=fill); y += lh
    return y

def title(t, sub):
    tw = f_title.getlength(t); d.text(((W - tw) / 2, 40), t, font=f_title, fill=INK)
    d.rectangle([(W - tw) / 2, 152, (W + tw) / 2, 159], fill=RED)
    d.text(((W - f_sub.getlength(sub)) / 2, 176), sub, font=f_sub, fill=GREY)

def section(box, t, fill=RED):
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], outline=LINE, width=3)
    d.rectangle([x0, y0, x1, y0 + 66], fill=fill)
    d.text(((x0 + x1) / 2 - f_hdr.getlength(t) / 2, y0 + 10), t, font=f_hdr, fill=WHITE)

def photo(path, box_w, box_h):
    im = Image.open(path).convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
    m = ImageOps.grayscale(im).point(lambda p: 255 if p < 240 else 0); bb = m.getbbox()
    if bb: im = im.crop(bb)
    sc = min(box_w / im.width, box_h / im.height, 3.0)
    return im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)

# ---------------- breadboard ----------------
class Breadboard:
    """Full-size 830-point board. hole(col 1..63, row 'a'..'j' | 'T+','T-','B+','B-')."""
    def __init__(s, x, y, cols=63, P=30):
        s.x, s.y, s.cols, s.P = x, y, cols, P
        s.mx, s.my = 44, 36
        s.w = cols * P + 2 * s.mx
        s.rows = {}
        yy = y + s.my + P / 2
        s.rows['T-'] = yy; s.rows['T+'] = yy + P; yy += 2 * P + 26
        for i, r in enumerate('abcde'): s.rows[r] = yy + i * P
        yy += 5 * P + int(1.4 * P)
        for i, r in enumerate('fghij'): s.rows[r] = yy + i * P
        yy += 5 * P + 26
        s.rows['B+'] = yy; s.rows['B-'] = yy + P
        s.h = int(yy + P + P / 2 + s.my - y)
    def col_x(s, c): return s.x + s.mx + (c - 0.5) * s.P
    def hole(s, c, r): return (s.col_x(c), s.rows[r])
    def draw(s):
        d.rounded_rectangle([s.x, s.y, s.x + s.w, s.y + s.h], radius=14, fill=BB_BODY, outline=BB_LINE, width=3)
        # centre channel
        ya = s.rows['e'] + s.P * 0.7; yb = s.rows['f'] - s.P * 0.7
        d.rectangle([s.x + 8, ya, s.x + s.w - 8, yb], fill=(222, 222, 215), outline=(200, 200, 192), width=2)
        # rail lines
        for key, col, off in (('T+', W_RED, -1), ('T-', W_BLU, 1), ('B+', W_RED, 1), ('B-', W_BLU, -1)):
            yy = s.rows[key] + off * s.P * 0.6
            d.line([(s.col_x(1) - 12, yy), (s.col_x(s.cols) + 12, yy)], fill=col, width=4)
            lab = '+' if key[1] == '+' else '−'
            d.text((s.x + 10, yy - 16), lab, font=f_mod, fill=col); d.text((s.x + s.w - 34, yy - 16), lab, font=f_mod, fill=col)
        # holes
        r = 5
        for c in range(1, s.cols + 1):
            for rr in 'abcdefghij':
                x, y = s.hole(c, rr); d.rounded_rectangle([x - r, y - r, x + r, y + r], radius=2, fill=HOLE)
            if (c - 1) % 6 != 5 or c == s.cols:   # rails in groups of five
                for rr in ('T+', 'T-', 'B+', 'B-'):
                    x, y = s.hole(c, rr); d.rounded_rectangle([x - r, y - r, x + r, y + r], radius=2, fill=HOLE)
        # numbers and letters
        for c in range(1, s.cols + 1):
            if c == 1 or c % 5 == 0:
                d.text((s.col_x(c), s.rows['a'] - 22), str(c), font=f_pin_s, fill=GREY, anchor='mm')
                d.text((s.col_x(c), s.rows['j'] + 22), str(c), font=f_pin_s, fill=GREY, anchor='mm')
        for rr in 'abcdefghij':
            d.text((s.x + s.mx - 22, s.rows[rr]), rr, font=f_pin_s, fill=GREY, anchor='mm')
            d.text((s.x + s.w - s.mx + 22, s.rows[rr]), rr, font=f_pin_s, fill=GREY, anchor='mm')

# ---------------- modules ----------------
class Module:
    """Rectangular board with pin rows. pins: dict side -> list of (name, colour) left-to-right / top-to-bottom. Returns pin coords."""
    def __init__(s, x, y, w, h, name, sub='', color=PCB_BLUE, pins=None, pitch=34, photo_path=None, photo_box=(220, 160), photo_pos='tr', label_color=WHITE, pin_font=f_pin):
        s.x, s.y, s.w, s.h = x, y, w, h; s.name = name; s.sub = sub; s.color = color; s.pins = pins or {}; s.pitch = pitch
        s.photo_path = photo_path; s.photo_box = photo_box; s.photo_pos = photo_pos; s.label_color = label_color; s.pin_font = pin_font
        s.P = {}
    def draw(s):
        d.rounded_rectangle([s.x, s.y, s.x + s.w, s.y + s.h], radius=16, fill=s.color, outline=(20, 20, 20), width=3)
        # mounting holes
        for cx, cy in ((s.x + 22, s.y + 22), (s.x + s.w - 22, s.y + 22), (s.x + 22, s.y + s.h - 22), (s.x + s.w - 22, s.y + s.h - 22)):
            d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(230, 200, 120), outline=(120, 100, 50), width=2)
        cy = s.y + s.h * (0.70 if (s.photo_path and 't' in s.photo_pos) else (0.34 if s.photo_path else 0.5))
        d.text((s.x + s.w / 2, cy - (18 if s.sub else 0)), s.name, font=f_mod, fill=s.label_color, anchor='mm')
        if s.sub: d.text((s.x + s.w / 2, cy + 24), s.sub, font=f_small, fill=s.label_color, anchor='mm')
        if s.photo_path:
            p = photo(s.photo_path, *s.photo_box)
            px = s.x + s.w - p.width - 14 if 'r' in s.photo_pos else s.x + 14
            py = s.y + 14 if 't' in s.photo_pos else s.y + s.h - p.height - 14
            d.rectangle([px - 4, py - 4, px + p.width + 4, py + p.height + 4], fill=WHITE, outline=(200, 200, 200), width=2)
            img.paste(p, (px, py))
        for side, lst in s.pins.items(): s._pins(side, lst)
    def _pins(s, side, lst):
        n = len(lst); pitch = s.pitch
        for i, (name, col) in enumerate(lst):
            if side in ('left', 'right'):
                y = s.y + s.h / 2 + (i - (n - 1) / 2) * pitch
                x = s.x if side == 'left' else s.x + s.w
                s._pin_sq(x, y, col)
                if side == 'left': d.text((x + 18, y), name, font=s.pin_font, fill=s.label_color, anchor='lm')
                else: d.text((x - 18, y), name, font=s.pin_font, fill=s.label_color, anchor='rm')
            else:
                x = s.x + s.w / 2 + (i - (n - 1) / 2) * pitch
                y = s.y if side == 'top' else s.y + s.h
                s._pin_sq(x, y, col)
                # vertical label
                t = Image.new('RGBA', (int(s.pin_font.getlength(name)) + 8, 30), (0, 0, 0, 0)); ImageDraw.Draw(t).text((4, 2), name, font=s.pin_font, fill=s.label_color); t = t.rotate(90, expand=True)
                ty = y + 16 if side == 'top' else y - 16 - t.height
                img.paste(t, (int(x - t.width / 2), int(ty)), t)
            s.P[name] = (x, y)
    def _pin_sq(s, x, y, col):
        d.rectangle([x - 11, y - 11, x + 11, y + 11], fill=(235, 235, 235), outline=(40, 40, 40), width=2)
        d.rectangle([x - 5, y - 5, x + 5, y + 5], fill=col if col else (120, 120, 120))

def screw_terminal(x, y, names, pitch=52, horizontal=True, color=(40, 140, 60)):
    """block of screw terminals; returns dict name -> (x, y) of the wire entry"""
    P = {}
    n = len(names)
    if horizontal:
        d.rounded_rectangle([x - 26, y - 26, x + (n - 1) * pitch + 26, y + 26], radius=6, fill=color, outline=(20, 20, 20), width=2)
        for i, nm in enumerate(names):
            cx = x + i * pitch; d.ellipse([cx - 14, cy := y, cx + 14, y + 0] if False else [cx - 14, y - 14, cx + 14, y + 14], fill=(200, 200, 200), outline=(40, 40, 40), width=2)
            d.line([(cx - 8, y), (cx + 8, y)], fill=(60, 60, 60), width=3)
            d.text((cx, y + 36), nm, font=f_pin, fill=INK, anchor='mm'); P[nm] = (cx, y - 26)
    else:
        d.rounded_rectangle([x - 26, y - 26, x + 26, y + (n - 1) * pitch + 26], radius=6, fill=color, outline=(20, 20, 20), width=2)
        for i, nm in enumerate(names):
            cy = y + i * pitch; d.ellipse([x - 14, cy - 14, x + 14, cy + 14], fill=(200, 200, 200), outline=(40, 40, 40), width=2)
            d.line([(x - 8, cy), (x + 8, cy)], fill=(60, 60, 60), width=3)
            d.text((x + 40, cy), nm, font=f_pin, fill=INK, anchor='lm'); P[nm] = (x - 26, cy)
    return P

# ---------------- wires ----------------
def wire(pts, col, w=9, r=28, end=True, start=True):
    """polyline with rounded corners"""
    pts = [(float(a), float(b)) for a, b in pts]
    path = []
    for i, p in enumerate(pts):
        if i == 0 or i == len(pts) - 1: path.append(p); continue
        a, b = pts[i - 1], pts[i + 1]
        for q in (a, b):
            L = math.dist(p, q); k = min(r, L / 2) / (L or 1)
            path.append((p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k))
        # insert corner control: approximate arc with midpoint
        p1, p2 = path[-2], path[-1]
        mid = ((p1[0] + p2[0]) / 2 * 0.5 + p[0] * 0.5, (p1[1] + p2[1]) / 2 * 0.5 + p[1] * 0.5)
        path.insert(len(path) - 1, mid)
    # outline then colour
    d.line(path, fill=(20, 20, 20), width=w + 4, joint='curve')
    d.line(path, fill=col, width=w, joint='curve')
    rr = w / 2 + 3
    for p, on in ((pts[0], start), (pts[-1], end)):
        if on:
            d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=(230, 230, 230), outline=(20, 20, 20), width=2)

def tag(x, y, t, col, bg=WHITE, font=f_tag, anchor='c'):
    tw = font.getlength(t); h = 36
    x0 = x - tw / 2 - 12 if anchor == 'c' else (x if anchor == 'l' else x - tw - 24)
    d.rounded_rectangle([x0, y - h / 2, x0 + tw + 24, y + h / 2], radius=10, fill=bg, outline=col, width=3)
    d.text((x0 + 12, y - h / 2 + 4), t, font=font, fill=col)

def num_badge(x, y, n, col=RED):
    d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=col); d.text((x, y), str(n), font=f_num, fill=WHITE, anchor='mm')

def resistor(p0, p1, label, col_bands=((120, 75, 30), (30, 30, 30), (230, 180, 30))):
    """axial resistor between two points"""
    x0, y0 = p0; x1, y1 = p1; L = math.dist(p0, p1); ux, uy = (x1 - x0) / L, (y1 - y0) / L
    bx0, by0 = x0 + ux * (L / 2 - 38), y0 + uy * (L / 2 - 38); bx1, by1 = x0 + ux * (L / 2 + 38), y0 + uy * (L / 2 + 38)
    d.line([p0, p1], fill=(150, 150, 150), width=5)
    ang = math.degrees(math.atan2(uy, ux))
    body = Image.new('RGBA', (76, 26), (0, 0, 0, 0)); g = ImageDraw.Draw(body)
    g.rounded_rectangle([0, 0, 75, 25], radius=11, fill=(235, 215, 175), outline=(90, 70, 40), width=2)
    for i, c in enumerate(col_bands): g.rectangle([14 + i * 11, 2, 21 + i * 11, 23], fill=c)
    g.rectangle([56, 2, 63, 23], fill=(210, 170, 60))
    body = body.rotate(-ang, expand=True)
    cx, cy = x0 + ux * L / 2, y0 + uy * L / 2
    img.paste(body, (int(cx - body.width / 2), int(cy - body.height / 2)), body)
    nx, ny = -uy, ux
    if label: d.text((cx + nx * 30, cy + ny * 30), label, font=f_pin, fill=INK, anchor='mm')

def servo_icon(x, y, w=260, h=150, label='TD-8120MG', photo_path=None):
    d.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=PCB_BLACK, outline=(10, 10, 10), width=3)
    d.rectangle([x - 26, y + 30, x + w + 26, y + 50], fill=(70, 70, 72), outline=(10, 10, 10), width=2)
    for cx in (x - 14, x + w + 14): d.ellipse([cx - 7, y + 33, cx + 7, y + 47], fill=(230, 230, 230))
    d.ellipse([x + 44, y - 40, x + 116, y + 32], fill=(240, 240, 240), outline=(10, 10, 10), width=3)
    d.rounded_rectangle([x + 70, y - 24, x + 190, y - 4], radius=8, fill=(240, 240, 240), outline=(10, 10, 10), width=2)
    d.text((x + w / 2, y + h / 2 + 10), label, font=f_pin, fill=WHITE, anchor='mm')
    if photo_path:
        p = photo(photo_path, 150, 120); d.rectangle([x + w - p.width - 12, y + h - p.height - 12, x + w - 4, y + h - 4], fill=WHITE); img.paste(p, (x + w - p.width - 8, y + h - p.height - 8))
    return (x + w, y + h - 30)   # cable exit

def motor_icon(x, y, label='ROB0154 мотор (ляв)'):
    d.rounded_rectangle([x, y, x + 150, y + 240], radius=20, fill=(190, 192, 196), outline=(40, 40, 40), width=3)
    d.rectangle([x + 20, y - 40, x + 130, y], fill=(220, 180, 70), outline=(40, 40, 40), width=3)
    d.rectangle([x + 68, y - 70, x + 82, y - 40], fill=(120, 120, 120))
    d.text((x + 75, y + 120), 'M', font=f_hdr, fill=INK, anchor='mm')
    d.text((x + 75, y + 270), label, font=f_pin, fill=INK, anchor='mm')
    return {'1': (x + 40, y + 240), '2': (x + 110, y + 240)}

def lipo_icon(x, y, label='Turnigy 3S 2200 mAh'):
    d.rounded_rectangle([x, y, x + 420, y + 150], radius=14, fill=(40, 90, 200), outline=(20, 20, 20), width=3)
    d.text((x + 210, y + 55), label, font=f_mod, fill=WHITE, anchor='mm'); d.text((x + 210, y + 100), '11.1 V · XT60', font=f_small, fill=WHITE, anchor='mm')
    # XT60
    d.rounded_rectangle([x + 420, y + 45, x + 480, y + 105], radius=8, fill=(230, 200, 40), outline=(20, 20, 20), width=2)
    d.text((x + 450, y + 75), 'XT60', font=f_pin_s, fill=INK, anchor='mm')
    return {'+': (x + 480, y + 60), '-': (x + 480, y + 90)}

def toggle_icon(x, y, label='Главен ключ 50 A'):
    d.rounded_rectangle([x, y, x + 120, y + 120], radius=10, fill=(200, 200, 205), outline=(20, 20, 20), width=3)
    d.ellipse([x + 35, y + 35, x + 85, y + 85], fill=(120, 120, 125), outline=(20, 20, 20), width=2)
    d.line([(x + 60, y + 60), (x + 100, y + 15)], fill=(60, 60, 60), width=14)
    d.text((x + 60, y + 150), label, font=f_pin, fill=INK, anchor='mm')
    return {'1': (x, y + 60), '2': (x + 120, y + 60)}

def fuse_icon(x, y, label='Inline бушон GT4652', value='10 A'):
    d.rounded_rectangle([x, y, x + 200, y + 80], radius=30, fill=(40, 40, 42), outline=(10, 10, 10), width=3)
    d.rounded_rectangle([x + 70, y + 16, x + 130, y + 64], radius=6, fill=(230, 60, 60), outline=(10, 10, 10), width=2)
    d.text((x + 100, y + 40), value, font=f_pin_s, fill=WHITE, anchor='mm')
    d.text((x + 100, y + 108), label, font=f_pin, fill=INK, anchor='mm')
    return {'1': (x, y + 40), '2': (x + 200, y + 40)}

def rocker_icon(x, y, label='Rocker ON-ON (kill)'):
    d.rounded_rectangle([x, y, x + 110, y + 180], radius=10, fill=(40, 40, 42), outline=(10, 10, 10), width=3)
    d.polygon([(x + 20, y + 30), (x + 90, y + 30), (x + 90, y + 95), (x + 20, y + 110)], fill=(80, 80, 84))
    d.polygon([(x + 20, y + 110), (x + 90, y + 95), (x + 90, y + 150), (x + 20, y + 150)], fill=(60, 60, 64))
    d.text((x + 55, y - 24), label, font=f_pin, fill=INK, anchor='mm')
    P = {}
    for i, nm in enumerate(('1', 'C', '2')):
        px = x + 25 + i * 30; d.rectangle([px - 6, y + 180, px + 6, y + 210], fill=(200, 200, 200), outline=(20, 20, 20), width=2); P[nm] = (px, y + 210)
        d.text((px, y + 228), nm, font=f_pin_s, fill=INK, anchor='mm')
    return P

def pot_on_board(bb, col, row='g', label='Потенциометър 10 k'):
    """3-pin pot on columns col..col+2, row; returns pin coords (board holes)"""
    x0, y0 = bb.hole(col, row); x2, _ = bb.hole(col + 2, row)
    cx = (x0 + x2) / 2
    d.rounded_rectangle([cx - 60, y0 - 150, cx + 60, y0 - 10], radius=10, fill=(40, 100, 200), outline=(20, 20, 20), width=3)
    d.ellipse([cx - 40, y0 - 130, cx + 40, y0 - 50], fill=(230, 230, 230), outline=(20, 20, 20), width=2)
    d.line([(cx, y0 - 90), (cx + 28, y0 - 118)], fill=(40, 40, 40), width=6)
    for c in range(3):
        px, _ = bb.hole(col + c, row); d.line([(px, y0 - 10), (px, y0)], fill=(150, 150, 150), width=5)
    d.text((cx, y0 - 170), label, font=f_pin, fill=INK, anchor='mm')
    return {'1': bb.hole(col, row), 'W': bb.hole(col + 1, row), '3': bb.hole(col + 2, row)}

def leak_probe(x, y):
    d.rounded_rectangle([x, y, x + 60, y + 44], radius=8, fill=(240, 240, 235), outline=(60, 60, 60), width=3)
    for i, c in enumerate((W_RED, W_BLK)):
        yy = y + 12 + i * 20; d.line([(x + 60, yy), (x + 150, yy)], fill=c, width=8); d.line([(x + 150, yy), (x + 190, yy)], fill=(205, 140, 70), width=6)
    d.text((x + 95, y + 70), 'leak probe (2 голи жила)', font=f_pin_s, fill=INK, anchor='mm')
    return {'1': (x, y + 12), '2': (x, y + 32)}

def legend(x, y, items, cols=3, colw=520):
    for i, (col, t) in enumerate(items):
        cx = x + (i % cols) * colw; cy = y + (i // cols) * 46
        d.line([(cx, cy + 14), (cx + 60, cy + 14)], fill=(20, 20, 20), width=14); d.line([(cx, cy + 14), (cx + 60, cy + 14)], fill=col, width=9)
        d.text((cx + 76, cy), t, font=f_small, fill=INK)

def steps(x, y, lst, width, font=f_txt):
    for i, t in enumerate(lst):
        num_badge(x + 26, y + 22, i + 1)
        yy = y
        for ln in wrap(t, font, width - 80): d.text((x + 70, yy), ln, font=font, fill=INK); yy += int(font.size * 1.38)
        y = max(yy, y + 60) + 14
    return y

def arc_wire(p0, p1, bulge, col, w=8):
    """quadratic-bezier jumper between two holes; bulge > 0 bows downward (+y)"""
    x0, y0 = p0; x1, y1 = p1; mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + bulge
    pts = []
    for i in range(41):
        t = i / 40; a = (1 - t) ** 2; b = 2 * (1 - t) * t; c = t ** 2
        pts.append((a * x0 + b * mx + c * x1, a * y0 + b * my + c * y1))
    d.line(pts, fill=(20, 20, 20), width=w + 4, joint='curve'); d.line(pts, fill=col, width=w, joint='curve')
    rr = w / 2 + 3
    for p in (p0, p1): d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=(230, 230, 230), outline=(20, 20, 20), width=2)
