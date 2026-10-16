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
| C007 | 2026-10-11 | hull_fore in the bathtub: floats, leaks, draft | Pass | C007_2026-10-11_bathtub |
| C008 | 2026-10-10 | Print hull_fore (PLA white fit prototype, 4 walls, 0.2, diagonal; tree supports under the 2 rim bosses) | Pass | C008_2026-10-10_hull-fore-print |
| C010 | 2026-10-09 | GitHub: PR for T1 (state machine) → CI green? → merge into dev | Pass | C010_2026-10-09_devkit-module |
| C011 | 2026-10-11 | Print the orange plate: thruster_coupon + 2 arm_idler + 2 coupler + 1 arm_drive (PLA orange, external spool, ~1 h 20) | Partial | C011_2026-10-11_orange-plate |
| C015 | 2026-10-11 | GPIO39 at reset: is the left BTS7960 RPWM pulled high during boot? | Partial | C015_2026-10-11_gpio39-boot |
| C017 | 2026-10-10 | arm_drive (orange PLA) on the TD-8120MG disc horn: does it fit? | Pass | C017_2026-10-10_arm-drive |
| C019 | 2026-10-13 | 2 × pivot_bracket (black PLA) + 2 × TD-8120MG + linkages: do they assemble and swing? | open | C019_2026-10-13_linkage-fit |
| C021 | 2026-10-12 | Pesho v3 printed: warmer fits, lid closes, floats head out (thermal) and face-up (cradle) | open | C021_2026-10-12_pesho-warmer |
| C022 | 2026-10-11 | R1b frame: right hull_fore (mirrored, white) + 2 × arch_post (black) + the arch tube | open | C022_2026-10-11_r1b-frame |
| C030 | 2026-10-11 | Freeze the DevKit-Lipo pinout before the perfboard and the PCB | open | C030_2026-10-11_devkit-pinout |
| C032 | 2026-10-13 | Carrier rev B (DevKit-Lipo) → KiCad → DRC → 1:1 paper check → order 3 at Aisler | open | C032_2026-10-13_carrier-revB |
| C034 | 2026-10-12 | Print hull_aft x2 in PETG (left, then right mirrored): 2 x ~7-8 h, tree supports under 2 bosses + the transom pad | open | C034_2026-10-12_hull-aft-print |
| C035 | 2026-10-12 | Arrivals 12.10: lab supply, 4 × ST3215, MLX90640 110°, BNO055, Pi 5, logic analyser, fasteners | open | C035_2026-10-12_arrivals |
| C037 | 2026-10-13 | Print the black R1b plate: 2 × pivot_bracket (left + mirrored) + 2 × arch_post | Pass | C037_2026-10-13_r1b-black-print |
| C038 | 2026-10-13 | Cut the cable slot in both pivot_brackets by hand, so the TD-8120MG seats with its ears flat | Pass | C019_2026-10-13_linkage-fit |
| C039 | 2026-10-12 | Print Pesho v3: head + lid in white PETG, then the body in red PLA (two plates) | Partial | C021_2026-10-12_pesho-warmer |
| C040 | 2026-10-13 | Arrivals 13.10: the last Amazon batch: MLX90642-D45, soldering kit (fume extractor, third hand), wiring and prototyping parts | open | C040_2026-10-13_arrivals |
| C041 | 2026-10-15 | Print the thruster kick-up mounts: 2 × thruster_bracket + 2 × thruster_arm, PETG (after the CAD fix) | Pass | C041_2026-10-15_thruster-mounts |
