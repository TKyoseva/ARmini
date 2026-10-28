# Media links (iCloud Drive)

Photos and videos are not in git. They live in iCloud Drive `AR-Mini-Media/`:
`00_Inbox` → `01_Loops/C###_YYYY-MM-DD_name/` (photos, video, `captions.md`) → `02_Parts` · `03_Prints` · `04_Releases` · `05_Fails` · `06_Edit` · `07_Portfolio`.
File name: `C006_01.HEIC`, `C006_02.MOV` … in the order they were taken. `captions.md` in the same folder says what each file shows and the reading on the instrument; ★ marks a portfolio pick. One card ID everywhere: board, iCloud folder, CSV, commit, video caption. The same folder name is the card's `media` field on the board and in `data/board/board.json`; the card's `files` field lists the repo files (drawings, PDFs, CAD, PCB, data) that go with the photos — `docs/portfolio/ASSETS.md` is the generated index of both.

Share links exist only where Teddy made one in Finder (C001–C003); the other folders are named only.

| Card | Date | What | Outcome | iCloud folder |
|---|---|---|---|---|
| C001 | 2026-10-08 | Cuifati thruster: dimensions, bolt pattern, mass | Partial | [C001_2026-10-08_thruster-measure](https://www.icloud.com/iclouddrive/08aBlD2PmWlmLUKzUCxIMDYVw) |
| C002 | 2026-10-08 | Thruster: the 4 wires, ESC or phases (no 12 V) | Pass | [C002_2026-10-08_thruster-wires](https://www.icloud.com/iclouddrive/003fqj7BXTbCD54QjDjdgEcww) |
| C003 | 2026-10-09 | ROB0154 plate: slots vs beams, size, mass | Fail | [C003_2026-10-09_rob0154-plate](https://www.icloud.com/iclouddrive/0d0WTgwnKRnblAFmnYWTkLQ8w) |
| C005 | 2026-10-23 | thruster_arm on the thruster: do the 4 M4 screws fit (coupon skipped) | Pass | C005_2026-10-23_thruster-arm-fit |
| C006 | 2026-10-21 | Thruster ESC: 9 V with 0.10 A limit, in a bucket | Pass | C006_2026-10-21_esc-bucket |
| C007 | 2026-10-11 | hull_fore in the bathtub: floats, leaks, draft | Pass | C007_2026-10-11_bathtub |
| C008 | 2026-10-10 | Print hull_fore (PLA white fit prototype, 4 walls, 0.2, diagonal; tree supports under the 2 rim bosses) | Pass | C008_2026-10-10_hull-fore-print |
| C010 | 2026-10-09 | GitHub: PR for T1 (state machine) → CI green? → merge into dev | Pass | C010_2026-10-09_devkit-module |
| C011 | 2026-10-11 | Print the orange plate: thruster_coupon + 2 arm_idler + 2 coupler + 1 arm_drive (PLA orange, external spool, ~1 h 20) | Partial | C011_2026-10-11_orange-plate |
| C015 | 2026-10-11 | GPIO39 at reset: is the left BTS7960 RPWM pulled high during boot? | Partial | C015_2026-10-11_gpio39-boot |
| C017 | 2026-10-10 | arm_drive (orange PLA) on the TD-8120MG disc horn: does it fit? | Pass | C017_2026-10-10_arm-drive |
| C019 | 2026-10-13 | 2 × pivot_bracket (black PLA) + 2 × TD-8120MG + linkages: do they assemble and swing? | open | C019_2026-10-13_linkage-fit |
| C020 | 2026-10-22 | Bend the cradle: Ø5 aluminium rod into a U, legs 228, base 112 between rod centres | Pass | C020_2026-10-22_cradle-bend |
| C021 | 2026-10-12 | Pesho v3 printed: warmer fits, lid closes, floats head out (thermal) and face-up (cradle) | open | C021_2026-10-12_pesho-warmer |
| C022 | 2026-10-11 | R1b frame: right hull_fore (mirrored, white) + 2 × arch_post (black) + the arch tube | open | C022_2026-10-11_r1b-frame |
| C023 | 2026-10-22 | Bench pca9685 'pair': two TD-8120MG mirrored, slow ramp 45° → 215° | Pass | C023_2026-10-22_servo-pair |
| C025 | 2026-10-23 | Thruster spins in a bucket: DevKit → ESC, forward and reverse | Pass | C025_2026-10-23_thruster-devkit |
| C027 | 2026-10-23 | Ladder bench: battery divider, leak probe and KILL rocker on the DevKit | Pass | C027_2026-10-23_vbat-cal |
| C028 | 2026-10-23 | Drive on remote over WiFi: phone page with 2 sliders + big STOP | Partial | C028_2026-10-23_remote-wifi |
| C029 | 2026-10-25 | MLX90640 110° on the arch, wired to the DevKit: does it see Pesho at 37 °C from 1 m? | Partial | C029_2026-10-25_mlx90640-arch |
| C030 | 2026-10-11 | Freeze the DevKit-Lipo pinout before the perfboard and the PCB | open | C030_2026-10-11_devkit-pinout |
| C032 | 2026-10-13 | Carrier rev B (DevKit-Lipo) → KiCad → DRC → 1:1 paper check → order 3 at Aisler | open | C032_2026-10-13_carrier-revB |
| C034 | 2026-10-12 | Print hull_aft x2 in PETG (left, then right mirrored): 2 x ~7-8 h, tree supports under 2 bosses + the transom pad | open | C034_2026-10-12_hull-aft-print |
| C035 | 2026-10-12 | Arrivals 12.10: lab supply, 4 × ST3215, MLX90640 110°, BNO055, Pi 5, logic analyser, fasteners | open | C035_2026-10-12_arrivals |
| C037 | 2026-10-13 | Print the black R1b plate: 2 × pivot_bracket (left + mirrored) + 2 × arch_post | Pass | C037_2026-10-13_r1b-black-print |
| C038 | 2026-10-13 | Cut the cable slot in both pivot_brackets by hand, so the TD-8120MG seats with its ears flat | Pass | C019_2026-10-13_linkage-fit |
| C039 | 2026-10-12 | Print Pesho v3: head + lid in white PETG, then the body in red PLA (two plates) | Partial | C021_2026-10-12_pesho-warmer |
| C040 | 2026-10-13 | Arrivals 13.10: the last Amazon batch: MLX90642-D45, soldering kit (fume extractor, third hand), wiring and prototyping parts | open | C040_2026-10-13_arrivals |
| C041 | 2026-10-15 | Print the thruster kick-up mounts: 2 × thruster_bracket + 2 × thruster_arm, PETG (after the CAD fix) | Pass | C041_2026-10-15_thruster-mounts |
| C042 | 2026-10-21 | Fit the thruster mounts (C005): M4 depth check, Ø5 hinge rod, M3 lock pin, 4 inserts in the transom pad, swing by hand | open | C042_2026-10-21_thruster-fit |
| C045 | 2026-10-20 | Print + dry-fit the beam brackets: 4 × beam_bracket (identical both sides) with the 15 × 15 aluminium beams | open | C045_2026-10-20_beam-brackets |
| C047 | 2026-10-23 | Print + fit the fixed camera mount on the arch: 2 thermal cameras + XIAO Sense (OV3660) | open | C047_2026-10-23_cam-fixed-mount |
| C048 | 2026-10-25 | MLX90642-D45 on the XIAO: first heat map, and how far it sees Pesho | Partial | C048_2026-10-25_d45-first-frame |
| C049 | 2026-10-25 | OV3660 on the XIAO Sense: first live picture from the arch on the phone | open | C049_2026-10-25_ov3660-stream |
| C050 | 2026-10-25 | Left track motor on the bench: one BTS7960 from the DevKit, tracks off the ground | Pass | C050_2026-10-25_bts-left-track |
| C051 | 2026-10-25 | Right track motor: second BTS7960 on GPIO41/42, direction map for both sides | open | C051_2026-10-25_bts-right-track |
| C053 | 2026-10-28 | First dry assembly of the whole robot with the tracks (record) | — | C053_2026-10-28_dry-assembly |
| C054 | 2026-10-28 | The home lab (record) | — | C054_2026-10-28_home-lab |

## History cards (CH##)

The story before the board (concept, research, CAD, simulation, MVP, courses, paper), for the portfolio. Board tab **History**; same folder rules (`CH##_NN.ext` + `captions.md`, ★ = portfolio pick). Cards with no files have no folder.

| Card | When | What | iCloud folder |
|---|---|---|---|
| CH01 | September 2025 | First concept drawings: AR closed and open | CH01_2025-09-01_first-concept |
| CH02 | September 2025 | Research begins with Horizon Academic | CH02_2025-09-02_horizon-research |
| CH03 | from September 2025 | C++ at school | — |
| CH04 | November 2025 | Fusion 360 CAD: AR closed and open | CH04_2025-11-01_fusion-cad |
| CH05 | January 2026 | Simulation suite complete (Gazebo) | CH05_2026-01-01_gazebo-sim |
| CH06 | January 2026 | Presented at UchIMI, Bulgarian Academy of Sciences | CH06_2026-01-14_uchimi |
| CH07 | February 2026 | System architecture | CH07_2026-02-01_architecture |
| CH08 | February 2026 | MVP design: hulls, joins, mechanical | CH08_2026-02-15_mvp |
| CH09 | February to June 2026 | Revision requested by reviewers | — |
| CH10 | March 2026 | Lego prototype | CH10_2026-03-01_lego-prototype |
| CH11 | March 2026 | CS50 | — |
| CH12 | June to August 2026 | Python: CS106A, Stanford University | — |
| CH13 | June to August 2026 | Electronics: ENGR40M, Stanford University | — |
| CH14 | June to September 2026 | Analysis rebuilt and traced to commits | — |
| CH15 | 30 September 2026 | Revised manuscript submitted | — |
