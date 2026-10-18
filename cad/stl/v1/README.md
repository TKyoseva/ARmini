# cad/stl/v1 — the STLs that were actually printed (exported from cad/openscad/AR-Mini_v1.scad)

Right-hand parts are the same STL mirrored along Y in Creality Print (`side = -1` in the .scad). Materials: hulls PETG; brackets/arch posts black PLA; moving parts orange PLA; Pesho red PLA + white PETG head/lid (Pesho's STLs are 8–34 MB and stay out of git — `cad/pesho/pesho.py` regenerates them).

| STL | Card | Printed | Notes |
|---|---|---|---|
| `hull_fore.stl` | C008 (left, white PLA fit prototype) · C022 (right, mirrored) | 10.10 · 11.10 | 305 mm section at 45° on the bed |
| `hull_aft.stl` | C034 (×2, PETG, mirrored) | 12.10 | tree supports under 2 bosses + the transom pad |
| `thruster_coupon.stl` | C011 | 11.10 | fit coupon for the thruster's M4 pattern (the C005 test was then skipped) |
| `arm_idler.stl` · `coupler.stl` · `arm_drive.stl` | C011 · C017 | 10–11.10 | linkage parts, orange |
| `pivot_bracket.stl` | C037 (×2, second mirrored) | 13.10 | 6 mm plate; cable slot drilled by hand afterwards (C038) |
| `arch_post.stl` | C037 (×2) | 13.10 | |
| `thruster_bracket.stl` · `thruster_arm.stl` | C041 (×2 each, PETG) | 14–15.10 | after FAILS 151 (`th_pin_dx` 14 → 19) |

Exported 12–14.10 with OpenSCAD (`part = "<name>"`, F6, Export STL). The whole-robot `AR-Mini_v1.stl` (10.7 MB) and `pivot_bracket_vp8.stl` (8 mm FEA variant, never printed) are not here.
