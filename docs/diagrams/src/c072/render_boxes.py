import html, sys
S = 4.2
WALL = 4.0           # only used for gland drawing offsets
GR = 13.0            # M20x1.5 gland nut radius (≈ 26 mm across)
PIL_R, PIL_OFF = 5.5, 6.5  # corner lid-screw pillars inside (05.11 photos, ≈ 12 mm)
GAP = 40             # between the boxes
PB = dict(name="POWER BOX · LANUCN IP65 200 × 100 × 70 (BOM 155)", ox=0, oy=0, w=100, h=200, iw=94, ih=192)
LB = dict(name="LOGIC BOX · LANUCN IP65 150 × 110 × 70 (BOM 26)", ox=100 + GAP, oy=25, w=110, h=150, iw=106, ih=146, tx=5, ty=6, tw=96, th=134)
BEAMS = [42.5, 157.5]  # beam centres, 115 mm apart (beam_leg channels x 385 / 500)
BEAM_W = 20            # MEASURE

o = []


def X(b, x):
    return (b["ox"] + (b["w"] - b["iw"]) / 2 + x) * S


def Y(b, y):
    return (b["oy"] + (b["h"] - b["ih"]) / 2 + y) * S


def rect(b, x, y, w, h, fill, stroke="#333", label="", sub="", dash=None, fs=12, tc="#111", op=1):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o.append(f'<rect x="{X(b,x)}" y="{Y(b,y)}" width="{w*S}" height="{h*S}" rx="3" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="1.6"{d}/>')
    if label:
        cy = Y(b, y + h / 2) - (6 if sub else -4)
        o.append(f'<text x="{X(b, x + w/2)}" y="{cy}" font-size="{fs}" text-anchor="middle" fill="{tc}" font-weight="700">{html.escape(label)}</text>')
    if sub:
        for i, s in enumerate(sub.split("|")):
            o.append(f'<text x="{X(b, x + w/2)}" y="{Y(b, y + h/2) + 10 + 12*i}" font-size="10" text-anchor="middle" fill="{tc}">{html.escape(s)}</text>')


def holes(b, x, y, w, h, inset=2.2, r=1.6, col="#c62828"):
    for cx, cy in [(x + inset, y + inset), (x + w - inset, y + inset), (x + inset, y + h - inset), (x + w - inset, y + h - inset)]:
        o.append(f'<circle cx="{X(b,cx)}" cy="{Y(b,cy)}" r="{r*S}" fill="#fff" stroke="{col}" stroke-width="1.6"/>')


def gland(b, wall, pos, tag, txt, spare=False):
    iw, ih = b["iw"], b["ih"]
    if wall == "bow":
        cx, cy, tx, ty, anc = pos, -WALL / 2, pos, -WALL - 17, "middle"
    elif wall == "stern":
        cx, cy, tx, ty, anc = pos, ih + WALL / 2, pos, ih + WALL + 22, "middle"
    elif wall == "port":
        cx, cy, tx, ty, anc = -WALL / 2, pos, -WALL - 16, pos + 4, "end"
    else:
        cx, cy, tx, ty, anc = iw + WALL / 2, pos, iw + WALL + 16, pos + 4, "start"
    fill = "#9e9e9e" if spare else "#263238"
    o.append(f'<circle cx="{X(b,cx)}" cy="{Y(b,cy)}" r="{GR*S}" fill="{fill}" stroke="#000" stroke-width="1.2" fill-opacity="0.9"/>')
    o.append(f'<circle cx="{X(b,cx)}" cy="{Y(b,cy)}" r="{5*S}" fill="#eceff1"/>')
    o.append(f'<text x="{X(b,cx)}" y="{Y(b,cy) + 4}" font-size="9.5" text-anchor="middle" fill="#000" font-weight="800">{tag}</text>')
    if txt:
        o.append(f'<text x="{X(b,tx)}" y="{Y(b,ty)}" font-size="10.5" text-anchor="{anc}" fill="#263238">{html.escape(txt)}</text>')


def box(b):
    o.append(f'<rect x="{b["ox"]*S}" y="{b["oy"]*S}" width="{b["w"]*S}" height="{b["h"]*S}" rx="{6*S}" fill="#2b2b2b" stroke="#000" stroke-width="2"/>')
    iw, ih = b["iw"], b["ih"]
    o.append(f'<rect x="{X(b,0)}" y="{Y(b,0)}" width="{iw*S}" height="{ih*S}" rx="{3*S}" fill="#f4f4f0" stroke="#000" stroke-width="1"/>')
    for cx, cy in [(PIL_OFF, PIL_OFF), (iw - PIL_OFF, PIL_OFF), (PIL_OFF, ih - PIL_OFF), (iw - PIL_OFF, ih - PIL_OFF)]:
        o.append(f'<circle cx="{X(b,cx)}" cy="{Y(b,cy)}" r="{PIL_R*S}" fill="#555" stroke="#000"/><circle cx="{X(b,cx)}" cy="{Y(b,cy)}" r="{1.4*S}" fill="#ddd"/>')
    o.append(f'<text x="{(b["ox"] + b["w"]/2)*S}" y="{b["oy"]*S - 86}" font-size="15" text-anchor="middle" font-weight="800">{html.escape(b["name"])}</text>')
    o.append(f'<text x="{(b["ox"] + b["w"]/2)*S}" y="{b["oy"]*S - 70}" font-size="11.5" text-anchor="middle" fill="#555">inside ≈ {iw:.0f} × {ih:.0f} mm at the rim (ruler photos 05.11) · depth ≈ 55 mm base + lid (caliper to confirm)</text>')
    # printed tray outline
    rect(b, b.get("tx", 1), b.get("ty", 1), b.get("tw", iw - 2), b.get("th", ih - 2), "none", stroke="#1e88e5", dash="10 5")


def page():
    W = (PB["w"] + GAP + LB["w"]) * S
    H = PB["h"] * S
    padx, pady = 260, 150
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-padx} {-pady} {W + 2*padx + 90} {H + pady + 230}" width="{W + 2*padx + 90}" height="{H + pady + 230}" font-family="Inter,Arial">')
    # beams under the boxes
    for by in BEAMS:
        o.append(f'<rect x="{-60}" y="{(by - BEAM_W/2)*S}" width="{W + 120}" height="{BEAM_W*S}" fill="#c8b38a" opacity="0.55"/>')
        o.append(f'<text x="-64" y="{by*S + 4}" font-size="11" text-anchor="end" fill="#6d5a33">beam (under) · 115 mm pitch</text>')
    box(PB); box(LB)
    pb, lb = PB, LB
    # ---------------- power box contents (inner 92 x 192)
    rect(pb, 4, 10, 44, 58, "#455a64", label="QIQIAZI", sub="5 V 5 A buck|servo V+ (lift)|≈ 44 × 58 est.", tc="#fff")
    rect(pb, 51, 10, 37, 58, "#37474f", label="MZHOU", sub="12 → 5 V 3 A|USB-C cable|≈ 37 × 58 est.", tc="#fff")
    rect(pb, 3, 72, 33, 108, "#1565c0", label="LiPo 3S", sub="2200 mAh|108 × 33 × 23|strap + cradle", tc="#fff")
    rect(pb, 40, 74, 47, 105, "#212121", label="6-way fuse block", sub="F1 20 A thruster L|F2 15 A QIQIAZI|F3 10 A → thruster R (C065)|F4 5 A MZHOU + VBAT sense|≈ 105 × 47 est.", tc="#fff")
    rect(pb, 6, 148, 26, 26, "none", stroke="#e53935", dash="4 3", label="S1", sub="on the lid|Ø12 + boot", tc="#e53935")
    rect(pb, 8, 80, 22, 30, "none", stroke="#ffb300", dash="4 3", label="F30", sub="inline|+ XT60|on top", tc="#ffb300", fs=10)
    rect(pb, 44, 168, 40, 20, "none", stroke="#8e24aa", dash="3 3", label="P5 leak comb", sub="floor pocket", tc="#8e24aa", fs=10)
    rect(pb, 52, 74, 28, 9, "#9e9e9e", stroke="#333", label="", sub="")
    o.append(f'<text x="{X(pb,66)}" y="{Y(pb,80.5)}" font-size="9" text-anchor="middle" fill="#000" font-weight="700">GND bus</text>')
    gland(pb, "stern", 22, "P1", "thruster L lead")
    gland(pb, "starboard", 160, "P2", "")
    o.append(f'<text x="{X(pb,72)}" y="{Y(pb,192 + 9)}" font-size="10.5" text-anchor="middle" fill="#777">thruster R (C065): new hole later</text>')
    # floor features from the top-down photo 05.11 (caliper: 36.18 mm boss pitch)
    for bx in (29, 65):
        for by in (41.7, 77.9, 114.1, 150.3):
            o.append(f'<circle cx="{X(pb,bx)}" cy="{Y(pb,by)}" r="{3.5*S}" fill="none" stroke="#00acc1" stroke-width="2.4"/>')
    for bx, by in [(4, 59.8), (90, 59.8), (4, 132.2), (90, 132.2), (47, 5), (47, 187)]:
        o.append(f'<circle cx="{X(pb,bx)}" cy="{Y(pb,by)}" r="{3*S}" fill="none" stroke="#00acc1" stroke-width="1.8" stroke-dasharray="3 2"/>')
    for bx, by in [(15, 14.2), (79, 14.2), (15, 177.8), (79, 177.8)]:
        o.append(f'<circle cx="{X(pb,bx)}" cy="{Y(pb,by)}" r="{11*S}" fill="none" stroke="#00acc1" stroke-width="2" stroke-dasharray="6 3"/>')
    # ---------------- logic box contents (inner 102 x 142)
    rect(lb, 20, 7, 66, 15, "#00695c", label="PCA9685 on the printed wall (part of the tray)", sub="lift CH12 / CH13 · servo pins up", tc="#fff", fs=10.5)
    rect(lb, 18, 26, 70, 50, "#2e7d32", label="P1 · MCU board 50 × 70", sub="DevKit-Lipo on female headers|USB-C ←  · → antenna|VBAT · LEAK · KILL · I²C-1", tc="#fff")
    holes(lb, 18, 26, 70, 50)
    rect(lb, 18, 78, 70, 30, "#388e3c", label="P2 · I/O board 30 × 70", sub="74HCT125 · ESC · rudder · I²C-0 hub", tc="#fff")
    holes(lb, 18, 78, 70, 30)
    rect(lb, 18, 109.5, 70, 30, "#1565c0")
    o.append(f'<text x="{X(lb,40)}" y="{Y(lb,121)}" font-size="12" fill="#fff" font-weight="700" text-anchor="middle">P4 · BNO055 plate</text><text x="{X(lb,40)}" y="{Y(lb,132)}" font-size="10" fill="#fff" text-anchor="middle">BOW ↑ · flat · far from V+</text>')
    holes(lb, 18, 109.5, 70, 30)
    rect(lb, 88, 36, 6, 30, "#ffcdd2", stroke="#e53935", dash="3 2", op=0.9)
    o.append(f'<text x="{X(lb,97)}" y="{Y(lb,51)}" font-size="10" fill="#c62828" transform="rotate(90 {X(lb,97)} {Y(lb,51)})" text-anchor="middle">antenna · keep free</text>')
    rect(lb, 3, 33, 14, 20, "none", stroke="#f28e00", dash="3 2")
    o.append(f'<text x="{X(lb,10)}" y="{Y(lb,43)}" font-size="9" text-anchor="middle" fill="#e65100" transform="rotate(-90 {X(lb,10)} {Y(lb,43)})">USB-C plug</text>')
    rect(lb, 2, 80, 14, 26, "none", stroke="#e53935", dash="4 3")
    o.append(f'<text x="{X(lb,9)}" y="{Y(lb,93)}" font-size="9.5" fill="#c62828" font-weight="700" text-anchor="middle" transform="rotate(-90 {X(lb,9)} {Y(lb,93)})">KILL (lid)</text>')
    rect(lb, 46, 109, 14, 8, "none", stroke="#e1bee7", dash="3 3")
    o.append(f'<text x="{X(lb,70)}" y="{Y(lb,115)}" font-size="9" fill="#f3e5f5" text-anchor="middle" font-weight="700">P5 on floor</text>')
    # floor features (photo + caliper 63.80 mm) and the tray screws
    for bx, by in [(21, 50), (85, 50), (12, 73), (94, 73)]:
        o.append(f'<circle cx="{X(lb,bx)}" cy="{Y(lb,by)}" r="{3.5*S}" fill="#00acc1" fill-opacity="0.35" stroke="#00838f" stroke-width="2.4"/>')
    for bx, by in [(21, 63), (85, 63)]:
        o.append(f'<circle cx="{X(lb,bx)}" cy="{Y(lb,by)}" r="{3*S}" fill="none" stroke="#00acc1" stroke-width="1.8" stroke-dasharray="3 2"/>')
    for bx, by in [(19.5, 20), (86.5, 20), (19.5, 126), (86.5, 126)]:
        o.append(f'<circle cx="{X(lb,bx)}" cy="{Y(lb,by)}" r="{11*S}" fill="none" stroke="#00acc1" stroke-width="2" stroke-dasharray="6 3"/>')
    gland(lb, "port", 100, "L1", "")
    gland(lb, "starboard", 30, "L2", "lift A + B")
    gland(lb, "starboard", 73, "L3", "rudder MG90S")
    gland(lb, "starboard", 116, "L4", "MLX90640 + XIAO + D45")
    o.append(f'<text x="{X(lb,106 + 18)}" y="{Y(lb,150)}" font-size="10.5" fill="#777">starboard = the wall with the 3 knockout rings</text>')
    # crossing harness
    for (py, ly_, txt, colr) in [(160, 100, "H1 + H2 in one round bundle", "#f28e00")]:
        x1 = (PB["ox"] + PB["w"]) * S + GR * S - 10
        y1 = Y(PB, py)
        x2 = LB["ox"] * S - GR * S + 10
        y2 = Y(LB, ly_)
        o.append(f'<path d="M {x1} {y1} C {x1 + 30} {y1}, {x2 - 30} {y2}, {x2} {y2}" stroke="{colr}" stroke-width="6" fill="none" stroke-linecap="round"/>')
    o.append(f'<text x="{(PB["ox"] + PB["w"] + GAP/2)*S}" y="{Y(PB, 128)}" font-size="10.5" text-anchor="middle" fill="#e65100" font-weight="700">H1+H2</text>')
    # bow arrow and scale
    o.append(f'<path d="M {W + 150} 260 L {W + 150} 120" stroke="#000" stroke-width="4" marker-end="url(#a)"/><text x="{W + 150}" y="110" font-size="15" text-anchor="middle" font-weight="800">BOW</text>')
    o.append(f'<text x="{W + 150}" y="290" font-size="11" text-anchor="middle">top view</text><text x="{W + 150}" y="305" font-size="11" text-anchor="middle">lids off</text>')
    o.append(f'<line x1="{W + 100}" y1="{H}" x2="{W + 100 + 50*S}" y2="{H}" stroke="#000" stroke-width="3"/><text x="{W + 100 + 25*S}" y="{H - 8}" font-size="11" text-anchor="middle">50 mm</text>')
    o.append('<defs><marker id="a" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>')
    o.append(f'<text x="{-padx + 10}" y="{H + 140}" font-size="11.5" fill="#333">Dark circles = the M20×1.5 glands that came with the boxes (Ø20 hole = the red hole saw, seal range printed on the gland, ≈ 6–12 mm round). Cyan = floor bosses (filled = the 4 tray screws M3 × 20, dashed big = floor knockout rings, never open).</text><text x="{-padx + 10}" y="{H + 158}" font-size="11.5" fill="#333">Red rings = M2/M3 board holes → bosses with ruthex M3 (Ø4.0) or Ø1.7 pilots for M2 in the printed tray (blue dashed).</text>')
    o.append(f'<text x="{-padx + 10}" y="{H + 176}" font-size="11.5" fill="#333">Inner sizes are read from the 05.11 ruler photos (± 2 mm). Bucks and fuse block are still estimates; logic tray = project files enclosure-1104/cad/C072_logic_tray.scad (print the 0.8 mm FIT template first).</text>')
    o.append(f'<text x="{-padx + 10}" y="{H + 194}" font-size="11.5" fill="#333">Boxes sit side by side across both beams (beam_leg channels 115 mm apart), centred on the beams; heavier power box to port of the logic box; both on printed PETG saddles + 2 straps, no holes in the box floors. Trays screw into the floor bosses (no drilling, IP65 kept).</text>')
    o.append("</svg>")


page()
css = "body{font-family:Inter,Arial,sans-serif;margin:24px;background:#fff;color:#111;width:1500px}h1{font-size:24px;margin:0 0 4px}p{font-size:13.5px;max-width:1450px}table{border-collapse:collapse;font-size:12.5px}td,th{border-bottom:1px solid #ddd;padding:4px 8px;text-align:left;vertical-align:top}"
glands = [("P1", "power", "stern", "thruster L lead: red/black → F1 / GND bus, yellow/white → harness", "round cable, check Ø is inside the printed range"),
          ("P2", "power", "starboard", "H1 + H2: QIQIAZI 5 V/GND (18 AWG), MZHOU USB pair, VBAT sense, power-box leak pair, ESC S/G", "one round bundle: 10 mm heat-shrink over the wires, filled with neutral silicone over 25 mm"),
          ("L1", "logic", "port", "H1 + H2 arriving → PCA9685 V+, DevKit USB-C, P1 J1 / J9b, P2 J2", "same bundle"),
          ("L2", "logic", "starboard (knockout)", "lift A + B (2 × TD-8120MG extensions) → PCA9685 CH12 / CH13", "6 wires, heat-shrink + silicone to round"),
          ("L3", "logic", "starboard (knockout)", "rudder MG90S → P2 J3", "flat 3-wire: heat-shrink + silicone to ≥ 6 mm round"),
          ("L4", "logic", "starboard (knockout)", "MLX90640 (4) → P1 J7 · XIAO 5 V/GND (2) → P2 J13 · MLX90642-D45 (4) → P2 J6", "10 wires, one bundle")]
rows = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{html.escape(d)}</td><td>{html.escape(e)}</td></tr>" for a, b, c, d, e in glands)
doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>AR-Mini C072 boxes</title><style>{css}</style></head><body>
<h1>AR-Mini · C072 · electronics in two IP65 boxes (top view, rev 2 · 05.11.2026)</h1>
<p>Power box (battery, fuses, both bucks — everything that is 12 V or carries amps) and logic box (no inductors, no 12 V except the 100 µA VBAT sense wire → the BNO055 magnetometer stays clean). Wiring = FINAL 2 (31.10) + BNO055 (C066) + leak (C068); boards = carrier rev B nets (C031 → C032).</p>
{''.join(o)}
<h2 style="font-size:17px">Glands: 6 × M20 from the box kits (no PG7 to buy)</h2>
<table><tr><th>#</th><th>box</th><th>wall</th><th>what passes</th><th>note</th></tr>{rows}</table>
<p style="font-size:12px;color:#555">Hole Ø20 with the hole saw, centre ≥ 18 mm below the lid edge and ≥ 32 mm from the next gland (nut ≈ 26 mm). A loose wire bundle does not seal: make it round first. Every cable passes the gland as a BARE end; its connector is crimped inside afterwards (Preciva kit). Drawing generated by render_boxes.py, project files enclosure-1104/src/.</p>
</body></html>"""
open(sys.argv[1], "w").write(doc)
