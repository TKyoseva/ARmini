"""AR-Mini · AI-augmented build loop — honest architecture poster (A3 landscape)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hardware', 'breadboard', 'src'))
import bb
from bb import *
img, d = bb.new()
I3 = '/home/claude/bom_img3'

f_big = F('InterDisplay-Bold.otf', 64); f_lay = F('Inter-Bold.otf', 34); f_role = F('Inter-Bold.otf', 32)
f_b = F('Inter-Regular.otf', 25); f_bb = F('Inter-SemiBold.otf', 25); f_it = F('Inter-Italic.otf', 25); f_kpi = F('InterDisplay-Bold.otf', 88)
BLUE = (36, 84, 160); BLUE_L = (232, 239, 250); GREEN = (40, 120, 70); GREEN_L = (231, 244, 235); RED_L = (250, 234, 234); AMBER = (190, 120, 10); AMBER_L = (253, 243, 224)

def card(x, y, w, h, fill, edge, r=18):
    d.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=fill, outline=edge, width=3)

def band(x, y, w, h, n, title, sub, col, fill):
    card(x, y, w, h, fill, col, 22)
    d.rounded_rectangle([x, y, x + 120, y + h], radius=22, fill=col); d.rectangle([x + 60, y, x + 120, y + h], fill=col)
    d.text((x + 60, y + h / 2), str(n), font=f_big, fill=WHITE, anchor='mm')
    d.text((x + 150, y + 22), title, font=f_lay, fill=col)
    d.text((x + 150, y + 66), sub, font=f_b, fill=GREY)

def arrow(x0, y0, x1, y1, col=LINE, w=6, head=18):
    d.line([(x0, y0), (x1, y1)], fill=col, width=w)
    import math
    a = math.atan2(y1 - y0, x1 - x0)
    p = [(x1, y1), (x1 - head * math.cos(a - 0.45), y1 - head * math.sin(a - 0.45)), (x1 - head * math.cos(a + 0.45), y1 - head * math.sin(a + 0.45))]
    d.polygon(p, fill=col)

title('AR-Mini  ·  How it is built: one engineer + one AI assistant + the physical world',
      'AI proposes, a measurement decides. Every number in the CAD traces to calipers, a datasheet or a test.  ·  28.09 – 07.10.2026, real artefacts only')

L, R = 60, 3560          # main column
# ---------- 0 · Architect ----------
y0 = 250
card(L, y0, R - L, 250, (30, 34, 40), (30, 34, 40), 22)
d.text((L + 40, y0 + 30), 'SYSTEM ARCHITECT  ·  Teodora Kyoseva', font=F('InterDisplay-Bold.otf', 52), fill=WHITE)
d.text((L + 40, y0 + 100), 'Sets requirements · measures every part · prints, wires, solders, tests · decides what is true · signs off every version', font=f_txt, fill=(210, 214, 220))
for i, t in enumerate(['owns the decisions', 'owns the measurements', 'owns the hardware', 'owns the commits']):
    x = L + 40 + i * 420; d.rounded_rectangle([x, y0 + 160, x + 390, y0 + 214], radius=27, outline=(120, 130, 140), width=2)
    d.text((x + 195, y0 + 187), t, font=f_bb, fill=WHITE, anchor='mm')
p = photo(f'{I3}/r121.png', 200, 200); img.paste(p, (R - 40 - p.width, y0 + 25))

# ---------- 1 · AI layer ----------
y1 = 560
band(L, y1, R - L, 790, 1, 'AI collaboration layer  ·  Claude (one assistant, one long conversation)',
     'Not autonomous agents: the same assistant takes five roles on request; nothing reaches the hardware without the architect.', BLUE, BLUE_L)
roles = [
    ('Mechanical', 'CAD · kinematics', ['AR-Mini_v1.scad v1.0 → v1.9', 'parallelogram lift, 215° / 45°', 'hull split for a 300 mm bed', '3D model + collision found'], 'r028.png'),
    ('Electronics', 'power · signals', ['architecture v1 + fuse tree', 'XIAO breakout rev 0 (KiCad)', 'carrier rev A spec', '3 breadboard sheets'], 'r071.png'),
    ('Firmware', 'C++ · ESP32-S3', ['bench_v1.ino (Mega)', 'PlatformIO skeleton', 'pin maps XIAO / DevKit-Lipo', 'state machine plan'], 'r061.png'),
    ('Sourcing', 'BOM · suppliers', ['BOM: 124 items with photos', 'listing checks (thrusters!)', 'BG shops vs Amazon.de', 'what NOT to buy'], 'r054.png'),
    ('Documentation', 'log · portfolio', ['FAILS_AND_FIXES: 142 entries', 'LOG · TIMELINE · decisions', 'GitHub repo structure', 'posters + visual BOM'], 'r092.png'),
]
cw = (R - L - 180 - 4 * 30) // 5
for i, (t, s, items, ph) in enumerate(roles):
    x = L + 150 + i * (cw + 30); y = y1 + 120
    card(x, y, cw, 620, WHITE, (180, 196, 222))
    pic = photo(f'{I3}/{ph}', cw - 60, 150); img.paste(pic, (int(x + (cw - pic.width) / 2), y + 20))
    d.text((x + 24, y + 190), t, font=f_role, fill=BLUE); d.text((x + 24, y + 234), s, font=f_b, fill=GREY)
    d.line([(x + 24, y + 278), (x + cw - 24, y + 278)], fill=(210, 220, 235), width=2)
    yy = y + 296
    for it in items:
        d.ellipse([x + 26, yy + 11, x + 36, yy + 21], fill=BLUE)
        for k, ln in enumerate(wrap(it, f_b, cw - 80)):
            d.text((x + 48, yy), ln, font=f_b, fill=INK); yy += 34
        yy += 12
    d.text((x + 24, y + 572), 'output → review by architect', font=f_it, fill=GREY)

# ---------- 2 · Tools & data ----------
y2 = 1410
band(L, y2, R - L, 470, 2, 'Tools & ground truth', 'Where proposals become files, and where they are checked.', GREEN, GREEN_L)
tools = [('OpenSCAD · Fusion 360', 'parametric CAD, one file = whole robot'), ('KiCad 9 + DRC', '32 → 19 → 15 → clean (05.10)'),
         ('Python', '3D model, renders, posters, BOM'), ('Datasheets & manuals', 'Olimex pinout, ROB0154 manual'),
         ('Calipers SUW-DIGIP54', 'TD-8120MG 28.0 / 10 / 4.34 / 10.4'), ('GitHub · ARmini', 'every version, honest dates')]
tw = (R - L - 180 - 5 * 26) // 6
for i, (a, b_) in enumerate(tools):
    x = L + 150 + i * (tw + 26); y = y2 + 130
    card(x, y, tw, 290, WHITE, (170, 205, 180))
    yy = y + 26
    for ln in wrap(a, f_role, tw - 40): d.text((x + 22, yy), ln, font=f_role, fill=GREEN); yy += 42
    yy += 8
    for ln in wrap(b_, f_b, tw - 40): d.text((x + 22, yy), ln, font=f_b, fill=INK); yy += 34

# ---------- 3 · Physical ----------
y3 = 1940
band(L, y3, R - L, 470, 3, 'Physical reality', 'The only layer that cannot be argued with.', RED, RED_L)
phys = [('r121.png', 'Creality K2 Pro', 'PLA fit prints → PETG'), ('r066.png', 'Breadboard stands', 'Mega bench · XIAO · DevKit'),
        ('r102.png', 'UT61E+ · logic analyzer', 'volts, ohms, I²C, UART'), ('r029.png', 'Thruster in a bucket', 'first wet test'),
        ('r117.png', 'Pool', 'draft, lift, rescue cycle')]
pw = (R - L - 180 - 4 * 26) // 5
for i, (ph, a, b_) in enumerate(phys):
    x = L + 150 + i * (pw + 26); y = y3 + 120
    card(x, y, pw, 310, WHITE, (225, 180, 180))
    pic = photo(f'{I3}/{ph}', 170, 150); img.paste(pic, (x + 20, int(y + 20 + (150 - pic.height) / 2)))
    d.text((x + 210, y + 40), '', font=f_b)
    yy = y + 40
    for ln in wrap(a, f_role, pw - 230): d.text((x + 205, yy), ln, font=f_role, fill=RED_DK); yy += 42
    for ln in wrap(b_, f_b, pw - 230): d.text((x + 205, yy + 6), ln, font=f_b, fill=INK); yy += 34
    d.text((x + 20, y + 250), ['in use', 'in use from 07.10', 'in use', 'next', 'Oct – Dec'][i], font=f_it, fill=GREY)

# arrows between layers (down = proposals, up = evidence)
for (ya, yb) in ((y0 + 250, y1), (y1 + 790, y2), (y2 + 470, y3)):
    arrow(1100, ya + 6, 1100, yb - 6, BLUE, 7); arrow(2500, yb - 6, 2500, ya + 6, RED, 7)
d.text((1130, y1 - 46), 'requirements, questions, photos', font=f_it, fill=BLUE)
d.text((2530, y1 - 46), 'measurements, test results', font=f_it, fill=RED)

# ---------- loop + evidence (bottom) ----------
y4 = 2470
card(L, y4, R - L, 900, (250, 250, 248), LINE, 22)
d.text((L + 40, y4 + 26), 'The loop  ·  propose → build → measure → correct', font=f_lay, fill=INK)
steps_ = [('Requirement', 'architect'), ('Proposal', 'AI: CAD / circuit / code'), ('Build', 'print · wire · solder'), ('Measure', 'calipers · meter · 3D view'), ('Correct', 'new version + log entry')]
sx = L + 40; sw = 520
for i, (a, b_) in enumerate(steps_):
    x = sx + i * (sw + 120); y = y4 + 100
    col = [INK, BLUE, RED, RED, GREEN][i]
    d.rounded_rectangle([x, y, x + sw, y + 110], radius=55, fill=WHITE, outline=col, width=5)
    d.text((x + sw / 2, y + 36), a, font=f_role, fill=col, anchor='mm'); d.text((x + sw / 2, y + 78), b_, font=f_b, fill=GREY, anchor='mm')
    if i < 4: arrow(x + sw + 10, y + 55, x + sw + 110, y + 55, LINE, 6)
# return arrow
d.line([(sx + 4 * (sw + 120) + sw / 2, y4 + 210), (sx + 4 * (sw + 120) + sw / 2, y4 + 250), (sx + sw / 2, y4 + 250)], fill=GREEN, width=6)
arrow(sx + sw / 2, y4 + 250, sx + sw / 2, y4 + 214, GREEN, 6)
d.text(((sx + sx + 4 * (sw + 120) + sw) / 2, y4 + 270), '9 CAD versions in 9 days', font=f_it, fill=GREEN, anchor='mm')

d.text((L + 40, y4 + 330), 'Real corrections from this loop (all logged in FAILS_AND_FIXES.md)', font=f_bb, fill=INK)
ev = [('3D view', 'Cross-beams ran through the power box (v1.5–1.8). Box moved onto the beams → CAD v1.9.'),
      ('Calipers', 'TD-8120MG ear plane 28.0, holes 10 apart Ø4.34, shaft 10.4 → servo pocket fixed in v1.8.'),
      ('DRC', 'First PCB: 32 → 19 → 15 violations → clean, then ready for AISLER.'),
      ('Manual photos', 'ROB0154 was assumed upside down for a day: motors high, not wet → hangers deleted.'),
      ('Arrival', 'Thruster is 112 × 77 mm, mounted from the top → transom pad redesign (open).'),
      ('Datasheet', 'Olimex board uses GPIO5/6 internally → second I²C bus moved to GPIO8/9.'),
      ('Listing check', 'Seven "thrusters" on Amazon were not thrusters → rule: thrust figure + ESC in the title.')]
ew = (R - L - 80 - 30) // 2
for i, (tag_, t) in enumerate(ev):
    x = L + 40 + (i % 2) * (ew + 30); y = y4 + 380 + (i // 2) * 120
    d.rounded_rectangle([x, y, x + 210, y + 44], radius=22, fill=AMBER)
    d.text((x + 105, y + 22), tag_, font=f_bb, fill=WHITE, anchor='mm')
    yy = y + 4
    for ln in wrap(t, f_b, ew - 250): d.text((x + 230, yy), ln, font=f_b, fill=INK); yy += 34

# ---------- right column: numbers + principles + roadmap ----------
RX = 3620
section((RX, 250, 4900, 3370), 'By the numbers')
kp = [('8', 'days, idea → orderable PCB'), ('1.9', 'current CAD version'), ('142', 'logged fails & fixes'), ('124', 'BOM items, all with photos'), ('3', 'DRC rounds to a clean board'), ('0', 'numbers without a source')]
for i, (n, t) in enumerate(kp):
    y = 350 + i * 190
    d.text((RX + 40, y), n, font=f_kpi, fill=RED)
    d.text((RX + 40 + f_kpi.getlength(n) + 26, y + 34), t, font=f_txt, fill=INK)
y = 350 + 6 * 190 + 20
d.line([(RX + 40, y), (4860, y)], fill=(200, 200, 200), width=3); y += 30
d.text((RX + 40, y), 'Rules that keep it honest', font=f_lay, fill=INK); y += 60
for t in ['AI output is a proposal until a measurement agrees.', 'Every figure lives in the numbers register with its source.',
          'Failures are logged the day they happen, with the fix.', 'The architect prints, wires, solders and tests.',
          'Commits carry the real date; earlier work is imported, not backdated.']:
    d.ellipse([RX + 44, y + 12, RX + 56, y + 24], fill=RED)
    for ln in wrap(t, f_b, 1150): d.text((RX + 76, y), ln, font=f_b, fill=INK); y += 34
    y += 12
y += 20; d.line([(RX + 40, y), (4860, y)], fill=(200, 200, 200), width=3); y += 30
d.text((RX + 40, y), 'Releases', font=f_lay, fill=INK); y += 60
rel = [('R1 · Oct', 'floats, lifts Pesho in the bathtub', 'next'), ('R2 · Nov', 'swims and steers in the pool', 'planned'), ('R3 · Dec', 'full autonomous rescue cycle', 'planned')]
for a, b_, st in rel:
    d.rounded_rectangle([RX + 40, y, RX + 250, y + 50], radius=25, fill=INK if st == 'next' else (150, 150, 150))
    d.text((RX + 145, y + 25), a, font=f_bb, fill=WHITE, anchor='mm')
    for ln in wrap(b_ + ('' if st == 'next' else '  (planned)'), f_b, 900): d.text((RX + 275, y + 8), ln, font=f_b, fill=INK); y += 34
    y += 36

d.text((60, H - 56), 'AmphiReach · AR-Mini · build process architecture · 07.10.2026 · T. Kyoseva.  Sources: docs/FAILS_AND_FIXES.md, docs/LOG.md, cad/, pcb/, docs/bom/ in github.com/TKyoseva/ARmini.', font=f_small, fill=GREY)
img.save('AR-Mini_build_process_architecture.png', dpi=(300, 300))
img.resize((W // 3, H // 3), Image.LANCZOS).save('AR-Mini_build_process_architecture_prev.png')
print('ok')
