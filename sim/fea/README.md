# sim/fea · static strength of the thruster mount (card C083)

Question: do the two printed PETG parts that carry the thruster, `beam_leg` (C056) and `thruster_bracket`,
hold the thrust with a safety factor of at least 3?

Tools: Gmsh 4.12 (mesh, second-order tetrahedra C3D10) and CalculiX 2.21 (linear static). Run on Linux in the
cloud on 18.11.2026; the same script runs on any machine with `gmsh`, `ccx`, numpy, scipy and matplotlib.

    python3 sim/fea/run_fea.py      # about 9 minutes; writes results/ (committed) and out/ (gitignored)

## Inputs and where they come from

| Input | Value | Source |
|---|---|---|
| Geometry | `beam_leg.geo`, `thruster_bracket.geo` | retyped from `cad/openscad/beam_leg.scad` and `module thruster_bracket()` in `AR-Mini_v1.scad` |
| Material | E 2100 MPa, nu 0.38, yield 25 MPa | "PETG printed", FAILS_AND_FIXES 35 (yield = half of the filament value); nu typical for PETG |
| Target | safety factor ≥ 3 | FAILS_AND_FIXES 35 |
| Thrust | 20 N | **ASSUMED, not measured.** No datasheet number exists for the Cuifati 560 KV. Replace with the C061 tub measurement |
| Thrust line | prop axis 79.1 mm below the hinge pin | `th_axis_z`, `th_pivot_z` in `AR-Mini_v1.scad` |

The model is linear, so every result scales with the thrust. `results/results.md` gives MPa per newton, so the
C061 number can be put in without a new solve.

## Load path

Forward thrust acts on the prop axis, 79.1 mm below the hinge pin. The swing arm is held by the Ø5 hinge pin
(force only) and the M3 lock pin 10 mm from it. The lock pin carries the whole moment:
lock force = thrust × 79.1 / 10 = 7.9 × thrust, hinge pin force = 7.4 × thrust. In the CAD the stop tab of the arm ends at x = 11 mm and the bracket plate face is at x = 6 mm (the pin moved
from 14 to 19 mm), so the tab is 5 mm short of the plate and is not counted. TO CHECK on the printed parts.

- `thruster_bracket`: back face fixed (it is bolted to the pad), the pin and lock holes of both lugs loaded.
- `beam_leg`: both beam channels fixed, the four insert holes of the deep rows (z 29 and 69) loaded by the thrust
  on the prop axis (z −34.1).

## Limits of this model (read before quoting a number)

1. Isotropic material. A printed part is weaker between layers. Both parts are printed so that the load lies in
   the layer plane; the 25 MPa yield is the project's allowance for print quality, not a measured value.
2. Pins and bolts are rigid and the beam channels and the bracket back face are fully fixed. Real clamping is softer.
   Stress closer than 3 mm to those faces is left out of the peak because it is an artefact of the rigid constraint;
   the pin bearing pressure is checked by hand instead (in `results.md`).
3. Static load only: no fatigue, no impact (hitting the bottom, lifting the boat by the thruster), no creep in
   warm water.
4. Not checked against a physical test. A dry pull test with the luggage scale on the thruster (BOM row 139)
   would be the second independent route.
