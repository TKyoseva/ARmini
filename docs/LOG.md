# Build log

Format: date · who · what I tried · what happened · what I change. Three lines are enough. Photos: card ID → iCloud folder (media/LINKS.md).

## 2026-10-04 (Sun) · Dimi
- Bauhaus: profiles, rod, silicone, Sikadur, tools. BOM v04.10.
- Repository created.
- Tomorrow: print the arms and couplers (PLA), measure the TD-8120MG (bottom → ears).

## 2026-10-05 (Mon) · Dimi
- Measured the TD-8120MG: bottom → ears 28.0, holes 10 mm, Ø4.34, shaft 10.4 from the front edge → CAD v1.8.
- XIAO breakout rev 0: DRC 32 → 19 → 15 (library warnings only) in three rounds. Ready for AISLER.
- 7 rolls of PLA → colour code. Tomorrow: print the arms and couplers.

## 2026-10-06 (Tue) · Dimi
- Ordered 3 × ESP32-S3-DevKit-Lipo + 3 × WROOM-1 N16R8 (Comet) and prototyping and soldering supplies (Amazon).
- BOM in one spreadsheet (120 items with photos), visual BOM, architecture diagram v1.
- 3D model of the whole robot → saw that the two beams pass through the power box → CAD v1.9: the box sits on the beams.
- The thruster and 2 × Bus Servo Adapter (A) arrived. The thruster is 112 mm long, 77 mm high (box) and mounts from the top — the CAD is for a different mount. Tomorrow: measurements + multimeter (ESC inside or bare motor?).
- Created the repository.

## 2026-10-07 (Wed) · Teddy
- Arrived: DevKit-Lipo + WROOM-1 (Comet), UT61E+, caliper, PETG 4 kg, servo driver, light and stands for filming. BOM v4 (133 rows).
- Breadboard sheets: motor/servo bench, XIAO controller, DevKit-Lipo. R10 on the carrier → 2.2 k pull-up (OE).
- New plan: I build alone, with AI agents; human in the loop. Deadline: portfolio on 01.11. Test tracker, repo rules for Cursor, checks in GitHub Actions.
- Tomorrow: measure the thruster, test its wires (no 12 V), measure the plate slots.

## 2026-10-08 (Thu) · Teddy
- C001 thruster measured: duct Ø72.27 (box says 77) × 112, mounting face 47.10 above the axis, M4 at ~35 × 15.6, 201 g. Partial: the listing dimensions are not real.
- C002 thruster wires: 4 wires, no shorts, asymmetric resistances → ESC inside. Pass.
- First night task (T1, mission state machine) given to a Cursor background agent.

## 2026-10-09 (Fri) · Teddy
- C003 ROB0154 plate: 151.82 × 134.8, slots land 10 mm off the beams with ch_x 290. Fail → CAD v2.0: ch_x 300.
- CAD v2.0: kick-up thruster mount on the transom from the C001 numbers (decision 0004). The tracker became a kanban board with cards C###.
- Specs for the parts agent (T4) and the release video agent (T5). Photos renamed to card IDs, captions written.

## 2026-10-18 (Sun) · Teddy
- Release R-1018 cut from Done (8 cards: C011, C015, C035, C037, C038, C039, C040, C041): R1b parts printed and fitted by hand, boot-safe motor pins, all parts in. Page: docs/releases/R-1018.md, tag r2026-10-18.

## 2026-10-24 (Sat) · Teddy
- C025 right thruster: it only clicks, on either channel (FAILS 173). The left thruster on the right channel (GPIO2, row 13) spins with no clicking → GPIO2 stage OK, the right thruster (ESC or motor inside) is faulty → claim with the seller.
- C028 first float of the whole robot (bathtub, tethered): stable, draft 20 mm, dry hulls; driven from the phone over WiFi on the left thruster only, 1640 µs · 0.58 A at 12 V. Partial (second thruster, range walk, pool still open).
- Release R-1024 cut from Done (13 cards: C005, C006, C019, C020, C022, C023, C024, C025, C027, C028, C034, C042, C045): frame with beams, arch and arm; arm lifts Pesho; thruster from the DevKit and the phone; the robot floats and moves. Page: docs/releases/R-1024.md, tag r2026-10-24.
