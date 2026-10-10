# 0005 · The boat's controller is the Olimex ESP32-S3-DevKit-Lipo — perfboard now, Aisler carrier in parallel

**Date:** 2026-10-10 · **Status:** accepted (Teddy) · **Cards:** C030 (pinout freeze), C031 (perfboard), C032 (Aisler carrier rev B)

## Problem
The v1 plan put a Seeed XIAO ESP32-S3 Sense on carrier rev A (`pcb/carrier-revA/SPEC.md`). The XIAO has 11 usable pins, so the leak
probe and the kill switch had to share one ADC pin (the resistor ladder) and every PWM went through the PCA9685. Since then all the
bench work (night task T3, `firmware/bench`, breadboard sheet 2b, `hardware/wiring/PINOUT.md` "DevKit-Lipo") and the mission firmware
env `devkit_lipo` were built on the Olimex ESP32-S3-DevKit-Lipo (ESP32-S3-WROOM-1, ~36 usable GPIO, made in Plovdiv, open hardware;
3 bought from Comet). Carrier rev A no longer matches the board everything runs on.

## Decision
- **v1 controller = Olimex ESP32-S3-DevKit-Lipo.** The DevKit-Lipo table in `hardware/wiring/PINOUT.md` and
  `firmware/bench/include/pins_devkit.h` are the master pin list.
- **Two carriers in parallel:**
  - a **perfboard** carrier for r2c (22.10, "swims on remote") — Teddy solders it, it is the boat's board until the PCB arrives;
  - a **2-layer PCB, carrier rev B**, ordered from **Aisler** (EU) — same nets as the perfboard, the clean version for the
    later releases and the portfolio.
- Both carry the DevKit on **female headers** (it stays removable) and only signals, 5 V and 3V3. 12 V for the thrusters, the servo
  bus and the BTS7960s stays on the fuse block (as in rev A).
- KILL and LEAK get their own pins (GPIO14, GPIO7): the shared ADC ladder is no longer needed on this board.
- Carrier rev A (XIAO) is not ordered. Its spec stays in the repo as history.

## Open (to measure / decide before the layout is fixed — card C030)
- EXT1 ↔ EXT2 row spacing and header pin numbers, measured on the board (PINOUT VERIFY 3).
- GPIO39 at reset (C015) → 10 k pull-downs on GPIO39–42 yes / no.
- ESC signal level (C006) → direct to GPIO1/2 or through a level shifter.
- BTS7960 IS_R / IS_L on GPIO10/11 — used or not.
- The role of the XIAO ESP32-S3 Sense in v1 (camera node or nothing).
- `firmware/armini` safety (T2) still decodes KILL + LEAK from the ADC ladder: switch it to the two digital pins for the DevKit (small Cursor task) — or keep the ladder on the perfboard if that is simpler. Decide with C030.
- Aisler lead time at checkout: standard ~8 working days + DHL to Sofia; "Blitz" much faster for a price. Order by ~13.10 for a
  board in hand before r3b (29.10).
