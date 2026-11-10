"""AR-Mini C072 / C031 perfboard layouts (top view, component side).
Hole (x, y): x = column 1..nx along the long side, y = row 1..ny.
Parts sit on top; bridges (bare, bottom) and wires (insulated, bottom) carry the nets.
check() fails if a hole carries two nets or a net is not connected."""
import collections

P = 2.54


def board(name, w, h, nx, ny, title):
    return dict(name=name, w=w, h=h, nx=nx, ny=ny, title=title, parts=[], bridges=[], wires=[], keep=[], notes=[])


def part(b, ref, kind, pins, label="", body=None, value=""):
    # pins: list of (x, y, net, pinname)
    b["parts"].append(dict(ref=ref, kind=kind, pins=pins, label=label, body=body, value=value))


def bridge(b, a, c, net):
    b["bridges"].append((a, c, net))


def wire(b, a, c, net):
    b["wires"].append((a, c, net))


def line_holes(a, c):
    (x1, y1), (x2, y2) = a, c
    assert x1 == x2 or y1 == y2, (a, c)
    if x1 == x2:
        s = 1 if y2 >= y1 else -1
        return [(x1, y) for y in range(y1, y2 + s, s)]
    s = 1 if x2 >= x1 else -1
    return [(x, y1) for x in range(x1, x2 + s, s)]


# ---------------------------------------------------------------- P1 MCU board
# 50 x 70, 24 x 18 holes. Coordinates are written with the antenna at x = 1
# and mirrored at the end (X = 25 - x) so the antenna points right (to the
# starboard wall of the logic box) and the USB-C end points left (port wall,
# where the 5 V USB cable enters).
def make_p1():
    b = board("P1", 70, 50, 24, 18, "P1 · MCU board · perfboard 50 × 70 (24 × 18 holes)")
    ext1 = {1: "3V3", 2: "3V3", 4: "VB_N", 7: "LK_N", 12: "SDA1", 15: "SCL1", 20: "K_N", 21: "+5V", 22: "GND"}
    ext2 = {1: "GND", 4: "ESC", 5: "RUD", 16: "SDA0", 17: "SCL0", 22: "GND"}
    gp1 = {4: "GPIO4", 7: "GPIO7", 12: "GPIO8", 15: "GPIO9", 20: "GPIO14", 21: "+5V", 22: "GND", 1: "3V3", 2: "3V3"}
    gp2 = {1: "GND", 4: "GPIO1", 5: "GPIO2", 16: "GPIO48", 17: "GPIO47", 22: "GND"}
    part(b, "H2", "fheader", [(n, 1, ext2.get(n, f"x2_{n}"), gp2.get(n, str(n))) for n in range(1, 23)],
         "EXT2 · female 1×22", value="")
    part(b, "H1", "fheader", [(n, 11, ext1.get(n, f"x1_{n}"), gp1.get(n, str(n))) for n in range(1, 23)],
         "EXT1 · female 1×22")
    # VBAT divider on GPIO4 (FINAL 2 group 5: 100 k / 30 k, 12.6 V -> 2.9 V)
    bridge(b, (4, 11), (4, 13), "VB_N"); bridge(b, (3, 13), (5, 13), "VB_N")
    part(b, "R1", "res_up", [(3, 13, "VB_N", ""), (3, 14, "VBAT", "")], "100k")
    part(b, "R2", "res_up", [(4, 13, "VB_N", ""), (4, 14, "GND", "")], "30k")
    part(b, "C1", "cap", [(5, 13, "VB_N", ""), (5, 14, "GND", "")], "100n")
    bridge(b, (3, 14), (3, 17), "VBAT"); bridge(b, (4, 14), (5, 14), "GND"); bridge(b, (4, 14), (4, 18), "GND")
    part(b, "J1", "jst", [(3, 17, "VBAT", "VBAT"), (4, 17, "GND", "GND")], "J1 VBAT_SENSE")
    # leak probe on GPIO7 (group 12: 10 k pull-up, 4.7 k series)
    bridge(b, (7, 11), (7, 13), "LK_N"); bridge(b, (7, 13), (8, 13), "LK_N")
    part(b, "R3", "res_up", [(8, 13, "LK_N", ""), (8, 14, "3V3", "")], "10k")
    part(b, "R4", "res_up", [(7, 13, "LK_N", ""), (7, 14, "PROBE", "")], "4k7")
    bridge(b, (7, 14), (7, 17), "PROBE")
    part(b, "J9", "jst", [(7, 17, "PROBE", "LEAK"), (8, 17, "GND", "GND")], "J9 LEAK logic box")
    bridge(b, (8, 17), (8, 18), "GND")
    part(b, "J9B", "jst", [(16, 17, "PROBE", "LEAK"), (17, 17, "GND", "GND")], "J9b LEAK power box")
    bridge(b, (17, 17), (17, 18), "GND")
    wire(b, (7, 15), (16, 17), "PROBE")
    # I2C-1 to the MLX90640 (group 11)
    part(b, "J7", "jst", [(11, 17, "3V3", "3V3"), (12, 17, "GND", "GND"), (13, 17, "SDA1", "SDA1"), (14, 17, "SCL1", "SCL1")],
         "J7 THERM_POD I²C-1")
    bridge(b, (12, 17), (12, 18), "GND")
    wire(b, (12, 11), (13, 17), "SDA1"); wire(b, (15, 11), (14, 17), "SCL1")
    # KILL rocker on GPIO14 (group 4: 10 k pull-up, RUN = 3V3, KILL = GND)
    bridge(b, (20, 11), (20, 17), "K_N"); bridge(b, (19, 13), (20, 13), "K_N")
    part(b, "R5", "res_up", [(19, 13, "K_N", ""), (19, 14, "3V3", "")], "10k")
    bridge(b, (19, 14), (19, 17), "3V3")
    part(b, "J10", "jst", [(19, 17, "3V3", "RUN"), (20, 17, "K_N", "C"), (21, 17, "GND", "KILL")], "J10 KILL rocker")
    bridge(b, (21, 17), (21, 18), "GND")
    # 3V3 from EXT1-2 (x = 1 stays clear: antenna end)
    bridge(b, (2, 11), (2, 13), "3V3")
    wire(b, (2, 13), (8, 14), "3V3"); wire(b, (8, 14), (11, 17), "3V3"); wire(b, (11, 17), (19, 14), "3V3")
    wire(b, (19, 15), (24, 15), "3V3")
    # GND: bus along row 18 (under the connector bodies) + column 23 (past the USB end)
    bridge(b, (4, 18), (23, 18), "GND"); bridge(b, (23, 1), (23, 18), "GND")
    bridge(b, (22, 1), (23, 1), "GND"); bridge(b, (22, 11), (23, 11), "GND")
    # link pads to P2 (7 wires, ~40 mm, 22 AWG)
    link = [(12, "GND"), (13, "SDA0"), (14, "SCL0"), (15, "3V3"), (16, "+5V"), (17, "ESC"), (18, "RUD")]
    part(b, "L1", "pads", [(24, y, n, n) for y, n in link], "to P2")
    bridge(b, (23, 12), (24, 12), "GND")
    wire(b, (16, 1), (24, 13), "SDA0"); wire(b, (17, 1), (24, 14), "SCL0")
    wire(b, (21, 11), (24, 16), "+5V"); wire(b, (4, 1), (24, 17), "ESC"); wire(b, (5, 1), (24, 18), "RUD")
    b["mirror"] = True
    b["outline"] = dict(kind="devkit", x0=1, x1=22, y0=1, y1=11)
    return b


# ---------------------------------------------------------------- P2 I/O board
# 30 x 70, 24 x 10 holes: 74HCT125 buffer, ESC + rudder headers, I2C-0 hub, XIAO 5 V
def make_p2():
    b = board("P2", 70, 30, 24, 10, "P2 · I/O board · perfboard 30 × 70 (24 × 10 holes)")
    link = [(2, "GND"), (3, "SDA0"), (4, "SCL0"), (5, "3V3"), (6, "+5V"), (7, "ESC"), (8, "RUD")]
    part(b, "L2", "pads", [(1, y, n, n) for y, n in link], "from P1")
    dip_bot = ["GND", "ESC", "ESC5", "GND", "RUD", "RUD5", "GND"]        # pins 1..7
    dip_top = ["+5V", "+5V", "+5V", "nc11", "+5V", "+5V", "nc8"]       # pins 14..8
    names_b = ["1OE", "1A", "1Y", "2OE", "2A", "2Y", "GND"]
    names_t = ["VCC", "4OE", "4A", "4Y", "3OE", "3A", "3Y"]
    pins = [(5 + i, 8, dip_bot[i], f"{i+1} {names_b[i]}") for i in range(7)]
    pins += [(5 + i, 5, dip_top[i], f"{14-i} {names_t[i]}") for i in range(7)]
    part(b, "U6", "dip", pins, "74HCT125 in DIP-14 socket, notch left")
    bridge(b, (3, 4), (10, 4), "+5V")
    for x in (5, 6, 7, 9, 10):
        bridge(b, (x, 4), (x, 5), "+5V")
    bridge(b, (2, 9), (23, 9), "GND")
    for x in (5, 8, 11):
        bridge(b, (x, 8), (x, 9), "GND")
    wire(b, (1, 6), (3, 4), "+5V")
    wire(b, (1, 2), (3, 9), "GND")
    part(b, "C2", "cap", [(3, 5, "+5V", ""), (3, 8, "GND", "")], "100n")
    bridge(b, (3, 4), (3, 5), "+5V"); bridge(b, (3, 8), (3, 9), "GND")
    bridge(b, (1, 7), (2, 7), "ESC")
    part(b, "R6", "res_up", [(2, 7, "ESC", ""), (2, 8, "GND", "")], "10k")
    bridge(b, (2, 8), (2, 9), "GND")
    wire(b, (2, 7), (6, 8), "ESC"); wire(b, (1, 8), (9, 8), "RUD")
    part(b, "J2", "servo", [(16, 6, "ESC5", "S"), (16, 7, "nc_j2", "—"), (16, 8, "GND", "−")], "J2 ESC")
    part(b, "J3", "servo", [(19, 6, "RUD5", "S"), (19, 7, "+5V", "+"), (19, 8, "GND", "−")], "J3 rudder")
    bridge(b, (16, 8), (16, 9), "GND"); bridge(b, (19, 8), (19, 9), "GND")
    wire(b, (7, 8), (16, 6), "ESC5"); wire(b, (10, 8), (19, 6), "RUD5")
    wire(b, (10, 4), (19, 7), "+5V")
    part(b, "C3", "elko", [(22, 7, "+5V", "+"), (22, 8, "GND", "−")], "220µ 16V")
    bridge(b, (19, 7), (22, 7), "+5V"); bridge(b, (22, 8), (22, 9), "GND")
    # I2C-0 hub on the top edge
    part(b, "J12", "jst", [(3, 1, "GND", "GND"), (4, 1, "OE", "OE"), (5, 1, "SCL0", "SCL"), (6, 1, "SDA0", "SDA"), (7, 1, "3V3", "VCC")],
         "J12 PCA9685")
    part(b, "J11", "jst", [(9, 1, "3V3", "3V3"), (10, 1, "GND", "GND"), (11, 1, "SDA0", "SDA"), (12, 1, "SCL0", "SCL")], "J11 BNO055")
    part(b, "J6", "jst", [(14, 1, "3V3", "3V3"), (15, 1, "GND", "GND"), (16, 1, "SDA0", "SDA"), (17, 1, "SCL0", "SCL")], "J6 MLX90642")
    part(b, "J13", "jst", [(19, 1, "+5V", "5V"), (20, 1, "GND", "GND")], "J13 XIAO")
    for a, c, n in [((1, 2), (3, 1), "GND"), ((3, 1), (10, 1), "GND"), ((10, 1), (15, 1), "GND"), ((15, 1), (20, 1), "GND"),
                    ((1, 4), (5, 1), "SCL0"), ((5, 1), (12, 1), "SCL0"), ((12, 1), (17, 1), "SCL0"),
                    ((1, 3), (6, 1), "SDA0"), ((6, 1), (11, 1), "SDA0"), ((11, 1), (16, 1), "SDA0"),
                    ((1, 5), (7, 1), "3V3"), ((7, 1), (9, 1), "3V3"), ((9, 1), (14, 1), "3V3"),
                    ((19, 7), (19, 1), "+5V")]:
        wire(b, a, c, n)
    b["keep"].append(dict(x0=13, x1=23, y0=3, y1=5, label="reserved · C069 hardware KILL (Q2 S8050 + R10 1k + R24 10k → OE)"))
    b["single_ok"] = {"OE", "nc11", "nc8", "nc_j2"}
    return b


# ---------------------------------------------------------------- P4 IMU plate
def make_p4():
    b = board("P4", 70, 30, 24, 10, "P4 · BNO055 plate · perfboard 30 × 70 (24 × 10 holes)")
    jp1 = ["Vin", "3Vo", "GND", "SDA", "SCL", "RST"]
    nets = ["3V3", "n3vo", "GND", "SDA0", "SCL0", "nrst"]
    part(b, "JP1", "fheader", [(3 + i, 2, nets[i], jp1[i]) for i in range(6)], "female 1×6")
    jp2 = ["PS0", "PS1", "INT", "ADR"]
    part(b, "JP2", "fheader", [(4 + i, 9, f"n{jp2[i]}", jp2[i]) for i in range(4)], "female 1×4 (holds only)")
    part(b, "J14", "jst", [(20, 5, "3V3", "3V3"), (21, 5, "GND", "GND"), (22, 5, "SDA0", "SDA"), (23, 5, "SCL0", "SCL")], "J14 → P2 J11")
    wire(b, (3, 2), (20, 5), "3V3"); wire(b, (5, 2), (21, 5), "GND"); wire(b, (6, 2), (22, 5), "SDA0"); wire(b, (7, 2), (23, 5), "SCL0")
    b["outline"] = dict(kind="bno", x0=0.25, x1=10.75, y0=1.5, y1=9.5)
    b["single_ok"] = {"n3vo", "nrst", "nPS0", "nPS1", "nINT", "nADR"}
    return b


# ---------------------------------------------------------------- P5 leak comb
def make_p5():
    b = board("P5", 40, 20, 14, 8, "P5 · leak probe comb · half of a 20 × 80 strip (14 × 8 holes), ×2")
    bridge(b, (2, 2), (13, 2), "PROBE"); bridge(b, (2, 7), (13, 7), "GND")
    for x in range(2, 14, 2):
        bridge(b, (x, 2), (x, 5), "PROBE")
    for x in range(3, 14, 2):
        bridge(b, (x, 4), (x, 7), "GND")
    part(b, "W", "pads", [(1, 2, "PROBE", "LEAK"), (1, 7, "GND", "GND")], "2 wires")
    bridge(b, (1, 2), (2, 2), "PROBE"); bridge(b, (1, 7), (2, 7), "GND")
    b["notes"].append("Tin the comb fingers on the BOTTOM side; that side faces the box floor on 1 mm feet.")
    return b


def check(b):
    holes = collections.defaultdict(set)
    adj = collections.defaultdict(set)
    nx, ny = b["nx"], b["ny"]

    def put(h, net, what):
        x, y = h
        assert 1 <= x <= nx and 1 <= y <= ny, (b["name"], what, h)
        holes[h].add(net)

    pin_holes = collections.Counter()
    for p in b["parts"]:
        for (x, y, net, _) in p["pins"]:
            put((x, y), net, p["ref"]); pin_holes[(x, y)] += 1
    for a, c, net in b["bridges"]:
        hs = line_holes(a, c)
        for h in hs:
            put(h, net, "bridge")
        for u, v in zip(hs, hs[1:]):
            adj[u].add(v); adj[v].add(u)
    if b["name"] == "P1":  # DevKit pins of one net are joined inside the DevKit
        same = collections.defaultdict(list)
        for p in b["parts"]:
            if p["ref"] in ("H1", "H2"):
                for (x, y, net, _) in p["pins"]:
                    same[net].append((x, y))
        for hs in same.values():
            for u in hs[1:]:
                adj[hs[0]].add(u); adj[u].add(hs[0])
    for a, c, net in b["wires"]:
        put(a, net, "wire"); put(c, net, "wire")
        adj[a].add(c); adj[c].add(a)
    errs = [f"{b['name']} hole {h} nets {sorted(n)}" for h, n in holes.items() if len(n) > 1]
    errs += [f"{b['name']} hole {h} has {k} part pins" for h, k in pin_holes.items() if k > 1]
    # connectivity per net
    bynet = collections.defaultdict(set)
    for h, n in holes.items():
        for nn in n:
            bynet[nn].add(h)
    single_ok = b.get("single_ok", set())
    for net, hs in bynet.items():
        if net.startswith(("x1_", "x2_")) or net in single_ok:
            continue
        start = next(iter(hs)); seen = {start}; st = [start]
        while st:
            u = st.pop()
            for v in adj[u]:
                if v not in seen and v in hs:
                    seen.add(v); st.append(v)
        if seen != hs:
            errs.append(f"{b['name']} net {net} split: {sorted(hs - seen)} not reached from {start}")
    return errs, bynet


BOARDS = [make_p1(), make_p2(), make_p4(), make_p5()]

if __name__ == "__main__":
    bad = False
    for b in BOARDS:
        e, nets = check(b)
        print(b["name"], "nets:", len([n for n in nets if not n.startswith(('x1_', 'x2_'))]), "errors:", len(e))
        for x in e:
            print("  ", x); bad = True
    raise SystemExit(1 if bad else 0)
