import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, FancyBboxPatch

fig, ax = plt.subplots(figsize=(15, 11), dpi=150)
ax.set_xlim(0, 136); ax.set_ylim(-8, 104); ax.set_aspect("equal"); ax.axis("off")

COL = {"brown": "#7b3f00", "black": "#111", "red": "#d22", "orange": "#f80", "yellow": "#ffd400",
       "green": "#2a2", "blue": "#24c", "violet": "#80f", "grey": "#888", "white": "#fff", "gold": "#c9a227"}
CODES = {"100k": ["brown", "black", "black", "orange", "brown"],
         "33k":  ["orange", "orange", "black", "red", "brown"],
         "10k":  ["brown", "black", "black", "red", "brown"],
         "4k7":  ["yellow", "violet", "black", "brown", "brown"]}

def wire(p, q, c="#222", lw=2.2, z=3):
    ax.plot([p[0], q[0]], [p[1], q[1]], color=c, lw=lw, solid_capstyle="round", zorder=z)

def dot(p, c="#222"):
    ax.add_patch(Circle(p, 0.9, fc=c, ec="none", zorder=5))

def resistor(p, q, value, label=None, lw=2.2):
    """resistor body in the middle of the p→q wire, 5 colour bands"""
    import math
    (x1, y1), (x2, y2) = p, q
    L = math.hypot(x2 - x1, y2 - y1); ux, uy = (x2 - x1)/L, (y2 - y1)/L
    bl = 9.0; bw = 3.2
    mx, my = (x1 + x2)/2, (y1 + y2)/2
    wire((x1, y1), (mx - ux*bl/2, my - uy*bl/2), lw=lw)
    wire((mx + ux*bl/2, my + uy*bl/2), (x2, y2), lw=lw)
    ang = math.degrees(math.atan2(uy, ux))
    body = Rectangle((mx - bl/2, my - bw/2), bl, bw, fc="#3b6bd6", ec="#123", lw=1, zorder=6)
    import matplotlib.transforms as T
    tr = T.Affine2D().rotate_deg_around(mx, my, ang) + ax.transData
    body.set_transform(tr); ax.add_patch(body)
    for i, cname in enumerate(CODES[value]):
        off = -bl/2 + 1.3 + i*1.45 + (0.8 if i == 4 else 0)
        band = Rectangle((mx + off - 0.45, my - bw/2), 0.9, bw, fc=COL[cname], ec="none", zorder=7)
        band.set_transform(tr); ax.add_patch(band)
    if label:
        lx, ly = mx - uy*3.6, my + ux*3.6
        ax.text(lx, ly, label, ha="center", va="center", fontsize=8.5, weight="bold", color="#123", zorder=8,
                rotation=(ang if abs(ang) < 1 else 90))

def tap(p, kind):
    x, y = p
    if kind == "gnd":
        wire((x, y), (x - 2.5, y), c="#24c");
        for i, w in enumerate((2.6, 1.7, 0.8)):
            ax.plot([x - 2.5 - 0.6*i, x - 2.5 - 0.6*i], [y - w/2, y + w/2], color="#24c", lw=2)
        ax.text(x - 4.6, y + 2.2, "→ − rail\nGND", ha="right", va="center", fontsize=7, color="#24c")
    else:
        wire((x, y), (x - 2.5, y), c="#d22")
        ax.add_patch(Polygon([[x - 2.5, y - 1.3], [x - 2.5, y + 1.3], [x - 5.0, y]], closed=True, fc="#d22", ec="none"))
        ax.text(x - 5.6, y, "+ rail\n3V3", ha="right", va="center", fontsize=7, color="#d22")

# ---------- rails (left breadboard edge)
for x, c, lab in [(10, "#24c", "−  GND"), (15, "#d22", "+  3V3")]:
    ax.plot([x, x], [2, 97], color=c, lw=3, alpha=0.9)
    for yy in range(4, 97, 4): ax.add_patch(Circle((x, yy), 0.6, fc="white", ec=c, lw=0.8))
    ax.text(x, 99.5, lab, ha="center", fontsize=9, weight="bold", color=c)
ax.text(3.5, 50, "шините на левия BB400 · + е 3V3 от EXT1 пин 1, НЕ 5 V", ha="center", va="center", fontsize=7.5, color="#333", rotation=90)

# ---------- DevKit
DX, DY, DW, DH = 70, 14, 26, 78
ax.add_patch(Rectangle((DX, DY), DW, DH, fc="#d44", ec="#600", lw=1.5, zorder=2))
ax.add_patch(Rectangle((DX + 4.5, DY + 52), 17, 20, fc="#999", ec="#333", lw=0.8, zorder=3))
ax.text(DX + 13, DY + 62, "WROOM-1", ha="center", va="center", fontsize=7, zorder=4)
ax.add_patch(Rectangle((DX + 4.5, DY + DH), 17, 4.5, fc="#bbb", ec="#333", hatch="//", zorder=3))
ax.text(DX + 13, DY + DH + 2.2, "антена ↑", ha="center", va="center", fontsize=7, zorder=4)
for xx, lab in ((DX + 4, "OTG1 → Mac"), (DX + 15, "UART1")):
    ax.add_patch(Rectangle((xx, DY - 2.6), 7, 2.6, fc="#444", ec="#111", zorder=3))
    ax.text(xx + 3.5, DY - 4.4, lab, ha="center", fontsize=6.2, color="#333")
ax.text(DX + 13, DY + 30, "ESP32-S3\nDevKit-Lipo", ha="center", va="center", fontsize=9, weight="bold", zorder=4)
ax.text(DX + 13, DY + 20, "антената нагоре,\nEXT1 вляво, EXT2 вдясно", ha="center", va="center", fontsize=6.5, zorder=4)

def ypin(k): return DY + DH - 2 - (k - 1) * 3.5
used = {1: "3V3", 2: "3V3", 4: "GPIO4  VBAT", 7: "GPIO7  LEAK", 20: "GPIO14  KILL", 21: "+5V (не!)", 22: "GND"}
for k in range(1, 23):
    y = ypin(k)
    for xx, side in ((DX + 1.5, "L"), (DX + DW - 1.5, "R")):
        ax.add_patch(Circle((xx, y), 0.75, fc="white", ec="#333", lw=0.5, zorder=4))
    ax.text(DX - 0.8 + 0.0, y, str(k), ha="right", va="center", fontsize=5.2, color="#eee", zorder=4) if False else None
    if k in used:
        ax.text(DX + 3.2, y, f"{k}", ha="left", va="center", fontsize=5.5, color="white", zorder=4)
# EXT names
ax.text(DX + 1.5, DY + DH + 1.2, "EXT1", ha="center", fontsize=7, weight="bold", color="#600")
ax.text(DX + DW - 1.5, DY + DH + 1.2, "EXT2", ha="center", fontsize=7, weight="bold", color="#600")
ax.text(DX + DW - 4.2, DY + 26, "EXT2: тази вечер не се пипа · R12–R15 (10 k към GND, пин 6–9) остават", ha="center", va="center", fontsize=5.8, color="white", rotation=90, zorder=4)

# breadboard row stubs for the used EXT1 pins (the 5 connected holes of the row)
STUB = 58
for k, name in used.items():
    y = ypin(k)
    ax.plot([STUB, DX + 1.5], [y, y], color="#bbb", lw=4, zorder=1, solid_capstyle="round")
    for i in range(4): ax.add_patch(Circle((STUB + 1.5 + i*3.0, y), 0.6, fc="white", ec="#999", lw=0.5, zorder=2))
    short = {1: "пин 1 · 3V3", 2: "пин 2 · 3V3", 4: "пин 4 · GPIO4", 7: "пин 7 · GPIO7", 20: "пин 20 · GPIO14", 21: "пин 21 · +5V — не!", 22: "пин 22 · GND"}[k]
    ax.text(STUB + 0.3, y + 1.9, short, ha="left", va="center", fontsize=6.3, weight="bold",
            color=("#d22" if "3V3" in name else "#24c" if name == "GND" else "#555" if "5V" in name else "#123"))

# ---------- jumpers to the rails
y1 = ypin(1)
wire((STUB, y1), (STUB - 1, y1), c="#d22"); wire((STUB - 1, y1), (STUB - 1, 96.5), c="#d22"); wire((STUB - 1, 96.5), (15, 96.5), c="#d22"); dot((15, 96.5), "#d22")
ax.text(36, 97.8, "червен джъмпер: пин 1 → + шина (3V3)", ha="center", fontsize=7, color="#d22")
y22 = ypin(22)
wire((STUB, y22), (10, y22), c="#111"); dot((10, y22), "#111")
ax.text(34, y22 - 2.4, "черен джъмпер: пин 22 → − шина (GND)", ha="center", fontsize=7, color="#111")
# Jesverty minus
wire((10, 2), (10, -1.5), c="#111");
ax.text(10, -3.0, "Jesverty −", ha="center", va="top", fontsize=7.5, weight="bold")

# ---------- VBAT divider
y4 = ypin(4)
VB = (30, 8)
wire((25, -2.5), (25, 2.5), c="#ffd400", lw=2.8); wire((25, 2.5), VB, c="#ffd400", lw=2.8); dot(VB, "#b80")
ax.text(25, -3.6, "Jesverty +\n12.00 V · лимит 0.10 A", ha="center", va="top", fontsize=7.5, weight="bold", color="#8a6d00")
ax.text(32.5, 9.4, "VBAT възел (мери тук)", ha="left", va="center", fontsize=7, color="#8a6d00")
wire(VB, (30, y4), c="#ffd400", lw=2.8)
dot((30, y4), "#b80")
resistor((30, y4), (50, y4), "100k", "R1  100 k")
dot((50, y4), "#222"); wire((50, y4), (STUB, y4))
resistor((50, y4), (50, 88), "33k", "R2  33 k"); tap((50, 89.5), "gnd") if False else None
wire((50, 88), (50, 89.5)); tap((50, 89.5), "gnd")

# ---------- LEAK
y7 = ypin(7)
resistor((36, y7), (STUB, y7), "10k", "R20  10 k"); tap((36, y7), "3v3")
dot((STUB, y7), "#222")
resistor((STUB, y7), (STUB, 55), "4k7", "R21  4.7 k")
wire((STUB, 55), (52, 51), c="#80f", lw=2.4)
# cup
ax.add_patch(Polygon([[41, 36], [55, 36], [53.5, 50], [42.5, 50]], closed=True, fc="#dff3ff", ec="#39c", lw=1.5, zorder=2))
ax.add_patch(Rectangle((42.5, 36.5), 11.5, 9, fc="#9fd6ff", ec="none", zorder=2))
ax.text(48, 32.5, "чаша чешмяна вода", ha="center", fontsize=7, color="#126")
wire((52, 51), (51, 40), c="#80f", lw=2.4); wire((44, 51), (45, 40), c="#111", lw=2.4)
ax.text(48, 46.5, "сонда:\n2 голи\nжички", ha="center", va="center", fontsize=6.5, color="#126", zorder=3)
wire((44, 51), (40, 55), c="#111", lw=2.4); tap((40, 55), "gnd")

# ---------- KILL
y20 = ypin(20)
resistor((36, y20), (STUB, y20), "10k", "R22  10 k"); tap((36, y20), "3v3")
dot((STUB, y20), "#222")
wire((STUB, y20), (55, 21), c="#80f", lw=2.4); wire((55, 21), (55, 12), c="#80f", lw=2.4); wire((55, 12), (65, 12), c="#80f", lw=2.4); wire((65, 12), (65, 10), c="#80f", lw=2.4)
# rocker
ax.add_patch(FancyBboxPatch((57, 2), 16, 8.5, boxstyle="round,pad=0,rounding_size=1.2", fc="#eee", ec="#333", lw=1.2, zorder=2))
ax.text(65, 8.2, "ключ (rocker)", ha="center", fontsize=7, weight="bold", zorder=3)
for xx, lab in ((59.5, "KILL"), (65, "C"), (70.5, "RUN")):
    ax.add_patch(Circle((xx, 4.2), 0.9, fc="#333", ec="none", zorder=3)); ax.text(xx, 5.9, lab, ha="center", fontsize=6.2, zorder=3)
wire((59.5, 4.2), (59.5, 0.3), c="#111"); wire((59.5, 0.3), (10, 0.3), c="#111"); dot((10, 0.3), "#111")
ax.text(42, -1.0, "KILL контакт → − шина (GND)", ha="center", va="top", fontsize=6.5, color="#111")
ax.text(73.8, 3.6, "RUN: свободен", ha="left", va="center", fontsize=6.2, color="#555")
ax.text(54.0, 19.6, "C → GPIO14", ha="right", va="center", fontsize=6.5, color="#80f")

# ---------- checks box
bx, by = 102, 96
ax.text(bx, by, "С мултицета, ПРЕДИ Jesverty:", fontsize=9, weight="bold", va="top")
checks = ["Ω  VBAT възел ↔ GPIO4 ред ≈ 100 k",
          "Ω  GPIO4 ред ↔ GND ≈ 33 k",
          "звънене VBAT ↔ GPIO4: БЕЗ звук",
          "   (пряка връзка = 12 V на чипа)",
          "Ω  GPIO7 ↔ 3V3 ≈ 10 k",
          "Ω  GPIO14 ↔ 3V3 ≈ 10 k",
          "звънене GPIO14 ↔ GND,",
          "   ключ на KILL: звъни"]
for i, t in enumerate(checks):
    ax.text(bx, by - 4.2 - i*3.4, t, fontsize=7.8, va="top", family="DejaVu Sans")
ax.text(bx, by - 34, "После:", fontsize=9, weight="bold", va="top")
steps = ["1  само USB, монитор 115200, `?`",
         "   leak_mV ≈ 3300, kill следва ключа",
         "2  Jesverty 12.00 V → v_adc_mV ≈ 2978",
         "3  `cal 12.00` (числото от мултицета)",
         "4  9.9 · 10.0 · 10.5 · 11.0 V → ±0.1 V",
         "5  12.6 V: спира ли над ~12.4? запиши",
         "6  сонда суха / във водата / допряна:",
         "   3300 / ~1000 / ~1055 mV",
         "7  ключ RUN→KILL→RUN: kill 0→1→0"]
for i, t in enumerate(steps):
    ax.text(bx, by - 38.2 - i*3.4, t, fontsize=7.6, va="top")

# ---------- colour code legend
lx, ly = 102, 26
ax.text(lx, ly, "Резистори (MOGAOPI 1 %, 5 ленти):", fontsize=8.5, weight="bold", va="top")
for i, (v, lab) in enumerate([("100k", "100 kΩ"), ("33k", "33 kΩ"), ("10k", "10 kΩ  ×2"), ("4k7", "4.7 kΩ")]):
    yy = ly - 5 - i*4.6
    resistor((lx + 1, yy), (lx + 14, yy), v)
    ax.text(lx + 16, yy, lab + "  " + "-".join(CODES[v]), fontsize=7, va="center")

ax.text(0, 103, "C027 · ladder bench на breadboard-а · DevKit-Lipo · делител за батерията, сонда за теч, ключ KILL", fontsize=12.5, weight="bold", va="bottom")
fig.savefig("AR-Mini_breadboard_2b_ladder-step.png", bbox_inches="tight", facecolor="white")
print("ok")
