# Bench protocol · esc · two thruster ESCs on GPIO1 (L) / GPIO2 (R) · C006 → C025

Env `esc` · CSV `t_ms,l_us,r_us,kill,armed` at 10 Hz · pins from `include/pins_devkit.h`.
Thruster listing (C002, **not confirmed for this unit**): PWM 50 Hz, 1500 µs = stop, 1500 → 2000 forward, 1500 → 1000 reverse; arming not documented.
**Not yet run on hardware.**

## 1. C006 — signal level (done 23.10)

Measured with the signal not connected: Jesverty 9.00 V, ESC idle 0.009 A.

| Probe | Reading |
|---|---|
| yellow (signal) ↔ black, open | **4.983 V** |
| yellow ↔ black, 10 kΩ from yellow to black | **3.58 V**, so the ESC has an internal pull-up of about 3.9 kΩ to 5 V |
| white ↔ black | 0.0002 V (white is the signal ground) |

**Yellow must never touch GPIO1/2 directly**: the ESP32-S3 is 3.3 V only. Each channel goes through an S8050 NPN instead (open collector). The NPN inverts, so the `esc` env inverts too: the banner says `# ESC output INVERTED (NPN level shifter, C006)`.

Measure the second ESC the same way before wiring it.

## 2. Wiring (per channel, the right ESC the same on GPIO2)

S8050 TO-92 legs are **E-B-C** with the flat face toward you, legs down (FAILS 162).

| From | Through | To | Note |
|---|---|---|---|
| GPIO1 `PIN_ESC_L` (EXT2 4) | **1 kΩ** | S8050 base | GPIO2 `PIN_ESC_R` (EXT2 5) for the right ESC |
| S8050 base | **10 kΩ** | GND | holds the transistor off while the pin floats at boot |
| S8050 emitter | — | GND | |
| S8050 collector | — | ESC **yellow** | the ESC's own ≈ 3.9 k pull-up makes it 5 V when the transistor is off |
| ESC **white** | — | GND | signal ground |
| Jesverty − | — | DevKit GND (EXT1 22) | common ground |
| GPIO14 `PIN_KILL` | rocker **C** | | 10 k GPIO14 → 3V3; rocker **KILL** pole → GND. Low = KILL |

Pin HIGH turns the transistor on and pulls yellow LOW. So the sketch keeps the pin LOW for the pulse and HIGH for the rest of the 20 ms frame, and the collector carries the normal pulse.

**Boot state:** until `setup()` runs, the pin floats, the 10 k pulls the base low and the transistor is off. The ESC holds yellow HIGH, which means no pulses, so the ESC does not arm. From the first line of `setup()` the collector carries 1500 µs.

**Before power:** meter on the ESC side, yellow ↔ white with the DevKit unplugged: ≈ 5 V (transistor off). Base ↔ GND ≈ 10 kΩ. Collector ↔ emitter: no beep.

KILL is a **software** stop here (the sketch writes 1500 µs). The hardware stop is the bench supply **OUTPUT** button; on the LiPo, the main switch / 20 A fuse slot.

## 3. Flash and first look

Flash `esc`; **monitor on the left USB-C** (`/dev/cu.usbmodem…`, this env keeps `CDC_ON_BOOT=1`; FAILS 171). Banner: `# ESC output INVERTED (NPN level shifter, C006)`, then `both 1500 us, NOT armed`. Optional, logic analyser on the **collector**: HIGH for 1.5 ms, LOW for the rest of the 20 ms frame. On GPIO1 itself the same signal is the inverse: LOW for 1.5 ms, HIGH for the rest. CSV shows `l_us` 1500, `r_us` 1500, `armed` 0; `kill` follows the rocker.

## 4. Steps — C025, thruster in the bucket

Jesverty **12.0 V, CC 3 A**, meter **in series** on the 10 A jack. `dm 15000` first: each step holds 10 s, and the 2 s default dead-man would cut it (a dead-man also disarms → `arm` again).

| # | Command | Watch | Expected |
|---|---|---|---|
| 0 | `dm 15000` | `# OK dead-man 15000 ms` | |
| 1 | `l 1550` before arming | `# WARN not armed …` | refused, nothing moves |
| 2 | `arm` | ESC beeps; after 3 s `# ARMED`, `armed` 1 | `expected: record` the beep pattern |
| 3 | `l 1550`, 10 s | current, direction | ramps at 200 µs/s; `expected: record` A + forward/reverse |
| 4 | `l 1450`, 10 s | current, direction | passes 1500 on the way; `expected: record` |
| 5 | `l 1600`, 10 s | current, direction | `expected: record` |
| 6 | `l 1650`, 10 s | current, direction | `expected: record` |
| 7 | `l 1700` | `# ERR LIMIT` | refused, no move (narrow limit 1350–1650) |
| 8 | while spinning: rocker → KILL, **on video** | prop | `# KILL …`, `l_us` 1500 in the same row, `armed` 0; **prop stops < 0.5 s** |
| 9 | `0` at any time | | both 1500 µs at once, `armed` 0 |

## 5. Full power — LiPo only

Only on the LiPo through the inline fuse + 20 A slot, never on the Jesverty. `arm`, `limit wide` (`# WARN …`), then the step ≤ **5 s**, then `0`. `limit narrow` returns to 1350–1650.

## 6. Pass

C006: done 23.10 (4.98 V idle → S8050 NPN, inverted output). C025: `arm` → `# ARMED`, current + direction recorded at 1450 / 1550 / 1600 / 1650, `1700` refused, KILL stops the prop < 0.5 s on video.

Log: `python3 scripts/bench_log.py --port /dev/cu.usbmodem* --card C025 --name esc-bucket` (repo root).

## 7. Photos / video (card folder, `C###_NN.jpg`)

`_01` meter on yellow ↔ black (C006) · `_02` wiring with both S8050s (flat faces visible) · `_03` meter in series + CSV row at each step · `_04` KILL video, slow-mo, prop in view.
