import html, sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from boards import BOARDS, check, line_holes, P

S = 8.0  # px per mm
NETC = {"GND": "#111", "3V3": "#d7191c", "+5V": "#f28e00", "SDA0": "#1a9641", "SCL0": "#0e8f8f", "SDA1": "#1a9641",
        "SCL1": "#0e8f8f", "ESC": "#d4b000", "ESC5": "#d4b000", "RUD": "#2b6cd4", "RUD5": "#2b6cd4", "VBAT": "#8b0000",
        "VB_N": "#c2185b", "LK_N": "#7b3fa0", "PROBE": "#7b3fa0", "K_N": "#6a1b9a", "OE": "#777"}


def col(n):
    return NETC.get(n, "#888")


def geom(b, bottom=False):
    mx = (b["w"] - (b["nx"] - 1) * P) / 2
    my = (b["h"] - (b["ny"] - 1) * P) / 2
    mir = b.get("mirror", False)

    def hx(x):
        X = (b["nx"] + 1 - x) if mir else x
        if bottom:
            X = b["nx"] + 1 - X
        return (mx + (X - 1) * P) * S

    def hy(y):
        return (my + (y - 1) * P) * S
    return hx, hy, mx, my


def label_x(b, x, bottom=False):
    X = (b["nx"] + 1 - x) if b.get("mirror") else x
    return X


def svg_board(b, bottom=False):
    hx, hy, mx, my = geom(b, bottom)
    W, H = b["w"] * S, b["h"] * S
    pad = 34; padb = 72
    o = []
    o.append(f'<svg viewBox="{-pad} {-pad} {W + 2*pad} {H + pad + padb}" width="{W + 2*pad}" height="{H + pad + padb}" xmlns="http://www.w3.org/2000/svg" font-family="Inter,Arial" >')
    o.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="6" fill="#2f7d5b" stroke="#1d5139" stroke-width="2"/>')
    # corner mounting holes (approx. 2 mm from the edges — measure)
    for cx, cy in [(2.2, 2.2), (b["w"] - 2.2, 2.2), (2.2, b["h"] - 2.2), (b["w"] - 2.2, b["h"] - 2.2)]:
        o.append(f'<circle cx="{cx*S}" cy="{cy*S}" r="{1.1*S}" fill="#fff" stroke="#c00" stroke-width="1.5"/>')
    # column / row numbers
    for x in range(1, b["nx"] + 1):
        lx = label_x(b, x, bottom)
        X = hx(x)
        o.append(f'<text x="{X}" y="-8" font-size="10" text-anchor="middle" fill="#444">{lx}</text>')
        o.append(f'<text x="{X}" y="{H + 18}" font-size="10" text-anchor="middle" fill="#444">{lx}</text>')
    for y in range(1, b["ny"] + 1):
        o.append(f'<text x="-10" y="{hy(y) + 3.5}" font-size="10" text-anchor="end" fill="#444">{y}</text>')
        o.append(f'<text x="{W + 10}" y="{hy(y) + 3.5}" font-size="10" fill="#444">{y}</text>')
    # keep-out areas
    for k in b["keep"]:
        x0, x1 = sorted([hx(k["x0"]), hx(k["x1"])])
        o.append(f'<rect x="{x0 - 9}" y="{hy(k["y0"]) - 9}" width="{x1 - x0 + 18}" height="{hy(k["y1"]) - hy(k["y0"]) + 18}" fill="none" stroke="#ffd54f" stroke-dasharray="5 4" stroke-width="2"/>')
        o.append(f'<rect x="{x0 - 6}" y="{hy(k["y0"]) + (hy(k["y1"]) - hy(k["y0"]))/2 - 8}" width="{x1 - x0 + 12}" height="15" fill="#3e2f00" opacity="0.85"/>')
        o.append(f'<text x="{(x0 + x1)/2}" y="{hy(k["y0"]) + (hy(k["y1"]) - hy(k["y0"]))/2 + 4}" font-size="10" text-anchor="middle" fill="#ffe082">{html.escape(k["label"][:44])}</text>')
    # holes
    for x in range(1, b["nx"] + 1):
        for y in range(1, b["ny"] + 1):
            o.append(f'<circle cx="{hx(x)}" cy="{hy(y)}" r="{0.85*S}" fill="#d9d4c7" stroke="#9c9789" stroke-width="0.8"/><circle cx="{hx(x)}" cy="{hy(y)}" r="{0.45*S}" fill="#2a2a2a"/>')
    # module outline (DevKit / BNO055) on top view
    ol = b.get("outline")
    if ol and not bottom:
        xa, xb = sorted([hx(ol["x0"]), hx(ol["x1"])])
        if ol["kind"] == "devkit":
            # DevKit board 55.88 x 28.09 around the pin rows
            ext = 1.27 * S
            o.append(f'<rect x="{xa - ext}" y="{hy(ol["y0"]) - 1.35*S}" width="{xb - xa + 2*ext}" height="{hy(ol["y1"]) - hy(ol["y0"]) + 2.7*S}" fill="#d32f2f" fill-opacity="0.16" stroke="#d32f2f" stroke-width="2" stroke-dasharray="8 4"/>')
            ax = xb + ext
            o.append(f'<rect x="{ax - 2}" y="{hy(3)}" width="{6*S}" height="{hy(9) - hy(3)}" fill="#ffcdd2" fill-opacity="0.5" stroke="#d32f2f" stroke-dasharray="3 3"/>')
            o.append(f'<text x="{ax + 3*S}" y="{hy(6)}" font-size="11" text-anchor="middle" fill="#fff" transform="rotate(90 {ax + 3*S} {hy(6)})">ANTENNA → over the edge</text>')
            o.append(f'<text x="{xa + 16}" y="{hy(6)}" font-size="11" text-anchor="middle" fill="#fff" font-weight="700" transform="rotate(-90 {xa + 16} {hy(6)})">USB-C end · 15 mm free</text>')
            o.append(f'<text x="{(xa + xb)/2}" y="{hy(6) + 4}" font-size="14" text-anchor="middle" fill="#fff" font-weight="700">ESP32-S3-DevKit-Lipo (plugs in on top)</text>')
            o.append(f'<text x="{(xa + xb)/2}" y="{hy(6) + 22}" font-size="11" text-anchor="middle" fill="#fff">under it: only bottom-side wires, nothing taller than 2 mm on top</text>')
        if ol["kind"] == "bno":
            xa2 = min(hx(ol["x0"]), hx(ol["x1"])); xb2 = max(hx(ol["x0"]), hx(ol["x1"]))
            o.append(f'<rect x="{xa2}" y="{hy(ol["y0"])}" width="{xb2 - xa2}" height="{hy(ol["y1"]) - hy(ol["y0"])}" fill="#1565c0" fill-opacity="0.18" stroke="#90caf9" stroke-width="2" stroke-dasharray="8 4"/>')
            o.append(f'<text x="{(xa2 + xb2)/2}" y="{hy(5.3)}" font-size="12" text-anchor="middle" fill="#fff" font-weight="700">Adafruit BNO055 #2472</text>')
            o.append(f'<text x="{(xa2 + xb2)/2}" y="{hy(6.3)}" font-size="10" text-anchor="middle" fill="#fff">Vin = 3V3 only · 26.7 × 20.3</text>')
            ar = hx(14) if not bottom else hx(14)
            o.append(f'<path d="M {hx(14)} {hy(8.5)} L {hx(14)} {hy(1.6)}" stroke="#fff" stroke-width="4" marker-end="url(#arr)"/>')
            o.append(f'<text x="{hx(14) + 10}" y="{hy(4)}" font-size="13" fill="#fff" font-weight="700">BOW</text>')
    o.append('<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#fff"/></marker></defs>')
    # bridges (bare tinned wire on the bottom)
    for a, c, net in b["bridges"]:
        x1, y1, x2, y2 = hx(a[0]), hy(a[1]), hx(c[0]), hy(c[1])
        dash = '' if bottom else ' stroke-dasharray="1 0"'
        o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#cfd8dc" stroke-width="{1.5*S if bottom else 0.9*S}" stroke-linecap="round" opacity="{0.95 if bottom else 0.55}"/>')
        o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col(net)}" stroke-width="2" stroke-linecap="round" opacity="0.9"/>')
    # insulated wires on the bottom
    for i, (a, c, net) in enumerate(b["wires"]):
        x1, y1, x2, y2 = hx(a[0]), hy(a[1]), hx(c[0]), hy(c[1])
        mx_, my_ = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        L = max((dx*dx + dy*dy) ** 0.5, 1)
        k = 10 + (i % 3) * 5
        cx_, cy_ = mx_ - dy / L * k, my_ + dx / L * k
        op = 0.95 if bottom else 0.6
        o.append(f'<path d="M {x1} {y1} Q {cx_} {cy_} {x2} {y2}" fill="none" stroke="{col(net)}" stroke-width="{3.2 if bottom else 2.2}" stroke-dasharray="{"" if bottom else "6 3"}" opacity="{op}"/>')
    # parts
    for p in b["parts"]:
        pins = p["pins"]
        xs = [hx(x) for x, y, *_ in pins]; ys = [hy(y) for x, y, *_ in pins]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        k = p["kind"]
        if not bottom:
            if k == "fheader":
                o.append(f'<rect x="{x0 - 1.27*S}" y="{y0 - 1.27*S}" width="{x1 - x0 + 2.54*S}" height="{y1 - y0 + 2.54*S}" fill="#222" opacity="0.85" rx="2"/>')
            elif k == "jst":
                o.append(f'<rect x="{x0 - 2.45*S}" y="{y0 - 1.0*S}" width="{x1 - x0 + 4.9*S}" height="{y1 - y0 + 2.3*S}" fill="#f5f1e6" stroke="#8d8577" rx="2" opacity="0.95"/>')
            elif k == "servo":
                o.append(f'<rect x="{x0 - 1.27*S}" y="{y0 - 1.27*S}" width="{x1 - x0 + 2.54*S}" height="{y1 - y0 + 2.54*S}" fill="#111" rx="2" opacity="0.9"/>')
            elif k == "dip":
                o.append(f'<rect x="{x0 - 1.6*S}" y="{y0 - 1.6*S}" width="{x1 - x0 + 3.2*S}" height="{y1 - y0 + 3.2*S}" fill="#333" stroke="#000" rx="2" opacity="0.92"/>')
                o.append(f'<circle cx="{x0 - 0.9*S}" cy="{(y0+y1)/2}" r="{0.9*S}" fill="#2f7d5b"/>')
            elif k == "res_up":
                (ax, ay), (bx, by) = (xs[0], ys[0]), (xs[1], ys[1])
                o.append(f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="#bbb" stroke-width="2"/>')
                o.append(f'<circle cx="{ax}" cy="{ay}" r="{1.25*S}" fill="#c8a165" stroke="#6d4c22" stroke-width="1.5"/>')
            elif k == "cap":
                o.append(f'<line x1="{xs[0]}" y1="{ys[0]}" x2="{xs[1]}" y2="{ys[1]}" stroke="#bbb" stroke-width="2"/>')
                o.append(f'<ellipse cx="{(xs[0]+xs[1])/2}" cy="{(ys[0]+ys[1])/2}" rx="{1.4*S}" ry="{1.4*S}" fill="#f2c94c" stroke="#8a6d00"/>')
            elif k == "elko":
                o.append(f'<circle cx="{(xs[0]+xs[1])/2}" cy="{(ys[0]+ys[1])/2}" r="{3.1*S}" fill="#1e3a8a" stroke="#0b1d4d" opacity="0.92"/>')
                o.append(f'<text x="{(xs[0]+xs[1])/2}" y="{(ys[0]+ys[1])/2 + 4}" font-size="10" text-anchor="middle" fill="#fff">+ −</text>')
        for (x, y, net, nm) in pins:
            X, Y = hx(x), hy(y)
            o.append(f'<circle cx="{X}" cy="{Y}" r="{0.75*S}" fill="{col(net)}" stroke="#fff" stroke-width="1.2"/>')
        # labels
        if k in ("fheader",) and not bottom:
            for (x, y, net, nm) in pins:
                if not net.startswith(("x1_", "x2_")) and nm:
                    dy = -14 if y == min(yy for _, yy, *_ in pins) and p["ref"] in ("H2", "JP1") else 18
                    if p["ref"] == "H1":
                        dy = -12
                    if p["ref"] == "H2":
                        dy = 20
                    if p["ref"] == "JP2":
                        dy = -12
                    ty = hy(y) + (14 if dy > 0 else -14)
                    anc = "end" if dy > 0 else "start"
                    if p["ref"] in ("JP1",):
                        ty = hy(y) - 12; anc = "start"
                    o.append(f'<text x="{hx(x) + 3}" y="{ty}" font-size="8.5" text-anchor="{anc}" fill="#fff" font-weight="700" transform="rotate(-90 {hx(x) + 3} {ty})">{html.escape(nm)}</text>')
        if k in ("jst", "servo", "pads") and not bottom:
            for (x, y, net, nm) in pins:
                if k == "servo" or k == "pads":
                    side = 1 if k == "servo" else (-1 if hx(x) > W / 2 else 1)
                    tx = hx(x) + (16 if (k == "servo") else (-14 if hx(x) > W/2 else 14))
                    anchor = "start" if tx > hx(x) else "end"
                    o.append(f'<text x="{tx}" y="{hy(y) + 3.5}" font-size="9" text-anchor="{anchor}" fill="#fff">{html.escape(nm)}</text>')
                else:
                    o.append(f'<text x="{hx(x)}" y="{hy(y) + (13 if y > b["ny"]/2 else -9)}" font-size="7" text-anchor="middle" fill="#3e3a33" font-weight="700">{html.escape(nm[:4])}</text>')
        if not bottom and k != "fheader":
            if k == "dip":
                for (x, y, net, nm) in pins:
                    o.append(f'<text x="{hx(x)}" y="{hy(y) + (-9 if y == max(yy for _, yy, *_ in pins) else 15)}" font-size="8" text-anchor="middle" fill="#fff">{html.escape(nm.split()[0])}</text>')
            lx = (x0 + x1) / 2
            if k in ("res_up", "cap"):
                o.append(f'<text x="{xs[0]}" y="{ys[0] - 12}" font-size="9" text-anchor="middle" fill="#fff" font-weight="700">{p["ref"]}</text>')
            elif k == "elko":
                o.append(f'<text x="{lx}" y="{y0 - 30}" font-size="9" text-anchor="middle" fill="#fff" font-weight="700">C3</text>')
            elif k == "jst":
                js = sorted([q for q in b["parts"] if q["kind"] == "jst"], key=lambda q: min(hx(t[0]) for t in q["pins"]))
                jidx = [q["ref"] for q in js].index(p["ref"])
                ly = (H + 30 + 11 * (jidx % 3)) if y0 > H / 2 else (y0 - 22 if y0 > 30 else -20)
                o.append(f'<text x="{lx}" y="{ly}" font-size="9.5" text-anchor="middle" fill="#00332a" font-weight="700">{html.escape(p["label"] if y0 < H/2 else p["label"])}</text>')
            elif k == "servo":
                o.append(f'<text x="{lx}" y="{y0 - 14}" font-size="10" text-anchor="middle" fill="#fff" font-weight="700">{html.escape(p["label"])}</text>')
            elif k == "dip":
                o.append(f'<text x="{lx}" y="{(y0+y1)/2 + 4}" font-size="11" text-anchor="middle" fill="#fff" font-weight="700">U6 74HCT125</text>')
    side = "BOTTOM (solder side) — board turned over left↔right" if bottom else "TOP (component side)"
    o.append(f'<text x="{W/2}" y="{H + 68}" font-size="12" text-anchor="middle" fill="#333" font-weight="700">{side}</text>')
    o.append('</svg>')
    return "\n".join(o)


def netlist(b):
    import collections
    rows = collections.defaultdict(list)
    for p in b["parts"]:
        for (x, y, net, nm) in p["pins"]:
            if net.startswith(("x1_", "x2_")) or net.startswith("n") and net not in ("nc_j2",):
                continue
            rows[net].append(f'{p["ref"]}{("." + nm) if nm else ""} ({label_x(b, x)},{y})')
    out = ['<table class="nl"><tr><th>net</th><th>pins (column,row as printed on the drawing)</th></tr>']
    for net in sorted(rows):
        if net in ("nc11", "nc8", "nc_j2"):
            continue
        out.append(f'<tr><td><span class="sw" style="background:{col(net)}"></span>{html.escape(net)}</td><td>{html.escape(" · ".join(rows[net]))}</td></tr>')
    out.append("</table>")
    return "\n".join(out)


def page():
    for b in BOARDS:
        e, _ = check(b)
        assert not e, e
    css = """body{font-family:Inter,Arial,sans-serif;margin:24px;color:#1b1b1b;background:#fff;width:2050px}
h1{font-size:26px;margin:0 0 6px} h2{font-size:19px;margin:26px 0 6px} p,li{font-size:13.5px;line-height:1.45}
.row{display:flex;gap:26px;align-items:flex-start;flex-wrap:wrap}.card{border:1px solid #ddd;border-radius:10px;padding:12px 14px;background:#fafafa}
table.nl{border-collapse:collapse;font-size:11.5px;max-width:620px} table.nl td,table.nl th{border-bottom:1px solid #e3e3e3;padding:3px 6px;text-align:left;vertical-align:top}
.sw{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.leg span{display:inline-block;margin-right:16px;font-size:12.5px}.small{font-size:12px;color:#555}"""
    o = [f"<!doctype html><html><head><meta charset='utf-8'><title>AR-Mini C072 perfboards</title><style>{css}</style></head><body>"]
    o.append("<h1>AR-Mini · C031 / C072 · perfboards that replace the two breadboards (04.11.2026)</h1>")
    o.append("<p>Same nets as the FINAL 2 breadboard (31.10) and carrier rev B (SPEC.md), so firmware <b>remote_pool</b> runs unchanged. "
             "Grid 2.54 mm; numbers on the edges are the hole column / row. Every layout here is machine-checked: no hole carries two nets, every net is one connected piece. "
             "Corner holes in red: Ø and position <b>to measure</b> (≈2 mm from the edges on these boards).</p>")
    o.append("<p class='leg'><span><b>Grey thick line</b> = bare tinned wire on the bottom (bridge)</span><span><b>Coloured curve</b> = insulated wire on the bottom (Hailege 22 AWG jumper or silicone wire)</span>"
             "<span><b>Brown dot + line</b> = resistor standing upright (body on the dot)</span><span><b>Yellow</b> = 100 nF</span><span><b>Cream box</b> = JST-XH 2.54 header, latch to the board edge</span>"
             "<span><b>Black 3-pin</b> = male 2.54 header for a servo plug</span></p>")
    o.append("<p class='leg'>" + "".join(f"<span><span class='sw' style='background:{c}'></span>{n}</span>" for n, c in
             [("GND", "#111"), ("3V3", "#d7191c"), ("+5V (DevKit EXT1-21)", "#f28e00"), ("SDA", "#1a9641"), ("SCL", "#0e8f8f"), ("ESC GPIO1", "#d4b000"), ("rudder GPIO2", "#2b6cd4"), ("VBAT / divider", "#c2185b"), ("leak / KILL", "#7b3fa0")]) + "</p>")
    for b in BOARDS:
        o.append(f"<h2>{html.escape(b['title'])}</h2>")
        o.append("<div class='row'>")
        o.append(f"<div class='card'>{svg_board(b, False)}</div>")
        o.append(f"<div class='card'>{svg_board(b, True)}</div>")
        vals = " · ".join(f"{p['ref']} {p['label']}" for p in b["parts"] if p["kind"] in ("res_up", "cap", "elko"))
        o.append(f"<div class='card'><b>Netlist {b['name']}</b>" + (f"<p class='small'><b>Values:</b> {html.escape(vals)}</p>" if vals else "") + netlist(b))
        for n in b["notes"]:
            o.append(f"<p class='small'>{html.escape(n)}</p>")
        o.append("</div></div>")
    o.append("""<h2>Rules while soldering</h2><ul>
<li>P1 headers: plug both female 1×22 onto the DevKit first, then put the DevKit + headers into P1 and solder 2 corner pins of each header ("sandwich" — SPEC §2). Then all 44.</li>
<li>Column 1 of P1 stays empty except the EXT pins: that end is under the antenna. Nothing on top under the DevKit taller than 2 mm; all wiring there is on the bottom.</li>
<li>Never bridge a header pin to the hole next to it unless the drawing shows it (e.g. EXT1-19 and R5 are neighbours but different nets).</li>
<li>P2: socket notch to the LEFT (pin 1 = 1OE bottom-left). 3A / 4A / 3OE / 4OE go to +5V here (TI: unused inputs to VCC or GND, both fine); outputs 3 and 4 stay off because their OE is HIGH.</li>
<li>J2 ESC pin order follows SPEC J2 (S · NC · GND). The thruster's white 3-pin plug is still unmeasured: find the ≈5 V pin (signal) and the 0 V pin first, then build the adapter.</li>
<li>Before the DevKit goes in: meter beep test of every net in the table, and NO beep between 3V3, +5V and GND.</li></ul>
<p class='small'>Generated by boards.py / render_boards.py (container), project files enclosure-1104/src/. Claude · thread "Премести електрониката на перфоборд в здрави кутии".</p>""")
    o.append("</body></html>")
    return "\n".join(o)


if __name__ == "__main__":
    open(sys.argv[1], "w").write(page())
