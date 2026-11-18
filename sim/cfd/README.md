# sim/cfd · hull drag vs speed (card C085)

Question: how much drag do the two hulls make between 0.2 and 1.0 m/s, so that the G2 water test has a number
to be compared with?

Tools: OpenFOAM v1912 (Ubuntu package) on 4 cores in the cloud, 18.11.2026. `snappyHexMesh` mesh on the wetted
part of the hull, `simpleFoam` with k-omega SST.

    sim/cfd/run_all.sh          # 12 runs, about 1 h; writes out/ (gitignored)
    python3 sim/cfd/report.py   # table + plot into results/ (committed)

Files: `hull_wet.scad` (the wetted hull, outline copied from `AR-Mini_v1.scad`) → `hull_wet.stl`;
`make_case.py` writes one case; `run_case.sh` meshes and solves it; `forces.py` integrates the drag.

## Inputs and where they come from

| Input | Value | Source |
|---|---|---|
| Hull | 610 × 100 mm, parabolic bow 150 mm, flat bottom, square transom | `outline2d()` in `cad/openscad/AR-Mini_v1.scad` |
| Draft | 23 mm, level trim | 2.5 kg (C063) × 9.1 mm/kg (C007 waterplane); the bathtub reading on 24.10 was 20 mm |
| Hull spacing | 350 mm centre to centre | `gap` 250 + `hull_W` 100 |
| Water | fresh, 20 °C: 998.2 kg/m³, 1.0e-6 m²/s | table value; the lake in November is colder (more viscous, a few % more friction) |
| Appendages | none | thruster, bracket, rudder and beam_leg are NOT in the model |

## What "double-body" means and why it matters

The water surface is a flat mirror: the model has friction and the pressure drag of the blunt transom, but
**no waves**. That is a fair model while the Froude number U / sqrt(g·L) is below about 0.3, here about
0.7 m/s. Above it a real hull also makes waves, and the square transom starts to run dry, which changes
its pressure drag. So the 0.8 and 1.0 m/s rows are a LOWER bound for the bare hulls, not a prediction.

## Limits (read before quoting a number)

1. No waves, no trim or sinkage, no wind, no thruster duct (Ø72 mm, most of it under water) and no rudder.
   The duct alone can add drag of the same order as one hull.
2. The flow is treated as fully turbulent. At these Reynolds numbers (1e5 to 6e5) part of the real boundary
   layer is laminar, so the friction here is on the high side at 0.2 to 0.4 m/s.
3. Steady solver behind a square transom: the real wake sheds vortices; the steady answer is an average.
4. The Ubuntu OpenFOAM package crashes on every function object ("sha1" stream error), so the drag is
   integrated afterwards by `forces.py` (same definition as OpenFOAM's `forces`). Checked against the
   ITTC-57 friction line in `results/results.md`.
5. Not compared with any measurement yet. C061 (thrust) and a timed run on the lake give the second route:
   at steady speed, thrust = drag.

## Result in one paragraph (18.11.2026)

Both hulls together: 0.05 N at 0.2 m/s, 0.42 N at 0.6 m/s, 1.13 N at 1.0 m/s (no waves, no appendages).
More than half of it is pressure drag of the square transom, not friction. The catamaran equals twice one hull
within 1 %: at 350 mm the hulls do not disturb each other in this model. Mesh check at 0.6 m/s: 3 meshes,
the two finest differ by 4.6 %, and the pressure part is still falling with refinement, so read the numbers as ±10 %.
Six of the 12 runs met the residual targets; the other six (0.6 m/s catamaran and fine mesh, all at 0.8 and 1.0 m/s) stopped at
the 2000-iteration limit with residuals near 1e-6, as expected behind a square transom (limit 3).
