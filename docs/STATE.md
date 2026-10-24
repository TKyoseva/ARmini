# AR-Mini · STATE

The current state on one page. Updated in the workshop chat after every decision. The truth is in the repository; this is the summary.

**Date:** 2026-10-24 · **CAD:** v2.0 + measured TD-8120MG pocket, thruster pattern 35.0 × 15.9, cradle 112 · **Releases:** R1a cut 11.10 ✓ · R-1018 ✓ · R-1024 ✓ (24.10) · R2a criteria met (cut pending) · R2c half-way · R3a 26.10 · R3b 29.10 · R4 31.10 · submit 01.11
**Where things are:** decisions and files → workshop chat (Claude) · code and commits → Cursor (branch `dev`, night tasks `night/*`) · test cards → AR-Mini Board (export in `data/board/board.json`) · photos and video → iCloud `AR-Mini-Media/01_Loops/C###_…` · missing parts → `parts/needs.yaml` · v2 thrusters → `parts/watch.yaml`

## Closed cards
| Card | Result | What it changed |
|---|---|---|
| **R-1024 (24.10), 13 cards** · see docs/releases/R-1024.md | frame built: both hulls (PETG aft + PLA fore) on 2 beams at x 385 / 500, arch, arm, cradle; `pair` lifts Pesho at ~0.24 A (C019–C023, C034, C045); thruster mounts fitted, M4 × 12 (C005, C042); ESC input 5 V pulled up → S8050 shifter, inverted output (C006, C024); thruster from the DevKit: 1600 µs 0.22 A, 1650 µs 0.58 A, KILL 40 ms (C025); v_bat ±0.02 V (C027) | right thruster faulty (FAILS 173) → replacement; R2a met |
| C028 phone remote + first float of the whole robot (24.10) · Partial | bathtub, tethered: stable, **draft 20 mm**, dry hulls; left thruster 1640 µs · 0.58 A at 12 V moves and turns it; SAFE on stop / kill / disconnect / heartbeat | env `remote` still only on `night/remote` → merge to dev; next: both thrusters, range walk, pool (R2c) |
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
- Right thruster faulty (FAILS 173): claim + replacement; both-thruster test after it arrives.
- Robot mass as floated: draft 20 mm × ~996 cm² waterplane (C007, 4 sections) ≈ 2.0 kg → weigh to confirm.
- ~~GPIO39–42 at boot~~ → DECIDED 11.10 (C015): 10 kΩ pull-down to GND on each; GPIO39 is weakly HIGH after boot, 39/40 in download mode (PINOUT.md item 4).
- DevKit-Lipo pinout freeze → C030 (rows 25.40, EXT1/EXT2 anchors and GPIO38 confirmed 11.10) → PINOUT.md + `pins_devkit.h`.
- Firmware `armini` Safety still reads the old ADC ladder (`Ladder.h`, `Safety.cpp`, `hal_devkit`) → separate KILL / LEAK pins (0005).
- 10 mm submergence of the duct in waves → pool, R2c.
- CAD fixes, not urgent: coupler rod boss flush (prints without supports); 45° gussets under the hull rim bosses (PETG hull without supports).

## Next cards
| Card | What | Release |
|---|---|---|
| C021 · C030 · C032 · C047 | Pesho v3 floats · pinout freeze · carrier rev B · fixed camera mount (in Today) | R3a / R3b |
| — | right thruster replacement → both thrusters from the phone, range walk, pool run | R2c |
| C004 | assembled chassis: track → plate edge, M3 through the slots | R2b |
| C026 · C031 | power chain on the bench · perfboard carrier | R2c |
| C029 | MLX90640 sees Pesho at 37 °C from 1 m | R3a |
| C013 · C016 · C033 | public-ready check (29–30.10) · parts agent first run · v2 carrier rev C (after 1.11) | — |

## Agents (Cursor background agents and tools)
T1 state machine (merged) · T2 safety · T3 bench sketches · T4 parts agent (hourly workflow from `main`) · T5 release video (`tools/video/make.py`) · T6 thruster watch (`parts/watch.yaml`) → `tasks/night/`. Status: the pull requests on GitHub.

## Numbers that do not change without a measurement
Hull 610 × 100 × 120 (printed section: height 119.70, 323 g), gap 250, draft 42 at 4.7 kg (CAD 8.9 mm/kg; C007 measured 249 cm² per section → 9.1 mm/kg, ~43) · joint bolts z 75 / 105 (lowest hole edge 73.26) · beams x 385 / 500 · arm 110, deploy 215°, stow 45° · cradle rods 112 between centres · ROB0154: 300 × 230 × 124.6, plate 151.82 × 134.8, motor axis 62 · box 152 × 135 × 66 at z 141 · fuses 30 A inline → 50 A switch → 20/15/10/5/5 A.
