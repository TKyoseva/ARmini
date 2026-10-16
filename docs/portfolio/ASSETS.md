# Portfolio assets — every card's evidence in one table

Generated 16.10.2026 from the board (`data/board/board.json`): for each card the files in this repo and the iCloud media folder. Photos and videos stay in iCloud (`media/LINKS.md`); ★ picks are in each folder's `captions.md`. The portfolio can quote the data files directly: drawings, 1:1 PDFs, DRC reports, STLs, board exports, analyses.

| Card | Title | Outcome | Repo files | iCloud |
|---|---|---|---|---|
| C001 | Cuifati thruster: dimensions, bolt pattern, mass | Partial | `interfaces/interfaces.json` — thruster bolt pattern and mass as measured<br>`docs/bom/bom.csv` — Cuifati 12 V thruster row | C001_2026-10-08_thruster-measure |
| C002 | Thruster: the 4 wires, ESC or phases (no 12 V) | Pass | `docs/diagrams/AR-Mini_hardware_poster_A3.pdf` — ESC wiring on the poster<br>`pcb/carrier-revB/SPEC.md` — §8 ESC signal level, JP1/JP2 | C002_2026-10-08_thruster-wires |
| C003 | ROB0154 plate: slots vs beams, size, mass | Fail | `docs/decisions/0002-chassis-on-beams.md`<br>`cad/openscad/AR-Mini_v1.scad` — chassis hangers deleted after this test | C003_2026-10-09_rob0154-plate |
| C004 | Assembled ROB0154: where the plate sits on the tracks | open | `docs/decisions/0002-chassis-on-beams.md` | — |
| C005 | thruster_arm on the thruster: do the 4 M4 screws fit (coupon skipped) | open | `docs/decisions/0004-kick-up-thruster-mount.md`<br>`cad/stl/v1/thruster_coupon.stl` — the coupon that stood in for this test | — |
| C006 | Thruster ESC: 9 V with 0.10 A limit, in a bucket | open | `pcb/carrier-revB/SPEC.md` — §8: this test sets the JP1/JP2 default<br>`firmware/bench/README.md` | — |
| C007 | hull_fore in the bathtub: floats, leaks, draft | Pass | `cad/fusion/AR_Mini_hull.py` — hydrostatics: draft 42 mm predicted<br>`cad/openscad/AR-Mini_v1.scad` — hull_fore<br>`docs/FAILS_AND_FIXES.md` | C007_2026-10-11_bathtub |
| C008 | Print hull_fore (PLA white fit prototype, 4 walls, 0.2, diagonal; tree supports under the 2 rim bosses) | Pass | `cad/stl/v1/hull_fore.stl` | C008_2026-10-10_hull-fore-print |
| C009 | Cursor: commit CAD v2.0 + decision 0004 + STATE.md to dev | Pass | `cad/openscad/AR-Mini_v1.scad` — v2.0<br>`docs/decisions/0004-kick-up-thruster-mount.md`<br>`docs/STATE.md` | — |
| C010 | GitHub: PR for T1 (state machine) → CI green? → merge into dev | Pass | `tasks/night/2026-10-08_T1_state-machine.md`<br>`firmware/armini/lib/core/StateMachine.cpp`<br>`docs/diagrams/AR-Mini_states_T1_mission.pdf` | C010_2026-10-09_devkit-module |
| C011 | Print the orange plate: thruster_coupon + 2 arm_idler + 2 coupler + 1 arm_drive (PLA orange, external spool, ~1 h 20) | Partial | `cad/stl/v1/thruster_coupon.stl`<br>`cad/stl/v1/arm_idler.stl`<br>`cad/stl/v1/coupler.stl`<br>`cad/stl/v1/arm_drive.stl` | C011_2026-10-11_orange-plate |
| C012 | Cursor: start night tasks T2 (safety) and T3 (bench) before sleep | Pass | `tasks/night/2026-10-08_T2_safety.md`<br>`tasks/night/2026-10-08_T3_bench.md`<br>`docs/diagrams/AR-Mini_states_T2_safety.pdf`<br>`docs/diagrams/AR-Mini_states_T3_bench.pdf`<br>`firmware/armini/lib/core/Safety.cpp`<br>`firmware/bench/README.md` | — |
| C013 | Public-ready check, then make the repo public (29–30.10) | open | `README.md`<br>`LICENSE`<br>`CONTRIBUTORS.md`<br>`docs/decisions/0001-license.md` | — |
| C014 | Ask John Hood: may sim/ be public under MIT? | Pass | `docs/decisions/0001-license.md` | — |
| C015 | GPIO39 at reset: is the left BTS7960 RPWM pulled high during boot? | Partial | `pcb/carrier-revB/SPEC.md` — §3 R12–R15 pull-downs came from this<br>`hardware/breadboard/AR-Mini_breadboard_2b_devkit-lipo.png`<br>`firmware/bench/src/bts7960/PROTOCOL.md` | C015_2026-10-11_gpio39-boot |
| C016 | Parts agent: real needs, Telegram bot, first run | open | `tools/parts/agent.py`<br>`parts/needs.yaml`<br>`tasks/night/2026-10-09_T4_parts-agent.md` | — |
| C017 | arm_drive (orange PLA) on the TD-8120MG disc horn: does it fit? | Pass | `cad/stl/v1/arm_drive.stl`<br>`cad/openscad/AR-Mini_v1.scad` — TD-8120MG horn numbers | C017_2026-10-10_arm-drive |
| C018 | Cursor: night task T6 — thruster watch for v2 | Pass | `tasks/night/2026-10-10_T6_thruster-watch.md`<br>`tools/parts/watch.py`<br>`parts/watch.yaml` | — |
| C019 | 2 × pivot_bracket (black PLA) + 2 × TD-8120MG + linkages: do they assemble and swing? | open | `docs/diagrams/AR-Mini_pivot_bracket_mount.png` — how the bracket sits on the rim boss, cross-section<br>`cad/stl/v1/pivot_bracket.stl`<br>`cad/stl/v1/arm_idler.stl`<br>`cad/stl/v1/coupler.stl`<br>`cad/openscad/AR-Mini_v1.scad` | C019_2026-10-13_linkage-fit |
| C020 | Bend the cradle: Ø5 aluminium rod into a U, legs 228, base 112 between rod centres | open | `cad/openscad/AR-Mini_v1.scad` — cradle U, 112 between rod centres<br>`interfaces/interfaces.json` | — |
| C021 | Pesho v3 printed: warmer fits, lid closes, floats head out (thermal) and face-up (cradle) | open | `cad/pesho/pesho.py`<br>`cad/pesho/pesho_views.png`<br>`cad/pesho/pesho_float.png` — floats head-out<br>`cad/pesho/float.txt` — buoyancy numbers | C021_2026-10-12_pesho-warmer |
| C022 | R1b frame: right hull_fore (mirrored, white) + 2 × arch_post (black) + the arch tube | open | `cad/stl/v1/hull_fore.stl` — right hull = mirrored along Y<br>`cad/stl/v1/arch_post.stl` | C022_2026-10-11_r1b-frame |
| C023 | Cursor: bench pca9685 'pair' command — two TD-8120MG mirrored, slow ramp 45° → 215° | open | `firmware/bench/src/pca9685/main.cpp`<br>`firmware/bench/src/pca9685/PROTOCOL.md`<br>`hardware/datasheets/PCA9685.md` — prescale 121, calibrate the oscillator | — |
| C024 | Cursor: bench `esc` env — both thruster ESCs on LEDC GPIO1/2 | open | `pcb/carrier-revB/SPEC.md` — §8<br>`firmware/bench/README.md` | — |
| C025 | Thruster spins in a bucket: DevKit → ESC, forward and reverse | open | `docs/bom/bom.csv` — row 139: hanging scales 50 kg / 10 g ×2<br>`data/thrust-test/` — where the table goes | — |
| C026 | Power chain on the bench, no loads: fuse → 50 A switch → fuse block → 5 V buck | open | `docs/diagrams/AR-Mini_hardware_poster_A3.pdf` — power chain<br>`docs/bom/bom.csv` | — |
| C027 | Ladder bench: battery divider, leak probe and KILL rocker on the DevKit | open | `hardware/breadboard/AR-Mini_breadboard_2b_ladder-step.png`<br>`hardware/breadboard/src/ladder_step.py`<br>`firmware/bench/src/ladder/PROTOCOL.md`<br>`pcb/carrier-revB/SPEC.md` — §6 KILL on the SPDT rocker | — |
| C028 | Night task T7 (Cursor): drive on remote over WiFi — phone page with 2 sliders + big STOP | open | — | — |
| C029 | MLX90640 110° on the bench: does it see Pesho at 37 °C from 1 m? | open | `firmware/bench/src/mlx90640/PROTOCOL.md`<br>`cad/pesho/pesho_float.png` — head-out float, the target | — |
| C030 | Freeze the DevKit-Lipo pinout before the perfboard and the PCB | open | `hardware/wiring/PINOUT.md`<br>`hardware/breadboard/Olimex_DevKit-Lipo_pinout_manual-p7.png`<br>`docs/decisions/0005-v1-controller-devkit-lipo.md` | C030_2026-10-11_devkit-pinout |
| C031 | Perfboard carrier for the DevKit-Lipo (the boat's board until the PCB arrives) | open | `hardware/breadboard/AR-Mini_breadboard_3_v1-all.png`<br>`hardware/breadboard/src/v1_all.py` | — |
| C032 | Carrier rev B (DevKit-Lipo) → KiCad → DRC → 1:1 paper check → order 3 at Aisler | open | `pcb/carrier-revB/SPEC.md`<br>`pcb/carrier-revB/gen.py` — writes the board<br>`pcb/carrier-revB/AR-Mini_carrier_revB.kicad_pcb` — the file for Aisler<br>`pcb/carrier-revB/drc/2026-10-15_clean.rpt` — 0 / 0 / 0<br>`pcb/carrier-revB/AR-Mini_carrier_revB_1to1_F.pdf` — 1:1 front<br>`pcb/carrier-revB/AR-Mini_carrier_revB_fitcheck_1to1.pdf` — pads-only fit check<br>`pcb/carrier-revB/AR-Mini_carrier_revB_top_view_v2.png`<br>`pcb/carrier-revB/AR-Mini_carrier_revB_assembled.png` — how it looks built<br>`pcb/carrier-revB/measure/U2_PCA9685_measure.png` — what to measure on the module<br>`pcb/carrier-revB/history/2026-10-13_U2-54.26_failed-paper-check.kicad_pcb` — the board that failed the paper check<br>`pcb/carrier-revB/src/README.md` — the checking scripts<br>`hardware/datasheets/PCA9685.md` — datasheet check<br>`docs/FAILS_AND_FIXES.md` — 152 | C032_2026-10-13_carrier-revB |
| C033 | v2 (after 1.11): carrier rev C — the bare ESP32-S3-WROOM-1-N16R8 soldered on my own board | open | `docs/decisions/0005-v1-controller-devkit-lipo.md` | — |
| C034 | Print hull_aft x2 in PETG (left, then right mirrored): 2 x ~7-8 h, tree supports under 2 bosses + the transom pad | open | `cad/stl/v1/hull_aft.stl` | C034_2026-10-12_hull-aft-print |
| C035 | Arrivals 12.10: lab supply, 4 × ST3215, MLX90640 110°, BNO055, Pi 5, logic analyser, fasteners | open | `docs/bom/bom.csv` | C035_2026-10-12_arrivals |
| C036 | Fusion Static Stress on the Lenovo: arm_drive and pivot_bracket (6 vs 8 mm plate) | open | `cad/openscad/AR-Mini_v1.scad` — pivot_bracket 6 vs 8 mm plate | — |
| C037 | Print the black R1b plate: 2 × pivot_bracket (left + mirrored) + 2 × arch_post | Pass | `cad/stl/v1/pivot_bracket.stl`<br>`cad/stl/v1/arch_post.stl` | C037_2026-10-13_r1b-black-print |
| C038 | Cut the cable slot in both pivot_brackets by hand, so the TD-8120MG seats with its ears flat | Pass | `docs/diagrams/AR-Mini_pivot_bracket_mount.png`<br>`docs/FAILS_AND_FIXES.md` | C019_2026-10-13_linkage-fit |
| C039 | Print Pesho v3: head + lid in white PETG, then the body in red PLA (two plates) | Partial | `cad/pesho/pesho.py`<br>`cad/pesho/pesho_views.png` | C021_2026-10-12_pesho-warmer |
| C040 | Arrivals 13.10: the last Amazon batch: MLX90642-D45, soldering kit (fume extractor, third hand), wiring and prototyping parts | open | `docs/bom/bom.csv`<br>`hardware/datasheets/PCA9685.md` | C040_2026-10-13_arrivals |
| C041 | Print the thruster kick-up mounts: 2 × thruster_bracket + 2 × thruster_arm, PETG (after the CAD fix) | Pass | `cad/stl/v1/thruster_bracket.stl`<br>`cad/stl/v1/thruster_arm.stl`<br>`docs/diagrams/AR-Mini_thruster_kickup_mount.png` — side and end views, the collision and the fix<br>`docs/diagrams/src/thruster_kickup_mount.py`<br>`cad/openscad/AR-Mini_v1.scad` — th_pin_dx 19<br>`docs/FAILS_AND_FIXES.md` — 151 | C041_2026-10-15_thruster-mounts |
| C042 | Fit the thruster mounts (C005): M4 depth check, Ø5 hinge rod, M3 lock pin, 4 inserts in the transom pad, swing by hand | open | `docs/decisions/0004-kick-up-thruster-mount.md`<br>`docs/diagrams/AR-Mini_thruster_kickup_mount.png`<br>`cad/stl/v1/thruster_arm.stl` | — |
| C043 | v2 perception compute: Pi 5 (+ AI HAT) vs Jetson Orin Nano 2 — decide from the C029 numbers, January 2027 | open | — | — |

## Analyses written (seeds for the roadmap)

| Card | Activity | Impact N&P / fin / sci | When | Status |
|---|---|---|---|---|
| C021 | research | 3 / 2 / 2 | 2027 | draft |
| C041 | publication | 2 / 1 / 1 | 2027 | final |
| C032 | opensource | 1 / 1 / 0 | uni1 | final |

## Other data files worth the portfolio (not tied to one card)

- `docs/diagrams/history/2026-09-29_AR-Mini_v1_layout_BG.png` — the first drawing
- `docs/process/*` and `docs/process/history/*` — how the way of working changed (team of three → human in the loop)
- `cad/3d/AR-Mini_3D.html` — the interactive model
- `docs/bom/bom.csv` — 139 rows of parts with status (no prices)
- `docs/FAILS_AND_FIXES.md` — 152 numbered failures and fixes
- `tools/board/ar-mini-board.html` + `data/board/board.json` — the kanban itself, with goals, analyses, roadmap
- `pcb/carrier-revB/drc/` + `history/` — three DRC rounds and the board that failed the paper check
