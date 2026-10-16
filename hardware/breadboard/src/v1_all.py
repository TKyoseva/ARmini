import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon

fig, ax = plt.subplots(figsize=(21, 14.5), dpi=140)
ax.set_xlim(0, 204); ax.set_ylim(-1, 147); ax.set_aspect("equal"); ax.axis("off")

C = dict(v12="#e6b800", v5="#f08000", v33="#d22", gnd="#111", sda="#2a9d4a", scl="#1b8f9f",
         pwm="#1f5fd6", sig="#5e35b1", en="#ff2d95", srv="#8b5a2b")

def wire(pts, c, lw=2.0, z=3, ls="-"):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=c, lw=lw, solid_joinstyle="round", solid_capstyle="round", zorder=z, ls=ls)
def dot(p, c="#111", r=0.8): ax.add_patch(Circle(p, r, fc=c, ec="none", zorder=7))
def label(p, t, c="#222", fs=6.5, ha="center", va="center", rot=0, bold=False, z=9):
    ax.text(p[0], p[1], t, color=c, fontsize=fs, ha=ha, va=va, rotation=rot, weight=("bold" if bold else "normal"), zorder=z)
def gnd(p, c="#111"):
    x, y = p
    wire([(x, y), (x, y - 1.6)], c, 1.4)
    for i, w in enumerate((2.4, 1.5, 0.7)): ax.plot([x - w/2, x + w/2], [y - 1.6 - i*0.55]*2, color=c, lw=1.4, zorder=5)
def module(x, y, w, h, title, sub=None, fc="#2b4f8a", fs=8, z=4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec="#111", lw=1.2, zorder=z))
    label((x + w/2, y + h - 2.5), title, c="white", fs=fs, bold=True, z=z+1)
    if sub: label((x + w/2, y + h - 5.4), sub, c="white", fs=fs-2, z=z+1)
def pinrow(x, y, names, dy=-1.8, side="left", fs=4.8):
    out = {}
    for i, n in enumerate(names):
        yy = y + i*dy
        ax.add_patch(Rectangle((x - 0.7, yy - 0.7), 1.4, 1.4, fc="#ffd", ec="#333", lw=0.5, zorder=7))
        label((x + (1.6 if side == "left" else -1.6), yy), n, c="#eee", fs=fs, ha=("left" if side == "left" else "right"))
        out[n] = (x, yy)
    return out
def res(p, q, txt, lab_side=1):
    (x1, y1), (x2, y2) = p, q; mx, my = (x1 + x2)/2, (y1 + y2)/2
    if abs(x2 - x1) >= abs(y2 - y1):
        wire([p, (mx - 2.6, my)], "#222", 1.5); wire([(mx + 2.6, my), q], "#222", 1.5)
        ax.add_patch(Rectangle((mx - 2.6, my - 0.9), 5.2, 1.8, fc="#3b6bd6", ec="#123", lw=0.8, zorder=6))
        label((mx, my + 1.9*lab_side), txt, fs=5.4, bold=True)
    else:
        wire([p, (mx, my - 2.6)], "#222", 1.5); wire([(mx, my + 2.6), q], "#222", 1.5)
        ax.add_patch(Rectangle((mx - 0.9, my - 2.6), 1.8, 5.2, fc="#3b6bd6", ec="#123", lw=0.8, zorder=6))
        label((mx + 1.9*lab_side, my), txt, fs=5.4, bold=True, rot=90)

# ================= breadboards
def bb400(x, y, w, h, rails):
    ax.add_patch(Rectangle((x, y), w, h, fc="#f1f1ec", ec="#999", lw=1.2, zorder=1))
    rx = (x + 2.0, x + 4.0) if rails == "left" else (x + w - 2.0, x + w - 4.0)
    for xx, cc in zip(rx, ("#24c", "#d22")): ax.plot([xx, xx], [y + 2, y + h - 2], color=cc, lw=1.6, alpha=0.8, zorder=2)
    for yy in range(int(y) + 3, int(y + h) - 2, 3):
        for xx in range(int(x) + 8, int(x + w) - 6, 3): ax.add_patch(Circle((xx, yy), 0.45, fc="#ddd", ec="none", zorder=2))
    return rx
GNDL, V33L = bb400(62, 28, 33, 73, "left")      # 64, 66
GNDR, V33R = bb400(100, 28, 25, 73, "right")    # 123, 121
label((69, 29.3), "BB400 ляв", fs=5.5, c="#777", ha="left"); label((101, 29.3), "BB400 десен", fs=5.5, c="#777", ha="left")
label((65, 102.3), "− GND  + 3V3", fs=6, c="#333"); label((117, 102.3), "+ 3V3  − GND", fs=6, c="#333", ha="right")

# ================= DevKit
DX, DY, DW, DH = 86, 41, 23, 58
ax.add_patch(Rectangle((DX, DY), DW, DH, fc="#d44", ec="#600", lw=1.5, zorder=3))
ax.add_patch(Rectangle((DX + 4, DY + 40), 15, 15, fc="#999", ec="#333", lw=0.8, zorder=4)); label((DX + 11.5, DY + 47.5), "WROOM-1", fs=6.5)
ax.add_patch(Rectangle((DX + 4, DY + DH), 15, 3.5, fc="#bbb", ec="#333", hatch="//", zorder=4)); label((DX + 11.5, DY + DH + 1.7), "антена", fs=6)
for xx, lab in ((DX + 3.5, "OTG1"), (DX + 13, "UART1")):
    ax.add_patch(Rectangle((xx, DY - 2.4), 6.5, 2.4, fc="#444", ec="#111", zorder=4)); label((xx + 3.2, DY - 1.2), lab, c="white", fs=4.6)
label((DX + 11.5, DY + 25), "ESP32-S3\nDevKit-Lipo", c="white", fs=8.5, bold=True)
label((DX + 11.5, DY + 15.5), "на два BB400 един до друг:\nредовете са на 25.40\n= 10 стъпки (C030)", c="white", fs=5.2)
label((DX + 1.5, DY + DH + 1.6), "EXT1", fs=6, bold=True, c="#600"); label((DX + DW - 1.5, DY + DH + 1.6), "EXT2", fs=6, bold=True, c="#600")
def yp(k): return DY + DH - 2 - (k - 1) * 2.5
X1 = DX + 1.5; X2 = DX + DW - 1.5
for k in range(1, 23):
    for xx in (X1, X2): ax.add_patch(Circle((xx, yp(k)), 0.65, fc="white", ec="#333", lw=0.4, zorder=5))
E1 = {1: "3V3", 2: "3V3", 4: "GPIO4·VBAT", 7: "GPIO7·LEAK", 12: "GPIO8·SDA1", 15: "GPIO9·SCL1", 20: "GPIO14·KILL", 21: "+5V in", 22: "GND"}
E2 = {1: "GND", 4: "GPIO1·ESC_L", 5: "GPIO2·ESC_R", 6: "GPIO42·R LPWM", 7: "GPIO41·R RPWM", 8: "GPIO40·L LPWM", 9: "GPIO39·L RPWM", 16: "GPIO48·SDA0", 17: "GPIO47·SCL0", 22: "GND"}
S1 = 76.5; S2 = 116.0
for k, n in E1.items():
    ax.plot([S1, X1], [yp(k), yp(k)], color="#c8c8c0", lw=3.2, zorder=2, solid_capstyle="round")
    label((S1 + 0.2, yp(k) + 1.55), f"{k}·{n}", fs=4.9, ha="left", bold=True, c="#123")
for k, n in E2.items():
    ax.plot([X2, S2], [yp(k), yp(k)], color="#c8c8c0", lw=3.2, zorder=2, solid_capstyle="round")
    label((S2 - 0.2, yp(k) + 1.55), f"{k}·{n}", fs=4.9, ha="right", bold=True, c="#123")

# rails hookup
wire([(S1, yp(1)), (75.3, yp(1)), (75.3, 99), (V33L, 99)], C["v33"]); dot((V33L, 99), C["v33"])
wire([(S1, yp(22)), (GNDL, yp(22))], C["gnd"]); dot((GNDL, yp(22)))
wire([(S2, yp(1)), (GNDR, yp(1))], C["gnd"]); dot((GNDR, yp(1)))
wire([(V33L, 99), (V33L, 103.5), (V33R, 103.5), (V33R, 99)], C["v33"], ls=(0, (3, 2)))
label((93.5, 105.2), "+ шини = 3V3 от EXT1 пин 1 · − шини = GND · 5 V НЕ е на шина", fs=6, c="#a00", bold=True)
wire([(GNDL, 30), (GNDL, 27), (GNDR, 27), (GNDR, 30)], C["gnd"], ls=(0, (3, 2)))

# ================= LEFT: divider, leak, kill
y4, y7, y20, y21, y12, y15 = yp(4), yp(7), yp(20), yp(21), yp(12), yp(15)
VB = (68, y4)
res((VB[0], y4), (S1, y4), "100 k"); dot(VB, "#b80"); label((69.2, y4 + 1.9), "VBAT", fs=4.8, c="#8a6d00")
res((74.5, y4 - 8.5), (74.5, y4), "33 k"); dot((74.5, y4)); wire([(74.5, y4 - 8.5), (GNDL, y4 - 8.5)], C["gnd"], 1.5); dot((GNDL, y4 - 8.5))
res((V33L, y7), (S1, y7), "10 k"); dot((V33L, y7), C["v33"])
res((74, y7 - 8), (74, y7), "4.7 k"); dot((74, y7))
wire([(74, y7 - 8), (41.5, y7 - 8), (41.5, 71)], C["sig"], 1.8)
ax.add_patch(Polygon([[39.5, 63], [48.5, 63], [48, 71], [40, 71]], closed=True, fc="#cfe9ff", ec="#39c", lw=1, zorder=2))
label((43.5, 76.3), "сонда за теч: 2 голи жички\nна дъното на корпуса", fs=4.8, c="#126")
wire([(48.3, 66), (53, 66)], C["gnd"], 1.5); gnd((53, 66))
res((V33L, y20), (S1, y20), "10 k", lab_side=-1); dot((V33L, y20), C["v33"])
# I2C1 to MLX90640 (top left)
module(46, 108, 24, 10, "MLX90640 110°", "I2C1 0x33 · на люлката", fc="#1a6f3a")
wire([(S1, y12), (57, y12), (57, 108)], C["sda"], 1.5); wire([(S1, y15), (59, y15), (59, 108)], C["scl"], 1.5)
label((72, 113), "SDA GPIO8 → EXT1 12\nSCL GPIO9 → EXT1 15\n3V3 + GND от левите шини", fs=4.8, c="#444", ha="left")

# ================= EN node, Q2, 5 V
EN = (70, 37); label((70, 39.4), "EN възел", fs=5.2, c=C["en"], bold=True); dot(EN, C["en"])
res((GNDL, 37), (EN[0], 37), "10 k", lab_side=-1); dot((GNDL, 37))
ax.add_patch(Circle((79, 33), 2.1, fc="#eee", ec="#333", lw=1, zorder=6)); label((79, 33), "Q2", fs=5.2)
res((EN[0], 33), (76.9, 33), "10 k", lab_side=-1); wire([(EN[0], 37), (EN[0], 33)], C["en"], 1.5)
wire([(79, 30.9), (79, 29.3)], C["gnd"], 1.4); gnd((79, 29.3))
wire([(79, 35.1), (79, 38.5)], C["en"], 1.5); dot((79, 38.5), C["en"])
res((79, 38.5), (85, 38.5), "2.2 k"); wire([(85, 38.5), (85, 40.3)], C["v33"], 1.5); label((85, 41.6), "3V3", fs=4.6, c=C["v33"])
label((83.2, 33), "BC337", fs=4.4, c="#444", ha="left")
# OE to the PCA9685 (routed under the boards)
wire([(79, 38.5), (82, 38.5), (82, 16.5), (133.5, 16.5), (133.5, 20)], C["en"], 1.4)
# 5 V from the buck
V5X = 59
wire([(56, 55), (V5X, 55), (V5X, 24), (77.5, 24), (77.5, y21), (S1, y21)], C["v5"], 1.8)
label((V5X - 0.6, 52), "5 V", fs=5, c=C["v5"], ha="right")

# ================= rocker DPDT
RK = (30, 30)
ax.add_patch(FancyBboxPatch(RK, 24, 11, boxstyle="round,pad=0,rounding_size=1.2", fc="#eee", ec="#333", lw=1.2, zorder=4))
label((RK[0] + 12, RK[1] + 9.3), "ключ DPDT ON-ON · RUN / KILL", fs=6, bold=True)
poles = [(33, "RUN"), (37, "C1"), (41, "KILL"), (46, "RUN"), (50, "C2"), (54, "KILL")]
for xx, nm in poles:
    ax.add_patch(Circle((xx, RK[1] + 4), 0.9, fc="#333", ec="none", zorder=5)); label((xx, RK[1] + 6.2), nm, fs=4.8)
label((37, RK[1] + 1.5), "полюс 1 → EN", fs=4.6, c=C["en"]); label((50, RK[1] + 1.5), "полюс 2 → GPIO14", fs=4.6, c=C["sig"])
wire([(37, 34), (37, 44.5), (62, 44.5), (62, 37), (EN[0], 37)], C["en"], 1.6)            # C1 -> EN
wire([(33, 34), (33, 46.5), (57, 46.5), (57, 55), (V5X, 55)], C["v5"], 1.6)             # RUN -> 5 V
wire([(41, 34), (41, 28.5)], C["gnd"], 1.4); gnd((41, 28.5))                              # KILL -> GND
wire([(50, 34), (50, 42.5), (72.5, 42.5), (72.5, y20)], C["sig"], 1.6); dot((72.5, y20))  # C2 -> GPIO14 row
wire([(54, 34), (54, 28.5)], C["gnd"], 1.4); gnd((54, 28.5))

# ================= POWER (far left)
module(4, 120, 22, 14, "LiPo 3S 2200 mAh", "11.1 V · XT60", fc="#1f4fbf")
module(4, 106, 22, 10, "30 A inline fuse", "GT4652, до 10 cm от XT60", fc="#555")
module(4, 92, 22, 10, "главен ключ 50 A", "спира 12 V за всичко", fc="#555")
module(4, 50, 26, 38, "fuse block · 6 слота", None, fc="#222")
FUSE = {}
for i, (nm, txt) in enumerate([("F1", "20 A · тръстери ×2"), ("F2", "15 A · servo buck"), ("F3", "10 A · BTS7960 ×2"), ("F4", "5 A · logic buck + VBAT"), ("F5", "5 A · Pi (v2, празен)")]):
    yy = 50 + 32 - i*5.5
    ax.add_patch(Rectangle((6, yy - 1.4), 5, 2.8, fc=("#d22" if i < 4 else "#777"), ec="none", zorder=5)); label((8.5, yy), nm, c="white", fs=5.2, bold=True)
    label((12.3, yy), txt, c="#eee", fs=5.2, ha="left"); FUSE[nm] = (30, yy)
    ax.add_patch(Circle((30, yy), 0.7, fc="#ffd", ec="#333", lw=0.5, zorder=6))
label((17, 52.5), "общ 12 V вход от главния ключ", c="#bbb", fs=4.8)
wire([(15, 120), (15, 116)], C["v12"], 2.6); wire([(15, 106), (15, 102)], C["v12"], 2.6); wire([(15, 92), (15, 88)], C["v12"], 2.6)
for yy in (118, 104, 90): label((16.8, yy), "+", fs=7, bold=True, c=C["v12"])
wire([(8, 120), (2, 120), (2, 8.5), (GNDL, 8.5), (GNDL, 27)], C["gnd"], 2.4); label((1.1, 62), "LiPo − = общ GND (всички GND в листа)", fs=5.4, c="#111", rot=90)
# logic buck
module(36, 48, 20, 12, "MZHOU buck", "12 → 5 V · 3 A", fc="#8b1a1a"); label((46, 50.6), "измери 4.9–5.2 V преди връзка", c="#fdd", fs=4.2)
wire([FUSE["F4"], (33.5, FUSE["F4"][1]), (33.5, 57), (36, 57)], C["v12"], 1.8); label((34.2, 59), "IN", fs=4.6, c=C["v12"])
wire([(36, 51), (34.5, 51), (34.5, 45.5)], C["gnd"], 1.4); gnd((34.5, 45.5))
label((57.5, 57.2), "OUT 5 V", fs=4.6, c=C["v5"])
# VBAT 12 V to the divider
wire([FUSE["F4"], (32.5, FUSE["F4"][1]), (32.5, 104.5), (60.5, 104.5), (60.5, y4), (VB[0], y4)], C["v12"], 1.5)
label((36, 105.8), "F4 12 V → 100 k (само за мерене, 95 µA)", fs=5, c="#8a6d00", ha="left")

# ================= RIGHT BOARD: pull-downs block
ax.add_patch(Rectangle((116.6, yp(9) - 1.3), 3.0, yp(6) - yp(9) + 2.6, fc="#3b6bd6", ec="#123", lw=0.8, zorder=6))
label((118.1, (yp(6) + yp(9))/2), "4 × 10 k", c="white", fs=4.4, rot=90, bold=True)
wire([(118.1, yp(9) - 1.3), (118.1, 72.5), (GNDR, 72.5)], C["gnd"], 1.4); dot((GNDR, 72.5))
label((118.3, 70.6), "R12–R15 → GND (C015)", fs=4.6, c="#123", ha="left")

# ================= BTS7960 + motors
def bts(x, y, name):
    ax.add_patch(FancyBboxPatch((x, y), 30, 15, boxstyle="round,pad=0,rounding_size=1.2", fc="#2d2d2d", ec="#111", lw=1.2, zorder=4))
    label((x + 10, y + 12.5), f"BTS7960 {name}", c="white", fs=7.5, bold=True); label((x + 10, y + 9.9), "43 A H-bridge", c="white", fs=5.5)
    pins = pinrow(x + 2, y + 8.4, ["RPWM", "LPWM", "EN", "VCC", "GND"], dy=-1.75, side="left", fs=4.6)
    ax.add_patch(Rectangle((x + 19.5, y + 9.5), 10, 4.2, fc="#0a5", ec="#111", zorder=5)); label((x + 24.5, y + 11.6), "B+ B− M+ M−", c="white", fs=4.4)
    return pins
BR = bts(138, 86, "R (десен)"); BL = bts(138, 64, "L (ляв)")
label((153, 61.8), "R_EN и L_EN на модула свързани заедно → EN", fs=4.8, c="#444")
PWMX = {7: 131, 6: 132.5, 9: 134, 8: 135.5}
for k, pin in ((7, BR["RPWM"]), (6, BR["LPWM"]), (9, BL["RPWM"]), (8, BL["LPWM"])):
    wire([(119.6, yp(k)), (PWMX[k], yp(k)), (PWMX[k], pin[1]), pin], C["pwm"], 1.5)
for p, xoff in ((BR, 0), (BL, 0)):
    wire([p["GND"], (138.6, p["GND"][1]), (138.6, p["GND"][1] - 3.2)], C["gnd"], 1.3); gnd((138.6, p["GND"][1] - 3.2))
    wire([p["VCC"], (136.6, p["VCC"][1]), (136.6, 22), (77.5, 22), (77.5, 24)], C["v5"], 1.3)
    wire([p["EN"], (137.6, p["EN"][1]), (137.6, 20.5), (62, 20.5), (62, 37)], C["en"], 1.3)
label((100, 25.3), "оранжево = 5 V към VCC на двата BTS · розово = EN към R_EN+L_EN на двата", fs=4.8, c="#444", ha="left")
module(174, 86, 21, 10, "верига R", "мотор ROB0154", fc="#444"); module(174, 64, 21, 10, "верига L", "мотор ROB0154", fc="#444")
wire([(167.5, 95.5), (171, 95.5), (171, 91), (174, 91)], C["srv"], 2.0); wire([(167.5, 73.5), (171, 73.5), (171, 69), (174, 69)], C["srv"], 2.0)
# 12 V to B+ (F3) along the top and the far right
wire([FUSE["F3"], (31.5, FUSE["F3"][1]), (31.5, 136.5), (197, 136.5), (197, 97.5), (167.5, 97.5)], C["v12"], 2.0); wire([(197, 97.5), (197, 75.5), (167.5, 75.5)], C["v12"], 2.0)
label((70, 137.4), "F3 10 A → B+ на двата BTS7960 · B− → GND", fs=5, c="#8a6d00")

# ================= thrusters
module(138, 104, 26, 11, "тръстер L", "ESC вътре · S от GPIO1 · G → GND", fc="#1a6f8a", fs=7.5); module(166, 104, 26, 11, "тръстер R", "ESC вътре · S от GPIO2 · G → GND", fc="#1a6f8a", fs=7.5)
for x0 in (138, 166):
    for i, (nm, col) in enumerate([("+", C["v12"]), ("−", C["gnd"]), ("S", C["pwm"]), ("G", "#999")]):
        xx = x0 + 4 + i*5.5
        ax.add_patch(Circle((xx, 104), 0.8, fc=col, ec="#111", lw=0.4, zorder=6)); label((xx, 106.2), nm, c="white", fs=4.6)
wire([(119.6, yp(4)), (129.2, yp(4)), (129.2, 102.8), (149, 102.8), (149, 104)], C["pwm"], 1.5)
wire([(119.6, yp(5)), (128.0, yp(5)), (128.0, 101.8), (177, 101.8), (177, 104)], C["pwm"], 1.5)

for x0 in (138, 166):
    wire([(x0 + 9.5, 104), (x0 + 9.5, 102.0)], C["gnd"], 1.2); gnd((x0 + 9.5, 102.0))
    wire([(x0 + 20.5, 104), (x0 + 20.5, 102.6)], "#999", 1.2); gnd((x0 + 20.5, 102.6), "#999")
wire([FUSE["F1"], (31, FUSE["F1"][1]), (31, 134.5), (136.5, 134.5), (136.5, 116.3), (142, 116.3), (142, 115)], C["v12"], 2.0); wire([(136.5, 134.5), (164.5, 134.5), (164.5, 116.3), (170, 116.3), (170, 115)], C["v12"], 2.0)
label((70, 135.4), "F1 20 A → червено (+) на двата тръстера · черно (−) → GND", fs=5, c="#8a6d00")

# ================= PCA9685, servos, servo buck
module(138, 34, 32, 18, "PCA9685", "I2C0 0x40 · 16 × PWM · OE · V+", fc="#2b4f8a")
PP = pinrow(140, 45.5, ["VCC", "GND", "SDA", "SCL", "OE"], dy=-2.0, side="left", fs=4.6)
ax.add_patch(Rectangle((160, 36), 8, 5, fc="#0a5", ec="#111", zorder=5)); label((164, 38.5), "V+  GND", c="white", fs=4.4)
CHX = {}
for i, ch in enumerate(["CH6", "CH7", "CH8", "CH9", "CH10", "CH11"]):
    xx = 142 + i*4.0; CHX[ch] = xx
    ax.add_patch(Rectangle((xx - 0.6, 35.0), 1.2, 1.2, fc="#ffd", ec="#333", lw=0.4, zorder=7)); label((xx, 33.4), ch, fs=4.0)
wire([PP["VCC"], (136, PP["VCC"][1]), (136, 31), (V33R, 31)], C["v33"], 1.3); dot((V33R, 31), C["v33"])
wire([PP["GND"], (135, PP["GND"][1]), (135, 30)], C["gnd"], 1.3); gnd((135, 30))
wire([(119.6, yp(16)), (126.2, yp(16)), (126.2, PP["SDA"][1]), PP["SDA"]], C["sda"], 1.5)
wire([(119.6, yp(17)), (125.0, yp(17)), (125.0, PP["SCL"][1]), PP["SCL"]], C["scl"], 1.5)
wire([(133.5, 20), (133.5, PP["OE"][1]), PP["OE"]], C["en"], 1.4)
module(174, 34, 22, 12, "servo buck", "12 → 6 V · ≥ 5 A", fc="#8b1a1a")
label((185, 31.2), "VERIFY: няма го в BOM. v1: QIQIAZI 5 V 5 A\n(Pi не е в лодката) или 6 V buck · от F2", fs=4.5, c="#a00")
wire([FUSE["F2"], (32, FUSE["F2"][1]), (32, 138.5), (199.5, 138.5), (199.5, 42), (196, 42)], C["v12"], 1.8)
label((70, 139.4), "F2 15 A → servo buck IN", fs=5, c="#8a6d00")
wire([(174, 38.5), (168, 38.5)], C["v5"], 1.8); label((171, 40.4), "6 V → V+", fs=4.4, c=C["v5"])
wire([(174, 36.5), (172, 36.5), (172, 34.5)], C["gnd"], 1.2); gnd((172, 34.5))
module(138, 8, 26, 10, "TD-8120MG  L", "люлка · CH10 · 6 V", fc="#444"); module(166, 8, 26, 10, "TD-8120MG  R", "люлка · CH11 · 6 V", fc="#444")
wire([(CHX["CH10"], 35), (CHX["CH10"], 18)], C["srv"], 1.6); wire([(CHX["CH11"], 35), (CHX["CH11"], 26.5), (179, 26.5), (179, 18)], C["srv"], 1.6)
label((170, 22.3), "сервата се включват в полето на модула:\nсигнал · V+ · GND на CH10 / CH11", fs=4.5, c="#444", ha="left")
# LEDs + buzzer next to CH6–9
for i, (col, nm) in enumerate([("#3c3", "LED1"), ("#ec3", "LED2"), ("#e33", "LED3")]):
    xx = CHX["CH7"] + i*4.0
    wire([(xx, 35), (xx, 29.5)], C["pwm"], 0.9); ax.add_patch(Circle((xx, 28.3), 1.1, fc=col, ec="#111", lw=0.5, zorder=6)); label((xx, 26.2), nm, fs=4.0)
wire([(CHX["CH6"], 35), (CHX["CH6"], 31), (136.8, 31), (136.8, 29.5)], C["pwm"], 0.9) if False else None
ax.add_patch(Circle((CHX["CH6"] - 1.5, 28.3), 2.0, fc="#222", ec="#000", zorder=6)); label((CHX["CH6"] - 1.5, 28.3), "BZ1", c="white", fs=4.2)
wire([(CHX["CH6"], 35), (CHX["CH6"], 30.3)], C["pwm"], 0.9)
label((148, 23.6), "LED1–3 + 330 Ω на CH7–9 · BZ1 (5 V) през Q3 BC337 + 1 k на CH6\nна свободните редове на десния BB400", fs=4.4, c="#444")

# ================= sensors I2C0
module(138, 120, 24, 10, "MLX90642-D45", "I2C0 0x33 · напред", fc="#1a6f3a"); module(166, 120, 24, 10, "BNO055", "I2C0 0x28 · IMU", fc="#1a6f3a")
wire([(126.2, yp(16)), (126.2, 118.6), (150, 118.6), (150, 120)], C["sda"], 1.3); wire([(150, 118.6), (178, 118.6), (178, 120)], C["sda"], 1.3)
wire([(125.0, yp(17)), (125.0, 117.6), (152, 117.6), (152, 120)], C["scl"], 1.3); wire([(152, 117.6), (180, 117.6), (180, 120)], C["scl"], 1.3)
label((100, 128.6), "I2C0: SDA GPIO48 (EXT2 16, зелено) · SCL GPIO47 (EXT2 17)\n→ MLX90642-D45, BNO055, PCA9685. 3V3 + GND от десните шини.\nPull-up 4.7 k към 3V3 само ако модулите нямат свои.", fs=5, c="#444", ha="left")

# ================= USB
wire([(DX + 6.7, DY - 2.4), (DX + 6.7, 19.5)], "#555", 1.4, ls=(0, (2, 1.5)))
label((DX + 6.7, 18), "USB-OTG1 → Mac: програмиране и монитор. В лодката: нищо (WiFi, T7)", fs=4.8, c="#555")

# ================= title, legend, notes
label((0.5, 146.3), "AR-Mini · v1 електрониката на breadboard · Olimex ESP32-S3-DevKit-Lipo · стендът до R2a (16.10) и R1b", fs=13, bold=True, ha="left", va="top")
label((0.5, 142.4), "Мрежите са от pcb/carrier-revB/SPEC.md (11.10). Перфоплатката (C031) е копие на това. 12 V не минава през breadboard-ите; всеки GND е LiPo −. Кръстосване без точка = не са свързани.", fs=7, ha="left", va="top", c="#333")
leg = [("v12", "12 V от бушон"), ("v5", "5 V (buck)"), ("v33", "3V3 (шини)"), ("gnd", "GND"), ("sda", "SDA"), ("scl", "SCL"), ("pwm", "PWM / ESC сигнал"), ("sig", "ADC / KILL / LEAK"), ("en", "EN / OE (kill верига)"), ("srv", "мотор / серво")]
for i, (k, t) in enumerate(leg):
    xx = 2 + (i % 5) * 12.5; yy = 5.5 - (i // 5) * 3.2
    wire([(xx, yy), (xx + 4, yy)], C[k], 2.6); label((xx + 5, yy), t, fs=5.4, ha="left")
notes = ["Ред на включване: USB само, buck OFF → всичко чете. Buck ON → 4.9–5.2 V на EXT1 пин 21.",
         "LiPo последна, ключът на KILL. При всяко качване на код или reset: KILL.",
         "KILL: полюс 1 сваля EN на двата BTS7960 → моторите спират в хардуера; Q2 вдига OE → PCA9685",
         "изходи OFF; полюс 2 казва на DevKit-а (GPIO14 = 0). ESC-тата спират от firmware-а (1500 µs).",
         "ESC сигнал: директно от GPIO1/2 (3.3 V); ако C006 покаже 5 V логика → 74AHCT125 между тях.",
         "Лист 2b „ред b / ред i на един 830“ е грешен: 25.40 = 10 стъпки → DevKit-ът е на два BB400."]
for i, t in enumerate(notes):
    label((4.5, 24.5 - i*2.5), ("• " if i in (0, 2, 4, 5) else "   ") + t, fs=5.0, ha="left", c="#222")

fig.savefig("AR-Mini_breadboard_3_v1-all.png", bbox_inches="tight", facecolor="white")
print("ok")
