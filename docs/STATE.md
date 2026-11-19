# AR-Mini · STATE

The current state on one page. Updated in the workshop chat after every decision. The truth is in the repository; this is the summary.

**Date:** 2026-11-18 · **CAD:** v2.0 + beam_leg + rudder_frame (lake configuration: one thruster on the centreline, MG90S rudder) · **Releases:** R1a cut 11.10 ✓ · R-1018 ✓ · R-1024 ✓ (24.10) · R-1101 ✓ (01.11) · tag `r2026-11-10` (C072 docs + BOM, no cards released) · R2a ✓ · R2c met in open water (lake, 01.11) · R3a / R3b not met · G1 portfolio v1 submitted 01.11 (MIT Early Action) · next goal G2, 30.12
**Where things are:** decisions and files → workshop chat (Claude) · code and commits → Cursor (branch `dev`, night tasks `night/*`) · test cards → AR-Mini Board (export in `data/board/board.json`) · photos and video → iCloud `AR-Mini-Media/01_Loops/C###_…` · missing parts → `parts/needs.yaml` · v2 thrusters → `parts/watch.yaml`

## Closed cards
| Card | Result | What it changed |
|---|---|---|
| **Mac-only week, 18.11 (no lab until 27.11): C075, C076, C077, C080, C083, C085** · Pass, all in simulation or on paper | architecture v5 generated from the board (C075); `remote_pool` goes SAFE on leak and on VBAT < 10.50 V (C076); heading-hold PI controller, 43 / 43 host tests (C077); rev B schematic from SPEC, ERC 0, parity 0, 2 SPEC errors fixed (C080); FEA at an assumed 20 N: beam_leg SF 16.8, bracket SF 8.1, lock pin SF 6.3 (C083); hull drag without waves 0.05 / 0.42 / 1.13 N at 0.2 / 0.6 / 1.0 m/s (C085) | every number waits for its measurement after 27.11: thrust (C061), leak and VBAT in water, heading on the boat (C066 → C067), speed on the lake |
| C063 robot mass (04.11) · Pass | 2.5 kg with the battery, without Pesho (estimate was 2.0 kg) | draft 23 mm at 9.1 mm/kg; C064 = 2.5 kg + Pesho |
| C060 lift on two channels (02.11) · Pass | FAILS 180 closed: the PCA9685 sits 180° in the box and its columns were counted from 1; both servos lift Pesho on CH12 / CH13 | rule: label the channel numbers on the module |
| **R-1101 (01.11), 10 cards** · see docs/releases/R-1101.md | **lake run at Pancharevo 01.11 (C059)**: launched from the bank, floated level, drove and turned from the phone and came back, on the 3S LiPo, FINAL 2 wiring in a food box, env `remote_pool` (74HCT125 → ESC, MG90S rudder, lift on PCA9685); beam_leg 123.0 g PETG (C056), rudder + rudder_frame (C057); LiPo 11.10 → 12.60 V, 1212 mAh (C058); right thruster faulty on a third driver (C055); left track from the DevKit, dead-man 2.000 s (C050); both thermal cameras give frames (C029, C048 partial); dry assembly with tracks (C053) | right thruster → replacement; lift single channel (FAILS 180) open; next: G2 measured numbers (thrust, runtime, thermal range) |
| **R-1024 (24.10), 13 cards** · see docs/releases/R-1024.md | frame built: both hulls (PETG aft + PLA fore) on 2 beams at x 385 / 500, arch, arm, cradle; `pair` lifts Pesho at ~0.24 A (C019–C023, C034, C045); thruster mounts fitted, M4 × 12 (C005, C042); ESC input 5 V pulled up → S8050 shifter, inverted output (C006, C024); thruster from the DevKit: 1600 µs 0.22 A, 1650 µs 0.58 A, KILL 40 ms (C025); v_bat ±0.02 V (C027) | right thruster faulty (FAILS 173) → replacement; R2a met |
| C028 phone remote + first float of the whole robot (24.10) · Partial | bathtub, tethered: stable, **draft 20 mm**, dry hulls; left thruster 1640 µs · 0.58 A at 12 V moves and turns it; SAFE on stop / kill / disconnect / heartbeat | env `remote` merged to dev; pool step done in the lake (C059) |
| C001 thruster measured (08.10) · Partial | duct Ø72.27 × 112 (box says 77), mounting face 47.10 above the axis, M4 pattern, 206 g, 4 wires | CAD v2.0: kick-up mount, nothing below the waterline (decision 0004) |
| C002 thruster wires (08.10) · Pass | no shorts; red +, black −; yellow probably signal, white probably signal ground; ESC inside (listing: 50 Hz, 1500 µs stop) | next: test at 9 V with a 0.10 A limit (C006) |
| C003 ROB0154 plate (09.10) · Fail | 151.82 × 134.8; slots 11.3 / 26.4 from the edges (≈114 apart); chassis 1175 g → draft 41.8 | CAD v2.0: ch_x 300, 3.4 × 7 slots in the power box |
| C008 print `hull_fore` (11.10) · Pass | white PLA, 6 h 16 min, 345.0 g (slicer 6 h 13, 344.79); tree supports under the 2 rim bosses | first full hull section; CAD fix later: 45° gussets under the bosses |
| C007 `hull_fore` in the bathtub (11.10) · Pass | 323 g, height 119.70; floats upright, dry inside; empty draft 12.99 mm (CAD 12.7) → 249 cm² per section (CAD 255); +1374 g → 63.57 mid-hull (trim by the stern; stern waterline ~3–5 mm under the joint holes) | two full hulls ≈ 9.1 mm/kg (CAD 8.9) → robot waterline ~43 instead of 42; heavy parts near the joint stay low and central |
| C017 `arm_drive` on the TD-8120MG disc horn (10.10) · Pass | plastic 25T disc, ring c-c ~16; servo body 40.40 × 20.17 × 40.85, ear holes c-c 48.26, d 4.05 | CAD: TD-8120MG pocket and disc stack measured (FAILS 147) |
| Task cards (C009, C010, C012, C014, C018) · Pass | CAD v2.0 committed; T1 merged; T2/T3 started; mentor asked about `sim/`; T6 thruster watch merged | — |

## Decisions (see docs/decisions/)
- 0001 · licence: MIT for code, CC BY 4.0 for CAD, PCB, docs and images.
- 0002 · the chassis hangs from the beams, tracks level with the hull bottom.
- 0003 · the power box sits on the beams (v1.9).
- 0004 · kick-up thruster mount on the transom, Ø5 pin at z 75, no holes below the waterline; M3 lock pin for reverse thrust and land. Pattern measured 35.0 × 15.9.
- 0005 · the v1 controller is the Olimex ESP32-S3-DevKit-Lipo: perfboard now (C031), Aisler carrier rev B in parallel (C032); KILL on GPIO14 and LEAK on GPIO7 as separate pins.
- C003 · the octagonal hole of the plate faces forward; the beams are drilled through the slots at assembly; `pb_beam_y` 30 stays.

## Open (VERIFY / MEASURE)
- ~~Thruster bolt pattern 35.0 × 15.9~~ → CONFIRMED C005 (M4 × 12 by hand).
- Is the plate centred on the tracks (CAD: 74.1 from the front edge)? → C004. Length of the plate slots (drawn as 100).
- ~~ESC: logic level and arming~~ → DONE C006/C025: input pulled up to 5 V, S8050 shifter, dead band ≈ 1450–1550 µs.
- Right thruster faulty (FAILS 173, confirmed C055 on an Arduino Mega): replacement Cuifati delivered 09.11, not bench-tested yet → C074; then the both-thruster test.
- ~~Cradle lift drives only the higher PCA9685 channel (FAILS 180)~~ → CLOSED C060 (02.11): channel off by one.
- Thermal 110° orientation (FLIP_110) unverified; MLX90640 intermittent "not found" at boot (C029).
- ~~Robot mass as floated ≈ 2.0 kg~~ → MEASURED C063 (04.11): 2.5 kg with the battery, without Pesho.
- Simulated numbers that need a measurement (FAILS 187–189): thrust for the FEA (C061), does the arm stop tab touch the bracket plate, heading overshoot on the boat (C067), speed vs thrust on the lake for the drag curve.
- `remote_pool` auto-SAFE (C076) tried on the host only: leak ADC level in water and VBAT under load are not measured.
- Electronics still on breadboards in a food box: C072 (two IP65 boxes, one EXP-14 board) planned, nothing printed or soldered; EXP-14 outer size and hole Ø to measure.
- ~~GPIO39–42 at boot~~ → DECIDED 11.10 (C015): 10 kΩ pull-down to GND on each; GPIO39 is weakly HIGH after boot, 39/40 in download mode (PINOUT.md item 4).
- DevKit-Lipo pinout freeze → C030 (rows 25.40, EXT1/EXT2 anchors and GPIO38 confirmed 11.10) → PINOUT.md + `pins_devkit.h`.
- Firmware `armini` Safety still reads the old ADC ladder (`Ladder.h`, `Safety.cpp`, `hal_devkit`) → separate KILL / LEAK pins (0005).
- 10 mm submergence of the duct in waves → seen in the lake videos (C059_77, C059_91), not measured.
- CAD fixes, not urgent: coupler rod boss flush (prints without supports); 45° gussets under the hull rim bosses (PETG hull without supports).

## Next cards
| Card | What | Release / goal |
|---|---|---|
| C047 · C049 | fixed camera mount on the arch · OV3660 live stream on the phone | G2 |
| C051 · C052 | right track motor · both tracks drive the chassis on the floor | G2 |
| C030 · C032 | pinout freeze · carrier rev B (order with Aisler) | G2 |
| C021 | Pesho v3 floats head out, warm | G2 |
| C074 · C061 · C062 · C064 | new right thruster on the bench → both thrusters; thrust in the tub; battery endurance; Pesho in the lift in water | G2 (30.12) |
| C066 · C067 | BNO055 heading on the robot → heading hold in water | G2 |
| C072 | electronics into the two IP65 boxes | G2 |
| C078 · C079 · C082 · C086 | Mac-only week: docs sync, portfolio v2 plan, release, Blender renders (then C081, C084, C087 if time) | until 27.11 |
| C013 · C016 · C033 | public-ready check · parts agent first run · v2 carrier rev C | G2 / G3 |

## Agents (Cursor background agents and tools)
T1 state machine (merged) · T2 safety · T3 bench sketches · T4 parts agent (hourly workflow from `main`) · T5 release video (`tools/video/make.py`) · T6 thruster watch (`parts/watch.yaml`) → `tasks/night/`. Status: the pull requests on GitHub.

## Numbers that do not change without a measurement
Hull 610 × 100 × 120 (printed section: height 119.70, 323 g), gap 250, draft 42 at 4.7 kg (CAD 8.9 mm/kg; C007 measured 249 cm² per section → 9.1 mm/kg, ~43); lake configuration 2.5 kg (C063) → draft ~23 · joint bolts z 75 / 105 (lowest hole edge 73.26) · beams x 385 / 500 · arm 110, deploy 215°, stow 45° · cradle rods 112 between centres · ROB0154: 300 × 230 × 124.6, plate 151.82 × 134.8, motor axis 62 · box 152 × 135 × 66 at z 141 · fuses 30 A inline → 50 A switch → 20/15/10/5/5 A.
