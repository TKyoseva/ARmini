# AR-Mini carrier board — rev B spec (DevKit-Lipo on headers; KiCad → Aisler)

**Date:** 2026-10-11 · **Decision:** 0005 · **Cards:** C030 (pinout), C031 (perfboard, same nets), C032 (this board)
**Status:** spec frozen for layout; two items are solder-jumper options so the order does not wait for them (§8).

Goal: one 2-layer THT board, 100 × 80 mm. The Olimex ESP32-S3-DevKit-Lipo plugs into two 1×22 female headers and stays
removable. **Only signals, 5 V and 3V3 go through the board.** 12 V for the thrusters, the servo supply and the BTS7960
power stage come from the fuse block, not from here. Same nets as the perfboard (C031), so firmware and wiring do not change
when the PCB arrives.

## 1. Board
- 100 × 80 mm, R3 corners, 4 × Ø3.2 mounting holes 3.5 mm from the edges (grid 93 × 73, same as rev A and the power box).
- 2 layers, 1.6 mm FR-4, 35 µm copper, lead-free HASL (or ENIG "Beautiful Boards").
- Tracks: signal 0.3 mm, 5 V 0.8 mm, GND as a full pour on the bottom layer.
- Silkscreen: name + pin 1 marker on every connector; "AR-Mini carrier rev B · 2026-10"; the DevKit outline with "ANTENNA →"
  and "USB-C" at its two short ends.
- Test points (bare Ø1.5 pads): TP1 12V_IN, TP2 5V, TP3 3V3, TP4 SDA0, TP5 SCL0, TP6 GND, TP7 KILL, TP8 EN.

## 2. DevKit-Lipo footprint (U1) — MEASURED 11.10 (C030)
- Two female headers 1×22, 2.54 mm pitch, **rows 25.40 mm apart** (centre to centre). The board is 55.88 × 28.09 mm.
- Pin 1 of both headers is at the **antenna end**: EXT1 pin 1 = 3V3, EXT2 pin 1 = GND (continuity-checked 11.10).
- The WROOM antenna overhangs the DevKit PCB at the antenna end. Place U1 so that end sits at the carrier edge with the antenna
  **hanging over the edge** (nothing under it). Keep-out: no copper on either layer within 10 mm of the antenna, no pour there.
- The two USB-C ports are at the other short end: that end faces a carrier edge too, with **15 mm free** for the cables.
  The DevKit therefore spans the 80 mm side of the carrier (56 mm board + overhang + cable room). The LiPo connector BAT1 and
  pUEXT on the DevKit's top side stay unused and unobstructed.
- No mounting holes on the DevKit: it is held by the headers only. Headers must be soldered with the DevKit plugged in so they stay
  parallel.
- VERIFY (Olimex manual): EXT1 pin 21 is "+5V power in/out". The carrier feeds 5 V in there from the buck; USB may be
  plugged at the same time for programming. Confirm in the manual that this is allowed (the board has a USB diode) before
  the first power-up with both.

## 3. DevKit pins used (master list: `hardware/wiring/PINOUT.md` "DevKit-Lipo", `firmware/bench/include/pins_devkit.h`)

| GPIO | Header | Net | To | Discretes on the carrier |
|---|---|---|---|---|
| 48 | EXT2 16 | SDA0 | J6 THERM_FWD, J11 IMU_EXT, U2 PCA9685, U3 BNO055 | R3 4.7 k to 3V3 |
| 47 | EXT2 17 | SCL0 | " | R4 4.7 k to 3V3 |
| 8 | EXT1 12 | SDA1 | J7 THERM_POD | R5 4.7 k to 3V3 |
| 9 | EXT1 15 | SCL1 | J7 THERM_POD | R6 4.7 k to 3V3 |
| 17 | EXT1 10 | SRV_TX | J8 SERVO_BUS (optional, bus servos later) | — |
| 18 | EXT1 11 | SRV_RX | J8 | — |
| 1 | EXT2 4 | ESC_L | J2 via JP1 (direct or U6) | see §8 |
| 2 | EXT2 5 | ESC_R | J3 via JP2 (direct or U6) | see §8 |
| 39 | EXT2 9 | BTS_L_RPWM | J4 pin 1 | **R12 10 k to GND** (C015) |
| 40 | EXT2 8 | BTS_L_LPWM | J4 pin 2 | **R13 10 k to GND** |
| 41 | EXT2 7 | BTS_R_RPWM | J5 pin 1 | **R14 10 k to GND** |
| 42 | EXT2 6 | BTS_R_LPWM | J5 pin 2 | **R15 10 k to GND** |
| 10 | EXT1 16 | BTS_IS_R | J5 pin 5 | R16 10 k series + R17 10 k to GND (DNP until VERIFY 2 is measured) |
| 11 | EXT1 17 | BTS_IS_L | J4 pin 5 | R18 / R19 as above (DNP) |
| 4 | EXT1 4 | VBAT_S | divider from 12V_IN | R1 100 k / R2 33 k 1 %, C5 100 nF to GND (12.6 V → 3.13 V) |
| 7 | EXT1 7 | LEAK | J9 | R20 10 k to 3V3; the probe pulls to GND through R21 4.7 k |
| 14 | EXT1 20 | KILL | J10 pole 2 | R22 10 k to 3V3 (low = KILL) |
| — | EXT1 1, 2 | 3V3 out (≤ 600 mA) | sensors, PCA9685 VCC, pull-ups | C3 100 nF |
| — | EXT1 21 | +5V in | from U4 | C2 100 nF, C4 100 µF |
| — | EXT1 22, EXT2 1, 22 | GND | pour | — |

Not connected on the carrier: GPIO 15/16 (Pi UART, v2 — bring to a 1×4 pin header JP3 for later), GPIO 5/6 (board sensors),
GPIO 0/38 (button, LED), 35–37, 3/45/46, 19/20 (PSRAM, strapping, USB).

## 4. Modules on headers (female 2.54 mm; measure every footprint with the caliper before fixing it)

| Ref | Module | Footprint | Note |
|---|---|---|---|
| U1 | ESP32-S3-DevKit-Lipo | 2 × 1×22, rows 25.40 | §2 |
| U2 | PCA9685 module (Ardboard) | 2 × 1×6 at the ends; the 16×3 servo field stays free above the board | **measure**: length, row distance. Only I2C, VCC (3V3), GND and OE go to the carrier. **V+ (servo power) goes to the module's own screw terminal from the 6 V servo buck — not through the carrier.** The two cradle TD-8120MG plug straight into the module's CH10 / CH11 (C023). |
| U3 | BNO055 breakout | 1 × 1×6 or 1×8 | **measure** (which breakout arrived) |
| U4 | Buck 12 → 5 V 3 A (MZHOU) | 2-pin in + 2-pin out, screw terminals or pads | feeds +5V; output set to 5.0 V before fitting |
| U6 | 74AHCT125 (DIP-14) | DIP socket | ESC level shifter, **DNP by default**, §8 |

## 5. Connectors (JST-XH 2.5 mm vertical unless noted; pin 1 = square pad; GND on pin 1 or the last pin, never in the middle)

| Ref | Name | Pins | To |
|---|---|---|---|
| J1 | 12V_IN | screw 5.08: 1 +12V, 2 GND | fuse "5 A logic" |
| J2 | ESC_L | 1 GND, 2 NC, 3 ESC_L | left thruster ESC signal + ground (ESC power from its 20 A fuse) |
| J3 | ESC_R | 1 GND, 2 NC, 3 ESC_R | right ESC |
| J4 | BTS_L | 1 RPWM, 2 LPWM, 3 EN, 4 GND, 5 IS_L | left BTS7960 (R_EN + L_EN tied together on the module → pin 3) |
| J5 | BTS_R | 1 RPWM, 2 LPWM, 3 EN, 4 GND, 5 IS_R | right BTS7960 |
| J6 | THERM_FWD | 1 +3V3, 2 GND, 3 SDA0, 4 SCL0 | MLX90642-D45 |
| J7 | THERM_POD | 1 +3V3, 2 GND, 3 SDA1, 4 SCL1 | MLX90640-110° |
| J8 | SERVO_BUS | 1 SRV_TX, 2 SRV_RX, 3 GND, 4 NC | Waveshare bus-servo driver (optional; its 12 V is separate) |
| J9 | LEAK | 1 LEAK, 2 GND | two bare wires in the bilge |
| J10 | ROCKER | 1 +5V, 2 EN, 3 GND, 4 KILL, 5 GND | DPDT ON-ON rocker, §6 |
| J11 | IMU_EXT | 1 +3V3, 2 GND, 3 SDA0, 4 SCL0 | spare I2C-0 |
| JP3 | PI_UART | 1×4 pin header: GND, PI_TX, PI_RX, +5V | v2, unpopulated |

## 6. KILL path (hardware, no firmware in the loop)
One **DPDT ON-ON rocker** (the Steinberger ASW-14D is DPDT; VERIFY the one bought):
- Pole 1: common → **EN** (J10-2). RUN contact → +5V (J10-1). KILL contact → GND (J10-3).
  EN goes to both BTS7960 modules (R_EN + L_EN). In KILL both power stages are disabled whatever the PWM pins do.
- Pole 2: common → **KILL** (J10-4, GPIO14 with R22 10 k to 3V3). KILL contact → GND (J10-5). RUN contact → open.
  GPIO14 reads 1 in RUN, 0 in KILL (same as PINOUT). A broken rocker wire reads as RUN on this pole — that is why pole 1 is the
  one that actually cuts power: a broken EN wire leaves EN low (R23 10 k EN → GND), i.e. motors off.
- PCA9685 **OE** must be LOW in RUN and HIGH in KILL (outputs off): Q2 BC337 inverter, base from EN through R24 10 k, collector =
  OE with R10 2.2 k to 3V3 (the module has 10 k to GND on OE, so 2.2 k wins). RUN → EN 5 V → Q2 on → OE low → outputs active.
- Pull-downs R12–R15 (§3) cover the boot window; firmware drives GPIO39–42 LOW first in `setup()`; the rocker is the third layer.

## 7. Other discretes
| Ref | Part | Purpose |
|---|---|---|
| Q1 | P-MOSFET IRF4905 (TO-220) | reverse polarity on J1 |
| D1 | TVS SMBJ15A | spikes on 12 V |
| C1 | 470 µF / 25 V | 12 V input |
| F1 | polyfuse 1.1 A | 5 V rail to the logic |
| Q3 + R11 1 k | BC337 | buzzer BZ1 (active 5 V, Ø12) from PCA9685 CH6 |
| LED1–3 + 330 Ω | green / yellow / red | status / armed / fault from PCA9685 CH7–9 |
| R12–R15 | 10 k | GPIO39–42 pull-downs (C015, measured) |
| R23 | 10 k | EN → GND (default off) |

## 8. The two items that are NOT settled, built so the order does not wait
1. **ESC signal level (C006 not done).** Both ESC lines go through **3-pad solder jumpers JP1 / JP2**: centre = J2/J3 signal,
   side A = DevKit GPIO direct (3.3 V), side B = U6 74AHCT125 output (5 V, powered from +5V, inputs from GPIO1/2).
   Default: A bridged, U6 not fitted. If C006 shows the ESC wants 5 V logic: fit U6 in its socket, cut A, bridge B.
2. **BTS7960 IS_R / IS_L (VERIFY 2).** Footprints R16–R19 present, DNP. Measure the module's IS voltage under load first
   (it can exceed 3.3 V); the 10 k / 10 k divider halves it if used.

## 9. Before "Push to AISLER" (Teddy)
1. DRC clean in KiCad (clearance 0.2 mm, via 0.6 / 0.3); CI `check` runs `kicad-cli` DRC + Gerbers on every push.
2. **1:1 print**: the DevKit on the sheet — all 44 pins in their holes, rows 25.40; PCA9685 and BNO055 the same.
3. Pin 1 of every JST where the poster says; GND never in the middle.
4. Antenna end over the edge, USB-C end with 15 mm free, both checked on the print with the real DevKit.
5. Mounting holes on the 93 × 73 grid.
6. Gerbers through the Eurocircuits PCB Visualizer; red → fix first.
7. Aisler: 2 layer · 1.6 mm · **3 pcs** · HASL · delivery to Bulgaria · **order by Tue 13.10** (standard ≈ 8 working days + DHL
   → in hand before r3b 29.10; "Blitz" if it slips).

## 10. Not on this board (on purpose)
12 V to ESCs / BTS / servo driver; 6 V servo supply (goes to the PCA9685 module terminal); the BTS7960 modules (on their own plate
by the motors); the Pi 5; the thruster ESCs (potted); the bare ESP32-S3-WROOM-1-N16R8 modules (carrier rev C, v2, after 1.11).
