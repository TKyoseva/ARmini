# AR-Mini · STATE

The current state on one page. Updated in the workshop chat after every decision. The truth is in the repository; this is the summary.

**Date:** 2026-10-09 · **CAD:** v2.0 · **Next releases:** r1a 11.10 · r2a 16.10 · r2c 22.10 · r3b 29.10 · submit 01.11
**Where things are:** decisions and files → workshop chat (Claude) · code and commits → Cursor (branch `dev`, night tasks `night/*`) · test cards → AR-Mini Board (export in `data/board/board.json`) · photos and video → iCloud `AR-Mini-Media/01_Loops/C###_…` · missing parts → `parts/needs.yaml`

## Closed cards
| Card | Result | What it changed |
|---|---|---|
| C001 thruster measured (08.10) · Partial | duct Ø72.27 × 112 (box says 77), mounting face 47.10 above the axis, M4 at ~35 × 15.6, 206 g, 4 wires | CAD v2.0: kick-up mount, nothing below the waterline (decision 0004) |
| C002 thruster wires (08.10) · Pass | no shorts; red +, black −; yellow probably signal, white probably signal ground; ESC inside (listing: 50 Hz, 1500 µs stop) | next: test at 9 V with a 0.10 A limit (C006) |
| C003 ROB0154 plate (09.10) · Fail | 151.82 × 134.8; slots 11.3 / 26.4 from the edges (≈114 apart); chassis 1175 g → draft 41.8 | CAD v2.0: ch_x 300, 3.4 × 7 slots in the power box |

## Decisions (see docs/decisions/)
- 0001 · licence: MIT for code, CC BY 4.0 for CAD, PCB, docs and images.
- 0003 · the power box sits on the beams (v1.9).
- 0004 · kick-up thruster mount on the transom, Ø5 pin at z 75, no holes below the waterline; M3 lock pin for reverse thrust and land.
- C003 · the octagonal hole of the plate faces forward; the beams are drilled through the slots at assembly; `pb_beam_y` 30 stays.

## Open (VERIFY / MEASURE)
- Thruster bolt pattern 35.0 × 15.6 → coupon C005 (`thruster_coupon`, PLA).
- Position of the frame along the duct (`th_frame_dx`) and M4 screw length for pad 5 + frame 9.68.
- Is the plate centred on the tracks (CAD: 74.1 from the front edge)? → C004.
- Length of the plate slots (drawn as 100).
- ESC: logic level and arming → C006 (9 V, 0.10 A, in a bucket).
- 10 mm submergence of the duct in waves → pool, r2c.

## Next cards
| Card | What | Release |
|---|---|---|
| C004 | assembled chassis: track → plate edge (front / back), M3 through the slots | r2b |
| C005 | coupon 50 × 30 × 5, 4 × Ø4.5 at 35 × 15.6: do the M4 screws go in by hand? | r2a |
| C006 | ESC: 9 V / 0.10 A in a bucket, V yellow→black, white→black, then with 10 kΩ to ground | r2a |
| C007 | `hull_fore` in water: floats, draft, leak (dry paper) | r1a |
| C008 | print `hull_fore` | r1a |
| C010 | review the T1 pull request (state machine) | — |
| C011 | print the thruster coupon | r2a |
| C012 | start night tasks T2 (safety) and T3 (bench sketches) | — |

## Agents (Cursor background agents and tools)
T1 state machine (PR open) · T2 safety · T3 bench sketches · T4 parts agent · T5 release video agent → `tasks/night/`. Status: the pull requests on GitHub.

## Numbers that do not change without a measurement
Hull 610 × 100 × 120, gap 250, draft 42 at 4.7 kg (8.9 mm/kg) · beams x 385 / 500 · arm 110, deploy 215°, stow 45° · ROB0154: 300 × 230 × 124.6, plate 151.82 × 134.8, motor axis 62 · box 152 × 135 × 66 at z 141 · fuses 30 A inline → 50 A switch → 20/15/10/5/5 A.
