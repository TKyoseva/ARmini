# AmphiReach / AR-Mini — every problem, every finding, every fix (9/2025 → 06.10.2026)

Format: **Problem** → what we found → what we did → where it lives. ⚡ = absurd, keep for the "what broke" video.
Numbers are the real ones from the conversation; parameters refer to `cad/openscad/AR-Mini_v1.scad` unless stated.

---

## 0. Before the prototype — simulation and paper (9/2025 → 9/2026)

These entries come from what you've told me about that year, not from a conversation I was in, so they are thinner than the rest. Each one marked **[fill in]** is a question only you can answer — and those answers are the oldest "process" evidence you have. Numbered S1… so the prototype numbering below doesn't shift.

S1. **The question that started it** → a swim scare in your first triathlon → "could a robot complete an entire rescue on its own?" → that sentence is the first line of the paper, the website and the portfolio. Everything after is an attempt to answer it with hardware.

S2. **Where to do it** → Horizon Academic research programme with mentor John C. Hood; the scope was set as *autonomous* (launch → find → recover → shore → hand-over), not remote-controlled — that one word is why the prototype needs thermal sensing and a state machine and not just a joystick. **[fill in]** what the scope looked like in the first proposal vs. what it became.

S3. ⚡ **The simulation that didn't want to exist** → the setup was "a long chain of tool failures" before it worked. **[fill in]** the chain: which tools you tried first, what each one refused to do (water physics? sensor models? CAD import? ROS2 bridging?), how long it took, and the moment you decided to stop forcing one tool to do everything.

S4. **Final architecture: one tool, one job** → Gazebo headless for water physics · Isaac Sim for sensors · ROS 2 connecting them · a Python script patching the CAD exports. This is the same design philosophy that later produced the boat's electronics (power never passes through the "smart" parts, each box does one thing). **[fill in]** what exactly the patch script fixed in the CAD exports — units, origins, broken meshes, inertia tensors? That detail is a portfolio screenshot.

S5. **64 missions, 62 successes** → the two failures are the most valuable numbers in the project: (a) a head current drained the battery near shore; (b) it chased debris mistaken for a person. → Both are now explicit design targets of AR-Mini: battery-voltage sensing on A0 with a buzzer threshold, and heat-based detection with a "confirm the casualty is in the cradle" second camera. **[fill in]** what the mission success criterion was, how long a mission took, and which parameters you varied between the 64 runs.

S6. **Simulation vs. reality** → the plan for December is 20 physical missions tabulated the same way (result / time / failure reason) so the slide reads "62/64 simulated · N/20 physical · here is why the gap". **[fill in]** anything the simulation assumed that the pool will not give you (flat water? known target temperature? perfect localisation?).

S7. **Writing the paper** → accepted by the National High School Journal of Science; reviewer feedback arrived, the revision was finished on 30.09.2026, ready to resubmit. **[fill in]** the three hardest reviewer comments and what you changed for each — those are "failures and fixes" exactly like a leaking hull, and reviewers of the Maker Portfolio love seeing that you've been reviewed before.

S8. **Presenting it** → Bulgarian Academy of Sciences / UchIMI: "certificate for very good performance" — write it exactly like that, not as an award. **[fill in]** the question from the audience you couldn't answer well; it probably points at something the prototype should measure.

S9. **The website** → amphireach.com states the four phases (launch, detect by heat, gentle recovery pod, amphibious transformation) and promises "fail-safes". AR-Mini maps one feature to each of those promises, and the fail-safes exist as real hardware now (50 A kill, OE kill, 30 A main fuse, leak sensor, battery alarm). **[fill in]** which website claims are still only concepts (heated pod, drift correction) so the portfolio says so before a reviewer notices.

S10. **What the paper could not show** → a simulation proves the logic, not the build. The Maker Portfolio exists because of that gap: the Research Supplement carries the paper and the 64 missions; the Maker Portfolio carries the thing you can hold. Keeping them separate was a deliberate decision on 28.09.2026.

S11. **Honesty items carried over** → mentor credited by name; simulation work clearly separated from hands-on work; scale stated (1:9 demonstrator); the "certificate" wording. These rules were set before the first part was printed.

S12. **Interview sheet for the year I wasn't there** — answer in one line each, with a date and the file/photo that proves it. Put the answers here and the dates in `docs/timeline/TIMELINE.md`.

| # | Question | What the answer becomes |
|---|---|---|
| S12.1 | First proposal to Horizon: what did "autonomous rescue robot" mean in September 2025 — which phases were in, which were out? | the "scope" slide; shows what you cut |
| S12.2 | First tool you tried for water physics. What exactly failed (no buoyancy plugin? crashed on the hull mesh? wrong wave model?) | failure #1 of the sim |
| S12.3 | First attempt at a thermal sensor in simulation: what did it see that wasn't there, or not see that was? | failure #2; links to Pesho and the two cameras |
| S12.4 | The day you split the stack (Gazebo headless / Isaac Sim / ROS 2): what was the trigger — a crash, a deadline, advice from the mentor? | the architecture decision |
| S12.5 | The Python CAD-patch script: what was broken in the exports — units (mm vs m), origin offset, inverted normals, inertia tensors, collision meshes too fine? How many lines is it? | one screenshot, one sentence |
| S12.6 | Mission definition: start state, success condition, time limit, what counts as "found", what counts as "recovered". | the table header for the 20 physical missions |
| S12.7 | What varied across the 64 runs — current, swimmer position, wave height, battery start level, debris? Random seed or a grid? | the "experiment design" sentence |
| S12.8 | Failure (a) battery drained in a head current: at what distance from shore, what current speed, what the battery model was. Which fix did you consider — bigger battery, return-home threshold, better path? | maps to A0 voltage sensing + alarm |
| S12.9 | Failure (b) chased debris: what the debris was in the sim, why the detector accepted it (size? temperature? no second check?). | maps to the 110° cradle-confirmation camera |
| S12.10 | How long one simulated mission took wall-clock, and how long the 64 took. | effort evidence |
| S12.11 | Paper: date submitted, date accepted, date of reviewer feedback, date revision finished (30.09.2026). | timeline rows |
| S12.12 | The three hardest reviewer comments, verbatim if you can, and the change each caused. | the "reviewed before" slide |
| S12.13 | Did a reviewer ask for something you could not provide from simulation alone? | that is the reason the prototype exists — quote it |
| S12.14 | UchIMI/BAS: date, format (poster/talk), the question you couldn't answer well. | timeline + a measurable target |
| S12.15 | Website: which of the four phases + fail-safes are demonstrated in sim, which are only designed. | honesty paragraph in the portfolio text |
| S12.16 | The first CAD of the physical robot (before 28.09): tool, date, what the render showed (the red catamaran with the dome and the U-rail). | the "v0" image, first in the process sequence |
| S12.17 | Who else touched the sim/paper besides you and the mentor (editors, friends, teachers)? | CONTRIBUTORS.md |

---

---

## 1. Scope — how a robot dog became a boat

1. **Buy Pupper v3 parts on Amazon.de?** → the BOM is a Google Sheet; the 12 Steadywin GIM4305 motors ($1,320 of $2,159) and both custom PCBs (JLCPCB + BNO086) are China-only; Amazon.de covers maybe a quarter (Pi 5, Waveshare 4" screen, DeWalt DCBP034 = EU name of the "20 V MAX" battery, DualSense, M2.5 inserts, screws). → Listed the Amazon.de part, the China part, the Digikey part. Also noted the Pi AI Kit is discontinued and the AI HAT+ doesn't fit Pupper's M.2 adapter.
2. **Motors from Bulgaria?** → nobody in Bulgaria or the EU stocks GIM4305; Steadywin's own store ships to 150+ countries in 12–26 days and has an explicit "Pupper V3 version with GDS34 driver" variant; AIFitLab backordered; **GDS/GDZ drivers are being phased out for the GDK series** → "email info@steadywin-motor.com before paying". AliExpress sells the standard version without Pupper firmware (a customer got burned exactly this way). Import = 20 % VAT + duty, ask for DDP.
3. ⚡ **"I just need a shoulder drive, conceptually"** → five classes: serial-bus smart servo (ST3215/STS3215, 30 kg·cm ≈ 3 N·m, magnetic encoder, load feedback, UART daisy-chain), high-torque PWM servo (TD-8120MG at Ardboard, same-day), NEMA17 + printed planetary, DC gearmotor + encoder, gimbal BLDC + SimpleFOC. Chose ST3215. That shoulder is now the cradle lift of an amphibious rescue robot.
4. **Where do ST3215s come from?** → not stocked in BG; BerryBase (DE) listed, later "currently not available"; Amazon.de sold by Waveshare in stock. Bought 4 (2 cradle, 1 camera pan, 1 dome/spare).
5. **MIT Maker Portfolio rules** → EA 1 Nov / RA 4 Jan 2027, $10, one Maker Portfolio per applicant, up to 25 attachments, **≤ 2 minutes of video total**, reviewers want process over result, questionnaire routes to a reviewer; Research Supplement is a separate submission → paper + 64 sim missions go there, the physical build goes in the Maker Portfolio.
6. **Full AmphiReach in 13 weeks?** → no. **AR-Mini, ~1:9**, four mission phases on a 50–60 cm catamaran: swim (2 thrusters), find by heat (MLX), gentle recovery (servo cradle with load-stop), shore (ROB0154 tracks). Honest label: "functional demonstrator, not a load-bearing platform".
7. **RA, CAD exists, budget > 400 €** → 13-week plan, submit 28.12, freeze features 6.12, 20 missions in December mirroring the 62/64 simulation stat.
8. **Three helping friends** → four streams: Dimi = integration/tests/docs; M = hull/cradle/mounting; E = power/perfboard/PCB; S = XIAO firmware/perception/logs. Saturday team session, Sundays protected for essays/SAT, Ironman week = zero tasks.
9. ⚡ **November water** → inflatable pool in the apartment; a desk fan makes "current" for the IMU heading-hold test.

## 2. Hull and structure

10. **Scale** → pick the dummy first: 20 cm figure ≈ 1:9 → cradle interior 22 × 9 cm → hull ~60 cm.
11. **Mass budget** → chassis 1.2 + hulls ~1.3–1.55 + electronics/servos 0.5 + thrusters 0.4 + battery 0.2 + cradle 0.2 + dummy 0.15 ≈ **4.7 kg** → waterplane 0.112 m² → **draft 42 mm** → hull 610 × 100 × 120, freeboard ~78.
12. **610 mm hull vs 300 × 300 bed** → two 305 mm sections placed at 45°: (305 + 6 pad + 100)/√2 = **291 of 300 mm**; `part = "plate_check"` draws it on the bed; fallback `hull_L = 600, cut_x = 300`.
13. **Thin printed walls weep** → 4 perimeters (1.8 mm), solid floor, 15 % gyroid, ribs instead of infill, epoxy inside, PETG (not PLA: softens at 55–60 °C, brittle cold, creeps; not ABS: cracks in cold water). PETG must be dried first; K2 Pro has a dry mode.
14. **Section joint** → each section ends in a full 3 mm bulkhead → every section is its own watertight compartment; the joint only needs to hold, not seal; 4 bolts at z = 75/105, y = ±32 (above the waterline); EVA 3 mm gasket. Ribs at 100/200/420/520 make 6 compartments; 10 mm cable notch at the rim.
15. **Pointed bow prints badly** → parabolic bow via `sqrt(t)` in OpenSCAD, one fitted spline in Fusion, tip rounded with `offset`.
16. **Through-holes below the waterline = leaks** → thruster pad with **blind** insert holes; rim bosses with vertical heat-set inserts (OD 4.0 → `insert_d = 4.0`, matches ruthex M3).
17. **Beams** → 15 × 15 × 1 aluminium tube on printed rim saddles with a clamp bolt; 3 × 294 → later 3 × 304 mm (gap 250) = 912 of 1000 → buy two tubes. Prettier options listed: black 2020 V-slot + T-nuts (adjustable, +0.26 kg), carbon Ø12 for the arch, printed PETG-CF truss, or ⚡ black heat-shrink over the bare tube.
18. **Cradle** → Ø5 aluminium rod (not hollow PETG — floats and fights the servo; not solid PETG — thick), U 220 × 123 mm, printed couplers with 5.3 mm hole + set screw.
19. **Single arm tips the casualty** → parallelogram: drive arm + idler arm on pivots `arm_gap` apart, coupler keeps the rod horizontal. `arm_len = 110`, deployed 215° (rod 34 mm under the waterline), stowed 45° (rod at 149 mm).
20. **Disc pad on the drive arm hit the idler boss** → `arm_gap` 14 → 18 → **22**; idler hole stays 7.7 mm clear of the servo pocket.
21. ⚡ **Any beam crossing the arm's sector gets hit** → swept 45°→215° numerically (`check2.py`), found the swept sector is a half-disc of radius 165 + the whole cradle → no beam allowed ahead of x ≈ 300 below z ≈ 240 → beams aft, and the only forward tie became the **arch at x = 165, underside z = 235** (16 mm margin) — which is why the thermal camera is on a mast.
22. **Arch at x = 100 sat in the bow taper** → the boss would poke out of the hull → moved to 165 (straight section); `boss_l` 36 → 30, `boss_pitch` 20 → 16 so arch and pivot bosses don't overlap.
23. **Pivot bracket** → clamps the rim boss, plate down the inner face, servo block in the gap with the pocket open toward the gap (shaft points inboard), idler boss Ø9, servo bottom 23 mm above the waterline (splash risk noted).
24. **Servo not here yet** → `servo_sel = "TD8120"` preset for the bathtub test with the TD-8120MG (measured 40.3 × 20.14, 50 mm ear span, 40.7 total; ear-plane height still to measure), `"ST3215"` for the final (45.22 × 24.72 × 35, MEASURE on arrival).
25. **Camera mount under the arch tube collided with the arm** → mounted on top: clamp slides onto the tube, pocket up, shaft up; camera 274 mm above the waterline, 15° down → centre at 1 m, 35° VFOV covers 0.45 m to the horizon.
26. **Pan servo (4th)** → two nested loops: inner keeps the hottest blob centred by turning the camera; outer steers the boat to zero the pan angle; pan angle = bearing to target, no encoder needed.
27. **Chassis, first guess** → "tray under the beams, `chassis_drop = 65`" with four printed hangers.
28. **Chassis, measured 124.6 mm** → that's the full height; the aluminium plate (152 × 135 × 2) is a **roof**, side plates hang from it. Motors assumed low → axis ~35 mm < waterline 42 → **wet motors**. Plan B: plate on top of the beams (raise 16.4), ⚡ narrow 200 mm ramp between the hulls so the tracks reach it while the hulls straddle it.
29. **Manual photos** → drive sprockets are at the top-front, motor axis measured **62 mm** above the tracks → 20 mm dry → reverted: `chassis_raise = 0`, tracks flush with the hull bottom, plate hangs **1.4 mm under the beams** (M4 + washer through the plate slots), **chassis hangers deleted** from the part list, wide ramp like the website, beams at 385/500 under the plate (364–516), `ch_x = 290` so the stowed cradle clears the chassis by 6 mm.
30. **Tracks 230 wide, gap 240** → `gap = 250`, overall beam 450 mm, cradle width 123.
31. ⚡ **"Battery in the chassis tray"** → the tray is a slotted plate; spray goes straight through → batteries in the hull compartments 305–420 (108 mm in 115 mm, 3.5 mm each side; move `rib_x` to 430 if tight), one per hull, parallel via a Y-cable.
32. **Fuse block "too big"** → it wasn't; the box was: BTS7960 ×2 (50 × 50 × 43) + fuse block + 100 × 80 carrier don't fit a 140 × 100 floor → **two boxes**. Power box printed to the plate size (152 × 135 × 66, PG7 ×6 on the aft wall, 50 A toggle on the **wall** because the lid carries the dome, M4 to the plate slots, gasket groove, Ø100 dome flange holes). Logic box (bought 150 × 110) on the port hull aft deck on printed saddles; ~1–2° list, fixable with 300 g ballast.
33. ⚡ **Ballast** → twelve M12 DIN 934 nuts, ~240 g. In the BOM as "Ballast".
34. **Fusion 360 script** → user parameters, spline outline, shell, ribs, bulkhead pair, bosses + insert holes, thruster pad + blind holes, joint holes (symmetric extent, 2·bulk_t + 4), split body, mirror, reference bodies. Fixes: negative extrusions written as `3 mm - boss_h`; transom features done with **symmetric extents about a mid-plane** so the YZ-plane normal direction doesn't matter. Synced to v1.6 (gap 250, beams 385/500, plate reference). Rule: Z sizes and thicknesses are parameters; X/Y positions and the outline need a re-run in a fresh document.
35. **Fusion simulation** → Education licence: hydrostatics without CFD (water box → Combine/Intersect keep tools → volume = buoyancy, centre of volume vs centre of mass = trim/stability), Static Stress on the arm (custom "PETG printed", yield 25 MPa = half, E 2.1 GPa, 3 N at the tip, target SF ≥ 3, deflection < 1 mm) and the pivot bracket (expect SF ~2 on the 6 mm plate → 8 mm), Motion Study for interference + a 10 s clip. No CFD (Fusion can't; the thrust rig gives the real number), no modal/thermal/buckling, don't FEA the shelled hull.
36. **Printing plan** → PLA now for fit parts (arms, couplers, pivot bracket, beam brackets, arch posts, dummy head, a white PLA `hull_fore` as a fit prototype), PETG for anything wet; corpus section bottom-down rotated 45°, 4 walls, 10 bottom layers, brim for PLA / skirt for PETG; first print check with calipers: 110.0 between arm holes, 3.3 mm hole = calibrated.
37. **Sikadur-31 CF Normal** → thixotropic paste, A:B 2:1, pot life ~45 min — bonds rod-to-coupler and bosses, fillets inside the hull; **not** a brushable coating; liquid epoxy / XTC-3D still needed.
38. **Pattex Neutral silicone** → neutral cure (no copper corrosion) but doesn't bond PETG → gasket/sealant role only.
39. **Nyloc M3 missing** (bought DIN 934 plain + M5 DIN 985) → Loctite 243 or a second nut on the pivot axles. M5 DIN 912 bolts work for plate-to-beam if the plate slots are ≥ 5.2 mm.

## 3. Electronics

40. **Raspberry Pi 5 for v1?** → XIAO ESP32S3 Sense replaces it: OV3660 camera (not OV2640 — the FPC says so; set the driver accordingly), microSD logging, WiFi telemetry + e-stop, 8 MB PSRAM reads MLX at 8–16 Hz. Pi kept for v2 (ROS 2); ordered anyway.
41. **XIAO has 11 GPIO, SD eats three** → PCA9685 (I2C, 16 PWM) for ESC ×2, BTS7960 ×2 (RPWM/LPWM), buzzer, LEDs; XIAO ↔ Pi over **USB** (serial) instead of UART; ⚡ leak sensor + kill switch on **one ADC pin** via a resistor ladder (10k/4.7k/1k → three voltage levels).
42. **Kill must work without the MCU** → kill → PCA9685 **OE** = all 16 PWM outputs off in hardware; plus the 50 A toggle on the battery; plus the ladder so the firmware knows.
43. **Two MLX90640s share I2C address 0x33** → Wire (D4/D5) and Wire1 on the ESP32-S3.
44. ⚡ **I2C-1 couldn't be routed without a crossing** → swapped in software: `Wire1.begin(SDA=4, SCL=3)`; D2 = SCL1, D3 = SDA1 on both the breakout and the carrier spec.
45. **I2C over breadboard jumpers above 400 kHz is flaky** → 400 kHz, < 15 cm, 4.7 kΩ pull-ups on the bench; 1 MHz only on the PCB.
46. **Power tree** → LiPo XT60 → inline **30 A** (within 10 cm) → **50 A toggle** (main kill) → 6-slot blade fuse block → 20 A thrusters / 15 A servo bus / 10 A tracks / 5 A logic / 5 A Pi. Minus never switched or fused. Buck 12→5 V 3 A (logic), buck 12→5 V 5 A USB-C (Pi 5). Common ground everywhere or PWM isn't read.
47. **Fuse holder question** → one inline main + the 6-slot block beats several inline holders: a blown branch shows itself; a stuck prop kills only the thruster, not the servo holding Pesho in the air.
48. **Which switch?** → 50 A screw-terminal toggle (DC-rated!) = main; the 20 A rocker turned out to be **ON-ON SPDT** → feature: common → signal, one side 3V3, other GND = clean logic level with no pull-down. AC-rated "20 A/250 VAC" rockers are ~5–8 A DC — avoid.
49. **Servo driver DC jack is ~5 A** → 4 × ST3215 can peak ~11 A → feed via the terminal with 14 AWG, 15 A fuse.
50. **Servo driver choice** → the plain Waveshare "Serial Bus Servo Driver Board" (TTL↔bus + power, no MCU) driven by XIAO UART1, not the ESP32 version; bought 2 (spare). IDs set via FT232 + Waveshare software, marker on each servo.
51. **5264-3P cables don't exist in Bulgaria** (and aren't JR) → splice the included 15 cm cables with heat-shrink; Mouser part numbers for DIY (Molex 50-37-5033 / 08-70-1040); later found Waveshare's own "5264-3PIN Servo Cable" mix pack (3 × 300 + 3 × 900) — ordered.
52. **L293D from the Freenove kit for the tracks?** → 0.6 A; ROB0154 motors need BTS7960 (43 A).
53. **ESCs** → calibrate with 1500 µs for 1–2 s at power-on; signal 3.3 V from PCA9685 is fine; thin red/black/yellow = potted ESC; three thick same-colour wires = bare motor.
54. **Breadboard** → signals only (nothing thicker than 22 AWG), never power (rails ~1 A), never on the water (jumpers vibrate out) → perfboard v0.5 in the box for the pool; skipped if Aisler lands by ~25.10.
55. **PCA9685 arrived as an Arduino shield** → module re-ordered; shield goes on the Mega thrust rig.
56. **Multimeter 10 A jack** → fine for one thruster (8 A), not for the main line (20–25 A) → lab PSU on the bench, clamp later. Lab PSU: set **CC = 3 A** when first powering any new board.
57. **Soldering iron HS-03** → ~40 min at 350 °C per charge → charge the night before; Sn60Pb40 at 300–320 °C, 350 for 14 AWG; ruthex inserts pressed at 230 °C, not 350.
58. **Carrier board rev A** → 100 × 80, THT, modules on headers (XIAO, PCA9685, BNO055), 11 JST-XH connectors with pin order defined, P-FET reverse polarity (IRF4905), TVS, 470 µF, polyfuse, divider 100k/33k, 4.7k pull-ups ×4, NPN buzzer, 3 LEDs, test points, mounting 93 × 73; power never through the board. Rule: **don't push to Aisler before 11.10** — BNO055 and the servo driver arrive 9.10 and footprints must be measured; breadboard must prove the ladder, OE kill, and dual I2C first.
59. **Learning board rev 0** → 50 × 40 mm `.kicad_pcb` generated by script (KiCad v7 format), XIAO + I2C0 + I2C1 + servo + 5 V + VBAT divider + LED; hand-routed with the staircase rule for planar pairs; 3V3 on B.Cu, GND zone on B.Cu, no vias; my crude clearance check passed; **KiCad's DRC is the real one**; upload the file straight to Aisler; ~15–20 € for three.
60. **Where to fab** → Bulgarian (SKA 24 h, Micron-20, BAS applied-dev centre, B2B), DIY etching only for a small sensor board, perfboard as fallback; **Aisler** chosen (EU, no customs, KiCad plugin, ~1 week, 3 pcs min); Eurocircuits PCB Visualizer for a free DFM; JLCPCB only with IOSS/VAT-paid.
61. **Enclosure heat** → thermal labels fade next to the BTS7960; don't label hot parts with the TEDi printer.

## 4. Thrusters — the saga

62. ⚡ **Listing 1**: "1.3 kg … Floodlight … Instant On At Maximum Speed No Control Required U2 Mini CW" → fixed-speed internal driver, no PWM, no reverse → no.
63. **"What is CW/CCW?"** → prop torque cancels with one of each; two CCW works with software trim.
64. **Listing 2**: Acouto F2838-500KV "motor" → bare waterproof outrunner, no ESC/duct → viable only as F2838 + bidirectional ESC + printed duct + CW/CCW props (~50 €/side, more work, nice thrust-rig story).
65. **Listing 3**: Cuifati "Deep Water Thruster 560KV Low Power 300 m Motor" → bare motor again ("compatible with 30A ESC", CW only).
66. **Listing 4**: Irfora 1000KV with 4-blade props → bare, bait-boat class, CW only.
67. **Listing 5**: surfboard thruster kit → 24–36 V, 300–800 W, forward only.
68. **Listing 6**: LICHIFIT 7.4 V 16800 RPM micro → 2S, hand-sized ROVs.
69. ⚡ **Listing 7**: the same "no control required" U2 Mini at **€182** from a reseller (KUTUP LTD) → no, and the thrusters were already in the 9.10 shipment.
70. **The rule** → title must have *Thruster* + a thrust figure + *ESC* (bi-directional); searches must include "ESC".
71. **Cuifati B0BP7H9XJC** → "mit bidirektionalem voll wasserdichtem ESC", 12 V 8 A 1.2 kg; the ambiguous "Passender ESC: 30A" resolved by the photo: three thin coloured wires + potted box = ESC inside. Verify on unboxing; if wrong, return.
72. **U2 Set unavailable** → ranking kept: Cuifati with ESC ×2 → U2 Mini "with ESC" CW+CCW → ApisQueen store direct (2–3 weeks).
73. **v2 thrusters** → Hobbywater TD2.5 CW+CCW (recommended), ApisQueen U2/U1/U3, Blue Robotics T200 + Basic ESC (the reference, ~250 €). Decide only after the thrust rig says what the current ones push.

## 5. Batteries

74. **Which LiPo** → 2 × 2200 mAh 3S (one per hull, symmetric, XT60 direct) over 1 × 5000 (XT90 adapter, 136–145 mm doesn't fit the 115 mm compartment, asymmetric) over 2 × 1100 (~9 min at 7 A → 3–4 missions; parallel Y-cable to 2200). Bought Turnigy 2200 40C XT60 ×2.
75. **Runtime math** → thrusters ~6 A + servos 0.5 + Pi/XIAO/sensors 0.7 ≈ 7 A → 2200 mAh ≈ 18 min ≈ 6–8 missions; two packs + charger between sessions for the 20-mission days.
76. **Lithium can't ship from Amazon** → NenovTechnic (Stara Zagora, Econt) / Sofia shops (MyHobby, Nitro Planet, Steldi, RCParts, Drones.bg with phone numbers and hours).
77. **Charger** → SkyRC iMAX B6 V2 (DC, from the lab PSU at 13 V) over B6AC; **clones everywhere → check the hologram**; 1C = 2.2 A, storage 3.8 V/cell, LiPo bag, never unattended; eMAG listing at 76 € = 2× price.
78. **Balance lead** → never cut, taped accessible in the compartment.

## 6. Sensors and Pesho

79. **110° thermal camera ordered instead of D55** → kept as the **cradle-confirmation** camera on Wire1; D55 for forward (Welectron 65 € → 96.90 €; Amazon.de variant menu).
80. **D55 unavailable → MLX90642-D45** → 45° × 35°, NETD 0.065 K, calibration on-chip (lighter driver), but a younger software ecosystem — accepted the risk.
81. **Pixel math** → 110° / 32 px = 3.4°/px → a 20 cm dummy at 2 m is < 2 px; D45 ≈ 1.4°/px; realistic detection of Pesho ~1.2–1.5 m, which fits a 2 m pool.
82. **Only what's above water is visible** → Pesho floats head **and** shoulders out (5 × 5 cm warm patch), ballast slots for "lying" (cradle test) and "vertical/vest" (thermal test).
83. ⚡ **Hand warmers suffocate in a sealed head** → `dummy_head` with 6 vents + vented lid; Wedze warmers 0.72 €/pc, 5–6 h, ~50 °C in air. For calibrated runs a 50 ml bottle of **37 °C** water + IR thermometer.
84. **IR thermometer** → emissivity fixed 0.95 → true on PETG/skin, 20–30 °C wrong on bare aluminium; 12:1 optics = Ø2.5 cm spot at 30 cm = Pesho's head.
85. **Scale** → 1:9 → 19 cm, ~100–150 g.
86. **Name** → Pesho. "Test target #1" says nothing; "Pesho, 19 cm, 110 g, 37 °C" sticks.

## 7. Shopping and logistics

87. **Amazon.de → Bulgaria** → free over 49 €, not all sellers ship; check "Deliver to Bulgaria" in the cart.
88. **Pi 5 at €199** from Astradis → cancel, ~€95 at BerryBase/Amazon proper.
89. **Raspberry Pi 5 power** → needs a 5 V 5 A USB-C buck; XIAO/PCA9685 on the 3 A buck.
90. **microSD 64 GB** → XIAO Sense reads ≤ 32 GB FAT32 → second card.
91. **Switch/fuse links** → Vikiwat R13-401A2A-07 (50 A/12 VDC), ASW-06-102 rocker, Steinberger ASW-14D illuminated; blade fuses 0.49 €; GT4652 inline holder; cable.bg inline + fuse set.
92. **Wire** → 18 AWG for signals/servos/bucks, **14 AWG** for battery → switch → block → thrusters; XT60 pigtails are 12 AWG but 10 cm.
93. **Heat shrink** → Commel 100-pc box 0.40 €; add 1 m Ø6 **adhesive-lined** for splices near water.
94. **FT232 vs CP2102** → FT232RL with a 3.3/5 V switch at Ardboard; connect TX↔RX, GND, no VCC.
95. **Helping hands** → heavy base + gooseneck arms (Proton ZD-126), not the 5 BGN wobbly one.
96. **Logic analyzer** → any FX2/CY7C68013A clone (Youmile with test hooks is fine); AZ-Delivery direct when Amazon was out; **PulseView**, not Saleae Logic 2.
97. **Crimper** → Preciva (0.25–1.5 mm², Dupont/JST-XH/waterproof) over a plain SN-28B kit; it can't do 5264 or 6.3 mm spades.
98. **Stripper** → Knipex NexStrip 12 72 190 over 12 62 180: 0.03–10 mm² covers the kits' 28 AWG, and it crimps ferrules — which the BTS7960/buck screw terminals need; Alkan 800-pc ferrules 0.5–10 mm².
99. **Solder/flux** → Sn60Pb40 0.8 mm (lead, easier with a battery iron), RMA gel; the 1.4 ml syringe is for SMD → bought 3; braid 2 mm; IPA 99 % + toothbrush.
100. **Oscilloscope** → not for this project; Rigol DHO804 parked in priority C with calipers, helping hands, crimp tool, kitchen scale.
101. **ESD mat vs silicone soldering mat** → different things, need both; mat grounded via 1 MΩ to Schuko earth or the PSU chassis.
102. **Bauhaus list** → 2 tubes, Ø5 rod, Sikadur, Pattex, gun, hacksaw + 24 TPI blades, needle files, flat file, P240/P400 + block, mounting tape, zip ties, ESD mat, two vises, iFixit kit, gloves, M12 nuts, M3/M5 hardware, label printer, power strip; M3 blisters only on the shelf → Galdi online for stainless.
103. **PETG filament** → 3DLarge (BG, Hyper PETG / Filalab), SUNLU on Amazon.de; **4 kg not 3** (2 hulls ≈ 1.6 kg + brackets + one failure); grey hulls / white mechanism for video contrast.
104. **Tripod/lighting** → MT-44 (147 cm, clamp + Bluetooth remote) for the pool, Magic Arm over the bench, VL49 5500 K CRI 95 bounced off a wall; MT-79 has no clamp/remote; Sofia: Photosynthesis, Ozone Pro, Dynaphos.
105. **Aluminium profile aesthetics** → hybrid: black 2020 for the chassis beams, carbon Ø12 for the arch, or heat-shrink over bare tube.
106. **Power box: buy or print?** → print (fits the plate; a bought 240 × 160 × 90 box has nowhere to sit); buy only 6 × PG7 glands.

## 8. Software, documentation, process

107. **"Photos or video?"** → both with different jobs: ~14 photos + ~7 screenshots carry the process, 90 s full-cycle (one static shot, real time, voice) + 30 s "what broke" carry the proof; film every test, never use a video still as a photo; folders by week; `YYYY-MM-DD_topic` file names.
108. **Screenshots** → code (20 decisive lines, not 400), CAD exploded view + parameter table, before/after (arch at 100 vs 165), sim-vs-real split; full-resolution, cropped, taken when it works.
109. **SlideRoom** → separate account; images ≤ 5 MB (export ~2000 px), video .mp4/.mov ≤ 250 MB (1080p, not 4K), PDF ≤ 10 MB, every attachment needs a description; order is yours: hero shot → 90 s video → process → data → "what broke" → next. Write the project text **after** ordering the files.
110. **PCB "to show electronics"** → carrier board as module-on-headers, never SMD smaller than 0805; the inevitable bodge wire is the best slide.
111. **Breadboard enough?** → for logic yes; see 54.
112. **GitHub** → one repo `amphireach`, eight folders by kind (docs/cad/pcb/firmware/sim/software/data/media/hardware), date-prefixed session folders, commit prefixes `cad:`/`fw:`/`pcb:`/`docs:`/`data:`, friends in `feat/<name>` branches + PRs, tags per milestone, Issues/Projects per phase, `docs/LOG.md` three lines a night; skeleton zip delivered with everything placed.
113. **Backdate a year of commits?** → **no** — it looks exactly like what it is; import the real files (EXIF intact — don't pass photos through WhatsApp), write `TIMELINE.md` with real dates.
114. **1 TB OneDrive** → mirror folder structure, big files there (video, raw photos, .f3d archives, datasheets, rosbags), index `.md` files in git with links, LFS not needed; **never `git init` inside a OneDrive-synced folder**.
115. **Software stack** → Fusion 360 Education, OpenSCAD, KiCad 9, Creality Print, VS Code + **PlatformIO** (not Arduino IDE, for XIAO), Arduino IDE 2 (Mega only), Waveshare Bus Servo Control, PulseView, Python + pandas/matplotlib, Git/GitHub, Pi OS + ROS 2 Jazzy (v2), Aisler, Eurocircuits Visualizer, Printables, DaVinci/CapCut, SlideRoom.
116. **Lab organisation** → Gridfinity bins from leftover PLA, three subsystem boxes (Power/Servo/Sensors), IKEA SAMLA 78 L for transport (robot is 61 × 45 cm), antistatic zip bags, L-rack, printed PCB vise, zones: ESD = clean, filing/epoxy elsewhere.

## 9. Things the assistant couldn't do (and the workaround)

117. **Can't open Amazon pages** (robots) → you paste titles/descriptions/screenshots; the ESC question was settled from a product photo.
118. **Can't run OpenSCAD/Fusion/KiCad here** → parametric files + Python numeric checks (buoyancy, sweep collisions, plate fit, trace clearances) + explicit "send me the traceback" requests.
119. **Can't download product images** → LABS sheet has photos only for items already pictured in Sheet1; Bauhaus items have an empty Picture cell for you to paste.
120. **Bounding-box collision checker cried wolf** → split into arm / coupler / rod boxes; the real clearances: 16 mm under the arch, 6 mm over the chassis.

## 12. Added 05–06.10 — PCB bring-up, printing, next controller

### PCB rev 0 — from file to "clean DRC"
121. ⚡ **"Which file do I send to Aisler — the .scad?"** → no: `.scad` is the 3D-print CAD; the board is `AR-Mini_xiao_breakout_rev0.kicad_pcb`. Two different worlds with similar-looking file names; the README now says it in the first line.
122. **DRC round 1 — 32 violations** (file loaded fine in KiCad, board placed at 99/55 mm in the sheet, 0 unconnected). Only **2 errors**: *starved thermal* on GND pads J2.2 and J3.2 (one spoke instead of two — the 3V3 trace on B.Cu sits 0.73 mm from J2.2; J3 sits at the board edge) → both pads set to **solid zone connection** (`zone_connect 2`). Warnings: 15× "no library AR-Mini" (expected, permanent), refs of J7/H1/H2 outside the edge, 6 labels under 0.8 mm, 3 label/ref overlaps, J1/J2 silk lines through R1/R2 pads, LED1 ref over R7 pad → v2: labels rotated beside the connectors, ≥ 0.8 mm, hole refs inside, J7 ref left of the connector, header silk lines removed, LED1 ref moved right.
123. **DRC round 2 — 0 errors, 4 silk overlaps** (rotated label through R1/R2 bodies; H1↔J3 and H2↔J5 refs) → v3: R1/R2 moved +1 mm (pads 7.5/15.12, traces re-routed), left labels at x = 5.5 between J3/J4 pads and the resistors, hole refs beside the holes.
124. **DRC round 3 — clean**: 15 library warnings only, 0 unconnected, 0 footprint errors. First board designed, checked and orderable (05.10). Pre-order ritual: 1:1 PDF print, XIAO and a JST housing laid on the paper.
125. **Assembled top-view render** (components at real size on the real coordinates) revealed two things the layout alone didn't: the Sense camera module is the tallest part → **≥ 15 mm clearance above it** in the box, camera up; LED1 sits next to the H4 standoff → if the standoff is wider than 5 mm, move the LED 2 mm left (one line in the generator).

### Printing the first mechanism parts
126. **Seven PLA rolls (black, red, white ×2, blue, green, orange)** → colour = meaning: orange = moving parts (arms, couplers, pivot brackets — fit version), black = structure (beam brackets, arch posts, camera mount), white = `hull_fore` fit prototype, red = Pesho, blue = enclosures/clips, green = Gridfinity. PLA never for anything wet or load-bearing on the water (creeps under Pesho, softens at 55 °C) → those are PETG after 9.10.
127. **Print order** → arms + couplers (orange, ~3.5 h, 4 walls, 40 %), pivot brackets after the ear measurement, black brackets, Pesho's head, white hull section overnight, blue power box fit version. First-print check with calipers: 110.0 between arm holes, 3.3 mm holes.
128. **TD-8120MG — the missing ear-plane number** → measured guide (four dimensions drawn): bottom → underside of the ear **28.0**, ear holes **10 mm** apart, hole **Ø4.34**, front edge → shaft axis **10.4** → CAD v1.8; preset was right to 0.1 mm, only `servo_shaft_off` changed 10.3 → 10.4.
129. **Ø4.34 ears = M4 servo, M3 inserts in the bracket** → M3 passes with 1.3 mm slop → washer under the head, or the head barely covers the hole.
130. **How to solder the XIAO without crooked pins** → "sandwich": male headers into the female headers into the PCB, XIAO on top, one corner pin, check flat, diagonal pin, the rest; HS-03 at 320 °C; then flip and solder the females. 14 joints, 10 minutes. Soldering the males into the XIAO "free-hand" = pins at an angle = won't plug in.

### Connectors
131. **Which JST-XH parts** → PCB side vertical **B4B-XH-A ×12, B3B-XH-A ×4, B2B-XH-A ×6** (rev 0 + rev A + spares); cable side XHP-4/3/2 housings + **SXH-001T-P0.6** contacts (22–28 AWG); the Preciva kit's 70 XH housings cover most of it.
132. ⚡ **XH 2.5 mm is sold as "XH2.54"** → same part, clone naming. **PH is 2.0, ZH is 1.5** (Pupper used ZH) → incompatible, don't buy. Sensor modules have 2.54 mm pin headers, not XH → cables are XH on the board end and Dupont on the sensor end; vertical headers, not right-angle (cables must exit toward the glands, not the wall).
133. **Long-term kits** → CQRobot 460 (30 headers + 30 housings each of 2/3/4-pin + 280 contacts) for the board side, plus a pre-crimped 22 AWG silicone-wire XH kit (push the pin in, no crimping, 6 colours → 3V3 red, GND black, SDA yellow, SCL green). ~25 € together. Avoid anything labelled PH 2.0 or SH 1.0.

### Next controller (for January, not before)
134. **Which MCU for v2** → stay on ESP32-S3 but in the big package: **ESP32-S3-WROOM-1 N16R8** soldered on carrier rev B, DevKitC-1 for prototyping. Reason: the only problem with the XIAO is pin count; the chip, firmware, PlatformIO, FreeRTOS and WiFi all carry over. Gains: ~36 GPIO (no PCA9685, no ADC ladder), 3 UARTs (servo bus + Pi + GPS), 2 I2C, built-in **TWAI/CAN** (+ SN65HVD230 → the door to Steadywin/CubeMars-class joints in v3), micro-ROS to the Pi. XIAO Sense stays as the camera node.
135. **Alternatives weighed** → Teensy 4.1 (600 MHz, 55 GPIO, 8 UART, 3 CAN; for v3 with many axes), STM32 Nucleo G4/H7 (industry path; learn it at university, not for this deadline), Arduino Giga/Portenta (pricey). Rule: **the controller is not touched before 28.12**; DevKitC isn't even bought in November so it can't tempt anyone.
136. **Where** → ⚡ **Olimex ESP32-S3-DevKit-Lipo — designed and made in Plovdiv**, open hardware, same WROOM-1 N8R8, LiPo charger on board; Comet (Sofia/Plovdiv) lists it at 7.95 € ex VAT but 0 in stock → write to Olimex directly. Otherwise Mouser.bg (Espressif DevKitC-1, WROOM modules, Teensy, Nucleo, transceivers; 2–3 days, no customs), TME, Amazon.de for DevKitC clones.
137. **The DevKitC → board process** → step 1 (Jan, 2 weeks): `board = esp32-s3-devkitc-1`, `qio_opi`, 16 MB partition, pin map in one `pins.h`, prove two UARTs + direct PWM + CAN on the breadboard; avoid GPIO26–32 (flash/PSRAM), **35–37 (octal PSRAM on N16R8)**, 0/3/45/46 (strapping), 19/20 (USB). Draft pins: UART1 17/18 servo, UART2 15/16 Pi, I2C-0 8/9, I2C-1 4/5, TWAI 21/47, ESC 1/2, BTS 6/7 + 10/11, ADC 12/13/14 (separate!), buzzer/LEDs 39–42, RGB 38. Step 2 (Feb): carrier rev B with the DevKitC on 2×22 female headers — **measure the row spacing**, v1.0 and v1.1 differ; this can be the final board. Step 3 (optional): rev C with the WROOM soldered.
138. **WROOM-1 minimal system** → LDO AP2112K-3.3 or SGM2212 (600–800 mA; not AMS1117), 10/22 µF + 100 nF, polyfuse 1.1 A + TVS SMBJ5.0A on 5 V, EN 10 kΩ + 1 µF + RESET button, GPIO0 10 kΩ + BOOT button, strapping 45/46 left alone, USB-C 16-pin with 2× 5.1 kΩ CC, D+/D− → GPIO20/19, USBLC6-2SC6 ESD, antenna over the board edge with a 15 mm copper keep-out, test points 3V3/GND/EN/GPIO0/GPIO43/44, status LED. **Not needed:** USB-UART bridge (native USB), crystal, flash, PSRAM. Everything 0805/SOT-23 → hand-solderable; ~5 € at Mouser/TME; KiCad has the `ESP32-S3-WROOM-1` footprint in RF_Module.
139. **Soldering a WROOM** → drag soldering: flux gel on the whole pad row, tack one corner, check alignment under magnification *before* continuing, solder on the tip (not the board), drag slowly, braid for bridges, continuity-check neighbours. Needs a loupe/USB microscope (~25 €) and a fine tip for the HS-03. The one joint in the project worth delaying to January or giving to Aisler's assembly.

### Found by the 3D model (06.10)
141. ⚡ **The cross-beams ran straight through the power box** (v1.5–v1.8, never noticed in 2D) → the box was placed on the ROB0154 plate (z 124.6–193.6) while the two 15 × 15 beams at x 385 / 500 sit at z 126–141 — inside the box. The 2D layout and the bounding-box checker only looked at the arm/cradle sweep, never at box vs beam. Seen at once in the first 3D render. **Fix, CAD v1.9:** the box floor sits **on top of the beams** (`pb_z` = 141, lid top 210); locating rails under the floor either side of each beam; **4 × M3×30 + washers** go box floor → beam tube → plate slot → nyloc, so one bolt stack holds box, beam and plate (`pb_beam_y` = ±30, MEASURE against the plate slots); the BTS7960 and fuse-block holes became printed bosses with heat-set inserts, because the beams now block screws from below (the old BTS hole at x −48.4 sat 0.9 mm over the beam). Cost: +16.4 mm height, nothing else moves (stowed cradle ends at x 286, box starts at 364). The blue PLA fit print from 03.10 is still fine for a fit check; the PETG box is printed from v1.9. Lesson: **check every pair of solids, not only the moving ones** — a 3D view is the cheapest collision checker.
142. **3D model without OpenSCAD** → OpenSCAD can't be installed in the cloud workspace, so the geometry was rebuilt in Python from the same parameters (hull outline, ribs, bosses, brackets, arms, cradle, chassis, boxes, thrusters, Pesho) → still renders (5 views) + an interactive WebGL viewer with the lift animation and part names. Same numbers as the `.scad`; if a parameter changes, the model and renders are regenerated from `3d/src`.

### Repo
140. **Repo names** → `amphireach` (private now, public later), `amphireach-paper` (private: manuscript in second-round review, reviewer comments, response letters — commit history is forever, so never inside the main repo), `amphireach-portfolio` (private: the 25 files + texts), `amphireach-sim` if the simulation has its own repo (rename, GitHub redirects). Lowercase, hyphens, no versions in names; organisation only after January if the project continues. Before going public: scan history for passwords, the manuscript, friends' personal data.

## 13. Added 08–10.10 — first measurements and the first print

143. ⚡ **The thruster is taller than the draft** (card C001, 08.10) → measured: duct OD **72.27 mm** (the box drawing says 77), 112 mm long, mounting face 47.10 mm above the prop axis, frame 9.68 mm, 4 brass inserts, M4 screws 28.4 mm, pattern 34.8–35.3 × 15.2–16.0 mm, 201 / 206 g. The CAD v1.9 stern pad was a guess (44 × 44, M3) and a 72 mm duct cannot sit under a 42 mm waterline on a flat pad. **Fix, CAD v2.0 + decision 0004:** kick-up hinge on the transom, pin above the waterline, thruster folds up on shore; test coupon 50 × 30 × 5 with 4 × Ø4.5 at 35.0 × 15.6 (C005). Lesson: **measure the bought part before drawing its mount.**
144. **"No supports" was wrong for hull_fore** (found while slicing, 09.10) → the two rim bosses at x 150–215 have a flat 24 mm underside 100 mm above the bed: a cantilever, not a bridge. The PLA fit print uses tree supports under them only. **Fix later in CAD:** a 45° gusset under each boss so the PETG hull prints without supports.
145. ⚡ **The printer moved but printed nothing** (C008, 09–10.10) → TR2852 "filament detector triggered abnormally", then FR0122 "spool holder filament in use", then, from the external spool with the CFS off, the head drew the part in the air. Evidence: a red bead on the nozzle (the last colour through it was red, not orange), the orange tip came back flat and unmelted, and with the extruder cover off a piece of **red PLA sat in the heat-break inlet** (photos C008_09, C008_10, C008_18). **Fix:** Creality K2 Pro jammed-filament procedure — extruder front cover off (3 screws, mind the spring), cleaning needle from the top with the nozzle hot, red purged from the nozzle (C008_20–21). Lesson: **a CFS error can be a broken piece of the previous filament still in the head — push the old colour out before changing spool or mode.**
146. **The first print after the jam came out thin: the nozzle was at 140 °C** (C017, 10.10) → the head followed the arm outline but laid down almost nothing; the printer screen showed the nozzle at **140 °C** (PLA needs ~220). **Fix:** in Creality Print Teddy set the filament source (spool holder, "Enable CFS" off) and the nozzle temperature for the plate, sliced again → arm_drive printed clean: **20 min, 13.0 g**, holes open (C017_01–07). Lesson: **when the extrusion is thin, read the nozzle temperature on the screen first (current / target) before taking the head apart.**
147. **The servo pocket was drawn from a wrong number** (C017, 10.10, caught before printing) → re-measuring the TD-8120MG for the arm fit: body **40.40** long (pocket was 40.5: no room), bottom → ear plane **28.51** (pocket 28.0: the servo would bottom out before the ears seat), ear holes **48.26 c-c** along the body, not 50 (two readings: inner edges 44.35, outer edges 52.16, average = c-c; the check (52.16 − 44.35)/2 = 3.9 matches the hole d4.05). With 50 the screws would have missed the inserts by ~1 mm each side. **Fix:** TD8120 preset → pocket 40.7 × 20.4 × 28.8, ear span 48.26, 9.65 across, case top 12.34. Lesson: **a hole-to-hole distance is never one caliper reading — measure inner and outer edges and average.** Same session: the plastic disc stands **8.84 mm** above the case top once pushed fully onto the spline (the first reading, 3.3 mm higher, had the disc sitting on the tip of the spline). The CAD guessed 4 → drive arm 4.5 mm further in, idler boss 16 → 20.5, cradle rod centres **123 → 112** (rod not bent yet, so nothing to redo).

---

### The short list for the "what broke" video
A simulation whose tools wouldn't talk to each other · a dog that became a boat · a mast that exists because of a swinging arm · a kill switch hiding on an ADC pin · a battery that couldn't live in a colander · twelve M12 nuts as ballast · Pesho's breathing holes · seven thrusters that weren't thrusters · a fan as the sea · a chassis that was upside down in our heads for a day · SDA and SCL swapped because of one copper trace · a .scad file almost sent to a PCB factory · a connector sold under the wrong pitch · two aluminium beams running straight through the power box, invisible until the robot was seen in 3D.

## 10. Day by day — when each decision was taken (so the LOG can start from here)

| Date | Decisions and findings (in order) |
|---|---|
| **Mon 28.09** | Pupper v3 researched; motors China-only; shoulder-drive alternatives; **AR-Mini scope** set; MIT rules (RA 4.01, 25 files, 2 min video); 13-week plan; the cradle render analysed → **parallelogram**; ST3215 chosen; TD-8120MG as interim; **CAD v1.0** (610×100×120, cut 310, draft 42, beams, arch, cradle); kinematic check deployed/stowed; K2 Pro + ROB0154 → chassis under beams (first guess), 2 sections at 45°, PETG 4 kg; Fusion script v1; order list v1 (ST3215 ×4, thrusters, Pi 5, MLX, …); 4 servos → **camera pan** added (CAD v1.2); XIAO ESP32S3 replaces the Pi for v1 (pin map, PCA9685); final list with Pi anyway. |
| **Tue 29.09** | Thruster listings 1–3 rejected; CW/CCW explained; search rule; Amazon list of real thrusters (U2 Set, Cuifati, TD1.2); U2 Set unavailable; Cuifati B0BP7H9XJC verified **from a photo**; Amazon order reviewed (Pi €199 → cancel, 110° camera, "Motor" thruster title, missing fuse/cables/wire); LiPo sources in Sofia + NenovTechnic; 2200 40C chosen over 5000/1100; JR cables ≠ 5264 → splice; Joy-IT Mega kit → thrust rig + bench servo tester. |
| **Thu 01.10** | BOM v01.10 reviewed; remaining-purchases list; "To buy" sheet with priorities; multimeter/oscilloscope/logic-analyzer decisions; Rigol parked in C. |
| **Fri 02.10** | **Hardware circuit diagram** (ladder, OE kill, USB to Pi, two I2C buses) + A3 **poster** with BOM photos; phases and days; aluminium aesthetics; Pesho designed (vents, posture, 37 °C bottle); Wedze warmers; measurements: **ROB0154 124.6 (plate on top)**, plate 152×135×2, TD-8120MG 40.3×20.14 / 50 mm ears, PCA9685 62.15, BTS7960 40.8, LiPo 108×33×23, XIAO 15.35 → CAD v1.4 (plate on beams, raise 16.4, narrow ramp) → manual photos → **v1.5 (tracks flush, hangers deleted)** → gap 250, motor axis 62 → **v1.6**; Fusion script synced; Fusion simulation plan; load-models-and-print walkthrough; "where is the whole robot" (OpenSCAD assembly). |
| **Sat 03.10** | Lab items (ESD, Gridfinity, SAMLA, label printer…); **power box printed, v1.7**; thrusters for v2 named; perfboard explained; **rev 0 breakout PCB** generated + README; carrier spec I2C-1 swapped to match. |
| **Sun 04.10** | Bauhaus haul; **BOM v04.10** with LABS Equipment sheet (usage column, specs column, Type column, software rows); EVA/Wedze/pool marked "to buy"; **GitHub structure + skeleton zip**; no backdating; OneDrive for big files; this file (first version); repo naming: `amphireach` / `amphireach-paper` / `amphireach-portfolio` / `amphireach-sim`. |
| **Mon 05.10** | Assembled top-view render of rev 0 (found: ≥ 15 mm clearance needed over the camera; LED1 next to the H4 standoff); **next-MCU decision**: ESP32-S3-WROOM/DevKitC-1 for v2, Teensy 4.1 for v3, STM32 later; where to buy (Olimex ESP32-S3-DevKit-Lipo via Comet, Mouser.bg, TME); the DevKitC → rev B → rev C process + S3 pin plan; ".scad vs .kicad_pcb" — which file goes to Aisler; **DRC round 1** (32 → fixed, v2), **round 2** (4 silk → v3), **round 3 clean**; 7 PLA rolls → colour code + print order; TD-8120MG measurement guide → **28 / 10 / 4.34 / 10.4** → CAD v1.8; step-by-step print session (STL → Creality Print → checks → dry fit). |
| **Tue 06.10** | JST-XH parts list (B4B/B3B/B2B counts, XHP housings, SXH contacts; XH ≠ PH ≠ ZH; sensors need XH→Dupont cables; vertical headers); two long-term kits (CQRobot 460 + pre-crimped silicone kit); how to solder the XIAO (header sandwich) vs a WROOM (drag soldering); the WROOM minimal system BOM; ordered 3 × ESP32-S3-DevKit-Lipo + 3 × WROOM-1 N16R8 (Comet) and prototyping/soldering extras (Amazon); BOM merged into one sheet (v2 → v3 sorted by type); visual BOM v2; architecture v1 poster; **3D model** (renders + interactive viewer) → **beams through the power box found → CAD v1.9: box on the beams**. |

## 11. Numbers register — every figure we rely on and where it came from

| Number | Value | Origin | Lives in |
|---|---|---|---|
| Scale | ~1:9 (19.4 cm person) | 20 cm dummy chosen first | README |
| Mass budget | 4.7 kg (chassis 1.2 measured by DFRobot spec; hulls ~1.55 calc.; rest estimated) | hand calc 28.09 | `draft` comment |
| Waterplane | ~0.112 m² for two hulls (0.056 each incl. taper loss) | polygon area of the outline | `check.py` |
| Draft | **42 mm** at 4.7 kg | mass / (waterplane × 1000) | `draft = 42` |
| Freeboard | ~78 mm | 120 − 42 | — |
| Hull | 610 × 100 × 120, bow taper 150, tip R6, wall 1.8, floor 2.0, cut 305, bulkhead 3, ribs 3 at 100/200/420/520, rim notch 10 | bed-fit + leak logic | `hull_*`, `rib_x` |
| Bed diagonal need | (305+6+100)/√2 = **291 mm** of 300 | geometry | `plate_check` |
| Joint bolts | z 75 and 105, y ±32, Ø3.4, above waterline | leak logic | `joint_bolt_*` |
| Inserts | OD 4.0 (ruthex M3) → hole 4.0 | ruthex spec | `insert_d` |
| Gap between hulls | 240 → **250** (tracks 230 + 10 + margin) | measured 02.10 | `gap` |
| Overall beam | 450 mm | 250 + 2×100 | — |
| Beams | 15×15×1 Al, at x = **385 / 500**, length **304** (2·(boss_y + 13), boss_y = 138.8) | plate 364–516 | `beam_x`, echo |
| Bosses | at 165 / 200 / 385 / 500; 30 long, 24 deep, 20 high, inserts 16 apart | arch/pivot/beams | `boss_*` |
| Arch | x **165**, underside z **235**, posts 115 + 19 tall | sweep clearance 16.4 mm | `arch_x`, `arch_z` |
| Pivot | x 200, shaft z 105; block bottom z 75 (33 above WL) | geometry | `pivot_x`, `shaft_z` |
| Arm | 110 × 12 × 6; parallelogram gap **22**; disc pad r 14 | clearance to idler boss | `arm_*` |
| Angles | deployed **215°** (rod 34 mm under WL, x 54…274 → cradle −110…110), stowed **45°** (rod z 149, coupler x 270–286) | kinematics | `deploy_a`, `stow_a` |
| Cradle | Ø5 rod, 220 long, **112** between rods (= 2·coupler_y; was 123 with the 4 mm disc guess) | derived from arm plane, TD-8120MG + plastic disc measured 10.10 | echo |
| Servo TD-8120MG | 40.3 × 20.14 × 40.7, ears 50 mm apart, ear plane ≈ 28 (to measure), shaft 10.3 from end | measured 02.10 | preset `TD8120` |
| Servo ST3215 | 45.22 × 24.72 × 35 (datasheet, MEASURE) | Waveshare | preset `ST3215` |
| ROB0154 | 300 × 230 × **124.6**, plate 152.2 × 134.8 × 2, motor axis **62** above tracks, footprint x 290–590 | measured 02.10 + manual | `ch_*`, `motor_axis` |
| Chassis mount | raise 0, plate hangs **1.4 mm** under beams (126 − 124.6) | geometry | `plate_gap` echo |
| Motor dryness | 62 − 42 = **20 mm** | — | echo |
| Camera | lens 274 mm above WL, tilt 15°, D45 45°×35°, centre of view at 1 m, coverage 0.45 m → horizon | geometry | `cam_tilt` |
| Pixel math | 110°/32 = 3.4°/px (dummy < 2 px at 2 m); D45 ≈ 1.4°/px | — | — |
| Power box | 152 × 135 × 66, wall 2.4, PG7 ×6 (Ø12.5), toggle Ø12.4; **v1.9: floor on the beams at z 141 (lid top 210)**, 4 × M3×30 through box + beam + plate at beam x / y ±30 (MEASURE slots), rails 3 mm, insert bosses h 6 | plate size; beam clash 06.10 | `pb_*`, `pb_z`, `pb_beam_y` |
| LiPo | 2× Turnigy 2200 mAh 3S 40C XT60, 108 × 33 × 23, ~204 g | bought | compartment 305–420 |
| Runtime | ~7 A average → ~18 min per 2200 pack | estimate | — |
| Fuses | main inline **30 A**; block 20 / 15 / 10 / 5 / 5 A; polyfuse 1.1 A on 5 V | — | spec §5 |
| Kill | 50 A/12 VDC toggle (main) + 20 A ON-ON rocker (logic → OE + ladder) | — | diagram |
| Divider | 100k / 33k → 12.6 V → 3.13 V, ~95 µA | — | breakout R1/R2 |
| Pull-ups | 4.7 kΩ ×4 | — | spec |
| XIAO pins | A0 VBAT, A1 ladder, D2 SCL1, D3 SDA1, D4 SDA0, D5 SCL0, D6 TX1, D7 RX1, SPI→SD, USB→Pi | pin budget | PINOUT.md |
| I2C addresses | MLX 0x33 (both → two buses), PCA9685 0x40, BNO055 0x28 | datasheets | — |
| Breakout | 50 × 40, holes 44 × 34, XIAO rows 15.24 (measured 15.35), JST-XH pads Ø1.0 | generated 03.10 | `.kicad_pcb` |
| Carrier | 100 × 80, holes 93 × 73 | spec | SPEC.md |
| Thrusters | Cuifati 12 V 8 A 1.2 kg (×2 = 2.4 kg for a 4.7 kg boat) | listing | — |
| Beams from tube | 3 × 304 = 912 of 1000 → 2 tubes | — | — |
| Ballast | 12 × M12 ≈ 240 g | Bauhaus | — |
| Pesho | 19 cm, ~100–150 g, head Ø46, 6 vents, 37 °C target, Wedze ~50 °C air | — | `head_*` |
| Pool | ~2 m, depth ≥ 40 cm | — | — |
| Portfolio | ≤ 25 files, ≤ 2 min video, images ≤ 5 MB, video ≤ 250 MB, submit 28.12, RA 4.01.2027 | MIT / SlideRoom | — |
| PCB fab | Aisler 3 pcs, ~15–20 € (rev 0), 30–40 € (carrier); order carrier ≥ 11.10 | — | README |
| rev 0 DRC | round 1: 32 (2 errors) → round 2: 0 errors / 4 silk → round 3: clean (15 lib warnings) | KiCad 05.10 | `..._rev0_v3.kicad_pcb` |
| rev 0 fixes | J2.2/J3.2 solid zone connect; R1/R2 pads 7.5/15.12; labels ≥ 0.8 mm at x 5.5 / 41.8 | generator | `gen.py` |
| TD-8120MG (final) | 40.3 × 20.14 × 40.7; ear plane 28.0; ears 50 apart, holes 10 apart Ø4.34; shaft 10.4 from front | measured 02/05.10 | preset `TD8120` (v1.8) |
| Camera clearance | ≥ 15 mm above the Sense module in the box | render 05.10 | logic box layout |
| JST-XH on boards | B4B ×12, B3B ×4, B2B ×6; housings XHP; contacts SXH-001T-P0.6 | rev 0 + rev A | spec, README |
| PLA on hand | 7 × 1 kg: black, red, white ×2, blue, green, orange | 05.10 | BOM row 28 |
| ESP32-S3 (v2) | WROOM-1 N16R8; avoid GPIO 26–32, 35–37, 0/3/45/46, 19/20; ~36 usable GPIO, 3 UART, 2 I2C, TWAI | datasheet | FAILS §12 |
| WROOM support parts | AP2112K-3.3, 10/22 µF, polyfuse 1.1 A, SMBJ5.0A, 10 kΩ + 1 µF on EN, 2× 5.1 kΩ CC, USBLC6-2SC6 | Espressif ref. design | — |
