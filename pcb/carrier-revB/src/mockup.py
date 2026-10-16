import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

W, H = 100.0, 80.0
fig, ax = plt.subplots(figsize=(13, 10.6), dpi=150)
ax.set_xlim(-6, 106); ax.set_ylim(-10, 90); ax.set_aspect("equal"); ax.axis("off")

BOARD = "#1f6f4a"; EDGE = "#0d3b27"; MOD = "#e8e8e8"; CONN = "#f2d25c"; TXT = "#111"
# board
ax.add_patch(FancyBboxPatch((0, 0), W, H, boxstyle="round,pad=0,rounding_size=3", fc=BOARD, ec=EDGE, lw=2))
for (x, y) in [(3.5, 3.5), (96.5, 3.5), (3.5, 76.5), (96.5, 76.5)]:
    ax.add_patch(Circle((x, y), 1.6, fc="white", ec=EDGE, lw=1))

def box(x, y, w, h, label, sub=None, fc=MOD, ec="#333", lw=1.2, fs=7.5, rot=0, ls="-"):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, ls=ls))
    if rot == 0:
        ax.text(x + w/2, y + h/2 + (1.6 if sub else 0), label, ha="center", va="center", fontsize=fs, color=TXT, weight="bold")
        if sub:
            ax.text(x + w/2, y + h/2 - 2.2, sub, ha="center", va="center", fontsize=fs-1.5, color="#333")
    else:
        ax.text(x + w/2 + (1.5 if sub else 0), y + h/2, label, ha="center", va="center", fontsize=fs, color=TXT, rotation=90, weight="bold")
        if sub:
            ax.text(x + w/2 - 1.8, y + h/2, sub, ha="center", va="center", fontsize=fs-1.5, color="#333", rotation=90)

def jst(x, y, w, h, label, sub=None, rot=0):
    box(x, y, w, h, label, sub, fc=CONN, ec="#6b5a00", fs=6.5, rot=rot)
    # pin 1 square
    if rot == 0:
        ax.add_patch(Rectangle((x + 0.8, y + h/2 - 0.8), 1.6, 1.6, fc="#333"))
    else:
        ax.add_patch(Rectangle((x + w/2 - 0.8, y + 0.8), 1.6, 1.6, fc="#333"))

# --- U1 DevKit-Lipo: PCB 28.09 x 55.88, header rows 25.40 apart, 22 pins at 2.54, pin 1 at the antenna end (top)
x0, y0 = 9.95, 17.0
ax.add_patch(Rectangle((x0, y0), 28.09, 55.88, fc="#d44", ec="#600", lw=1.2))
ax.text(x0 + 14.0 + 1.5, y0 + 18, "U1  ESP32-S3-DevKit-Lipo", ha="center", va="center", fontsize=8, weight="bold", rotation=90)
ax.text(x0 + 14.0 - 2.0, y0 + 18, "55.88 × 28.09 · 2 × 1×22 female headers", ha="center", va="center", fontsize=6.3, color="#300", rotation=90)
for xr in (x0 + 1.35, x0 + 28.09 - 1.35):
    for i in range(22):
        ax.add_patch(Circle((xr, y0 + 55.88 - 1.27 - i*2.54), 0.55, fc="white", ec="#333", lw=0.5))
ax.annotate("", xy=(x0 + 1.35, 11.6), xytext=(x0 + 28.09 - 1.35, 11.6), arrowprops=dict(arrowstyle="<->", lw=1, color="white"))
ax.text(x0 + 14, 12.4, "rows 25.40 (measured C030)", ha="center", fontsize=6.5, color="white")
ax.text(x0 - 1.0, y0 + 55.88 - 1.27, "EXT1·1 = 3V3", ha="right", va="center", fontsize=5.5, color="white")
ax.text(x0 + 28.09 + 1.0, y0 + 55.88 - 1.27, "EXT2·1 GND", ha="left", va="center", fontsize=5.5, color="white")
ax.text(x0 + 2.6, y0 + 1.3, "21 +5V · 22 GND", ha="left", va="center", fontsize=4.8, color="white")
ax.text(x0 + 28.09 - 2.6, y0 + 1.3, "22 GND", ha="right", va="center", fontsize=4.8, color="white")
# WROOM module + antenna
ax.add_patch(Rectangle((x0 + 5, y0 + 38), 18, 18, fc="#999", ec="#333", lw=0.8))
ax.text(x0 + 14, y0 + 47, "WROOM-1", ha="center", va="center", fontsize=6.5)
ax.add_patch(Rectangle((x0 + 5, y0 + 55.88), 18, 5.5, fc="#bbb", ec="#333", lw=0.8, hatch="//"))
ax.text(x0 + 14, y0 + 55.88 + 2.7, "antenna", ha="center", va="center", fontsize=6)
# USB-C ports at the bottom end
for xx in (x0 + 5, x0 + 16):
    ax.add_patch(Rectangle((xx, y0 - 2.2), 7, 2.4, fc="#444", ec="#111"))
ax.text(x0 + 8.5, y0 - 1.0, "OTG1", ha="center", va="center", fontsize=4.8, color="white")
ax.text(x0 + 19.5, y0 - 1.0, "UART1", ha="center", va="center", fontsize=4.8, color="white")
# keep-out and cable room
ax.add_patch(Rectangle((5, 72.9), 38, 7.1, fc="none", ec="#ff6b6b", lw=1.5, hatch="xx"))
ax.text(24, 81.3, "ANTENNA KEEP-OUT · no copper, no pour, nothing tall", ha="center", va="bottom", fontsize=6.5, color="#c33", weight="bold")
ax.add_patch(Rectangle((8, 1.5), 32, 8.0, fc="none", ec="#7fd0ff", lw=1.2, ls="--"))
ax.text(24, 5.5, "USB-C cable room · 15 mm free, no tall parts", ha="center", va="center", fontsize=6.5, color="#bfe6ff")

# --- U2 PCA9685 module (vertical), servo field free
box(45, 10, 25.4, 62, "U2  PCA9685 module", "I2C0 · 3V3 · OE ← Q2 · V+ from the 6 V servo buck (own terminal) · cradle servos on CH10/CH11", fc=MOD, fs=7.5, rot=90)
ax.text(57.7, 73.2, "MEASURE: length, 6-pin row distance", ha="center", fontsize=5.5, color="white")
for i in range(16):
    ax.add_patch(Rectangle((46.5, 13 + i*3.5), 2.2, 2.2, fc="#555", ec="none"))
# --- U3 BNO055
box(73, 50, 24, 16, "U3  BNO055", "1×6 or 1×8 — MEASURE", fs=7)
# --- U4 buck
box(73, 27, 19, 20, "U4  buck 12→5 V", "MZHOU 3 A, set 5.0 V", fs=7)
# --- U6 level shifter + jumpers
box(44, 1.2, 19, 7.6, "U6  74AHCT125", "DIP socket · DNP", fc="#f7f7f7", fs=6, ls="--")
box(64, 1.2, 3.6, 3.2, "", fc="#ddd", ec="#333", fs=5); ax.text(68.2, 2.8, "JP1", ha="left", va="center", fontsize=5.2, color="white")
box(64, 5.0, 3.6, 3.2, "", fc="#ddd", ec="#333", fs=5); ax.text(68.2, 6.6, "JP2", ha="left", va="center", fontsize=5.2, color="white")
# --- power entry
box(73, 11.5, 16, 12.5, "Q1 IRF4905\nD1 SMBJ15A\nC1 470 µF", fs=6)
jst(90, 6, 9.5, 13, "J1 12V_IN", "screw 5.08", rot=90)

# --- connectors bottom edge
jst(70.5, 0.2, 11.5, 5.5, "J4 BTS_L", "RPWM·LPWM·EN·GND·IS")
jst(83, 0.2, 11.5, 5.5, "J5 BTS_R", "RPWM·LPWM·EN·GND·IS")
# top edge I2C
jst(44, 74.2, 10.5, 5.5, "J6 THERM_FWD", "3V3 GND SDA0 SCL0")
jst(56, 74.2, 10.5, 5.5, "J7 THERM_POD", "3V3 GND SDA1 SCL1")
jst(68, 74.2, 10.5, 5.5, "J11 IMU_EXT", "I2C-0 spare")
# right edge
jst(94.5, 20, 5.5, 17, "J10 ROCKER", "+5V·EN·GND·KILL·GND", rot=90)
jst(94.5, 38.5, 5.5, 9, "J9", "LEAK", rot=90)
# left edge
jst(0.8, 18, 6, 11, "J2", "ESC_L", rot=90)
jst(0.8, 30.5, 6, 11, "J3", "ESC_R", rot=90)
jst(0.8, 53, 6, 15, "J8", "SERVO_BUS", rot=90)
box(1.2, 42, 3.2, 9.5, "JP3 PI_UART", fc="#ccc", fs=4.6, rot=90)
# LEDs, buzzer, inverter
for i, c in enumerate(["#3c3", "#ec3", "#e33"]):
    ax.add_patch(Circle((75 + i*3.2, 70.5), 1.3, fc=c, ec="#111", lw=0.6))
ax.text(78.2, 67.8, "LED1–3 (CH7–9)", ha="center", fontsize=5.5, color="white")
ax.add_patch(Circle((88.5, 71.5), 5.0, fc="#222", ec="#000"))
ax.text(88.5, 71.5, "BZ1", ha="center", va="center", fontsize=6, color="white")
box(73, 6.5, 16, 4.5, "Q2 · Q3  (EN→OE, buzzer)", fc=MOD, fs=5.2)
# pull-downs next to the EXT2 pins 6-9
ax.add_patch(Rectangle((39.5, 42), 4.2, 10.5, fc="#ddd", ec="#333", lw=0.8))
ax.text(41.6, 47.25, "R12–15\n10 k", ha="center", va="center", fontsize=5.2, rotation=90)
ax.text(41.6, 53.5, "GPIO39–42\n→ GND", fontsize=5, color="white", ha="center", va="bottom")
# test points
for (x, y, n) in [(91.5, 20.5, "TP1 12V"), (71.5, 25.5, "TP2 5V"), (71.5, 48.5, "TP3 3V3"), (43.3, 69.5, "TP4/5"), (97.5, 47.5, "TP6 GND"), (92.3, 36.0, "TP7 KILL"), (92.3, 25.0, "TP8 EN")]:
    ax.add_patch(Circle((x, y), 0.8, fc="white", ec="#111", lw=0.6))
    ax.text(x, y - 2.0, n, ha="center", fontsize=4.6, color="white")

# title and notes
ax.text(0, 86.5, "AR-Mini carrier rev B · 100 × 80 mm · 2 layers · DevKit-Lipo on headers", fontsize=12, weight="bold", color="#111")
ax.text(0, 83.0, "Top view, parts side. Placement from pcb/carrier-revB/SPEC.md (11.10). 12 V for thrusters, servos and the BTS7960 power stage is NOT on this board.", fontsize=7.5, color="#333")
ax.text(0, -3.0, "To measure before the footprints are fixed: U2 PCA9685 (length, row distance), U3 BNO055 (pin count), U4 buck (pads). "
                  "Jumpers JP1/JP2: ESC direct (default) or through U6. Holes Ø3.2 on a 93 × 73 grid.", fontsize=7, color="#333")
ax.text(0, -6.3, "Silkscreen: 'AR-Mini carrier rev B · 2026-10'. Mockup, not a layout: no tracks drawn.", fontsize=7, color="#333")
# scale bar
ax.plot([80, 100], [-8.6, -8.6], color="#111", lw=2); ax.text(90, -7.6, "20 mm", ha="center", va="bottom", fontsize=7)

fig.savefig("AR-Mini_carrier_revB_mockup.png", bbox_inches="tight", facecolor="white")
print("ok")
