# 0004 · Kick-up thruster mount on the transom

**Date:** 2026-10-09 · **Status:** accepted (Teddy) · **Loops:** L001 (thruster measured), L003 (plate measured) · **CAD:** v2.0

## Problem
CAD v1.9 had a flat stern pad below the waterline (44 × 44, M3 at 20 mm pitch, centre z 25) drawn before the thruster was in hand. L001 measured the Cuifati thruster: duct OD 72.27 mm, 112 long, mounting face 47.10 mm above the prop axis, M4 inserts at ~35 × 15.6, 206 g. A 72 mm duct cannot be fully under a 42 mm waterline on a pad above the hull bottom; fully submerged with 10 mm margin the duct bottom sits ~40 mm below the hull bottom, while the tracks are flush with the hull bottom. On the shore the thruster would hit the ground first. The pad also put four holes below the waterline in a 1.8 mm wall.

## Decision
- Hinge on the transom: a printed bracket bolted to a transom pad **above the waterline** (pad z 44..114, M3 inserts at z 59 / 99). No holes below the waterline.
- Pin: Ø5 aluminium rod (same stock as the cradle), 33 mm above the waterline (z 75), 14 mm aft of the pad.
- Swing arm: 50 × 30 × 5 plate on the thruster face (4 × M4 into its brass inserts), two cheeks to the pin, a forward tab as the stop against the bracket plate. Forward thrust pushes the arm onto the stop; hitting the ground pushes the duct aft and up, so it kicks up by itself.
- Lock pin (M3) through lug + cheek: "deployed" hole lets reverse thrust be used without lifting the thruster; "stowed" hole holds it up on land. Pull it before beaching.
- Deployed: prop axis z −4, duct top 10 mm under the waterline; overall length 733 mm. Kicked up 100°: duct bottom ≈ 74 mm above the hull bottom.

## Open (to measure / verify)
- Hole pattern 35.0 × 15.6 → **L005 coupon** (`thruster_coupon`, PLA, 20 min): do all four M4 go in by hand?
- Frame position along the duct (`th_frame_dx`) and the M4 screw length vs plate 5 mm + frame 9.68.
- Does 10 mm submergence hold in waves at this scale? Measure in the pool (R2).
- Reverse thrust with the lock pin out: does the arm lift? Expected yes; that is why the pin exists.

## Also in v2.0 (from L003)
ROB0154 plate measured 151.82 × 134.8; its transverse M3 slots are 11.3 mm from the forward edge (octagonal hole forward) and 26.4 from the aft edge, ≈114 mm apart. `ch_x` 290 → 300 puts them at x 385.4 / 499.5 under the beams at 385 / 500. Power-box beam holes are now 3.4 × 7 slots along x; the beam tubes are match-drilled through the plate slots on assembly. `pb_beam_y` 30 unchanged. Assumption still open: the plate is centred on the track footprint (74.1 mm from the track front) → **L004**.
