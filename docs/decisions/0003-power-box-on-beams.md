# 0003 · The power box sits on the beams (2026-10-06)

Context: from v1.5 to v1.8 the box stood on the ROB0154 plate (z 124.6–193.6), and the two 15 × 15 cross-beams (x 385 and 500, z 126–141) passed through it. This did not show in 2D or in the collision check, because the check only looked at moving parts. I saw it in the first 3D view.

Decision (CAD v1.9): the bottom of the box rests on the beams (z 141, lid 210). Rails under the bottom on both sides of each beam hold it in x. 4 × M3×30 with washers go bottom → tube → plate slot → nut, so one bolt holds all three parts. The mounts for the BTS7960 and the fuse block are printed bobbins with brass inserts, because the beams are now under the old holes.

Consequences: +16.4 mm height, nothing else moves (the stowed cradle ends at x 286, the box starts at 364). To measure: `pb_beam_y` (the plate slots under the beams) and `pb_fuse_x` (the feet of the fuse block). The blue PLA box from 03.10 stays as a test piece; the PETG box is from v1.9.
