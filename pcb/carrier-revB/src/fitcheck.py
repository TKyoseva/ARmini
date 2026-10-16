"""Pads-only 1:1 fit-check sheet from a .kicad_pcb (A4 landscape, 1 unit = 1 mm).

    python fitcheck.py ../AR-Mini_carrier_revB.kicad_pcb ../AR-Mini_carrier_revB_fitcheck_1to1.pdf

Why: before ordering, print this at 100 % (no "fit to page"), check the 100 mm bar with a ruler,
then push REAL header pins through the paper into every printed pad. By eye the 54.26 mm PCA9685
rows "looked fine"; the pins missed by 0.8 mm per end (FAILS 152). Pads, holes and the outline only —
no tracks, so nothing distracts from the fit.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sx import load, footprints
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Ellipse, FancyBboxPatch

src = sys.argv[1] if len(sys.argv) > 1 else "AR-Mini_carrier_revB.kicad_pcb"
out = sys.argv[2] if len(sys.argv) > 2 else "AR-Mini_carrier_revB_fitcheck_1to1.pdf"
BOARD_W, BOARD_H, R = 100.0, 80.0, 3.0          # outline: file coords x 20..120, y 20..100
OX, OY = 15.0, 15.0                              # where the board's (20, 20) lands on the sheet, mm

root = load(src)
fps = footprints(root)
W, H = 297.0, 210.0
fig = plt.figure(figsize=(W / 25.4, H / 25.4))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.set_aspect("equal"); ax.axis("off")
X = lambda x: OX + (x - 20.0); Y = lambda y: OY + (y - 20.0)

ax.add_patch(FancyBboxPatch((X(20), Y(20)), BOARD_W, BOARD_H, boxstyle=f"round,pad=0,rounding_size={R}", fill=False, lw=0.6, ec="k"))
for f in fps:
    for p in f["pads"]:
        x, y = X(p["x"]), Y(p["y"])
        if p["kind"] == "np_thru_hole" or (p["drill"] and p["drill"] >= 2.5):
            d = p["drill"]; ax.add_patch(Circle((x, y), d / 2, fill=False, lw=0.5, ec="k"))
            ax.plot([x - d / 2 - 0.6, x + d / 2 + 0.6], [y, y], lw=0.25, c="k"); ax.plot([x, x], [y - d / 2 - 0.6, y + d / 2 + 0.6], lw=0.25, c="k")
        elif p["kind"] == "thru_hole":
            if p["shape"] == "oval": ax.add_patch(Ellipse((x, y), p["sx"], p["sy"], fill=False, lw=0.35, ec="k"))
            elif p["shape"] == "rect": ax.add_patch(Rectangle((x - p["sx"] / 2, y - p["sy"] / 2), p["sx"], p["sy"], fill=False, lw=0.35, ec="k"))
            else: ax.add_patch(Circle((x, y), p["sx"] / 2, fill=False, lw=0.35, ec="k"))
            if p["drill"]: ax.add_patch(Circle((x, y), p["drill"] / 2, fill=True, fc="k", ec="none"))
        else:
            ax.add_patch(Rectangle((x - p["sx"] / 2, y - p["sy"] / 2), p["sx"], p["sy"], fill=False, lw=0.25, ec="0.5"))
    if not f["ref"].startswith("H"):
        ax.text(X(f["x"]) + 1.2, Y(f["y"]) - 1.2, f["ref"], fontsize=4, color="0.35", ha="left", va="bottom")

# module outlines and the numbers that must be true (SPEC §4, corrected 15.10)
ax.add_patch(Rectangle((X(71.5), Y(20.5)), 25.92, 58.98, fill=False, lw=0.3, ec="0.4", ls="--"))
ax.text(X(95.5), Y(50.0), "U2 PCA9685 · rows 55.88 · holes 55.88 x 19.05 · Ø3.0 · pin 1 = GND at left", fontsize=4.5, ha="center", va="center", color="0.3", rotation=90)
ax.text(X(108.66), Y(44.0), "U3 BNO055\nholes 21.59 x 15.24 · Ø3.0", fontsize=5, ha="center", va="center", color="0.3")
ax.text(X(56.7), Y(45.0), "U1 DevKit-Lipo · rows 25.40 · pin 1 at the antenna end", fontsize=5, ha="center", va="center", color="0.3", rotation=90)

# scale bar, instructions, reference square
ax.plot([X(20), X(120)], [Y(108), Y(108)], lw=0.6, c="k")
for t in range(0, 101, 10): ax.plot([X(20 + t)] * 2, [Y(107.2), Y(108.8)], lw=0.4, c="k")
ax.text(X(70), Y(111.5), "100 mm — measure with the ruler: must be 100.0 (print at 100 %, no \"fit to page\")", fontsize=6, ha="center")
ax.text(X(20), Y(118), f"{os.path.basename(src)} — FIT CHECK. FRONT view: this text reads normally; modules plug in from this side.", fontsize=6.5, ha="left")
ax.text(X(20), Y(123), "Check with real pins through the paper: DevKit 2 x 22, PCA9685 both 1 x 6 rows + 4 holes, BNO055 1 x 6 + 1 x 4 + 4 holes. Pads only, no tracks.", fontsize=6.5, ha="left")
ax.text(X(20), Y(128), "Reference 50 x 50 mm square below.", fontsize=6.5, ha="left")
ax.add_patch(Rectangle((X(20), Y(133)), 50, 50, fill=False, lw=0.5, ec="k"))
ax.text(X(45), Y(158), "50 x 50", fontsize=7, ha="center", va="center")
fig.savefig(out, format="pdf")
print("wrote", out)
