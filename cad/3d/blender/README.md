# Blender scene: the planned rescue cycle (C086)

An animation of the plan, built from the CAD in this repo. It is not a test and shows no measurement: the motion is keyframed by hand, there is no physics. The measured version of this cycle is card C073.

## What is in the scene

| Group | Source | Note |
|---|---|---|
| hulls, beam brackets, arch posts, pivot brackets, camera mount, lift arms, couplers, thruster bracket and arm | `cad/openscad/AR-Mini_v1.scad` | modules placed as in `assembly()` |
| beam_leg | `cad/openscad/beam_leg.scad` | lowered 4 mm: it was drawn for the measured beam height 130, the v1 CAD has 126 |
| rudder mount, blade, hub | `cad/openscad/rudder.scad` | blade turns ±25° in the return turn |
| Pesho | `cad/pesho/pesho.py` | decimated to about 30 000 triangles |
| thruster | simplified | duct Ø72.27 × 112 mm as measured in C001, not the real shape |
| two boxes on the beams | simplified | plain blocks 200 × 100 × 70 and 150 × 110 × 70 mm, the C072 plan; not built yet |
| cradle U, beams, arch tube | simplified | Ø5 rod and 15 × 15 tube |

Not in the scene: servos, cables, battery, tracks. Colours follow the prints where known (white hulls, black brackets, orange arms, red and white Pesho); the rest is neutral.

## The four steps (25 s, 24 fps, 600 frames)

1. Search, frames 1–96: the boat drives 2.6 m toward the dummy.
2. Approach, 97–215: cradle down at 215°, rods 34 mm under the waterline (draft 42 mm).
3. Lift, 216–383: both arms turn 215° → 120°, the parallelogram keeps the cradle level.
4. Return, 384–600: half circle of radius 0.55 m, then straight back.

The speeds, the turn radius and the lift angle are choices for the picture. C061, C065 and C064 replace them with measured values.

## Run

```
blender -b -P cad/3d/blender/scene.py -- --stills          # 3 stills 1920 × 1080 into out/
blender -b -P cad/3d/blender/scene.py -- --anim            # 600 frames into out/frames/, MP4 if ffmpeg is on the PATH
blender -b -P cad/3d/blender/scene.py -- --save out/scene.blend   # open it in Blender and change what you like
```

Options: `--res 1280 720`, `--samples 48`, `--step 2`, `--frame 300`, `--cpu`, `--out DIR`. A stopped `--anim` run continues with the missing frames. Cycles, GPU when Blender finds one. Written for Blender 4.2 to 5.x; tested with the `bpy` 5.3 module on Linux (CPU).

`out/` is ignored by git. The three stills in `renders/` were rendered in the cloud on 19.11.2026 (CPU, 48 samples). The MP4 goes to iCloud `01_Loops/C086_2026-11-18_blender-renders/`, not into the repo.

## Rebuild the parts

`parts/*.stl` are derived files (binary STL, mm, world coordinates of `AR-Mini_v1.scad`; the moving parts have their pivot on the origin). They are committed because the Mac has no OpenSCAD.

```
cad/3d/blender/export_parts.sh     # needs openscad and python3 with numpy, scikit-image, pyvista
```

`parts.scad` picks one group per run; `parts/kinematics.txt` is its echo (pivot, arm length, angles) and is read by `scene.py`.
