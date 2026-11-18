#!/usr/bin/env python3
"""AR-Mini carrier rev B — the netlist written again from SPEC.md, NOT from gen.py (card C080).

This is the second independent route to the copper (copper rule: a number becomes copper only after two
independent routes). Every entry cites the SPEC section it comes from. Where SPEC is silent, the entry says
where the value comes from instead (datasheet, module pinout), or it is left out and the comparison
(compare_nets.py) reports the PCB item as "PCB only, not in SPEC" for a human to decide.

PARTS maps reference → (value, {pin: net}); values use the board's short names (LED colours, 1 %, DNP live in the
comments and in DNP below); a net of None = no connection on purpose (gets a no-connect flag).
"""

GND, P3, P5 = "GND", "+3V3", "+5V"

PARTS = {}


def part(ref, value, pins):
    assert ref not in PARTS, ref
    PARTS[ref] = (value, dict(pins))


# --- U1 DevKit-Lipo, two 1×22 female headers (SPEC §2, §3). EXT1 = U1_1, EXT2 = U1_2. Pin 1 at the antenna end.
ext1 = {i: None for i in range(1, 23)}
ext1.update({1: P3, 2: P3,          # §3 "EXT1 1, 2 · 3V3 out"
             4: "VBAT_S",           # §3 GPIO4 EXT1 4
             7: "LEAK",             # §3 GPIO7 EXT1 7
             10: "SRV_TX",          # §3 GPIO17 EXT1 10
             11: "SRV_RX",          # §3 GPIO18 EXT1 11
             12: "SDA1",            # §3 GPIO8 EXT1 12
             15: "SCL1",            # §3 GPIO9 EXT1 15
             16: "BTS_IS_R",        # §3 GPIO10 EXT1 16
             17: "BTS_IS_L",        # §3 GPIO11 EXT1 17
             20: "KILL",            # §3 GPIO14 EXT1 20
             21: P5,                # §3 EXT1 21 +5V out
             22: GND})              # §3 EXT1 22 GND
# GPIO15/16 → JP3 (§3 "bring to a 1×4 pin header JP3"): SPEC names the GPIOs but not the EXT1 pins.
# Olimex ESP32-S3-DevKit-Lipo EXT1 order (same as DevKitC-1): pin 8 = GPIO15, pin 9 = GPIO16.
ext1.update({8: "PI_TX", 9: "PI_RX"})
part("U1_1", "DevKit_EXT1", ext1)

ext2 = {i: None for i in range(1, 23)}
ext2.update({1: GND, 22: GND,       # §3 "EXT2 1, 22 GND"
             4: "ESC_L",            # §3 GPIO1 EXT2 4
             5: "ESC_R",            # §3 GPIO2 EXT2 5
             9: "BTS_L_RPWM",       # §3 GPIO39 EXT2 9
             8: "BTS_L_LPWM",       # §3 GPIO40 EXT2 8
             7: "BTS_R_RPWM",       # §3 GPIO41 EXT2 7
             6: "BTS_R_LPWM",       # §3 GPIO42 EXT2 6
             16: "SDA0",            # §3 GPIO48 EXT2 16
             17: "SCL0"})           # §3 GPIO47 EXT2 17
part("U1_2", "DevKit_EXT2", ext2)

# --- U2 PCA9685 module, two 1×6 rows, order from the V+ terminal edge: GND, OE, SCL, SDA, VCC, V+ (SPEC §4).
# "Only I2C, VCC (3V3), GND and OE go to the carrier. V+ ... not through the carrier." One row is wired (U2_1),
# the other row is mechanical (U2_2).
part("U2_1", "PCA9685_row", {1: GND, 2: "OE", 3: "SCL0", 4: "SDA0", 5: P3, 6: None})
part("U2_2", "PCA9685_row", {i: None for i in range(1, 7)})

# --- U3 Adafruit BNO055 JP1 1×6: Vin, 3Vo, GND, SDA, SCL, RST (SPEC §4). Vin = +3V3 only; 3Vo, RST unconnected.
# JP2 1×4 (PS0, PS1, INT, ADR) "unconnected, mechanical" → pins B1–B4 (footprint pad names).
part("U3", "BNO055", {1: P3, 2: None, 3: GND, 4: "SDA0", 5: "SCL0", 6: None,
                            "B1": None, "B2": None, "B3": None, "B4": None})

# --- U6 74AHCT125 DIP-14, DNP by default (SPEC §8.1): powered from +5V, inputs GPIO1/2, outputs → JP side B.
# Pinout and unused-gate handling: TI SN74AHCT125 datasheet (1OE 1, 1A 2, 1Y 3, 2OE 4, 2A 5, 2Y 6, GND 7,
# 3Y 8, 3A 9, 3OE 10, 4Y 11, 4A 12, 4OE 13, VCC 14). OE is active low → OE1/OE2 to GND; unused gates:
# inputs to GND, OE high (output off), outputs open.
part("U6", "74AHCT125", {1: GND, 2: "ESC_L", 3: "ESC_L_5V", 4: GND, 5: "ESC_R", 6: "ESC_R_5V", 7: GND,
                         8: None, 9: GND, 10: P5, 11: None, 12: GND, 13: P5, 14: P5})

# --- JP1 / JP2 3-pad solder jumpers (SPEC §8.1): centre C = J2/J3 signal, A = GPIO direct, B = U6 output.
# Default A bridged → C and A are one net until the trace is cut.
part("JP1", "SJ", {"A": "ESC_L", "C": "ESC_L", "B": "ESC_L_5V"})
part("JP2", "SJ", {"A": "ESC_R", "C": "ESC_R", "B": "ESC_R_5V"})

# --- Connectors (SPEC §5)
part("J1", "VBAT_SENSE", {1: "VBAT", 2: GND})
part("J2", "ESC_L", {1: GND, 2: None, 3: "ESC_L"})
part("J3", "ESC_R", {1: GND, 2: None, 3: "ESC_R"})
# §5: J4/J5 "1 RPWM, 2 LPWM, 3 EN, 4 VCC (+3V3), 5 IS, 6 GND". The IS pin reaches the GPIO through R16/R18 (§3).
# NOTE §3 table says "J4 pin 6" / "J5 pin 6" for IS — contradicts §5 (pin 6 = GND, and "GND never in the middle"
# is satisfied either way). §5 is the connector table → used here; the §3 line is a SPEC typo (reported).
part("J4", "BTS_L", {1: "BTS_L_RPWM", 2: "BTS_L_LPWM", 3: "EN", 4: P3, 5: "IS_L_MOD", 6: GND})
part("J5", "BTS_R", {1: "BTS_R_RPWM", 2: "BTS_R_LPWM", 3: "EN", 4: P3, 5: "IS_R_MOD", 6: GND})
part("J6", "THERM_FWD", {1: P3, 2: GND, 3: "SDA0", 4: "SCL0"})
part("J7", "THERM_POD", {1: P3, 2: GND, 3: "SDA1", 4: "SCL1"})
part("J8", "SERVO_BUS", {1: "SRV_TX", 2: "SRV_RX", 3: GND, 4: None})
# §5 J9 "1 LEAK, 2 GND"; §3 "the probe pulls to GND through R21 4.7 k" → the connector pin is the probe side of R21.
part("J9", "LEAK", {1: "LEAK_P", 2: GND})
part("J10", "ROCKER", {1: P5, 2: "EN", 3: GND})          # §5 / §6
part("J11", "IMU_EXT", {1: P3, 2: GND, 3: "SDA0", 4: "SCL0"})
part("JP3", "PI_UART", {1: GND, 2: "PI_TX", 3: "PI_RX", 4: P5})

# --- Discretes (SPEC §3, §6, §7). Two-pin passives: orientation is not a design fact; compare ignores it.
part("R1", "100k", {1: "VBAT", 2: "VBAT_S"})          # §3 divider
part("R2", "33k", {1: "VBAT_S", 2: GND})
part("C5", "100nF", {1: "VBAT_S", 2: GND})
part("R3", "4k7", {1: "SDA0", 2: P3})                     # §3 I2C pull-ups
part("R4", "4k7", {1: "SCL0", 2: P3})
part("R5", "4k7", {1: "SDA1", 2: P3})
part("R6", "4k7", {1: "SCL1", 2: P3})
part("R12", "10k", {1: "BTS_L_RPWM", 2: GND})            # §3 pull-downs (C015)
part("R13", "10k", {1: "BTS_L_LPWM", 2: GND})
part("R14", "10k", {1: "BTS_R_RPWM", 2: GND})
part("R15", "10k", {1: "BTS_R_LPWM", 2: GND})
part("R16", "10k", {1: "IS_R_MOD", 2: "BTS_IS_R"})   # §3 / §8.2 IS divider, DNP
part("R17", "10k", {1: "BTS_IS_R", 2: GND})
part("R18", "10k", {1: "IS_L_MOD", 2: "BTS_IS_L"})
part("R19", "10k", {1: "BTS_IS_L", 2: GND})
part("R20", "10k", {1: "LEAK", 2: P3})                    # §3 leak
part("R21", "4k7", {1: "LEAK_P", 2: "LEAK"})
part("R22", "10k", {1: "EN", 2: "KILL"})                  # §6 KILL sense
part("R25", "20k", {1: "KILL", 2: GND})
part("R23", "10k", {1: "EN", 2: GND})                     # §6 / §7 EN default off
part("R24", "10k", {1: "EN", 2: "Q2B"})                   # §6 Q2 base
part("R10", "1k", {1: "OE", 2: P3})             # §6 / §4 note: 1 k at solder time
part("Q2", "S8050", {1: GND, 2: "Q2B", 3: "OE"})          # §7 pins E-B-C
part("C2", "100nF", {1: P5, 2: GND})                      # §3
part("C3", "100nF", {1: P3, 2: GND})
# §7: "Q3 + R11 1 k = buzzer BZ1 (active 5 V) from PCA9685 CH6"; "LED1–3 + 330 Ω from PCA9685 CH7–9".
# SPEC does not say how CH6–CH9 reach the carrier (they are on the module's servo field, not on its 1×6 rows).
part("R11", "1k", {1: "CH6", 2: "Q3B"})
part("Q3", "S8050", {1: GND, 2: "Q3B", 3: "BZ_N"})
part("BZ1", "BUZZER", {1: P5, 2: "BZ_N"})
part("R7", "330", {1: "CH7", 2: "LED1_A"})
part("R8", "330", {1: "CH8", 2: "LED2_A"})
part("R9", "330", {1: "CH9", 2: "LED3_A"})
part("LED1", "LED", {1: "LED1_A", 2: GND})
part("LED2", "LED", {1: "LED2_A", 2: GND})
part("LED3", "LED", {1: "LED3_A", 2: GND})
# JP4 1×4 pin header CH6–CH9: jumper wires from the PCA9685 servo field to R11 and R7–R9.
# NOT in SPEC 13.10 (found by this comparison, 18.11) → SPEC §5 gains the row "JP4 PCA_CH | 1 CH6, 2 CH7, 3 CH8, 4 CH9".
part("JP4", "CH6-9", {1: "CH6", 2: "CH7", 3: "CH8", 4: "CH9"})

# --- Test points (SPEC §1)
for i, n in enumerate(["VBAT", P5, P3, "SDA0", "SCL0", GND, "KILL", "EN"], start=1):
    part(f"TP{i}", n, {1: n})

# --- Mounting holes (SPEC §1): no pins
for i in range(1, 5):
    part(f"H{i}", "M3", {})


# Not fitted by default (SPEC §8): the IS dividers and the level shifter.
DNP = {"R16", "R17", "R18", "R19", "U6"}


def nets():
    out = {}
    for ref, (_, pins) in PARTS.items():
        for p, n in pins.items():
            if n is not None:
                out.setdefault(n, set()).add(f"{ref}.{p}")
    return out


if __name__ == "__main__":
    for n, m in sorted(nets().items()):
        print(f"{n:12s} {len(m):2d}  {' '.join(sorted(m))}")
