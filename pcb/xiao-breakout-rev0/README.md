# AR-Mini XIAO breakout — rev 0 (learning board for Aisler)

50 × 40 mm, 2 layers, THT only. Goal: go the whole way KiCad → DRC → Aisler → soldering → it works, with something that is really used afterwards: this is the XIAO part of the carrier board (sensors, servo bus, 5 V input, battery).

## What is on it
- J1/J2 — 2 × 1×7 female headers for the XIAO ESP32S3 Sense (15.24 mm between the rows). The XIAO's USB-C faces the top edge (silkscreen "USB-C ^").
- J3 I2C0 (JST-XH 4): 3V3 · GND · SDA0 (D4/GPIO5) · SCL0 (D5/GPIO6) → MLX90642-D45, BNO055, PCA9685
- J4 I2C1 (JST-XH 4): **SCL1 (D2/GPIO3) · SDA1 (D3/GPIO4)** · GND · 3V3 → MLX90640-110°. The pin order differs from J3 — on purpose, see the note.
- J5 SERVO (JST-XH 4): RX (D7/GPIO44 ← driver TX) · TX (D6/GPIO43 → driver RX) · GND · NC
- J6 PWR (JST-XH 2): +5 V · GND — from the buck
- J7 VBAT (JST-XH 2): VBAT · GND — from the "5 A logic" fuse (measurement only, almost zero current)
- R1 100k / R2 33k — divider to A0 (D0/GPIO1): 12.6 V → 3.13 V
- R7 330 Ω + LED1 — 3V3 indicator (on = the XIAO is alive)
- H1–H4 — Ø3.2 mounting holes, grid 44 × 34
- GND — pour on the bottom layer; 3V3 and I2C-1 are routed on the bottom, everything else on top.

Note: `Wire1.begin(4, 3)` (SDA=GPIO4, SCL=GPIO3). They are swapped so the tracks do not cross; the carrier board is the same.

## How to open and check it (10 minutes)
1. KiCad 8 or 9 → **PCB Editor** (standalone, without a project) → File → Open → `AR-Mini_xiao_breakout_rev0.kicad_pcb`. The file is in KiCad 7 format; on Save it will be converted — that is normal.
2. Press **B** (Fill all zones) — the bottom layer fills with ground.
3. **Inspect → Design Rules Checker → Run DRC.** Expect 0 errors. Warnings like "footprint not found in library" / "no schematic" are normal for a standalone board — ignore them.
4. **View → 3D Viewer** (Alt+3) — look at it. The headers and JSTs will have no 3D models (generated footprints), only pads — that is fine.
5. To change it before ordering: move tracks with **M**, add them with **X**; Edit → Edit Text and Graphics for the labels.

## Ordering from Aisler (5 minutes)
- Simplest: **aisler.net → New project → Upload** → upload the `.kicad_pcb` directly (they accept KiCad files; no Gerbers needed).
- Or: Plugin and Content Manager → install "AISLER Push for KiCad" → toolbar button → opens the site with the board uploaded.
- Choose: 2 Layer · 1.6 mm · **3 pcs** (minimum) · lead-free HASL (or "Beautiful Boards" for a black mask, +~10 €) · delivery to Bulgaria.
- Expected price: ~15–20 € for three. Lead time: 3–5 working days production + DHL.
- Before "Order": print 1:1 on paper (File → Plot → PDF, scale 1:1) and put the XIAO and the JSTs on the sheet. Every pin in its hole.

## Parts to solder (all THT, 15 minutes with the HS-03)
| What | Qty | From |
|---|---|---|
| Female header 1×7, 2.54 | 2 | Freenove/Joy-IT kit or Ardboard |
| JST-XH 2.5 mm vertical PCB header, 4 pins | 3 | Vikiwat / Ardboard (~0.20 €) |
| JST-XH vertical, 2 pins | 2 | same |
| Resistors 100k, 33k, 330 Ω (1/4 W) | 1 each | the Freenove kit has 330; 100k/33k from Vikiwat |
| LED 5 mm | 1 | the kit |
| M3 × 6 mm standoffs + screws | 4 | ruthex / DSM set |

Soldering order: resistors → LED → JSTs → headers last (with the XIAO plugged in, so they stay parallel).

## What it teaches that goes into the carrier rev A
- whether the 15.24 mm headers fit this XIAO (measured 15.35);
- whether JST-XH pads with a Ø1.0 hole are comfortable for the crimped wires from the Preciva kit;
- how accurate a 1:1 print is on the paper printer;
- how long it really takes from "Order" to "on the desk" with Aisler for Bulgaria — that number is needed for the rev A schedule.
