"""Render the EXP-14 logic carrier (boards_c0.py) as an HTML page with top view, bottom view and netlist.
usage: python3 render_c0.py out.html   → then node shot.js $PWD/out.html $PWD/out.png 2
"""
import html, sys, collections
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from boards_c0 import BOARDS, check
from boards import P

S = 8.0  # px per mm
NETC = {"GND": "#111", "3V3": "#d7191c", "+5V": "#f28e00", "SDA0": "#1a9641", "SCL0": "#0e8f8f", "SDA1": "#1a9641",
        "SCL1": "#0e8f8f", "ESC": "#d4b000", "ESC5": "#d4b000", "RUD": "#2b6cd4", "RUD5": "#2b6cd4", "VBAT": "#8b0000",
        "VB_N": "#c2185b", "LK_N": "#7b3fa0", "PROBE": "#7b3fa0", "K_N": "#6a1b9a", "OE": "#777"}
PARTNER = {"U2A": "U2B", "U2B": "U2A", "JP1": "JP2", "JP2": "JP1"}
LABEL_SIDE = {"R4": -1}
PADL, PADR, PADT, PADB = 74, 84, 66, 108


def col(n):
    return NETC.get(n, "#888")


def geom(b, bottom):
    w, mx0, my0 = b["w"], b["mx0"], b["my0"]

    def X(xmm):                     # mm from the PORT edge → px (mirrored on the bottom view)
        return ((w - xmm) if bottom else xmm) * S

    def hx(x):
        return X(mx0 + (x - 1) * P)

    def hy(y):
        return (my0 + (y - 1) * P) * S
    return hx, hy, X


LIGHT = {"#fff", "#ffe082", "#e3f2fd", "#bfe3cf", "#ffcdd2"}


def halo(fill):
    return ' paint-order="stroke" stroke="#14301f" stroke-width="2.6" stroke-linejoin="round"' if fill in LIGHT else ""


def rot(txt, x, y, ang, size=9, fill="#fff", anchor="start", weight="", extra=""):
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{fill}"{w}{halo(fill)} '
            f'transform="rotate({ang} {x:.1f} {y:.1f})" {extra}>{html.escape(txt)}</text>')


def txt(t, x, y, size=9, fill="#fff", anchor="middle", weight="", extra=""):
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{fill}"{w}{halo(fill)} {extra}>{html.escape(t)}</text>'


def dim_h(o, x1, x2, y, label, color="#c00"):
    o.append(f'<line x1="{x1:.1f}" y1="{y}" x2="{x2:.1f}" y2="{y}" stroke="{color}" stroke-width="1.2" marker-start="url(#da)" marker-end="url(#da)"/>')
    o.append(txt(label, (x1 + x2) / 2, y - 4, 10, color, weight="700"))


def dim_v(o, y1, y2, x, label, color="#c00"):
    o.append(f'<line x1="{x}" y1="{y1:.1f}" x2="{x}" y2="{y2:.1f}" stroke="{color}" stroke-width="1.2" marker-start="url(#da)" marker-end="url(#da)"/>')
    o.append(rot(label, x - 4, (y1 + y2) / 2, -90, 10, color, "middle", "700"))


def svg_board(b, bottom=False):
    hx, hy, X = geom(b, bottom)
    W, H = b["w"] * S, b["h"] * S
    nx, ny = b["nx"], b["ny"]
    o = [f'<svg viewBox="{-PADL} {-PADT} {W + PADL + PADR} {H + PADT + PADB}" width="{W + PADL + PADR}" height="{H + PADT + PADB}" '
         f'xmlns="http://www.w3.org/2000/svg" font-family="Inter,Arial">',
         '<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#fff"/></marker>'
         '<marker id="da" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto-start-reverse"><path d="M0,0 L6,3 L0,6 z" fill="#c00"/></marker></defs>']
    o.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="6" fill="#2f7d5b" stroke="#1d5139" stroke-width="2"/>')
    # blank starboard strip (no pads) — the antenna hangs over it
    xs0, xs1 = sorted([X(b["mx0"] + (nx - 1) * P + 1.27), X(b["w"])])
    o.append(f'<rect x="{xs0:.1f}" y="0" width="{xs1 - xs0:.1f}" height="{H}" fill="#255f47" opacity="0.9"/>')
    o.append(rot("blank strip ≈11 mm — no pads — WROOM antenna hangs over it", (xs0 + xs1) / 2 + 3, hy(31), -90, 8.5, "#bfe3cf", "start"))
    # mounting holes (NOT on the grid) + keep-out
    for (mx, my) in b["mholes"]:
        o.append(f'<circle cx="{X(mx):.1f}" cy="{my*S:.1f}" r="{b["mhole_r"]*S:.1f}" fill="none" stroke="#ffcdd2" stroke-dasharray="4 3" stroke-width="1.3"/>')
        o.append(f'<circle cx="{X(mx):.1f}" cy="{my*S:.1f}" r="{1.6*S:.1f}" fill="#fff" stroke="#c00" stroke-width="1.5"/>')
    # column / row numbers
    for x in range(1, nx + 1):
        o.append(txt(str(x), hx(x), -7, 8.5, "#444"))
        o.append(txt(str(x), hx(x), H + 15, 8.5, "#444"))
    for y in range(1, ny + 1):
        o.append(txt(str(y), -8, hy(y) + 3, 8.5, "#444", "end"))
        o.append(txt(str(y), W + 8, hy(y) + 3, 8.5, "#444", "start"))
    # compass
    left, right = ("STARBOARD", "PORT") if bottom else ("PORT", "STARBOARD")
    o.append(txt("BOW ↑", W / 2, -54, 13, "#1b1b1b", weight="700"))
    o.append(txt("STERN ↓  ·  «EXP-14» print on this edge (hole inset ≈3.6 mm)", W / 2, H + 78, 12, "#1b1b1b", weight="700"))
    o.append(rot(left, -60, H / 2, -90, 12, "#1b1b1b", "middle", "700"))
    o.append(rot(right, W + 68, H / 2, 90, 12, "#1b1b1b", "middle", "700"))
    if not bottom:
        dim_h(o, 0, W, -38, "90 (measure)")
        dim_h(o, X(b["mholes"][0][0]), X(b["mholes"][1][0]), -22, "holes ≈76.0 (measure)")
        dim_v(o, 0, H, W + 62, "100 (measure)")
        dim_v(o, b["mholes"][0][1] * S, b["mholes"][2][1] * S, W + 46, "holes ≈90.1 (measure)")
    # keep-outs
    for k in b["keep"]:
        x0, x1 = sorted([hx(k["x0"]), hx(k["x1"])])
        y0, y1 = hy(k["y0"]), hy(k["y1"])
        o.append(f'<rect x="{x0 - 9:.1f}" y="{y0 - 9:.1f}" width="{x1 - x0 + 18:.1f}" height="{y1 - y0 + 18:.1f}" fill="none" stroke="#ffd54f" stroke-dasharray="5 4" stroke-width="2"/>')
        if not bottom:
            o.append(rot(k["label"], (x0 + x1) / 2 + 3, (y0 + y1) / 2, -90, 8, "#ffe082", "middle"))
    # holes
    for x in range(1, nx + 1):
        for y in range(1, ny + 1):
            o.append(f'<circle cx="{hx(x):.1f}" cy="{hy(y):.1f}" r="{0.85*S}" fill="#d9d4c7" stroke="#9c9789" stroke-width="0.8"/>'
                     f'<circle cx="{hx(x):.1f}" cy="{hy(y):.1f}" r="{0.45*S}" fill="#2a2a2a"/>')
    # module outlines (top view only)
    if not bottom:
        for ol in [b["outline"]] + b["outlines"]:
            xa, xb = sorted([hx(ol["x0"]), hx(ol["x1"])])
            ya, yb = hy(ol["y0"]), hy(ol["y1"])
            if ol["kind"] == "devkit":
                ext, exty = 1.27 * S, 1.35 * S
                o.append(f'<rect x="{xa - ext:.1f}" y="{ya - exty:.1f}" width="{xb - xa + 2*ext:.1f}" height="{yb - ya + 2*exty:.1f}" fill="#d32f2f" fill-opacity="0.14" stroke="#d32f2f" stroke-width="2" stroke-dasharray="8 4"/>')
                ax = xb + ext
                o.append(f'<rect x="{ax:.1f}" y="{hy(16):.1f}" width="{6.5*S}" height="{hy(22) - hy(16):.1f}" fill="#ffcdd2" fill-opacity="0.55" stroke="#d32f2f" stroke-dasharray="3 3"/>')
                o.append(rot("ANTENNA over the blank strip", ax + 3.2 * S, hy(19), -90, 9, "#7f0000", "middle", "700"))
                ux = xa - ext
                o.append(f'<rect x="{ux - 9*S:.1f}" y="{hy(19) - 4.5*S:.1f}" width="{9*S}" height="{9*S}" fill="#eceff1" fill-opacity="0.5" stroke="#d32f2f" stroke-dasharray="3 3"/>')
                o.append(rot("USB-C → 90° adapter", ux - 4.5 * S, hy(19), -90, 9, "#fff", "middle", "700"))
                cx = (xa + xb) / 2
                o.append(txt("ESP32-S3-DevKit-LiPo on two female 1×22 — plugs in on top", cx, hy(18.6), 13, "#fff", weight="700"))
                o.append(txt("EXT1 = BOW row (pins 1, 2 = 3V3 at the antenna end) · EXT2 = STERN row (pin 1 = GND) · pin n = column 31 − n", cx, hy(19.6), 10, "#fff"))
                o.append(txt("CHECK with a meter before soldering: on EXT1 the two pins nearest the antenna beep together (both 3V3); on EXT2 they do not (GND, TX)", cx, hy(20.5), 9, "#ffe082"))
                o.append(txt("under the DevKit: only bottom-side wires, nothing on top", cx, hy(21.4), 9.5, "#fff"))
            elif ol["kind"] == "pca":
                ex, ey = 1.55 * S, 6.6 * S
                o.append(f'<rect x="{xa - ex:.1f}" y="{ya - ey:.1f}" width="{xb - xa + 2*ex:.1f}" height="{yb - ya + 2*ey:.1f}" fill="#1565c0" fill-opacity="0.16" stroke="#90caf9" stroke-width="2" stroke-dasharray="8 4"/>')
                o.append(f'<rect x="{xa + 10*S:.1f}" y="{ya - ey + 1.5*S:.1f}" width="{xb - xa - 2*ex - 10*S:.1f}" height="{7.6*S}" fill="#90caf9" fill-opacity="0.25" stroke="#90caf9" stroke-dasharray="2 2"/>')
                o.append(txt("servo field 16 × 3 pins (lift servos plug here, GND row outermost)", (xa + xb) / 2 + 5 * S, ya - ey + 5.6 * S, 9, "#e3f2fd"))
                o.append(f'<rect x="{xa + 2.5*S:.1f}" y="{ya - ey + 1.0*S:.1f}" width="{9*S}" height="{7.0*S}" fill="#263238" fill-opacity="0.25" stroke="#90caf9"/>')
                o.append(txt("V+ GND terminal", xa + 7.0 * S, ya - ey + 3.2 * S, 8, "#fff", weight="700"))
                o.append(txt("(screws face the bow)", xa + 7.0 * S, ya - ey + 5.6 * S, 7, "#e3f2fd"))
                o.append(txt("PCA9685 16-ch servo module — plugs in on top (both 1×6 ends)", (xa + xb) / 2, hy(10.2), 11, "#fff", weight="700"))
                o.append(txt("V+ only through the terminal from the QIQIAZI 5 V buck (power box) — the V+ header pin stays unconnected", (xa + xb) / 2, hy(11.2), 9, "#e3f2fd"))
            elif ol["kind"] == "bno":
                ex, ey = 1.27 * S, 7.0 * S
                o.append(f'<rect x="{xa - ex:.1f}" y="{ya - ey:.1f}" width="{xb - xa + 2*ex:.1f}" height="{yb - ya + 2*ey:.1f}" fill="#1565c0" fill-opacity="0.18" stroke="#90caf9" stroke-width="2" stroke-dasharray="8 4"/>')
                cx = (xa + xb) / 2
                o.append(txt("BNO055", cx, ya - ey + 2.6 * S, 11, "#fff", weight="700"))
                o.append(txt("Adafruit #2472", cx, ya - ey + 4.0 * S, 8.5, "#fff"))
                o.append(txt("Vin = 3V3 only", cx, ya - ey + 5.4 * S, 8.5, "#ffe082"))
                o.append(f'<path d="M {cx:.1f} {yb + 5.5*S:.1f} L {cx:.1f} {yb + 1.5*S:.1f}" stroke="#fff" stroke-width="4" marker-end="url(#arr)"/>')
                o.append(txt("axis arrow → BOW", cx, yb + 6.6 * S, 8, "#fff"))
    # bridges (bare tinned wire, bottom)
    for a, c, net in b["bridges"]:
        x1, y1, x2, y2 = hx(a[0]), hy(a[1]), hx(c[0]), hy(c[1])
        o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#cfd8dc" stroke-width="{1.5*S if bottom else 0.9*S}" stroke-linecap="round" opacity="{0.95 if bottom else 0.5}"/>')
        o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col(net)}" stroke-width="2" stroke-linecap="round" opacity="0.9"/>')
    # insulated wires (bottom)
    for i, (a, c, net) in enumerate(b["wires"]):
        x1, y1, x2, y2 = hx(a[0]), hy(a[1]), hx(c[0]), hy(c[1])
        mx_, my_ = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        L = max((dx * dx + dy * dy) ** 0.5, 1)
        k = (12 + (i % 4) * 6) * (1 if (i % 2) else -1)
        cx_, cy_ = mx_ - dy / L * k, my_ + dx / L * k
        o.append(f'<path d="M {x1:.1f} {y1:.1f} Q {cx_:.1f} {cy_:.1f} {x2:.1f} {y2:.1f}" fill="none" stroke="{col(net)}" stroke-width="{3.2 if bottom else 2.2}" '
                 f'stroke-dasharray="{"" if bottom else "6 3"}" opacity="{0.95 if bottom else 0.6}"/>')
    # parts
    jst_h = [p for p in b["parts"] if p["kind"] == "jst" and len({y for _, y, *_ in p["pins"]}) == 1]
    for p in b["parts"]:
        pins = p["pins"]; k = p["kind"]; ref = p["ref"]
        xs = [hx(x) for x, y, *_ in pins]; ys = [hy(y) for x, y, *_ in pins]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        vertical = len({x for x, *_ in pins}) == 1 and len(pins) > 1
        inner_right = (x0 + x1) / 2 < W / 2        # labels go toward the board centre
        sgn = 1 if inner_right else -1
        anc_in = "start" if inner_right else "end"
        op = 0.35 if bottom else 0.9
        if k == "fheader":
            o.append(f'<rect x="{x0 - 1.27*S:.1f}" y="{y0 - 1.27*S:.1f}" width="{x1 - x0 + 2.54*S:.1f}" height="{y1 - y0 + 2.54*S:.1f}" fill="#222" opacity="{op}" rx="2"/>')
        elif k == "jst":
            if vertical:
                o.append(f'<rect x="{x0 - 2.9*S:.1f}" y="{y0 - 2.45*S:.1f}" width="{5.8*S}" height="{y1 - y0 + 4.9*S:.1f}" fill="#f5f1e6" stroke="#8d8577" rx="2" opacity="{op}"/>')
                lx = x0 - sgn * 2.9 * S                 # latch toward the board edge
                o.append(f'<line x1="{lx:.1f}" y1="{y0 - 2.0*S:.1f}" x2="{lx:.1f}" y2="{y1 + 2.0*S:.1f}" stroke="#8d8577" stroke-width="3" opacity="{op}"/>')
            else:
                o.append(f'<rect x="{x0 - 2.45*S:.1f}" y="{y0 - 2.9*S:.1f}" width="{x1 - x0 + 4.9*S:.1f}" height="{5.8*S}" fill="#f5f1e6" stroke="#8d8577" rx="2" opacity="{op}"/>')
                o.append(f'<line x1="{x0 - 2.0*S:.1f}" y1="{y0 + 2.9*S:.1f}" x2="{x1 + 2.0*S:.1f}" y2="{y0 + 2.9*S:.1f}" stroke="#8d8577" stroke-width="3" opacity="{op}"/>')
        elif k == "servo":
            o.append(f'<rect x="{x0 - 1.27*S:.1f}" y="{y0 - 1.27*S:.1f}" width="{x1 - x0 + 2.54*S:.1f}" height="{y1 - y0 + 2.54*S:.1f}" fill="#111" rx="2" opacity="{op}"/>')
        elif k == "dip":
            o.append(f'<rect x="{x0 - 1.6*S:.1f}" y="{y0 - 1.6*S:.1f}" width="{x1 - x0 + 3.2*S:.1f}" height="{y1 - y0 + 3.2*S:.1f}" fill="#333" stroke="#000" rx="2" opacity="{op}"/>')
            p1x = hx(pins[0][0])                     # pin 1 end carries the notch
            nx_ = p1x - 0.9 * S if p1x < (x0 + x1) / 2 else p1x + 0.9 * S
            o.append(f'<circle cx="{nx_:.1f}" cy="{(y0+y1)/2:.1f}" r="{0.9*S}" fill="#2f7d5b" opacity="{op}"/>')
        elif k == "res_up" and not bottom:
            (ax, ay), (bx, by) = (xs[0], ys[0]), (xs[1], ys[1])
            o.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#bbb" stroke-width="2"/>')
            o.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="{1.25*S}" fill="#c8a165" stroke="#6d4c22" stroke-width="1.5"/>')
        elif k == "cap" and not bottom:
            o.append(f'<line x1="{xs[0]:.1f}" y1="{ys[0]:.1f}" x2="{xs[1]:.1f}" y2="{ys[1]:.1f}" stroke="#bbb" stroke-width="2"/>')
            o.append(f'<ellipse cx="{(xs[0]+xs[1])/2:.1f}" cy="{(ys[0]+ys[1])/2:.1f}" rx="{1.3*S}" ry="{1.3*S}" fill="#f2c94c" stroke="#8a6d00"/>')
        elif k == "elko" and not bottom:
            o.append(f'<circle cx="{(xs[0]+xs[1])/2:.1f}" cy="{(ys[0]+ys[1])/2:.1f}" r="{3.15*S}" fill="#1e3a8a" stroke="#0b1d4d" opacity="0.92"/>')
            o.append(txt("+", xs[0], ys[0] + 4, 11, "#fff", weight="700")); o.append(txt("−", xs[1], ys[1] + 4, 11, "#fff", weight="700"))
        for (x, y, net, nm) in pins:
            o.append(f'<circle cx="{hx(x):.1f}" cy="{hy(y):.1f}" r="{0.75*S}" fill="{col(net)}" stroke="#fff" stroke-width="1.2"/>')
        if bottom:
            if k in ("fheader", "dip", "jst", "servo"):
                o.append(txt(ref, (x0 + x1) / 2, (y0 + y1) / 2 + 4, 10, "#fff", weight="700", extra='opacity="0.8"'))
            continue
        # ---- labels (top view)
        if k == "fheader":
            if ref in ("H1", "H2"):
                for (x, y, net, nm) in pins:
                    n = 31 - x
                    if ref == "H1":
                        o.append(rot(nm, hx(x) + 3, hy(y) + 1.27 * S + 4, 90, 8.5, "#fff" if not net.startswith("x") else "#ffcdd2", "start", "700" if not net.startswith("x") else ""))
                    else:
                        o.append(rot(nm, hx(x) + 3, hy(y) - 1.27 * S - 4, -90, 8.5, "#fff" if not net.startswith("x") else "#ffcdd2", "start", "700" if not net.startswith("x") else ""))
                    if n in (1, 5, 10, 15, 20, 22):
                        yy = hy(y) - 1.27 * S - 4 if ref == "H1" else hy(y) + 1.27 * S + 10
                        o.append(txt(str(n), hx(x), yy, 7.5, "#ffe082", weight="700"))
                o.append(txt(ref.replace("H1", "EXT1").replace("H2", "EXT2"), x1 + 1.27 * S + 14, (y0 + y1) / 2 + 4, 9, "#fff", "start", "700"))
            else:
                px = hx(next(q for q in b["parts"] if q["ref"] == PARTNER[ref])["pins"][0][0])
                toward = 1 if px > x0 else -1
                for (x, y, net, nm) in pins:
                    o.append(txt(nm, hx(x) + toward * 9, hy(y) + 3.5, 8.5, "#fff", "start" if toward > 0 else "end", "700"))
                o.append(txt(ref, x0, y0 - 1.27 * S - 5, 8.5, "#fff", weight="700"))
        elif k in ("jst", "servo"):
            if vertical:
                off = (2.9 if k == "jst" else 1.27) * S + 5
                for (x, y, net, nm) in pins:
                    if ref == "J1":   # parts sit right next to J1: names inside the housing
                        o.append(txt(nm, hx(x) + 7, hy(y) + 3, 6.5, "#3e3a33", "start", "700"))
                    else:
                        o.append(txt(nm, hx(x) + sgn * off, hy(y) + 3.5, 8.5, "#fff", anc_in, "700"))
                lx = -30 if inner_right else W + 30
                o.append(rot(p["label"], lx, (y0 + y1) / 2, -90 if inner_right else 90, 9.5, "#00332a", "middle", "700"))
            else:
                for (x, y, net, nm) in pins:
                    o.append(txt(nm, hx(x), hy(y) - 2.9 * S - 3, 7.5, "#fff", weight="700"))
                j = [q["ref"] for q in jst_h].index(ref)
                o.append(txt(p["label"], (x0 + x1) / 2, H + 32 + 13 * (j % 3), 9.5, "#00332a", weight="700"))
        elif k == "dip":
            for (x, y, net, nm) in pins:
                num, name = nm.split()
                top_row = hy(y) == y0
                o.append(txt(name, hx(x), (y0 + 15) if top_row else (y1 - 8), 7.5, "#fff"))
                o.append(txt(num, hx(x), (y0 - 1.6 * S - 2) if top_row else (y1 + 1.6 * S + 9), 7.5, "#ffe082", weight="700"))
            o.append(txt("U6 74HCT125", (x0 + x1) / 2, (y0 + y1) / 2 + 4, 11, "#fff", weight="700"))
        elif k in ("res_up", "cap"):
            if ref in ("R1", "R2", "C1"):
                if ref == "C1":
                    o.append(txt("← R1 100k · R2 30k · C1 100n (VBAT ÷)", xs[0] + 12, ys[0] + 3.5, 8.5, "#fff", "start", "700"))
            else:
                sd = LABEL_SIDE.get(ref, sgn)
                o.append(txt(f"{ref} {p['label']}", xs[0] + sd * 11, ys[0] + 3.5, 8.5, "#fff", "start" if sd > 0 else "end", "700"))
        elif k == "elko":
            o.append(txt(f"{ref} {p['label']}", (xs[0] + xs[1]) / 2, y0 - 3.15 * S - 8, 8.5, "#fff", weight="700"))
    side = ("BOTTOM (solder side) — board turned over left↔right: STARBOARD is on the LEFT here"
            if bottom else "TOP (component side) — bow up, starboard right")
    o.append(txt(side, W / 2, H + 96, 12, "#333", weight="700"))
    o.append('</svg>')
    return "\n".join(o)


def netlist(b):
    rows = collections.defaultdict(list)
    for p in b["parts"]:
        for (x, y, net, nm) in p["pins"]:
            if net.startswith(("x1_", "x2_")) or (net.startswith("n") and net != "nc_j2"):
                continue
            rows[net].append(f'{p["ref"]}{("." + nm) if nm else ""} ({x},{y})')
    out = ['<table class="nl"><tr><th>net</th><th>pins (column,row)</th></tr>']
    for net in sorted(rows):
        if net in ("nc11", "nc8", "nc_j2"):
            continue
        out.append(f'<tr><td><span class="sw" style="background:{col(net)}"></span>{html.escape(net)}</td><td>{html.escape(" · ".join(rows[net]))}</td></tr>')
    out.append("</table>")
    return "\n".join(out)


def page():
    b = BOARDS[0]
    e, _ = check(b)
    assert not e, e
    nb = len(b["bridges"]); nw = len(b["wires"])
    css = """body{font-family:Inter,Arial,sans-serif;margin:24px;color:#1b1b1b;background:#fff;width:2080px}
h1{font-size:26px;margin:0 0 6px} h2{font-size:19px;margin:22px 0 6px} p,li{font-size:13.5px;line-height:1.45}
.row{display:flex;gap:22px;align-items:flex-start;flex-wrap:wrap}.card{border:1px solid #ddd;border-radius:10px;padding:12px 14px;background:#fafafa}
table.nl{border-collapse:collapse;font-size:11.5px;max-width:720px} table.nl td,table.nl th{border-bottom:1px solid #e3e3e3;padding:3px 6px;text-align:left;vertical-align:top} table.nl td:first-child{white-space:nowrap}
.sw{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.leg span{display:inline-block;margin-right:16px;font-size:12.5px}.small{font-size:12px;color:#555}"""
    o = [f"<!doctype html><html><head><meta charset='utf-8'><title>AR-Mini C072 · EXP-14 logic carrier</title><style>{css}</style></head><body>"]
    o.append("<h1>AR-Mini · C031 / C072 · ONE logic carrier on the Elimex EXP-14 (100 × 90, double-sided) — 06.11.2026</h1>")
    o.append("<p>Replaces the three small perfboards P1 / P2 / P4 of 04.11. Same nets as the FINAL 2 breadboard (31.10) and carrier rev B (SPEC.md), so firmware "
             "<b>remote_pool</b> runs unchanged; rev B gets this board's outline and 4 holes later, so the PCB drops onto the same tray. "
             "Grid 2.54 mm, columns 1–30 port → starboard, rows 1–36 bow → stern (if your board has 37 rows, the extra row stays empty). "
             f"Machine-checked: no hole carries two nets, every net is one connected piece; {nb} bare bridges, {nw} insulated wires. "
             "Red = dimensions still to confirm with the caliper / the printed FIT template.</p>")
    o.append("<p class='leg'><span><b>Grey thick line</b> = bare tinned wire on the bottom (bridge), soldered at every pad it crosses</span>"
             "<span><b>Coloured curve</b> = insulated wire on the bottom (22 AWG, hole to hole)</span>"
             "<span><b>Brown dot + line</b> = resistor standing upright (body on the dot)</span><span><b>Yellow</b> = 100 nF</span>"
             "<span><b>Cream box</b> = JST-XH 2.54 header, thick side = latch, to the board edge</span><span><b>Black 3-pin</b> = male header for a servo plug</span>"
             "<span><b>Dashed boxes</b> = modules that plug in on top (PCA9685, DevKit, BNO055)</span></p>")
    o.append("<p class='leg'>" + "".join(f"<span><span class='sw' style='background:{c}'></span>{n}</span>" for n, c in
             [("GND", "#111"), ("3V3", "#d7191c"), ("+5V (EXT1-21)", "#f28e00"), ("SDA", "#1a9641"), ("SCL", "#0e8f8f"), ("ESC GPIO1", "#d4b000"),
              ("rudder GPIO2", "#2b6cd4"), ("VBAT 12 V", "#8b0000"), ("VB_N divider", "#c2185b"), ("leak / KILL", "#7b3fa0")]) + "</p>")
    o.append(f"<h2>{html.escape(b['title'])}</h2>")
    o.append("<div class='row'>")
    o.append(f"<div class='card'>{svg_board(b, False)}</div>")
    o.append(f"<div class='card'>{svg_board(b, True)}</div>")
    o.append("</div><div class='row'>")
    vals = " · ".join(f"{p['ref']} {p['label']}" for p in b["parts"] if p["kind"] in ("res_up", "cap", "elko"))
    o.append(f"<div class='card'><b>Netlist C0</b><p class='small'><b>Values:</b> {html.escape(vals)}</p>" + netlist(b) + "</div>")
    o.append("""<div class='card' style='max-width:640px'><b>Where the cables come in (logic box 150 × 110, board centred: 8 mm to each long wall, 23 mm to bow / stern)</b><ul>
<li><b>L1 port wall ≈ 60–100 mm from the bow</b> — one bundle from the power box: VBAT sense → J1 (bow-port), ESC signal → J2, leak comb → J9b, USB power → DevKit USB-C (90° adapter, points along the port margin), V+ pair → PCA9685 terminal (bow).</li>
<li><b>L2 starboard knock-out ≈ 30 mm</b> — lift servos → PCA servo field, XIAO 5 V → J13, MLX90640 → J7.</li>
<li><b>L3 starboard ≈ 73 mm</b> — rudder servo → J3 (column 30, rows 26–28).</li>
<li><b>L4 starboard ≈ 116 mm</b> — MLX90642-D45 → J6; the logic-box leak comb → J9 at the stern edge.</li>
<li><b>KILL</b> button on the lid above the stern-port corner → J10 (C + KILL); RUN stays unused with a latching button.</li></ul>
<b>Rules while soldering</b><ul>
<li>Headers first: plug both female 1×22 onto the DevKit, put the sandwich into rows 14 / 24 (pin 1 at column 30), solder 2 corner pins of each, pull the DevKit, solder the rest. Same for the PCA9685 (columns 4 / 26) and the BNO055 (columns 18 / 25).</li>
<li>The EXP-14 is double-sided with plated holes: a bare bridge is soldered to <i>every</i> pad it crosses, so never run one through a hole that belongs to another net (the drawing never does).</li>
<li>U6 socket notch to PORT (pin 1 = column 4, row 30). 3A / 4A / 3OE / 4OE go to +5V (unused channels stay off).</li>
<li>Nothing taller than 2 mm on top under the DevKit (rows 15–23) or under the modules; all routing there is on the bottom.</li>
<li>Before the modules go in: meter beep test of every net in the table, and NO beep between 3V3, +5V, VBAT and GND.</li></ul>
<p class='small'>Generated by boards_c0.py / render_c0.py (project files enclosure-1104/src/). Claude · thread "Премести електрониката на перфоборд в здрави кутии".</p></div>""")
    o.append("</div>")
    for n in b["notes"]:
        o.append(f"<p class='small'>{html.escape(n)}</p>")
    o.append("</body></html>")
    return "\n".join(o)


if __name__ == "__main__":
    open(sys.argv[1], "w").write(page())
