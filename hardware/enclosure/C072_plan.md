# C072 · Electronics on perfboard in the two IP65 boxes

rev 1 04.11.2026 · rev 2 05.11.2026 (boxes measured from ruler and caliper photos) · rev 3 06.11.2026 (one EXP-14 logic board, measured; see the last section) · status: Backlog

Drawings: `docs/diagrams/C072_diagram_boxes.png` (both boxes, top view, rev 3), `docs/diagrams/C072_diagram_carrier_exp14.png` (the single logic board on the EXP-14, top and bottom + netlist, rev 3) and the superseded `docs/diagrams/C072_diagram_perfboards.png` (P1, P2, P4, P5). Sources: `docs/diagrams/src/c072/` (`boards.py` / `boards_c0.py` check that no hole carries two nets and every net is connected; `render_boards.py`, `render_c0.py`, `render_boxes.py`). Tray: `cad/openscad/C072_logic_tray.scad`.
Base: FINAL 2 breadboard (31.10, 15 wire groups) + BNO055 (C066, 3V3) + leak probe (C068). The nets are the same as carrier rev B (`pcb/carrier-revB/SPEC.md`), so firmware `remote_pool` runs unchanged. Perfboard is the step between the breadboard (C031) and the PCB (C032).

## Summary

- **Boxes:** use the two LANUCN IP65 boxes; print only the inner trays, the beam saddles and the probes. No printed boxes.
- **POWER box 200 × 100 × 70 (BOM 155):** LiPo, 30 A fuse + XT60, S1, fuse block, both bucks (QIQIAZI and MZHOU), GND bus.
- **LOGIC box 150 × 110 × 70 (BOM 26):** DevKit, 74HCT125, PCA9685, BNO055, leak probe. No inductors and no 12 V inside except the VBAT sense wire (≈ 100 µA), so the magnetometer stays clean.
- **Logic board (rev 3, 06.11):** ONE Elimex EXP-14 double-sided perfboard (BOM 156), measured ≈ 100 × 90 mm with 4 factory holes ≈ 76.0 × 90.1 mm. It is **not cut and not drilled**: the tray standoffs follow the factory holes and the rev B PCB takes the EXP-14 outline and holes later, so it drops onto the same 4 standoffs. Layout: `C072_diagram_carrier_exp14.png`. The older three-board layout (P1 50×70, P2 30×70, P4 30×70) stays in `C072_diagram_perfboards.png` and in the tray's `layout = "split"`.
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
- `layout = "carrier"` (default): 4 standoffs 8 mm for ruthex M3 inserts (BOM 18) on the EXP-14 factory holes 76.0 × 90.1, shifted 1.35 mm toward the stern (hole insets ≈ 6.3 mm bow / 3.6 mm stern), board centre (0, 6). The FIT template also carries a 0.4 mm groove with the board outline. `layout = "split"`: the old P1 / P2 / P4 standoffs + the standing PCA9685 wall.
- Print the FIT template first (`part = "fit"`, 0.8 mm, ≈ 10 min): the 4 Ø4 holes must sit over the bosses and the 4 large circles around the rings. Any offset → edit the measure block at the top of the SCAD.
- STLs are generated from the SCAD; they go to `cad/stl/` only after the tray is printed and fits.
- Power tray: waits for the fuse block, QIQIAZI and MZHOU sizes.

## One board: Elimex EXP-14 (rev 3 · 06.11)

Bought 06.11 (BOM 156). From the photos the board is **100 × 90 mm** (the shop says 86), green double-sided FR-4 with plated holes, 2.54 mm grid ≈ 30 × 36 pads plus a blank ≈ 11 mm strip along one long edge. The 4 factory holes are ≈ **76.0 × 90.1 mm** apart (caliper 76.02 / 91.19 with the jaw tips in the holes). They do not match the rev B grid (93 × 73) and new holes would overlap them, so the board is **not cut and not drilled**: the tray gets standoffs on the factory holes and carrier rev B (C032) takes the EXP-14 outline and holes later.

Drawing: `docs/diagrams/C072_diagram_carrier_exp14.png` (top and bottom + netlist; sources `docs/diagrams/src/c072/boards_c0.py`, `render_c0.py`; 32 nets, machine-checked: no hole carries two nets, every net is one connected piece; 56 bare bridges, 25 insulated wires). Columns 1–30 port → starboard, rows 1–36 bow → stern (if the board has 37 rows the last one stays empty).
- **Bow (rows 1–13):** PCA9685 on two female 1×6 (columns 4 and 26, rows 4–9); servo field and V+ terminal face the bow wall; V+ comes only through the terminal from the QIQIAZI buck, the V+ header pin stays unconnected. VBAT divider R1 100k / R2 30k / C1 100 nF next to J1 (column 2, rows 12–13), so 12 V stays in columns 2–4. J13 XIAO 5 V and J7 MLX90640 (I²C-1) on column 30.
- **DevKit (rows 14 and 24):** EXT1 is the bow row (pin 1 = 3V3 at the antenna end), EXT2 the stern row (pin 1 = GND); pin n = column 31 − n. Antenna over the blank strip (starboard), USB-C to port → **90° adapter** (BOM 159). Under the DevKit only bottom-side wires.
- **Stern (rows 25–36):** U6 74HCT125 in a socket (notch to port, pin 1 = column 4, row 30), R6 10k, C2 100 nF; J2 ESC on column 2 (rows 26–28); J3 rudder + C3 220 µF and J6 D45 (I²C-0) on column 30; BNO055 on female 1×6 + 1×4 (columns 18 / 25, rows 28–33, arrow to the bow); leak R3 10k / R4 4k7 + J9b / J9 and KILL R5 10k + J10 on row 35.
- **Check before soldering:** on the DevKit, antenna to the right and USB-C to the left, the row toward the bow must be EXT1: its two pins nearest the antenna beep together (both 3V3); on EXT2 they do not (GND, TX). If it is the other way round the layout is re-routed (not mirrored: the DIP and the BNO055 have a handedness).
- In the box (`C072_diagram_boxes.png` rev 3): board centred across (8 mm to the walls), 17 mm from the bow; L1 on the port wall ≈ 70 mm from the bow (the bundle fans out to the terminal, USB-C, J1, J2, J9b); L2 = lift + XIAO + MLX90640, L3 rudder, L4 D45. **The Ø19 KILL button goes in the lid over the free stern strip** (its body hangs ≈ 40 mm and cannot sit above the board).
- Still to measure: outer size, hole Ø and hole centre distances (inside jaws minus Ø), or just print the FIT template.
- Dropped: the three boards of the Circuit section, the 7 wires between P1 and P2, the standing PCA9685 wall (split layout only).
