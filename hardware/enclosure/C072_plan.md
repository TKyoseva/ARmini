# C072 · Electronics on perfboard in the two IP65 boxes

rev 1 04.11.2026 · rev 2 05.11.2026 (boxes measured from ruler and caliper photos) · status: Backlog

Drawings: `docs/diagrams/C072_diagram_boxes.png` (both boxes, top view) and `docs/diagrams/C072_diagram_perfboards.png` (P1, P2, P4, P5 top and bottom + netlist). Sources: `docs/diagrams/src/c072/` (`boards.py` checks that no hole carries two nets and every net is connected; `render_boards.py`, `render_boxes.py`). Tray: `cad/openscad/C072_logic_tray.scad`.
Base: FINAL 2 breadboard (31.10, 15 wire groups) + BNO055 (C066, 3V3) + leak probe (C068). The nets are the same as carrier rev B (`pcb/carrier-revB/SPEC.md`), so firmware `remote_pool` runs unchanged. Perfboard is the step between the breadboard (C031) and the PCB (C032).

## Summary

- **Boxes:** use the two LANUCN IP65 boxes; print only the inner trays, the beam saddles and the probes. No printed boxes.
- **POWER box 200 × 100 × 70 (BOM 155):** LiPo, 30 A fuse + XT60, S1, fuse block, both bucks (QIQIAZI and MZHOU), GND bus.
- **LOGIC box 150 × 110 × 70 (BOM 26):** DevKit, 74HCT125, PCA9685, BNO055, leak probe. No inductors and no 12 V inside except the VBAT sense wire (≈ 100 µA), so the magnetometer stays clean.
- **Logic board (05.11 decision):** ONE Elimex EXP14 double-sided perfboard (BOM 156) cut to 100 × 80 with 4 × Ø3.2 holes on 93 × 73 = the rev B outline. Parts go where the rev B 1:1 print puts them, so the rev B PCB later drops onto the same 4 standoffs. The older three-board layout (P1 50×70, P2 30×70, P4 30×70) stays in the drawings and in the tray's `layout = "split"`.
- **Glands: 6 × M20 × 1.5 that came with the boxes**, Ø20 hole with the supplied hole saw. PG7 is not needed (BOM 25 = 0). Unused positions are not drilled, so no blind plugs.
- **Measured 05.11:** inner size at the rim power ≈ 94 × 192 mm, logic ≈ 106 × 146 mm (± 2 mm), base depth ≈ 55 mm + lid. Bosses on the floor of both boxes → the trays screw in, no silicone and no holes in the floor.

## Printed boxes or IP65

| | printed PETG box (K2 Pro) | LANUCN IP65 |
|---|---|---|
| Water | PETG leaks between layers unless the walls are 100 % dense; needs a seal groove + TPU gasket (not on hand) | IP65 with gasket and 4 lid screws, already here |
| Time | ≈ 10–14 h of printing + lids + trials | 0 h |
| Risk | untested seal = another test cycle | tested by the maker |

Decision: IP65 boxes outside, printed trays inside (≈ 6–8 h PETG in total). IP65 = water jets, not immersion → a leak probe in each box and a tub test.

## Layout

The boxes sit side by side across the two beams (115 mm between the beams), 40 mm apart, fronts in line. Power to port (heavier, closer to the centre), logic to starboard.

**Power (inside ≈ 94 × 192):** both bucks at the bow; LiPo at the stern on the port side in a printed cradle with a strap; fuse block to starboard; GND bus on the fuse block. S1 on the lid above the battery. Glands: P1 left thruster (stern), P2 the round H1 + H2 bundle to the logic box (starboard, towards the stern). The right thruster (C065) gets its own hole when it arrives.

**Logic (inside ≈ 106 × 146):** the board 80 mm across, antenna to starboard over the edge, USB-C to port. Only ≈ 10–13 mm remain to the walls → the MZHOU → DevKit USB-C needs a **90° angled plug** (BOM 159). BNO055 at the stern end (≥ 80 mm from the PCA9685 V+, ≥ 20 mm from anything carrying current), arrow to the bow. KILL on the lid (BOM 157). Leak probe P5 in a pocket on the floor (lowest point). Glands: L1 bundle from the power box (port), L2 lift A + B, L3 rudder, L4 cameras MLX90640 + XIAO + D45 — L2–L4 in the three knockouts on the starboard wall. The bow wall stays blank.

## Circuit (same values as FINAL 2)

- VBAT divider R1 100k / R2 30k / C1 100 nF on GPIO4 (unchanged, so the calibration stays).
- Leak: R3 10k pull-up + R4 4k7 on GPIO7; two probes in parallel (J9 logic, J9b power via H2); water pulls GPIO7 to GND.
- KILL: R5 10k pull-up on GPIO14, J10 RUN / C / KILL.
- 74HCT125 in a DIP-14 socket (BOM 145), C2 100 nF, R6 10k pull-down on 1A. J2 ESC (S · NC · GND), J3 rudder (S · + · −), C3 220 µF at J3.
- I²C-0 hub: PCA9685 (GND, OE, SCL, SDA, VCC), BNO055, D45, XIAO 5 V. I²C-1 to the MLX90640. Space kept for C069 (hardware KILL through OE).
- BNO055 Vin = 3V3, never 5 V.

## Cables between the boxes and out

| cable | glands | wires | from → to |
|---|---|---|---|
| H1 power | P2 → L1 | 2 × 18 AWG + 2 USB wires | QIQIAZI → PCA9685 V+ / GND (ferrules); MZHOU USB-C cable cut, end passed through, spliced inside the power box |
| H2 signals | P2 → L1 (same bundle) | 5–7 × 22 AWG | F4 (12 V, 5 A) → VBAT sense; GND; power-box leak probe → J9b; thruster signal → J2 |
| thruster L | P1 | power + signal | red → F1 20 A, black → GND bus; signal → H2 (measure which pin is ≈ 5 V first) |
| lift A + B | L2 | 2 × 3 | servo extensions (BOM 153) → PCA9685 CH12 / CH13 (firmware numbering, from 0) |
| rudder | L3 | 3 | MG90S → J3 |
| cameras | L4 | 4 + 2 (+ 4 D45) | MLX90640 → I²C-1, XIAO → 5 V, D45 → I²C-0 |

M20 rule: a gland seals only a **round** cable within the range printed on it (usually 6–12 mm). A loose bundle does not seal → make it round with Ø10–12 mm heat-shrink over 25 mm and neutral silicone inside before shrinking. Pass every cable through with a bare end, crimp the connector inside afterwards. Twist the power pairs (magnetometer). Tie every long wire to the tray — the lake lesson: three wires worked loose in one day.

## Assembly order

0. Measure. Done 05.11: inner sizes, depth, bosses, M20 glands. Still needed (caliper): perfboard corner-hole Ø, fuse block / QIQIAZI / MZHOU sizes for the power tray, thruster cable Ø, the range printed on the M20 gland.
1. Photo of the breadboard as it is (C072_01…), then take it apart group by group (FINAL 2).
2. Logic board: female headers by the "sandwich" method (DevKit inside, 2 corner pins first, then all 44), resistors, capacitors, connectors, bare buses, then insulated wires. Continuity test against the netlist; **no beep between 3V3, +5V and GND**. The 74HCT125 goes in after the test.
3. Bench test over USB: `remote_pool` unchanged. I²C scan 0x40 + 0x70 (PCA), 0x28 (BNO), 0x66 (D45), 0x33 (MLX90640 on I²C-1). J2: 1500 µs, 5 V. Rudder centred. KILL works.
4. Print: power tray, logic tray, 2 beam saddles (PETG 240–250 °C).
5. Gland holes Ø20 with the hole saw: centre ≥ 18 mm below the lid edge, ≥ 32 mm between glands; trial hole in scrap first. S1 Ø12 and KILL Ø19 in the lids.
6. Power: tray → fuse block → bucks → GND bus → battery. Solder the MZHOU splice.
7. Logic: tray → board → probe → plug in the cables.
8. Power-on order (FINAL 2): KILL → S1 → 5.0–5.2 V at the MZHOU plug → 4.6–5 V at chip pin 14 → 5 V on V+ → WiFi → ARM.
9. **Leak test (C072 pass):** paper tissue in both boxes, 3 min shower from above and 10 min floating in the tub; tissues stay dry. A drop of water on each probe → GPIO7 = 0 (C068 adds SAFE).
10. Weigh the robot (C063 was 2.5 kg).

## Logic tray (`cad/openscad/C072_logic_tray.scad`)

- Bosses in the 150 box: two rows 63.80 mm apart (caliper), a pair 13 mm apart, singles at the long walls, a centre pin, 4 knockout rings in the floor (never opened). 200 box: 4 × 2 boss grid at 36.18 mm (caliper), winged bosses at the walls, 4 rings.
- Plate 96 × 134 × 3 mm, lifted 12 mm above the floor (clears the rings), 4 × M3 × 20 (BOM 154) into the bosses at (±32, +23) and (±41, 0), slotted ± 3 mm because the positions come from photos.
- `layout = "carrier"` (default): 4 standoffs 8 mm for ruthex M3 inserts (BOM 18) on 93 × 73, board centre (0, 6). `layout = "split"`: the old P1 / P2 / P4 standoffs + the standing PCA9685 wall.
- Print the FIT template first (`part = "fit"`, 0.8 mm, ≈ 10 min): the 4 Ø4 holes must sit over the bosses and the 4 large circles around the rings. Any offset → edit the measure block at the top of the SCAD.
- STLs are generated from the SCAD; they go to `cad/stl/` only after the tray is printed and fits.
- Power tray: waits for the fuse block, QIQIAZI and MZHOU sizes.
