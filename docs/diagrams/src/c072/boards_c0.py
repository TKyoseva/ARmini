"""AR-Mini C072 / C031 · ONE logic carrier on the Elimex EXP-14 perfboard (100 × 90, double-sided).
Replaces P1 + P2 + P4 of 04.11. Same nets as FINAL 2 (31.10) and carrier rev B (SPEC.md).

Grid: x = column 1..30 (port → starboard), y = row 1..36 (bow → stern), 2.54 mm.
Pad field of the EXP-14 ≈ 30 × 36(37); port margin to column 1 ≈ 4.7 mm, starboard margin after
column 30 ≈ 11.6 mm (blank strip: the WROOM antenna hangs over it). Mounting holes are NOT on the
grid: ≈ 76.0 apart across, ≈ 90.1 along (to be confirmed with the FIT template).

DevKit orientation (ESP32-S3-DevKitC-1 compatible): antenna → starboard, USB-C → port, components
up.  Then the row nearer the BOW is EXT1 (pins 1,2 = 3V3 at the antenna end) and the row nearer the
STERN is EXT2 (pin 1 = GND at the antenna end).  Verify with a meter before soldering (see notes).
"""
import collections
from boards import board, part, bridge, wire, line_holes, check as _check


def make_c0():
    b = board("C0", 90, 100, 30, 36, "C0 · logic carrier · Elimex EXP-14 100 × 90 (columns 1–30 × rows 1–36 used)")
    b["mx0"] = 4.7                 # port edge → column 1 (mm)   MEASURE
    b["my0"] = 5.5                 # bow edge → row 1 (mm)       MEASURE
    b["mholes"] = [(7.0, 6.3), (83.0, 6.3), (7.0, 96.4), (83.0, 96.4)]   # mm from the port/bow corner  MEASURE
    b["mhole_r"] = 3.8             # keep-out radius (screw head / standoff Ø 7.5)

    # ======================= BOW ZONE (rows 1–13) =======================
    # U2 PCA9685 on two female 1×6, 22 columns (55.88) apart; servo field + V+ terminal edge to the BOW
    pca = ["GND", "OE", "SCL", "SDA", "VCC", "V+"]
    netsA = ["GND", "OE", "SCL0", "SDA0", "3V3", "nVP"]
    part(b, "U2A", "fheader", [(4, 4 + i, netsA[i], pca[i]) for i in range(6)], "female 1×6 · PCA9685 port end (wired)")
    netsB = ["GND", "nOE2", "nSCL2", "nSDA2", "nVCC2", "nVP2"]
    part(b, "U2B", "fheader", [(26, 4 + i, netsB[i], pca[i]) for i in range(6)], "female 1×6 · PCA9685 starboard end (holds, GND only)")
    # GND: row 3 rail, column 9 down to EXT1-22, column 30 / 29 stubs for the starboard connectors
    bridge(b, (4, 4), (4, 3), "GND"); bridge(b, (26, 4), (26, 3), "GND")
    bridge(b, (4, 3), (30, 3), "GND")
    bridge(b, (9, 3), (9, 14), "GND")                                     # → EXT1-22
    # 3V3 rail row 11 (cols 11–28) fed from EXT1-2 (29,14) via (29,12) → (28,12) → (28,11)
    bridge(b, (29, 14), (29, 12), "3V3"); bridge(b, (29, 12), (28, 12), "3V3"); bridge(b, (28, 12), (28, 11), "3V3")
    bridge(b, (28, 11), (11, 11), "3V3")
    # I²C-0 rails rows 12 (SCL0) / 13 (SDA0), cols 11–27, fed from EXT2-17 / EXT2-16 by insulated wires under the DevKit
    bridge(b, (11, 12), (27, 12), "SCL0"); bridge(b, (11, 13), (27, 13), "SDA0")
    wire(b, (14, 24), (14, 12), "SCL0"); wire(b, (15, 24), (15, 13), "SDA0")
    # PCA9685 taps (insulated: they cross the GND column 9)
    wire(b, (11, 12), (4, 6), "SCL0"); wire(b, (11, 13), (4, 7), "SDA0"); wire(b, (11, 11), (4, 8), "3V3")

    # starboard bow connectors on column 30 (L2 gland): J13 XIAO 5 V, J7 MLX90640 on I²C-1
    part(b, "J13", "jst", [(30, 4, "GND", "GND"), (30, 5, "+5V", "5V")], "J13 XIAO 5 V")
    bridge(b, (30, 4), (30, 3), "GND")
    part(b, "J7", "jst", [(30, 9, "SCL1", "SCL"), (30, 10, "SDA1", "SDA"), (30, 11, "GND", "GND"), (30, 12, "3V3", "3V3")], "J7 MLX90640 I²C-1")
    bridge(b, (30, 11), (29, 11), "GND"); bridge(b, (29, 11), (29, 3), "GND")
    bridge(b, (30, 14), (30, 12), "3V3")                                   # EXT1-1 → J7 3V3
    wire(b, (19, 14), (30, 10), "SDA1"); wire(b, (16, 14), (30, 9), "SCL1")   # EXT1-12 GPIO8, EXT1-15 GPIO9
    # +5V: EXT1-21 (10,14) → (10,12) junction → J13 and the stern +5V rail
    bridge(b, (10, 14), (10, 12), "+5V")
    wire(b, (10, 13), (30, 5), "+5V"); wire(b, (10, 12), (10, 26), "+5V")

    # port bow: J1 VBAT_SENSE + divider R1 100k / R2 30k / C1 100n → GPIO4 (12 V stays in columns 2–4)
    part(b, "J1", "jst", [(2, 12, "VBAT", "VBAT"), (2, 13, "GND", "GND")], "J1 VBAT_SENSE")
    part(b, "R1", "res_up", [(4, 13, "VB_N", ""), (4, 12, "VBAT", "")], "100k")
    part(b, "R2", "res_up", [(5, 13, "VB_N", ""), (5, 12, "GND", "")], "30k")
    part(b, "C1", "cap", [(6, 13, "VB_N", ""), (6, 12, "GND", "")], "100n")
    bridge(b, (2, 12), (4, 12), "VBAT")
    bridge(b, (4, 13), (7, 13), "VB_N"); wire(b, (27, 14), (7, 13), "VB_N")    # EXT1-4 GPIO4
    bridge(b, (5, 12), (9, 12), "GND")
    bridge(b, (2, 13), (2, 25), "GND"); bridge(b, (2, 25), (3, 25), "GND")      # port margin, under the USB-C plug zone

    # ======================= DEVKIT (rows 14 / 24) =======================
    ext1 = {1: "3V3", 2: "3V3", 4: "VB_N", 7: "LK_N", 12: "SDA1", 15: "SCL1", 20: "K_N", 21: "+5V", 22: "GND"}
    ext2 = {1: "GND", 4: "ESC", 5: "RUD", 16: "SDA0", 17: "SCL0", 21: "GND", 22: "GND"}
    gp1 = {1: "3V3", 2: "3V3", 3: "RST", 4: "GPIO4", 7: "GPIO7", 12: "GPIO8", 15: "GPIO9", 20: "GPIO14", 21: "+5V", 22: "GND"}
    gp2 = {1: "GND", 2: "TX", 3: "RX", 4: "GPIO1", 5: "GPIO2", 16: "GPIO48", 17: "GPIO47", 21: "GND", 22: "GND"}
    part(b, "H1", "fheader", [(31 - n, 14, ext1.get(n, f"x1_{n}"), gp1.get(n, str(n))) for n in range(1, 23)], "EXT1 · female 1×22 (BOW row)")
    part(b, "H2", "fheader", [(31 - n, 24, ext2.get(n, f"x2_{n}"), gp2.get(n, str(n))) for n in range(1, 23)], "EXT2 · female 1×22 (STERN row)")

    # ======================= STERN ZONE (rows 25–36) =======================
    # GND: EXT2-22 → row 25 (3–9) → column 3 spine → row 36 bus; column 28 bus on the starboard side
    bridge(b, (9, 24), (9, 25), "GND"); bridge(b, (3, 25), (9, 25), "GND")
    bridge(b, (3, 25), (3, 34), "GND"); bridge(b, (3, 34), (4, 34), "GND"); bridge(b, (4, 34), (4, 36), "GND")
    bridge(b, (4, 36), (29, 36), "GND"); bridge(b, (29, 28), (29, 36), "GND")     # column 29 bus on the starboard side
    # 3V3 rail row 25 (12–29) fed from the bow rail by one insulated wire under the DevKit
    bridge(b, (12, 25), (29, 25), "3V3"); wire(b, (20, 11), (20, 25), "3V3")
    # +5V rail row 26 (4–10) over the DIP, stubs to pins 14/13/12/10/9; C2 100n across GND row 25 / +5V row 26
    bridge(b, (4, 26), (10, 26), "+5V")
    for x in (4, 5, 6, 8, 9):
        bridge(b, (x, 26), (x, 27), "+5V")
    part(b, "C2", "cap", [(7, 25, "GND", ""), (7, 26, "+5V", "")], "100n")

    # U6 74HCT125 in a DIP-14 socket, notch to PORT (pin 1 = (4,30) stern-port corner)
    dip_bot = ["GND", "ESC", "ESC5", "GND", "RUD", "RUD5", "GND"]
    dip_top = ["+5V", "+5V", "+5V", "nc11", "+5V", "+5V", "nc8"]
    names_b = ["1OE", "1A", "1Y", "2OE", "2A", "2Y", "GND"]
    names_t = ["VCC", "4OE", "4A", "4Y", "3OE", "3A", "3Y"]
    pins = [(4 + i, 30, dip_bot[i], f"{i+1} {names_b[i]}") for i in range(7)]
    pins += [(4 + i, 27, dip_top[i], f"{14-i} {names_t[i]}") for i in range(7)]
    part(b, "U6", "dip", pins, "74HCT125 in DIP-14 socket, notch to port")
    bridge(b, (4, 30), (3, 30), "GND"); bridge(b, (7, 30), (7, 36), "GND"); bridge(b, (10, 30), (10, 36), "GND")
    part(b, "R6", "res_up", [(5, 32, "ESC", ""), (5, 33, "GND", "")], "10k")
    bridge(b, (5, 30), (5, 32), "ESC"); bridge(b, (5, 33), (3, 33), "GND")
    wire(b, (27, 24), (5, 31), "ESC")                                          # EXT2-4 GPIO1 → 1A (+ R6 pull-down)
    wire(b, (26, 24), (8, 30), "RUD")                                          # EXT2-5 GPIO2 → 2A

    # port stern: J2 ESC (S · NC · GND) — L1 gland bundle from the power box
    part(b, "J2", "servo", [(2, 26, "ESC5", "S"), (2, 27, "nc_j2", "—"), (2, 28, "GND", "−")], "J2 ESC")
    bridge(b, (2, 28), (3, 28), "GND")
    wire(b, (6, 30), (2, 26), "ESC5")                                          # 1Y → ESC plug

    # starboard stern: J3 rudder (S · + · −) on column 30, C3 220 µ beside it, J6 MLX90642-D45 on I²C-0
    part(b, "J3", "servo", [(30, 26, "RUD5", "S"), (30, 27, "+5V", "+"), (30, 28, "GND", "−")], "J3 rudder")
    part(b, "C3", "elko", [(28, 27, "+5V", "+"), (28, 28, "GND", "−")], "220µ 16V")
    bridge(b, (28, 27), (30, 27), "+5V"); bridge(b, (28, 28), (30, 28), "GND")
    wire(b, (8, 26), (29, 27), "+5V")                                          # +5V rail → rudder
    wire(b, (9, 30), (30, 26), "RUD5")                                         # 2Y → rudder plug
    part(b, "J6", "jst", [(30, 30, "3V3", "3V3"), (30, 31, "GND", "GND"), (30, 32, "SDA0", "SDA"), (30, 33, "SCL0", "SCL")], "J6 MLX90642-D45 I²C-0")
    bridge(b, (30, 31), (29, 31), "GND")
    wire(b, (27, 25), (30, 30), "3V3")

    # U3 BNO055 on female 1×6 (JP1, column 18) + 1×4 (JP2, column 25, holds only); I²C-0 stubs under it feed J6
    jp1 = ["Vin", "3Vo", "GND", "SDA", "SCL", "RST"]; n1 = ["3V3", "n3vo", "GND", "SDA0", "SCL0", "nrst"]
    part(b, "JP1", "fheader", [(18, 28 + i, n1[i], jp1[i]) for i in range(6)], "female 1×6 · BNO055 JP1")
    jp2 = ["PS0", "PS1", "INT", "ADR"]
    part(b, "JP2", "fheader", [(25, 29 + i, f"n{jp2[i]}", jp2[i]) for i in range(4)], "female 1×4 · BNO055 JP2 (holds only)")
    bridge(b, (18, 25), (18, 28), "3V3")                                       # Vin = 3V3 ONLY
    bridge(b, (18, 30), (17, 30), "GND"); bridge(b, (17, 30), (17, 36), "GND")
    bridge(b, (18, 31), (24, 31), "SDA0"); bridge(b, (18, 32), (24, 32), "SCL0")
    wire(b, (18, 13), (21, 31), "SDA0"); wire(b, (19, 12), (21, 32), "SCL0")   # from the bow rails, under the DevKit
    wire(b, (24, 31), (30, 32), "SDA0"); wire(b, (24, 32), (30, 33), "SCL0")   # → J6

    # leak probe on GPIO7: R3 10k pull-up to 3V3, R4 4k7 series, two combs in parallel (J9b power box, J9 logic box)
    part(b, "R3", "res_up", [(15, 26, "LK_N", ""), (15, 25, "3V3", "")], "10k")
    part(b, "R4", "res_up", [(14, 26, "LK_N", ""), (14, 27, "PROBE", "")], "4k7")
    bridge(b, (13, 26), (15, 26), "LK_N"); wire(b, (24, 14), (13, 26), "LK_N")   # EXT1-7 GPIO7
    bridge(b, (14, 27), (14, 30), "PROBE")
    part(b, "J9B", "jst", [(5, 35, "PROBE", "LEAK"), (6, 35, "GND", "GND")], "J9b LEAK power box")
    part(b, "J9", "jst", [(8, 35, "PROBE", "LEAK"), (9, 35, "GND", "GND")], "J9 LEAK logic box")
    wire(b, (14, 29), (5, 35), "PROBE"); wire(b, (14, 30), (8, 35), "PROBE")
    bridge(b, (6, 35), (6, 36), "GND"); bridge(b, (9, 35), (9, 36), "GND")

    # KILL on GPIO14: R5 10k pull-up, J10 RUN · C · KILL (latching button or rocker between C and KILL)
    part(b, "R5", "res_up", [(13, 33, "K_N", ""), (13, 32, "3V3", "")], "10k")
    part(b, "J10", "jst", [(12, 35, "3V3", "RUN"), (13, 35, "K_N", "C"), (14, 35, "GND", "KILL")], "J10 KILL")
    bridge(b, (12, 25), (12, 35), "3V3"); bridge(b, (12, 32), (13, 32), "3V3")
    bridge(b, (13, 33), (13, 35), "K_N"); wire(b, (11, 14), (13, 34), "K_N")      # EXT1-20 GPIO14
    bridge(b, (14, 35), (14, 36), "GND")

    b["keep"].append(dict(x0=1, x1=3, y0=4, y1=10, label="C069 reserve: Q2 + R10/R24 → OE"))
    b["single_ok"] = {"OE", "nVP", "nOE2", "nSCL2", "nSDA2", "nVCC2", "nVP2", "nc11", "nc8", "nc_j2", "n3vo", "nrst",
                      "nPS0", "nPS1", "nINT", "nADR"}
    b["outline"] = dict(kind="devkit", x0=9, x1=30, y0=14, y1=24)
    b["outlines"] = [dict(kind="pca", x0=4, x1=26, y0=4, y1=9), dict(kind="bno", x0=18, x1=25, y0=28, y1=33)]
    b["notes"].append("Values: R1 100k · R2 30k · C1 100n (VBAT divider) · R3 10k · R4 4k7 (leak) · R5 10k (KILL) · R6 10k (ESC pull-down) · C2 100n · C3 220µ/16V.")
    return b


def check(b):
    """boards.check, with the DevKit's same-net pins (H1/H2) joined for any board name."""
    name = b["name"]
    b["name"] = "P1"          # boards.check joins H1/H2 same-net pins only for 'P1'
    try:
        errs, bynet = _check(b)
    finally:
        b["name"] = name
    return [e.replace("P1", name, 1) for e in errs], bynet


def hole_load(b):
    """What sits in each hole: part pins, bridge ends, bridge pass-throughs, wire ends."""
    load = collections.defaultdict(list)
    for p in b["parts"]:
        for (x, y, net, nm) in p["pins"]:
            load[(x, y)].append(f"pin {p['ref']}")
    for a, c, net in b["bridges"]:
        for h in line_holes(a, c):
            load[h].append("bridge-end" if h in (a, c) else "bridge-through")
    for a, c, net in b["wires"]:
        load[a].append("wire"); load[c].append("wire")
    return load


BOARDS = [make_c0()]

if __name__ == "__main__":
    bad = False
    for b in BOARDS:
        e, nets = check(b)
        print(b["name"], "nets:", len([n for n in nets if not n.startswith(('x1_', 'x2_'))]), "errors:", len(e))
        for x in e:
            print("  ", x); bad = True
        load = hole_load(b)
        pins = {(x, y): p["ref"] for p in b["parts"] for (x, y, *_) in p["pins"]}
        for h in sorted(load):
            items = [t for t in load[h] if t != "bridge-through"]
            if len(items) >= 3 and h in pins:
                print("  CROWDED pin hole", h, load[h]); bad = True
            elif len(items) >= 3:
                print("  busy hole (no pin)", h, load[h])
        # a bare bridge may pass through a part-pin hole only on the same net (check() already enforces the net)
        for a, c, net in b["bridges"]:
            for h in line_holes(a, c)[1:-1]:
                if h in pins:
                    print("  info: bridge", net, a, "→", c, "soldered to pin of", pins[h], "at", h)
        # holes inside the mounting-hole keep-outs must stay empty
        P_ = 2.54
        for (hx, hy) in b["mholes"]:
            for h in load:
                x = b["mx0"] + (h[0] - 1) * P_; y = b["my0"] + (h[1] - 1) * P_
                if (x - hx) ** 2 + (y - hy) ** 2 < (b["mhole_r"] + 0.9) ** 2:
                    print("  KEEP-OUT hit: hole", h, "near mounting hole", (hx, hy), load[h]); bad = True
    raise SystemExit(1 if bad else 0)
