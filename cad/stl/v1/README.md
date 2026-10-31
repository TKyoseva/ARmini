# cad/stl/v1 — the STLs that were actually printed (exported from cad/openscad/*.scad)

Right-hand parts are the same STL mirrored along Y in Creality Print (`side = -1` in the .scad). Materials: hulls PLA (fore) and PETG (aft); brackets/arch posts black PLA; moving parts orange PLA; everything for the pool/lake run black PETG; Pesho red PLA + white PETG head/lid (Pesho's STLs are 8–34 MB and stay out of git — `cad/pesho/pesho.py` regenerates them).
All printed parts laid out in one scene for Fusion 360 (STEP + 3MF): `cad/printed/`.

| STL | Card | Printed | Notes |
|---|---|---|---|
| `hull_fore.stl` | C008 (left, white PLA fit prototype) · C022 (right, mirrored) | 11.10 · 12.10 | 305 mm section at 45° on the bed |
| `hull_aft.stl` | C034 (×2, PETG, mirrored) | 12.10 · 13.10 | tree supports under 2 bosses + the transom pad |
| `thruster_coupon.stl` | C011 | **not printed** | fit coupon for the thruster's M4 pattern; skipped 11.10, the thruster_arm itself was the test (C005) |
| `arm_idler.stl` · `coupler.stl` · `arm_drive.stl` | C011 · C017 | 10–11.10 | linkage parts, orange; arm_drive printed twice |
| `pivot_bracket.stl` | C037 (×2, second mirrored) | 13.10 | 6 mm plate; cable slot drilled by hand afterwards (C038) |
| `arch_post.stl` | C037 (×2) | 13.10 | |
| `thruster_bracket.stl` · `thruster_arm.stl` | C041 (×2 each, PETG) | 14–15.10 | after FAILS 151 (`th_pin_dx` 14 → 19); a third thruster_bracket in black PETG on the C057 plate |
| `beam_bracket.stl` | C045 (×8, black PLA) | 20.10 | one plate, 1 h 14 · 39 g |
| `cam_fixed_mount.stl` | C047 (black) | 23.10 | 2 thermal cameras + XIAO Sense on the arch tube |
| `beam_leg.stl` | C056 (black PETG) | 29.10 | from `beam_leg.scad`; thruster on the centreline under the beams |
| `rudder_mount.stl` · `rudder_blade.stl` · `rudder_hub.stl` | C057 (black PETG) | 29.10 | from `rudder.scad`; rudder_mount's collar did not fit the duct → replaced by rudder_frame |
| `rudder_frame.stl` | C057 (black PETG) | 29.10 | from `rudder_frame.scad`; assembled 30.10 |

Exported with OpenSCAD (`part = "<name>"`, F6, Export STL). The whole-robot `AR-Mini_v1.stl` (10.7 MB), `pivot_bracket_vp8.stl` (8 mm FEA variant), `cam_pan_mount.stl`, `power_box.stl` / `power_lid.stl` were never printed and are not here.
