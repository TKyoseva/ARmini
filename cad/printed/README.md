# cad/printed — every part printed for AR-Mini (as of 31.10.2026)

One scene with all 19 printed models laid out side by side (615 × 431 mm), for Fusion 360 and for portfolio slide P26.

| File | What | Open in Fusion 360 |
|---|---|---|
| `AR-Mini_printed_parts.step` | 17 solid bodies (B-rep, named `<part> x<qty>`, coloured by filament). Pesho's head and body are organic meshes and are **not** in the STEP | File → Open → the .step. Bodies can be measured, sectioned and edited |
| `AR-Mini_printed_parts.3mf` | all 19 models as mesh bodies (Pesho decimated to 120 k triangles per part) | File → Open → the .3mf (mesh bodies; Mesh → Convert Mesh if you need solids) |
| `src/` | how they were made: `parts.py` (list + print data), `layout.py` (3MF), `step.py` (STEP via OCP), `render.html` + `shoot.js` (three.js renders), `slide.py` (P26) | — |

Sources: `cad/stl/v1/*.stl` (STLs that were printed) and `build/pesho_*.stl` (Pesho, not in git, regenerate with `cad/pesho/pesho.py`).
The STEP is made from the printed STL triangles with coplanar faces merged, so flat faces are clean and round faces are faceted. Volumes match the STLs to 0.1 cm³.

## What was printed

| Model | Qty | Card | Material | Printer screen |
|---|---|---|---|---|
| hull_fore | 2 (R = mirror Y) | C008 · C022 | white PLA | 6 h 16 / 6 h 17 · 345 g each |
| hull_aft | 2 (R = mirror Y) | C034 | white PETG | 7 h 30 / 7 h 34 · 410 g each |
| arm_drive | 2 | C017 · C011 | orange PLA | C017 alone 0 h 20 · 13 g |
| arm_idler, coupler | 2 + 2 | C011 | orange PLA | plate with one arm_drive: 1 h 12 · 41 g |
| pivot_bracket, arch_post | 2 + 2 | C037 | black PLA | one plate: 5 h 45 · 176 g |
| pesho_head + pesho_lid | 1 + 1 | C039 | white PETG | ~1 h 40 (no screen photo, no grams) |
| pesho_body | 1 | C039 | red PLA | 4 h 44 · 143 g |
| thruster_bracket, thruster_arm | 2 + 2 | C041 | white PETG | one plate: 2 h 52 · 96 g |
| beam_bracket | 8 | C045 | black PLA | one plate: 1 h 14 · 39 g |
| cam_fixed_mount | 1 | C047 | black | 1 h 24 · 39 g |
| beam_leg | 1 | C056 | black PETG | 2 h 37 · 123 g |
| rudder_mount, rudder_blade, rudder_hub + 1 thruster_bracket | 1 + 1 + 1 + 1 | C057 | black PETG | one plate: 3 h 09 · 103 g |
| rudder_frame | 1 | C057 | black PETG | 2 h 27 · 104 g |

Totals: 19 models, 36 parts, 15 print jobs (10.10 → 29.10.2026), ≈ 55 h, 2387 g (with supports and brim; Pesho head + lid not weighed).

Designed but **not** printed: `thruster_coupon` (skipped 11.10, C011), `cam_pan_mount`, `power_box` / `power_lid`, `pivot_bracket_vp8` (FEA variant). `rudder_mount` was printed but did not fit the duct (C057) and was replaced by `rudder_frame`.
