#!/usr/bin/env python3
"""AR-Mini carrier rev B — KiCad board from SPEC.md (C032, measured update 13.10).

Same method as the rev 0 breakout: one script writes the .kicad_pcb.
No schematic (rev 0 had none). Open in KiCad 9 or 10, press B to fill the
GND zone. Checks on this machine use KiCad 10.0.6 (kicad-cli).

  python3 pcb/carrier-revB/gen.py

Numbers are from pcb/carrier-revB/SPEC.md unless marked VERIFY.
U3 pin/hole positions: Adafruit "Adafruit BNO055.brd" (github adafruit/
Adafruit-BNO055-Breakout-PCB), the same numbers the caliper confirmed 13.10.
"""
import array
import math
import os
import uuid
from collections import defaultdict, deque

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AR-Mini_carrier_revB.kicad_pcb")
PRO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AR-Mini_carrier_revB.kicad_pro")

# SOURCE: SPEC.md §1. Y in the file grows downward (same as rev 0).
BW, BH = 100.0, 80.0
# Board origin on the A4 sheet. Everything below works in board coordinates (0,0 = top-left
# corner of the board); the offset is added only when the file is written, so the 1:1 PDF
# print (SPEC §9.2) is not clipped by the printer margin.
OX, OY = 20.0, 20.0
CORNER_R = 3.0
CLEAR = 0.20          # SPEC §9: clearance 0.2 mm
HOLE_CLEAR = 0.25     # .kicad_pro min_hole_clearance / min_hole_to_hole
VIA_D, VIA_DRILL = 0.6, 0.3
SIG_W, P5_W = 0.30, 0.80   # SPEC §1: signal 0.3, 5 V 0.8
P3_W = 0.50           # 3V3 is power; SPEC names only the 5 V width. 0.50 sits between signal and 5 V.

# DevKit — SOURCE: SPEC §2, measured C030. Pin 1 at the antenna end (small y).
# Inset of pin 1 from the PCB edge is (55.88 − 21×2.54)/2 = 1.27 if the row is centred.
EXT1_X, EXT2_X = 24.00, 49.40          # 25.40 apart
PIN1_Y, HPITCH, NPIN = 1.27, 2.54, 22
DEV_L, DEV_W = 55.88, 28.09
DEV_CX = (EXT1_X + EXT2_X) / 2
DEV_X0, DEV_X1 = DEV_CX - DEV_W / 2, DEV_CX + DEV_W / 2   # 20.655 … 50.745
DEV_Y0, DEV_Y1 = PIN1_Y - 1.27, PIN1_Y - 1.27 + DEV_L     # 0 … 55.88
CABLE_Y1 = 71.0        # SPEC §2: 15 mm free past the USB-C end

# Antenna keep-out between the headers, 10 mm from the edge the antenna hangs over.
# SOURCE: SPEC §2. Pads of pin 1 sit outside this rectangle.
KO = (26.2, 0.0, 47.2, 12.0)

# U2 PCA9685 module — SOURCE: SPEC §4, MEASURED 13.10 (C032).
# Board 58.98 × 25.92; two 1×6 rows along the short edges, 2.36 in from each end,
# row to row 54.26; 4 × Ø2.7 holes on 54.26 × 17.36 in line with the rows.
# The module lies along Y (rows along X) right of the DevKit, as in the 11.10 mockup.
U2_W, U2_L = 25.92, 58.98
U2_ROW, U2_HOLE_DX, U2_INSET = 54.26, 17.36, 2.36
U2_X0, U2_Y0 = 51.5, 0.5
U2_CX = U2_X0 + U2_W / 2                 # 64.46
U2_ROW1_Y = U2_Y0 + U2_INSET             # 2.86
U2_ROW2_Y = U2_ROW1_Y + U2_ROW           # 57.12
U2_PIN1_X = U2_CX - 2.5 * 2.54           # 58.11  VERIFY: row assumed centred across the 25.92 width
U2_HOLE_D = 2.7

# U3 Adafruit BNO055 #2472 — SOURCE: Adafruit Eagle file + caliper 13.10 (SPEC §4).
# Board 26.67 × 20.32. JP1 1×6 at 1.27 from one long edge, pins at 6.985 … 19.685 along it.
# JP2 1×4 on the other long edge (17.78 from JP1), pins at 9.525 … 17.145. Holes Ø2.5 on
# 21.59 × 15.24, 2.54 from the edges; the carrier drills Ø2.7 (user 13.10).
# Placed with the long axis along Y, JP1 toward U2.
U3_L, U3_W = 26.67, 20.32
U3_X0, U3_Y0 = 78.5, 25.0
U3_JP1_X = U3_X0 + 1.27                  # 79.77
U3_JP2_X = U3_X0 + 1.27 + 17.78          # 97.55
U3_JP1_Y1 = U3_Y0 + 6.985
U3_JP2_Y1 = U3_Y0 + 9.525
U3_HOLE_D = 2.7

MOUNT = ((3.5, 3.5), (96.5, 3.5), (3.5, 76.5), (96.5, 76.5))   # SPEC §1: 93 × 73 grid
SCREW_HEAD_R = 3.0     # M3 pan head Ø5.5–6: keep tall parts out

GRID = 0.25
EXTRA = 0.40           # past the copper edge: 0.20 clearance + 0.15 of a 0.3 mm neighbour + margin

# Escape stubs laid before routing: pins in the bottom JST row are reachable only from above
# (or along the edge), and the long nets seal both. Each (ref, pin) gets a vertical F.Cu stub
# from the pad up to STUB_Y, so every net fans out from open space above the housings.
STUB_Y = 69.0
STUBS = tuple((ref, str(pin)) for ref in ("J4", "J5") for pin in range(1, 6)) + \
    (("J2", "3"), ("J3", "3"), ("J1", "1"))


def uid():
    return str(uuid.uuid4())


# ---------------------------------------------------------------- pad geometry
# A pad is (net, x, y, hx, hy, shape, ref, padno, pth). hx/hy are half sizes.
def pad_edge_dist(px, py, pad):
    """Signed distance from a point to the pad's copper edge (negative inside)."""
    _n, x, y, hx, hy, shape = pad[:6]
    dx, dy = abs(px - x), abs(py - y)
    if shape == "rect":
        ox, oy = dx - hx, dy - hy
        if ox > 0 and oy > 0:
            return math.hypot(ox, oy)
        return max(ox, oy)
    if shape == "circle" or hx == hy:
        return math.hypot(dx, dy) - hx
    # oval = stadium
    r = min(hx, hy)
    if hx > hy:
        return math.hypot(max(dx - (hx - r), 0.0), dy) - r
    return math.hypot(dx, max(dy - (hy - r), 0.0)) - r


def pad_bound(pad):
    hx, hy, shape = pad[3], pad[4], pad[5]
    return math.hypot(hx, hy) if shape == "rect" else max(hx, hy)


def pad_boundary(pad, n=32):
    """Points on the pad's copper edge."""
    _n, x, y, hx, hy, shape = pad[:6]
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        c, s = math.cos(t), math.sin(t)
        if shape == "rect":
            m = max(abs(c) / hx, abs(s) / hy)
            pts.append((x + c / m, y + s / m))
        elif hx == hy or shape == "circle":
            pts.append((x + c * hx, y + s * hx))
        else:
            r = min(hx, hy)
            ox = math.copysign(hx - r, c) if hx > hy else 0.0
            oy = math.copysign(hy - r, s) if hy > hx else 0.0
            pts.append((x + ox + c * r, y + oy + s * r))
    return pts


class Board:
    def __init__(self):
        self.fps = []
        self.graphics = []
        self.pads = []          # see pad_edge_dist
        self.holes = []         # (x, y, r) NPTH, no copper
        self.traces = []        # (net, x0, y0, x1, y1, w, layer)
        self.vias = []
        self.smd = []           # (net, x, y) F.Cu only pads
        self.stubs = []         # (net, x, y_pad, y_top, w) escape stubs, trimmed after routing
        self.nets = {}
        self.bodies = []        # (ref, x0, y0, x1, y1, tall, zone) physical footprints

    def net_of(self, name):
        if not name:
            return None
        self.nets.setdefault(name, len(self.nets) + 1)
        return name

    def add_pad(self, net, x, y, sx, sy, shape, ref, padno, smd=False):
        net = self.net_of(net) if net else None
        self.pads.append((net, x, y, sx / 2, sy / 2, shape, ref, padno, not smd))
        if smd and net:
            self.smd.append((net, x, y))

    def add_hole(self, x, y, d):
        self.holes.append((x, y, d / 2))

    def body(self, ref, x0, y0, x1, y1, tall=True, zone=None):
        self.bodies.append((ref, min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), tall, zone))

    def fp(self, text):
        self.fps.append(text)

    def gr(self, text):
        self.graphics.append(text)


B = Board()


def prop(name, value, x, y, layer, hide=False, size=0.8):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return (
        f'\t\t(property "{name}" "{value}"\n'
        f'\t\t\t(at {x} {y} 0)\n'
        f'\t\t\t(layer "{layer}"){h}\n'
        f'\t\t\t(uuid "{uid()}")\n'
        f'\t\t\t(effects (font (size {size} {size}) (thickness 0.12)))\n'
        f'\t\t)'
    )


def pad_sexp(num, shape, x, y, sx, sy, drill, net, plated=True):
    kind = "thru_hole" if plated else "np_thru_hole"
    n = f'\n\t\t\t(net "{net}")' if net else ""
    dr = f"\n\t\t\t(drill {drill})" if drill else ""
    return (
        f'\t\t(pad "{num}" {kind} {shape}\n'
        f'\t\t\t(at {x} {y})\n'
        f'\t\t\t(size {sx} {sy}){dr}\n'
        f'\t\t\t(layers "*.Cu" "*.Mask")\n'
        f'\t\t\t(zone_connect 2){n}\n'
        f'\t\t\t(uuid "{uid()}")\n'
        f'\t\t)'
    )


def smd_pad(num, x, y, sx, sy, net):
    n = f'\n\t\t\t(net "{net}")' if net else ""
    return (
        f'\t\t(pad "{num}" smd roundrect\n'
        f'\t\t\t(at {x} {y})\n'
        f'\t\t\t(size {sx} {sy})\n'
        f'\t\t\t(layers "F.Cu" "F.Mask" "F.Paste")\n'
        f'\t\t\t(zone_connect 2)\n'
        f'\t\t\t(roundrect_rratio 0.15){n}\n'
        f'\t\t\t(uuid "{uid()}")\n'
        f'\t\t)'
    )


def fp_line(x0, y0, x1, y1, layer="F.SilkS", w=0.15):
    return (
        f'\t\t(fp_line (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f})\n'
        f'\t\t\t(stroke (width {w}) (type solid)) (layer "{layer}") (uuid "{uid()}"))'
    )


def fp_rect(x0, y0, x1, y1, layer, w=0.05):
    return (
        f'\t\t(fp_rect (start {x0:.3f} {y0:.3f}) (end {x1:.3f} {y1:.3f})\n'
        f'\t\t\t(stroke (width {w}) (type default)) (fill no) (layer "{layer}") (uuid "{uid()}"))'
    )


def footprint(name, ref, value, atx, aty, body, dnp=False, ref_at=(0, -2.2), smd=False):
    attr = ("smd" if smd else "through_hole") + (" dnp" if dnp else "")
    return (
        f'\t(footprint "AR-Mini:{name}"\n'
        f'\t\t(layer "F.Cu")\n'
        f'\t\t(uuid "{uid()}")\n'
        f'\t\t(at {atx + OX:.3f} {aty + OY:.3f})\n'
        f'{prop("Reference", ref, ref_at[0], ref_at[1], "F.SilkS", size=1.0)}\n'
        f'{prop("Value", value, 0, 0, "F.Fab", hide=True)}\n'
        f'{prop("Datasheet", "", 0, 0, "F.Fab", hide=True, size=1.0)}\n'
        f'{prop("Description", "", 0, 0, "F.Fab", hide=True, size=1.0)}\n'
        + (f'{prop("dnp", "yes", 0, 0, "F.Fab", hide=True)}\n' if dnp else "")
        + f'\t\t(attr {attr})\n'
        f'\t\t(duplicate_pad_numbers_are_jumpers no)\n'
        f'{body}\n'
        f'\t\t(embedded_fonts no)\n'
        f'\t)'
    )


def header(ref, value, x, y, n, pitch, nets, dx=0, dy=1, drill=1.0, pad=1.7, dnp=False,
           tick="top", body=None, tall=True, zone=None, holes=(), pad_sizes=None, ref_at=None,
           extra=""):
    """Pin 1 at (x, y). dx,dy is the step to the next pin (file axes, y down).
    body = courtyard rectangle relative to pin 1 (x0, y0, x1, y1); None = header strip.
    holes = NPTH (px, py, d) relative to pin 1, part of this footprint.
    pad_sizes = {pin_index: (sx, sy)} overrides (shape stays rect for pin 1, oval otherwise)."""
    lines = []
    for i in range(n):
        px, py = i * pitch * dx, i * pitch * dy
        net = nets[i] if i < len(nets) else None
        sx, sy = (pad_sizes or {}).get(i, (pad, pad))
        shape = "rect" if i == 0 else "oval"
        B.add_pad(net, x + px, y + py, sx, sy, shape, ref, str(i + 1))
        lines.append(pad_sexp(str(i + 1), shape, px, py, sx, sy, drill, net))
    for px, py, d in holes:
        B.add_hole(x + px, y + py, d)
        lines.append(pad_sexp("", "circle", px, py, d, d, d, None, plated=False))
    # pin-1 silk tick
    if tick == "top":
        lines.append(fp_line(-0.9, -1.3, 0.9, -1.3))
    elif tick == "left":
        lines.append(fp_line(-1.3, -0.4, -1.3, 0.9))
    elif tick == "right":
        lines.append(fp_line(1.3, -0.4, 1.3, 0.9))
    ex = (n - 1) * pitch
    if body is None:
        body = (-1.27, -1.27, ex * dx + 1.27, ex * dy + 1.27)
    lines.append(fp_rect(*body, "F.CrtYd"))
    B.body(ref, x + body[0], y + body[1], x + body[2], y + body[3], tall, zone)
    if extra:
        lines.append(extra)
    if ref_at is None:
        ref_at = (ex * dx / 2, -2.2) if dy == 0 else (0, -2.2)
    B.fp(footprint(ref, ref, value, x, y, "\n".join(lines), dnp=dnp, ref_at=ref_at))


def jst_body(n, dx, dy):
    """JST-XH B?B-XH-A top entry: 2.5 × (n−1) + 4.9 long, 5.75 deep, 7 mm tall. Drawn symmetric."""
    L = 2.5 * (n - 1)
    if dx:
        return (-2.45, -2.875, L + 2.45, 2.875)
    return (-2.875, -2.45, 2.875, L + 2.45)


def jst(ref, value, x, y, n, nets, dx=0, dy=1, ref_at=None):
    if ref_at is None:
        ref_at = (2.5 * (n - 1) / 2, -3.9) if dx else (0, -3.9)
    header(ref, value, x, y, n, 2.50, nets, dx, dy, body=jst_body(n, dx, dy), ref_at=ref_at)


def resistor(ref, value, x, y, a, b, dnp=False):
    """Axial 0207, leads bent to 5.08, lying flat (2.5 mm tall) — allowed under the modules."""
    header(ref, value, x, y, 2, 5.08, [a, b], dx=1, dy=0, drill=0.8, pad=1.5, dnp=dnp,
           body=(-1.1, -1.3, 6.18, 1.3), tall=False)


def cap(ref, value, x, y, a, b, pitch=5.08):
    header(ref, value, x, y, 2, pitch, [a, b], dx=1, dy=0, drill=0.8, pad=1.5,
           body=(-1.1, -1.4, pitch + 1.1, 1.4))


def to92(ref, value, x, y, nets):
    """TO-92 in line, 2.54 pitch along +x. S8050 order E-B-C with the flat face toward
    the viewer, legs down (SPEC §7). Body 4.8 × 4.2 centred on the middle pin."""
    header(ref, value, x, y, 3, 2.54, nets, dx=1, dy=0, drill=0.8, pad=1.5,
           body=(2.54 - 2.5, -2.2, 2.54 + 2.5, 2.2), ref_at=(0.3, 3.0))
    B.gr(silk_text("E B C", x + 5.2, y + 3.0, 0.8))


def led(ref, x, y, net_a):
    """5 mm LED, anode pin 1 (square), cathode GND. Pins along +y, flange Ø5.8."""
    header(ref, "LED", x, y, 2, 2.54, [net_a, "GND"], dx=0, dy=1, drill=0.9, pad=1.6,
           body=(-2.9, 1.27 - 2.9, 2.9, 1.27 + 2.9), ref_at=(-4.6, 0.0))


def silk_text(text, x, y, size=0.8, ang=0, layer="F.SilkS"):
    return (
        f'\t(gr_text "{text}"\n'
        f'\t\t(at {x + OX:.3f} {y + OY:.3f} {ang})\n'
        f'\t\t(layer "{layer}")\n'
        f'\t\t(uuid "{uid()}")\n'
        f'\t\t(effects (font (size {size} {size}) (thickness 0.12)))\n'
        f'\t)'
    )


def fab_text(text, x, y, size=0.8):
    return silk_text(text, x, y, size, 0, "F.Fab")


def rect(x0, y0, x1, y1, layer, w=0.15):
    return (
        f'\t(gr_rect (start {x0 + OX:.3f} {y0 + OY:.3f}) (end {x1 + OX:.3f} {y1 + OY:.3f})\n'
        f'\t\t(stroke (width {w}) (type default)) (fill no) (layer "{layer}")\n'
        f'\t\t(uuid "{uid()}"))'
    )


def gr_line(x0, y0, x1, y1, layer="F.SilkS", w=0.15):
    return (
        f'\t(gr_line (start {x0 + OX:.3f} {y0 + OY:.3f}) (end {x1 + OX:.3f} {y1 + OY:.3f})\n'
        f'\t\t(stroke (width {w}) (type default)) (layer "{layer}") (uuid "{uid()}"))'
    )


# ---------------------------------------------------------------- placements
def ext_nets():
    """SPEC §3. Pin index 0 = pin 1 at the antenna end."""
    e1 = [None] * 22
    e2 = [None] * 22
    e1[0] = e1[1] = "+3V3"
    e1[3] = "VBAT_S"
    e1[6] = "LEAK"
    e1[7] = "PI_TX"
    e1[8] = "PI_RX"
    e1[9] = "SRV_TX"
    e1[10] = "SRV_RX"
    e1[11] = "SDA1"
    e1[14] = "SCL1"
    e1[15] = "BTS_IS_R"
    e1[16] = "BTS_IS_L"
    e1[19] = "KILL"
    e1[20] = "+5V"          # SPEC §2/§3 [13.10]: +5V OUT from the DevKit (buck on its OTG USB-C)
    e1[21] = "GND"
    e2[0] = e2[21] = "GND"
    e2[3] = "ESC_L"          # GPIO1, jumper A bridged to J2
    e2[4] = "ESC_R"
    e2[5] = "BTS_R_LPWM"     # GPIO42, EXT2 pin 6
    e2[6] = "BTS_R_RPWM"     # GPIO41
    e2[7] = "BTS_L_LPWM"     # GPIO40
    e2[8] = "BTS_L_RPWM"     # GPIO39
    e2[15] = "SDA0"
    e2[16] = "SCL0"
    return e1, e2


def place_parts():
    e1, e2 = ext_nets()
    dev_body = (-1.27, -1.27, 1.27, 21 * HPITCH + 1.27)
    header("U1A", "DevKit_EXT1", EXT1_X, PIN1_Y, 22, HPITCH, e1, tick="right", body=dev_body, zone="U1")
    header("U1B", "DevKit_EXT2", EXT2_X, PIN1_Y, 22, HPITCH, e2, tick="left", body=dev_body, zone="U1")

    # ---- U2 PCA9685: two 1×6 rows along X + 4 × Ø2.7, V+ (pin 6) not connected (SPEC §4).
    # Pin order from the V+ terminal edge: GND, OE, SCL, SDA, VCC, V+. Pin 1 at small x.
    # Pins 1 and 6 are 1.4 × 2.2 so the Ø2.7 hole 2.33 mm away keeps 0.25 mm hole clearance.
    u2_nets = ["GND", "OE", "SCL0", "SDA0", "+3V3", None]
    u2_sizes = {0: (1.4, 2.2), 5: (1.4, 2.2)}
    u2_holes = ((-U2_HOLE_DX / 2 + 2.5 * 2.54, 0, U2_HOLE_D), (U2_HOLE_DX / 2 + 2.5 * 2.54, 0, U2_HOLE_D))
    for ref, yy, nets, ry in (("U2A", U2_ROW1_Y, u2_nets, 2.3), ("U2B", U2_ROW2_Y, [None] * 6, -2.3)):
        header(ref, "PCA9685_row", U2_PIN1_X, yy, 6, 2.54, nets, dx=1, dy=0, pad_sizes=u2_sizes,
               tick="top", holes=u2_holes, zone="U2", ref_at=(16.0, ry))
    B.gr(rect(U2_X0, U2_Y0, U2_X0 + U2_W, U2_Y0 + U2_L, "F.SilkS", 0.12))
    B.gr(silk_text("U2 PCA9685 · V+ terminal side <-", U2_CX, 8.5, 0.8))
    B.gr(silk_text("GND OE SCL SDA VCC V+", U2_CX, U2_ROW1_Y + 2.4, 0.8))
    B.gr(silk_text("GND OE SCL SDA VCC V+", U2_CX, U2_ROW2_Y - 2.4, 0.8))
    B.gr(silk_text("U2B mechanical only", U2_CX, 60.6, 0.8))
    B.gr(fab_text("VERIFY U2: pin row centred across 25.92 (1:1 print, SPEC §9.2)", U2_CX, 12.0, 0.8))
    B.gr(fab_text("U2 pads 1/6 1.4 x 2.2, ring 0.2 (hole 2.33 mm away)", U2_CX, 14.0, 0.8))

    # ---- U3 BNO055: JP1 1×6 connected, JP2 1×4 mechanical, 4 × Ø2.7.
    # JP1: Vin=+3V3 only (SPEC §4), 3Vo NC, GND, SDA0, SCL0, RST NC.
    u3_holes = tuple((U3_X0 + hx - U3_JP1_X, U3_Y0 + hy - U3_JP1_Y1, U3_HOLE_D)
                     for hx in (2.54, 17.78) for hy in (2.54, 24.13))
    jp2 = "\n".join(
        pad_sexp(f"B{i + 1}", "oval", U3_JP2_X - U3_JP1_X, U3_JP2_Y1 + i * 2.54 - U3_JP1_Y1, 1.7, 1.7, 1.0, None)
        for i in range(4))
    for i in range(4):
        B.add_pad(None, U3_JP2_X, U3_JP2_Y1 + i * 2.54, 1.7, 1.7, "oval", "U3", f"B{i + 1}")
    jp2 += "\n" + fp_rect(U3_JP2_X - U3_JP1_X - 1.27, U3_JP2_Y1 - U3_JP1_Y1 - 1.27,
                          U3_JP2_X - U3_JP1_X + 1.27, U3_JP2_Y1 - U3_JP1_Y1 + 3 * 2.54 + 1.27, "F.CrtYd")
    B.body("U3", U3_JP2_X - 1.27, U3_JP2_Y1 - 1.27, U3_JP2_X + 1.27, U3_JP2_Y1 + 3 * 2.54 + 1.27, zone="U3")
    header("U3", "BNO055", U3_JP1_X, U3_JP1_Y1, 6, 2.54, ["+3V3", None, "GND", "SDA0", "SCL0", None],
           tick="top", holes=u3_holes, zone="U3", extra=jp2, ref_at=(8.9, 6.4))
    B.gr(rect(U3_X0, U3_Y0, U3_X0 + U3_W, U3_Y0 + U3_L, "F.SilkS", 0.12))
    B.gr(silk_text("Vin 3vo GND SDA SCL RST", U3_JP1_X + 2.0, U3_Y0 + U3_L / 2, 0.8, 90))
    B.gr(silk_text("PS0 PS1 INT ADR (NC)", U3_JP2_X - 2.0, U3_Y0 + U3_L / 2, 0.8, 90))
    B.gr(silk_text("BOW", U3_X0 + U3_W / 2, U3_Y0 - 1.0, 0.8))
    ax = U3_X0 + U3_W / 2 - 3.0
    B.gr(gr_line(ax, U3_Y0 - 0.4, ax, U3_Y0 - 1.8))
    B.gr(gr_line(ax - 0.6, U3_Y0 - 1.2, ax, U3_Y0 - 1.8))
    B.gr(gr_line(ax + 0.6, U3_Y0 - 1.2, ax, U3_Y0 - 1.8))
    B.gr(fab_text("VERIFY BOW: arrow points to the antenna edge; SPEC §4 gives no direction", 88.6, 30.0, 0.8))
    B.gr(fab_text("U3 holes/pins: Adafruit BNO055.brd", 88.6, 32.0, 0.8))

    # ---- Left edge, next to EXT1. SOURCE: SPEC §5.
    jst("J6", "THERM_FWD", 9.5, 4.5, 4, ["+3V3", "GND", "SDA0", "SCL0"], dx=1, dy=0, ref_at=(3.75, 3.9))
    header("JP3", "PI_UART", 9.0, 12.5, 4, 2.54, ["GND", "PI_TX", "PI_RX", "+5V"])
    jst("J8", "SERVO_BUS", 9.0, 25.5, 4, ["SRV_TX", "SRV_RX", "GND", None])
    jst("J7", "THERM_POD", 9.0, 38.5, 4, ["+3V3", "GND", "SDA1", "SCL1"])
    jst("J9", "LEAK", 9.0, 51.5, 2, ["LEAK_P", "GND"])

    # ---- Right edge, top band (above U3). SOURCE: SPEC §5, §6.
    jst("J11", "IMU_EXT", 80.5, 6.5, 4, ["+3V3", "GND", "SDA0", "SCL0"], dx=1, dy=0)
    jst("J10", "ROCKER", 95.5, 10.5, 3, ["+5V", "EN", "GND"])          # SPDT: 1 RUN +5V, 2 common EN, 3 KILL GND
    # JP4 brings PCA9685 CH6–CH9 onto the carrier (the servo field stays on the module).
    # SPEC §7: buzzer from CH6, LEDs from CH7–CH9. Not a module footprint — a wire header.
    header("JP4", "CH6-9", 79.0, 17.5, 4, 2.54, ["CH6", "CH7", "CH8", "CH9"], dx=1, dy=0)
    to92("Q2", "S8050", 91.0, 21.0, ["GND", "Q2B", "OE"])              # OE inverter (SPEC §6)

    # ---- Right edge, bottom band (below U3).
    to92("Q3", "S8050", 80.0, 54.5, ["GND", "Q3B", "BZ_N"])            # buzzer driver (SPEC §7)
    header("BZ1", "BUZZER", 81.2, 63.5, 2, 7.6, ["+5V", "BZ_N"], dx=1, dy=0, drill=0.9, pad=1.7,
           body=(3.8 - 6.0, -6.0, 3.8 + 6.0, 6.0), ref_at=(3.8, -4.0))
    for i, (ref, net, yy) in enumerate((("LED1", "LED1_A", 53.5), ("LED2", "LED2_A", 59.5), ("LED3", "LED3_A", 65.5))):
        led(ref, 96.0, yy, net)
    for lbl, yy in (("G", 56.3), ("Y", 62.3), ("R", 68.3)):
        B.gr(silk_text(lbl, 92.3, yy, 0.8))

    # ---- U6 74AHCT125 DIP-14 in the left strip below J9, long axis along y (the bottom strip
    # is one row of JST-XH). SOURCE: TI pinout. DNP. Rows 7.62, pitch 2.54. Pin 1 top-left,
    # pins 1–7 down the left row, 8–14 up the right row.
    dip_nets = [
        "GND", "ESC_L", "ESC_L_5V", "GND", "ESC_R", "ESC_R_5V", "GND",   # 1..7
        None, "GND", "+5V", None, "GND", "+5V", "+5V",                     # 8..14
    ]
    dip_lines = []
    dip_x, dip_y = 10.0, 58.5
    for i in range(14):
        if i < 7:
            px, py = 0.0, i * 2.54
        else:
            px, py = 7.62, (13 - i) * 2.54
        net = dip_nets[i]
        B.add_pad(net, dip_x + px, dip_y + py, 1.6, 1.6, "rect" if i == 0 else "oval", "U6", str(i + 1))
        dip_lines.append(pad_sexp(str(i + 1), "rect" if i == 0 else "oval", px, py, 1.6, 1.6, 0.8, net))
    dip_lines.append(fp_line(-1.1, -0.6, -1.1, 0.6))
    dip_lines.append(fp_rect(-1.1, -1.3, 7.62 + 1.1, 6 * 2.54 + 1.3, "F.CrtYd"))
    B.body("U6", dip_x - 1.1, dip_y - 1.3, dip_x + 7.62 + 1.1, dip_y + 6 * 2.54 + 1.3)
    B.fp(footprint("U6", "U6", "74AHCT125", dip_x, dip_y, "\n".join(dip_lines), dnp=True, ref_at=(3.81, -2.6)))
    B.gr(silk_text("DNP", 13.8, 66.1, 0.8))

    # JP1 / JP2 solder jumpers. A bridged to centre = ESC direct (SPEC §8). B = U6 output.
    def jumper(ref, x, y, net_a, net_b):
        body = []
        for i, (px, net, shape) in enumerate(((0.0, net_a, "rect"), (1.8, net_a, "rect"), (3.6, net_b, "rect"))):
            B.add_pad(net, x + px, y, 1.3, 1.6, "rect", ref, "ACB"[i], smd=True)
            body.append(smd_pad("ACB"[i], px, 0.0, 1.3, 1.6, net))
        body.append(fp_rect(-0.9, -1.1, 4.5, 1.1, "F.CrtYd"))
        B.body(ref, x - 0.9, y - 1.1, x + 4.5, y + 1.1)
        B.fp(footprint(ref, ref, "SJ", x, y, "\n".join(body), ref_at=(1.8, -2.0), smd=True))
        # default bridge A–C, wider than the 0.5 mm gap so the copper joins the two pads
        B.traces.append((net_a, x, y, x + 1.8, y, 0.8, "F.Cu"))
        B.gr(silk_text("A", x - 0.2, y + 1.9, 0.8))
        B.gr(silk_text("B", x + 3.8, y + 1.9, 0.8))

    jumper("JP1", 25.5, 72.2, "ESC_L", "ESC_L_5V")
    jumper("JP2", 25.5, 77.6, "ESC_R", "ESC_R_5V")
    B.gr(silk_text("JP1/2: A = ESC direct", 27.0, 66.4, 0.8))

    JY = 75.5
    jst("J2", "ESC_L", 33.0, JY, 3, ["GND", None, "ESC_L"], dx=1, dy=0)
    jst("J3", "ESC_R", 43.0, JY, 3, ["GND", None, "ESC_R"], dx=1, dy=0)
    # [13.10] 6-pin: RPWM, LPWM, EN, VCC (+3V3 for the 74HC244 input buffer), IS, GND
    jst("J4", "BTS_L", 53.0, JY, 6, ["BTS_L_RPWM", "BTS_L_LPWM", "EN", "+3V3", "IS_L_MOD", "GND"], dx=1, dy=0)
    jst("J5", "BTS_R", 70.5, JY, 6, ["BTS_R_RPWM", "BTS_R_LPWM", "EN", "+3V3", "IS_R_MOD", "GND"], dx=1, dy=0)
    jst("J1", "VBAT_SENSE", 88.0, JY, 2, ["VBAT", "GND"], dx=1, dy=0, ref_at=(-1.0, -3.9))   # [13.10] sense only

    # ---- Axial resistors, leads bent to 5.08 (DIN0207), lying flat.
    # Left column sits between the JSTs (x=9) and the DevKit (x≈20.7); the resistors may
    # run under the DevKit edge (2.5 mm tall under an 8.5 mm header).
    left = [
        ("R5", "4k7", "SDA1", "+3V3"),
        ("R6", "4k7", "SCL1", "+3V3"),
        ("R20", "10k", "LEAK", "+3V3"),
        ("R21", "4k7", "LEAK_P", "LEAK"),
        ("R22", "10k", "EN", "KILL"),        # [13.10] KILL reads the EN node: 10 k series …
        ("R25", "20k", "KILL", "GND"),       # … + 20 k to GND (4.6 V → 3.1 V RUN)
        ("R23", "10k", "EN", "GND"),         # default off
    ]
    for i, (ref, val, a, b) in enumerate(left):
        resistor(ref, val, 15.0, 12.5 + i * 3.6, a, b)
    cap("C3", "100nF", 15.0, 40.0, "+3V3", "GND")
    cap("C2", "100nF", 15.0, 44.0, "+5V", "GND")       # next to EXT1 pin 21/22 (+5V out, GND)

    # Column A under U2, between EXT2 (x≈50.7) and the U2 pins (x≥57.4). x=54.5 leaves ~3.5 mm
    # for the PWM / ESC / I2C escapes. Only resistors here (SPEC §4: nothing tall under U2).
    col_a = [
        ("R3", "4k7", "SDA0", "+3V3", False),
        ("R4", "4k7", "SCL0", "+3V3", False),
        ("R12", "10k", "BTS_L_RPWM", "GND", False),
        ("R13", "10k", "BTS_L_LPWM", "GND", False),
        ("R14", "10k", "BTS_R_RPWM", "GND", False),
        ("R15", "10k", "BTS_R_LPWM", "GND", False),
        ("R16", "10k", "IS_R_MOD", "BTS_IS_R", True),
        ("R17", "10k", "BTS_IS_R", "GND", True),
        ("R18", "10k", "IS_L_MOD", "BTS_IS_L", True),
        ("R19", "10k", "BTS_IS_L", "GND", True),
        ("R1", "100k", "VBAT", "VBAT_S", False),      # [13.10] from J1 VBAT_SENSE
        ("R2", "33k", "VBAT_S", "GND", False),
    ]
    for i, (ref, val, a, b, dnp) in enumerate(col_a):
        resistor(ref, val, 54.5, 14.0 + i * 3.6, a, b, dnp=dnp)
    B.gr(silk_text("R16-19 DNP", 61.2, 41.0, 0.8, 90))
    # Column B under U2, between the two U2 rows.
    col_b = [
        ("R10", "2k2", "OE", "+3V3"),
        ("R24", "10k", "EN", "Q2B"),
        ("R11", "1k", "CH6", "Q3B"),
        ("R7", "330", "CH7", "LED1_A"),
        ("R8", "330", "CH8", "LED2_A"),
        ("R9", "330", "CH9", "LED3_A"),
    ]
    for i, (ref, val, a, b) in enumerate(col_b):
        resistor(ref, val, 63.5, 14.0 + i * 3.6, a, b)

    cap("C5", "100nF", 54.5, 63.0, "VBAT_S", "GND")

    # Test points, bare Ø1.5. SPEC §1 [13.10]: TP1 = VBAT. SMD so they stay flat.
    tps = [
        ("TP1", "VBAT", 90.5, 70.5),
        ("TP2", "+5V", 71.0, 64.0),
        ("TP3", "+3V3", 11.5, 9.8),
        ("TP4", "SDA0", 80.0, 13.0),
        ("TP5", "SCL0", 84.0, 13.0),
        ("TP6", "GND", 88.0, 13.0),
        ("TP7", "KILL", 63.0, 64.0),
        ("TP8", "EN", 67.0, 64.0),
    ]
    for ref, net, x, y in tps:
        B.add_pad(net, x, y, 1.5, 1.5, "rect", ref, "1", smd=True)
        body = smd_pad("1", 0, 0, 1.5, 1.5, net) + "\n" + fp_rect(-1.0, -1.0, 1.0, 1.0, "F.CrtYd")
        B.body(ref, x - 1.0, y - 1.0, x + 1.0, y + 1.0)
        B.fp(footprint(ref, ref, net, x, y, body, ref_at=(0, -1.6), smd=True))

    # Mounting holes Ø3.2, 3.5 mm from the edges → grid 93 × 73. SPEC §1.
    for i, (x, y) in enumerate(MOUNT, start=1):
        ref = f"H{i}"
        body = pad_sexp("", "circle", 0, 0, 3.2, 3.2, 3.2, None, plated=False)
        B.fp(footprint("M3", ref, "M3", x, y, body, ref_at=(0, -2.6)))
        B.add_hole(x, y, 3.2)
        B.body(ref, x - SCREW_HEAD_R, y - SCREW_HEAD_R, x + SCREW_HEAD_R, y + SCREW_HEAD_R)

    # Outline, silk, fab notes.
    B.gr(rect(DEV_X0, 0.1, DEV_X1, DEV_Y1, "F.SilkS", 0.15))
    B.gr(silk_text("U1 DevKit-Lipo · pin 1 at the antenna end", DEV_CX, 30.0, 0.9, 90))
    B.gr(silk_text("ANTENNA ->", DEV_CX, 14.0, 0.9))
    B.gr(silk_text("USB-C", DEV_CX, 60.0, 1.0))
    B.gr(rect(DEV_X0, 57.5, DEV_X1, CABLE_Y1, "Dwgs.User", 0.12))
    B.gr(silk_text("AR-Mini carrier rev B · 2026-10", DEV_CX, 68.2, 0.9))
    B.gr(fab_text("antenna keep-out — no copper", 36.0, 8.0, 0.8))
    B.gr(fab_text("J4/J5 pin 4 = +3V3 (BTS7960 74HC244 VCC, SPEC §5)", 61.5, 70.5, 0.8))


def audit():
    """Pad-to-pad clearance, edges, keep-out, physical bodies. Returns a list of problems."""
    bad = []
    for i, a in enumerate(B.pads):
        for b in B.pads[i + 1:]:
            if a[6] == b[6] and a[7] == b[7]:
                continue
            d = pad_edge_dist(b[1], b[2], a) - pad_bound(b)
            if d >= CLEAR + 0.25:
                continue
            # exact enough: distance from a to points on b's edge
            dmin = min(pad_edge_dist(px, py, a) for px, py in pad_boundary(b))
            same = a[0] and a[0] == b[0]
            if dmin < CLEAR - 1e-6 and not same:
                bad.append(("clearance", round(dmin, 3), a[6], a[7], b[6], b[7], a[0], b[0]))
            elif dmin < -0.05 and same:
                bad.append(("overlap", round(dmin, 3), a[6], a[7], b[6], b[7], a[0]))
    x0, y0, x1, y1 = KO
    for pad in B.pads:
        net, x, y = pad[0], pad[1], pad[2]
        rx, ry = (pad[3], pad[4]) if pad[5] != "circle" else (pad[3], pad[3])
        if x - rx < 0.4 or y - ry < 0.4 or x + rx > BW - 0.4 or y + ry > BH - 0.4:
            bad.append(("edge", pad[6], pad[7], x, y))
        if x0 < x < x1 and y0 < y < y1:
            bad.append(("keepout", pad[6], pad[7], x, y))
        for hx, hy, hr in B.holes:
            if pad_edge_dist(hx, hy, pad) - hr < HOLE_CLEAR - 1e-6:
                bad.append(("hole", pad[6], pad[7], round(pad_edge_dist(hx, hy, pad) - hr, 3), hx, hy))
    for i, (ax, ay, ar) in enumerate(B.holes):
        for bx, by, br in B.holes[i + 1:]:
            if math.hypot(ax - bx, ay - by) - ar - br < HOLE_CLEAR:
                bad.append(("hole-hole", ax, ay, bx, by))
    # physical bodies: tall parts never overlap each other or the module areas
    zones = {
        "U1": (DEV_X0, DEV_Y0, DEV_X1, CABLE_Y1),
        "U2": (U2_X0, U2_Y0, U2_X0 + U2_W, U2_Y0 + U2_L),
        "U3": (U3_X0, U3_Y0, U3_X0 + U3_W, U3_Y0 + U3_L),
    }

    def overlap(a, b):
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

    for i, a in enumerate(B.bodies):
        ra, box_a, tall_a, zone_a = a[0], a[1:5], a[5], a[6]
        for b in B.bodies[i + 1:]:
            if ra == b[0]:
                continue
            if tall_a and b[5] and overlap(box_a, b[1:5]):
                bad.append(("body", ra, b[0]))
        if tall_a:
            for z, zb in zones.items():
                if z != zone_a and overlap(box_a, zb):
                    bad.append(("under-module", ra, z))
        if box_a[0] < 0 or box_a[1] < 0 or box_a[2] > BW or box_a[3] > BH:
            bad.append(("body-edge", ra, box_a))
    return bad


# ---------------------------------------------------------------- router
def route():
    g = GRID
    W = int(BW / g) + 3
    H = int(BH / g) + 3
    N = W * H
    names = [None] + list(B.nets.keys())
    copper = [bytearray(N), bytearray(N)]
    block = [bytearray(N), bytearray(N)]
    # How far real copper extends past this cell's centre, in mm.
    extent = [array.array("f", [0.0]) * N, array.array("f", [0.0]) * N]
    occupied = [{}, {}]  # (ix>>2, iy>>2) -> [(ix, iy), ...] copper cells

    def note(layer, ix, iy):
        occupied[layer].setdefault((ix >> 2, iy >> 2), []).append((ix, iy))

    WALL = 255

    def cell(x, y):
        return int(round(x / g)), int(round(y / g))

    def stamp_disk(x, y, r_cu, r_blk, net_id, layers=(0, 1)):
        ix, iy = cell(x, y)
        rad = int(math.ceil(r_blk / g)) + 1
        for layer in layers:
            cu, bl = copper[layer], block[layer]
            for dy in range(-rad, rad + 1):
                yy = iy + dy
                if yy < 0 or yy >= H:
                    continue
                for dx in range(-rad, rad + 1):
                    xx = ix + dx
                    if xx < 0 or xx >= W:
                        continue
                    dist = math.hypot(xx * g - x, yy * g - y)
                    k = yy * W + xx
                    if cu[k] == WALL or bl[k] == WALL:
                        continue
                    if dist <= r_cu:
                        if cu[k] not in (0, net_id):
                            continue
                        if cu[k] == 0:
                            note(layer, xx, yy)
                        cu[k] = net_id
                        bl[k] = net_id
                        extra = r_cu - dist
                        if extra > extent[layer][k]:
                            extent[layer][k] = extra
                    elif dist <= r_blk and bl[k] == 0 and cu[k] == 0:
                        bl[k] = net_id

    def stamp_pad(pad, net_id, layers):
        """Copper cells inside the real pad shape; block ring EXTRA outside it."""
        x, y = pad[1], pad[2]
        ix, iy = cell(x, y)
        rad = int(math.ceil((pad_bound(pad) + EXTRA) / g)) + 1
        for layer in layers:
            cu, bl = copper[layer], block[layer]
            for dy in range(-rad, rad + 1):
                yy = iy + dy
                if yy < 0 or yy >= H:
                    continue
                for dx in range(-rad, rad + 1):
                    xx = ix + dx
                    if xx < 0 or xx >= W:
                        continue
                    d = pad_edge_dist(xx * g, yy * g, pad)
                    k = yy * W + xx
                    if cu[k] == WALL or bl[k] == WALL:
                        continue
                    if d <= 0:
                        if cu[k] not in (0, net_id):
                            continue
                        if cu[k] == 0:
                            note(layer, xx, yy)
                        cu[k] = net_id
                        bl[k] = net_id
                        if -d > extent[layer][k]:
                            extent[layer][k] = -d
                    elif d <= EXTRA and bl[k] == 0 and cu[k] == 0 and net_id != WALL:
                        bl[k] = net_id   # a WALL ring would stop the router stamping its own path

    def stamp_seg(x0, y0, x1, y1, width, net_id, layer):
        length = math.hypot(x1 - x0, y1 - y0)
        steps = max(1, int(length / (g * 0.5)))
        r = width / 2
        for s in range(steps + 1):
            t = s / steps
            stamp_disk(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, r + EXTRA, net_id, (layer,))

    # walls: edge margin (incl. the R3 corners), antenna keep-out
    for layer in (0, 1):
        cu, bl = copper[layer], block[layer]
        for iy in range(H):
            for ix in range(W):
                x, y = ix * g, iy * g
                k = iy * W + ix
                wall = x < 0.6 or y < 0.6 or x > BW - 0.6 or y > BH - 0.6
                if not wall:
                    for cx, cy in ((CORNER_R, CORNER_R), (BW - CORNER_R, CORNER_R),
                                   (CORNER_R, BH - CORNER_R), (BW - CORNER_R, BH - CORNER_R)):
                        if abs(x - cx) <= CORNER_R and abs(y - cy) <= CORNER_R and \
                                math.hypot(x - cx, y - cy) > CORNER_R - 0.6:
                            wall = True
                x0, y0, x1, y1 = KO
                if x0 <= x <= x1 and y0 <= y <= y1:
                    wall = True
                if wall:
                    if cu[k] == 0:
                        note(layer, ix, iy)
                    cu[k] = bl[k] = WALL
        for x, y, r in B.holes:
            stamp_disk(x, y, r, r, WALL, (0, 1))

    # pads. PTH barrels are copper on both layers; SMD is F.Cu only.
    id_of = {name: i for i, name in enumerate(names) if name}
    for pad in B.pads:
        net = pad[0]
        layers = (0, 1) if pad[8] else (0,)
        if net is None:
            stamp_pad(pad, WALL, layers)
            continue
        stamp_pad(pad, id_of[net], layers)

    # pre-stamped bridges (JP1/JP2)
    for net, x0, y0, x1, y1, w, layer in list(B.traces):
        stamp_seg(x0, y0, x1, y1, w, id_of[net], 0 if layer == "F.Cu" else 1)

    width_of = {}
    for name in names:
        if not name:
            continue
        if name == "+5V":
            width_of[name] = P5_W
        elif name == "+3V3":
            width_of[name] = P3_W
        else:
            width_of[name] = SIG_W

    groups = defaultdict(list)
    for pad in B.pads:
        if pad[0]:
            groups[pad[0]].append((pad[1], pad[2], pad[6], pad[7]))

    def component(net_id, seed):
        """Copper cells (both layers) connected to seed (layer, ix, iy)."""
        seen = set()
        dq = deque()
        layer, ix, iy = seed
        if copper[layer][iy * W + ix] != net_id:
            for L in (0, 1):
                if copper[L][iy * W + ix] == net_id:
                    layer = L
                    break
            else:
                return seen
        seen.add((layer, ix, iy))
        dq.append((layer, ix, iy))
        while dq:
            layer, ix, iy = dq.popleft()
            for dix, diy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = ix + dix, iy + diy
                if nx < 0 or ny < 0 or nx >= W or ny >= H:
                    continue
                if copper[layer][ny * W + nx] == net_id:
                    key = (layer, nx, ny)
                    if key not in seen:
                        seen.add(key)
                        dq.append(key)
            other = 1 - layer
            if copper[other][iy * W + ix] == net_id:
                key = (other, ix, iy)
                if key not in seen:
                    seen.add(key)
                    dq.append(key)
        return seen

    # pad obstacles in 1 mm buckets so foreign() only looks at neighbours
    MAXREACH = 1.0
    pad_buckets = [defaultdict(list), defaultdict(list)]
    pth_buckets = defaultdict(list)
    for pad in B.pads:
        nid = id_of[pad[0]] if pad[0] else WALL
        R = pad_bound(pad) + MAXREACH
        bx0, bx1 = int((pad[1] - R) / g) >> 2, int((pad[1] + R) / g) >> 2
        by0, by1 = int((pad[2] - R) / g) >> 2, int((pad[2] + R) / g) >> 2
        for L in ((0, 1) if pad[8] else (0,)):
            for bx in range(bx0, bx1 + 1):
                for by in range(by0, by1 + 1):
                    pad_buckets[L][(bx, by)].append((pad, nid))
        if pad[8]:
            for bx in range(bx0, bx1 + 1):
                for by in range(by0, by1 + 1):
                    pth_buckets[(bx, by)].append(pad)
    holes = list(B.holes)
    via_cells = set()

    def foreign(layer, ix, iy, radius, net_id):
        """True if this track centre would sit closer than CLEAR to other copper."""
        radius += 0.03  # a straight segment sags toward a pad between 0.25 mm samples
        cx, cy = ix * g, iy * g
        for pad, pn in pad_buckets[layer].get((ix >> 2, iy >> 2), ()):
            if pn == net_id:
                continue
            if pad_edge_dist(cx, cy, pad) < radius:
                return True
        # drills must clear other copper by the board's 0.25 mm hole rule (CLEAR is 0.2)
        for x, y, r in holes:
            dx, dy = cx - x, cy - y
            lim = r + radius + 0.05
            if dx * dx + dy * dy < lim * lim:
                return True
        reach = radius + 0.45  # half of the 0.8 mm power tracks
        reach2 = reach * reach
        rad = int(math.ceil(reach / g))
        span = (rad >> 2) + 1
        cu = copper[layer]
        ex = extent[layer]
        bx, by = ix >> 2, iy >> 2
        buckets = occupied[layer]
        for dby in range(-span, span + 1):
            for dbx in range(-span, span + 1):
                for jx, jy in buckets.get((bx + dbx, by + dby), ()):
                    dx, dy = jx - ix, jy - iy
                    dist2 = (dx * g) * (dx * g) + (dy * g) * (dy * g)
                    if dist2 > reach2:
                        continue
                    k = jy * W + jx
                    c = cu[k]
                    if c == 0 or c == net_id:
                        continue
                    if c != WALL and ex[k] > 0.45:
                        continue  # pad interior; the pad list above uses the true shape
                    lim = ex[k] + radius
                    if dist2 < lim * lim:
                        return True
        if cx < radius or cy < radius or cx > BW - radius or cy > BH - radius:
            return True
        return False

    def via_ok(ix, iy, net_id):
        """A via must not sit in any PTH pad (hole-to-hole 0.25) nor next to another via."""
        cx, cy = ix * g, iy * g
        for pad in pth_buckets.get((ix >> 2, iy >> 2), ()):
            if pad_edge_dist(cx, cy, pad) < VIA_D / 2 + CLEAR:
                return False
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if (ix + dx, iy + dy) in via_cells and math.hypot(dx, dy) * g < 0.7:
                    return False
        return True

    def astar(net_id, start_cells, goals, width):
        """start_cells are (layer, ix, iy); goals are (layer, ix, iy)."""
        import heapq
        if not start_cells:
            return None
        reach = width / 2 + CLEAR
        via_r = VIA_D / 2 + CLEAR
        goal_set = set(goals)
        pq = []
        for layer, ix, iy in start_cells:
            pq.append((0, 0, layer, ix, iy, None))
        heapq.heapify(pq)
        seen = set()
        parent = {}
        while pq:
            _f, gcost, layer, ix, iy, prev = heapq.heappop(pq)
            key = (layer, ix, iy)
            if key in seen:
                continue
            seen.add(key)
            parent[key] = prev
            if key in goal_set and prev is not None:
                path = [key]
                while parent[path[-1]] is not None:
                    path.append(parent[path[-1]])
                path.reverse()
                return path
            for dl, dix, diy, step in ((0, 1, 0, 1), (0, -1, 0, 1), (0, 0, 1, 1), (0, 0, -1, 1), (1, 0, 0, 12)):
                nlayer = layer if dl == 0 else 1 - layer
                nx, ny = ix + dix, iy + diy
                if nx < 0 or ny < 0 or nx >= W or ny >= H:
                    continue
                nkey = (nlayer, nx, ny)
                if nkey in seen:
                    continue
                if dl == 1:
                    if foreign(layer, ix, iy, via_r, net_id) or foreign(nlayer, ix, iy, via_r, net_id):
                        continue
                    if not via_ok(ix, iy, net_id):
                        continue
                elif foreign(nlayer, nx, ny, reach, net_id):
                    continue
                ng = gcost + step + (0 if nlayer == 0 else 8)
                h = min(abs(nx - gx) + abs(ny - gy) + (0 if nlayer == gl else 3) for gl, gx, gy in goals)
                heapq.heappush(pq, (ng + h, ng, nlayer, nx, ny, key))
        astar.explored = len(seen)
        return None

    # SMD pads are only on F.Cu. A via in the pad lets B.Cu tracks and the GND zone reach them.
    # Unused ones are dropped after routing (see main()).
    for net, x, y in B.smd:
        B.vias.append((net, x, y))
        via_cells.add(cell(x, y))
        stamp_disk(x, y, VIA_D / 2, VIA_D / 2, id_of[net], (0, 1))

    def span(name):
        xs = [p[0] for p in groups.get(name, [])]
        return (max(xs) - min(xs)) if xs else 0

    def commit(name, nid, w, path):
        """Stamp a found path and turn it into segments and vias."""
        for layer, ix, iy in path:
            stamp_disk(ix * g, iy * g, max(w / 2, g * 0.49), max(w / 2, g * 0.49), nid, (layer,))
        raw = [(layer, ix * g, iy * g) for layer, ix, iy in path]
        pts = [raw[0]]
        for i in range(1, len(raw) - 1):
            a, b, c = pts[-1], raw[i], raw[i + 1]
            if a[0] != b[0] or b[0] != c[0]:
                pts.append(b)
                continue
            cross = (b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1])
            if abs(cross) > 0.01:
                pts.append(b)
        pts.append(raw[-1])
        for i in range(len(pts) - 1):
            l0, x0, y0 = pts[i]
            l1, x1, y1 = pts[i + 1]
            if l0 != l1:
                B.vias.append((name, x0, y0))
                via_cells.add(cell(x0, y0))
                stamp_disk(x0, y0, VIA_D / 2, VIA_D / 2 + EXTRA, nid, (0, 1))
                continue
            layer = "F.Cu" if l0 == 0 else "B.Cu"
            if math.hypot(x1 - x0, y1 - y0) < 0.01:
                continue
            B.traces.append((name, x0, y0, x1, y1, w, layer))
        if w / 2 > g * 0.49:
            for layer, ix, iy in path:
                stamp_disk(ix * g, iy * g, w / 2, w / 2, nid, (layer,))

    failed = []
    pad_by = {(p[6], p[7]): p for p in B.pads}

    # Escape stubs (see STUBS): straight F.Cu segments from the pad up to STUB_Y.
    # The stub top is an extra A* goal for its pad; unused length is trimmed in main().
    stub_top = {}
    for key in STUBS:
        pad = pad_by[key]
        name = pad[0]
        nid, w = id_of[name], width_of[name]
        x, y = pad[1], pad[2]
        stamp_seg(x, y, x, STUB_Y, w, nid, 0)
        B.traces.append((name, x, y, x, STUB_Y, w, "F.Cu"))
        B.stubs.append((name, x, y, STUB_Y, w))
        stub_top[key] = cell(x, STUB_Y)

    # Short DevKit escapes first. Power is wider, so if it goes first it seals the
    # slot between EXT2 and the column-A resistors.
    early = (
        "IS_R_MOD", "IS_L_MOD", "BTS_IS_R", "BTS_IS_L",
        "PI_TX", "PI_RX", "SRV_TX", "SRV_RX",
        "BTS_L_RPWM", "BTS_L_LPWM", "BTS_R_RPWM", "BTS_R_LPWM",
        "ESC_L", "ESC_R", "SDA0", "SCL0", "SDA1", "SCL1", "LEAK", "LEAK_P",
        "VBAT_S", "KILL", "OE", "Q2B", "Q3B", "BZ_N", "EN",
    )

    def order_key(name):
        if name in early:
            return (0, early.index(name))
        return (1, -span(name))

    for name in sorted(id_of, key=order_key):
        nid = id_of[name]
        if name == "GND":
            continue
        pads = groups.get(name, [])
        if len(pads) < 2:
            if len(pads) == 1:
                failed.append((name, "single pad", pads[0][2]))
            continue
        w = width_of[name]
        guard = 0
        while guard < len(pads) + 2:
            guard += 1
            sx, sy = cell(pads[0][0], pads[0][1])
            comp = component(nid, (0, sx, sy))
            targets = []
            for x, y, ref, pno in pads[1:]:
                ix, iy = cell(x, y)
                if (0, ix, iy) not in comp and (1, ix, iy) not in comp:
                    layer = 0 if copper[0][iy * W + ix] == nid else 1
                    targets.append((layer, ix, iy, ref))
                    if (ref, pno) in stub_top:
                        tx, ty = stub_top[(ref, pno)]
                        targets.append((0, tx, ty, ref))
            if not targets:
                break
            goals = [(t[0], t[1], t[2]) for t in targets]
            path = astar(nid, comp, goals, w)
            if not path:
                failed.append((name, "no path", targets[0][3], len(targets), getattr(astar, "explored", 0)))
                break
            before = len(targets)
            commit(name, nid, w, path)
            sx, sy = cell(pads[0][0], pads[0][1])
            comp2 = component(nid, (0, sx, sy))
            left = 0
            for x, y, ref, pno in pads[1:]:
                ix, iy = cell(x, y)
                if (0, ix, iy) not in comp2 and (1, ix, iy) not in comp2:
                    left += 1
            if left >= before:
                failed.append((name, "stuck", targets[0][3], left))
                break
        else:
            failed.append((name, "guard", "", ""))
        # stitch grid ends to the real pad centres
        for x, y, ref, pno in pads:
            ix, iy = cell(x, y)
            if abs(ix * g - x) > 0.02 or abs(iy * g - y) > 0.02:
                if copper[0][iy * W + ix] == nid:
                    B.traces.append((name, ix * g, iy * g, x, y, w, "F.Cu"))
    return failed


def merge_traces():
    """Drop zero-length segments."""
    B.traces = [t for t in B.traces if math.hypot(t[3] - t[1], t[4] - t[2]) > 0.01]


def trim_stubs():
    """Cut each escape stub back to the highest point another same-net track or via touches it;
    drop it when nothing does (the net reached the pad another way)."""
    trimmed = 0
    for net, x, y_pad, y_top, w in B.stubs:
        own = (net, x, y_pad, x, y_top, w, "F.Cu")
        ys = []
        for t in B.traces:
            if t == own or t[0] != net:
                continue
            for px, py in ((t[1], t[2]), (t[3], t[4])):
                if abs(px - x) < 0.01 and y_top - 0.01 <= py <= y_pad:
                    ys.append(py)
        for vn, vx, vy in B.vias:
            if vn == net and abs(vx - x) < 0.01 and y_top - 0.01 <= vy <= y_pad:
                ys.append(vy)
        B.traces = [t for t in B.traces if t != own]
        if ys:
            new_top = min(ys)
            if new_top < y_pad - 0.01:
                B.traces.append((net, x, y_pad, x, new_top, w, "F.Cu"))
            if new_top > y_top + 0.01:
                trimmed += 1
        else:
            trimmed += 1
    return trimmed


def drop_dangling_vias():
    """Vias pre-placed in SMD pads that no B.Cu track reached (GND reaches the pour)."""
    ends = set()
    for net, x0, y0, x1, y1, w, layer in B.traces:
        if layer == "B.Cu":
            ends.add((round(x0, 2), round(y0, 2)))
            ends.add((round(x1, 2), round(y1, 2)))
    keep = []
    for net, x, y in B.vias:
        if net == "GND" or (round(x, 2), round(y, 2)) in ends:
            keep.append((net, x, y))
    dropped = len(B.vias) - len(keep)
    B.vias = keep
    return dropped


def edge_cuts():
    """100 × 80, R3 corners. Lines + 90° arcs."""
    r = CORNER_R
    corners = [
        (r, r, (0, r), (r, 0)),
        (BW - r, r, (BW, r), (BW - r, 0)),
        (r, BH - r, (0, BH - r), (r, BH)),
        (BW - r, BH - r, (BW, BH - r), (BW - r, BH)),
    ]
    out = []

    def line(x0, y0, x1, y1):
        out.append(
            f'\t(gr_line (start {x0 + OX:.3f} {y0 + OY:.3f}) (end {x1 + OX:.3f} {y1 + OY:.3f})\n'
            f'\t\t(stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid()}"))'
        )

    def arc(cx, cy, a, b):
        ax, ay = a[0] - cx, a[1] - cy
        bx, by = b[0] - cx, b[1] - cy
        mx, my = ax + bx, ay + by
        norm = math.hypot(mx, my)
        mx, my = cx + r * mx / norm, cy + r * my / norm
        out.append(
            f'\t(gr_arc (start {a[0] + OX:.3f} {a[1] + OY:.3f}) (mid {mx + OX:.3f} {my + OY:.3f}) '
            f'(end {b[0] + OX:.3f} {b[1] + OY:.3f})\n'
            f'\t\t(stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid()}"))'
        )
    line(r, 0, BW - r, 0)
    line(r, BH, BW - r, BH)
    line(0, r, 0, BH - r)
    line(BW, r, BW, BH - r)
    for cx, cy, a, b in corners:
        arc(cx, cy, a, b)
    return "\n".join(out)


def zone():
    # GND pour on B.Cu, inset 0.5 mm. Antenna keep-out is a second zone.
    x0, y0, x1, y1 = 0.5 + OX, 0.5 + OY, BW - 0.5 + OX, BH - 0.5 + OY
    kx0, ky0, kx1, ky1 = KO[0] + OX, KO[1] + OY, KO[2] + OX, KO[3] + OY
    gnd = (
        f'\t(zone (net "GND") (layer "B.Cu") (uuid "{uid()}")\n'
        f'\t\t(hatch edge 0.5)\n'
        f'\t\t(priority 0)\n'
        f'\t\t(connect_pads yes (clearance 0.2))\n'
        f'\t\t(min_thickness 0.25)\n'
        f'\t\t(fill (thermal_gap 0.5) (thermal_bridge_width 0.4) (island_removal_mode 0))\n'
        f'\t\t(polygon (pts (xy {x0} {y0}) (xy {x1} {y0}) (xy {x1} {y1}) (xy {x0} {y1})))\n'
        f'\t)'
    )
    keep = (
        f'\t(zone (layers "F.Cu" "B.Cu") (uuid "{uid()}")\n'
        f'\t\t(hatch edge 0.5)\n'
        f'\t\t(priority 1)\n'
        f'\t\t(name "ANTENNA")\n'
        f'\t\t(keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed)\n'
        f'\t\t\t(copperpour not_allowed) (footprints allowed))\n'
        f'\t\t(polygon (pts (xy {kx0} {ky0}) (xy {kx1} {ky0}) (xy {kx1} {ky1}) (xy {kx0} {ky1})))\n'
        f'\t)'
    )
    return gnd + "\n" + keep


def emit():
    segs = []
    for net, x0, y0, x1, y1, w, layer in B.traces:
        segs.append(
            f'\t(segment (start {x0 + OX:.3f} {y0 + OY:.3f}) (end {x1 + OX:.3f} {y1 + OY:.3f})\n'
            f'\t\t(width {w:.2f}) (layer "{layer}") (net "{net}") (uuid "{uid()}"))'
        )
    vias = []
    for net, x, y in B.vias:
        vias.append(
            f'\t(via (at {x + OX:.3f} {y + OY:.3f}) (size {VIA_D}) (drill {VIA_DRILL})\n'
            f'\t\t(layers "F.Cu" "B.Cu") (net "{net}") (uuid "{uid()}"))'
        )
    layers = """\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1")
\t\t(23 "Eco2.User" user "User.Eco2")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t\t(39 "User.1" user)
\t)"""
    body = f"""(kicad_pcb
\t(version 20260206)
\t(generator "armini_gen")
\t(generator_version "10.0")
\t(general (thickness 1.6) (legacy_teardrops no))
\t(paper "A4")
{layers}
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(tenting (front yes) (back yes))
\t)
{chr(10).join(B.fps)}
{chr(10).join(B.graphics)}
{edge_cuts()}
{chr(10).join(segs)}
{chr(10).join(vias)}
{zone()}
\t(embedded_fonts no)
)
"""
    with open(OUT, "w") as f:
        f.write(body)
    pro = r'''{
  "board": {
    "design_settings": {
      "defaults": {
        "board_outline_line_width": 0.05,
        "copper_line_width": 0.3,
        "other_line_width": 0.15,
        "vias": { "via_diameter": 0.6, "via_drill": 0.3 }
      },
      "rules": {
        "min_clearance": 0.2,
        "min_connection": 0.0,
        "min_copper_edge_clearance": 0.3,
        "min_hole_clearance": 0.25,
        "min_hole_to_hole": 0.25,
        "min_track_width": 0.2,
        "min_via_diameter": 0.6,
        "min_via_drill": 0.3,
        "min_through_hole_diameter": 0.3
      },
      "track_widths": [0.3, 0.5, 0.8],
      "via_dimensions": [{ "diameter": 0.6, "drill": 0.3 }]
    }
  },
  "meta": { "filename": "AR-Mini_carrier_revB.kicad_pro", "version": 3 },
  "net_settings": {
    "classes": [{
      "name": "Default",
      "clearance": 0.2,
      "track_width": 0.3,
      "via_diameter": 0.6,
      "via_drill": 0.3,
      "microvia_diameter": 0.3,
      "microvia_drill": 0.1,
      "diff_pair_width": 0.2,
      "diff_pair_gap": 0.25,
      "diff_pair_via_gap": 0.25
    }],
    "netclass_patterns": []
  }
}
'''
    with open(PRO, "w") as f:
        f.write(pro)


def main():
    place_parts()
    bad = audit()
    print(f"pads {len(B.pads)}  holes {len(B.holes)}  bodies {len(B.bodies)}  audit {len(bad)}")
    for row in bad[:60]:
        print(" ", row)
    if bad:
        print("AUDIT FAILED — not routing")
        return 1
    if os.environ.get("GEN_NO_ROUTE"):
        emit()
        print("wrote (unrouted)", OUT)
        return 0
    failed = route()
    merge_traces()
    trimmed = trim_stubs()
    dropped = drop_dangling_vias()
    print(f"traces {len(B.traces)}  vias {len(B.vias)} (dropped {dropped} unused)  "
          f"stubs trimmed {trimmed}  unrouted {len(failed)}")
    for row in failed:
        print(" ", row)
    emit()
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
