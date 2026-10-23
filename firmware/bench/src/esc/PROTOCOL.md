# Bench protocol · esc · two thruster ESCs on GPIO1 (L) / GPIO2 (R) · C006 → C025

Env `esc` · CSV `t_ms,l_us,r_us,kill,armed` at 10 Hz · pins from `include/pins_devkit.h`.
Thruster listing (C002, **not confirmed for this unit**): PWM 50 Hz, 1500 µs = stop, 1500 → 2000 forward, 1500 → 1000 reverse; arming not documented.
**Not yet run on hardware.**

## 1. C006 first — signal NOT connected

The ESP32-S3 is 3.3 V only. Nobody knows yet whether the ESC's yellow signal wire idles above 3.3 V. Measure it before GPIO1 is ever connected.

1. Thruster in a bucket, duct under water, held down.
2. Jesverty **9.0 V, CC 0.10 A**: red → +, black → −. Signal wires (yellow, white) touch nothing.
3. Meter DC V: **yellow ↔ black** and **white ↔ black**. Write both numbers on C006.

| yellow ↔ black | Next |
|---|---|
| ≤ 3.6 V | connect directly: yellow → GPIO1 `PIN_ESC_L` (EXT2 4), white → GND |
| > 3.6 V | **stop, do not connect.** Level shifter first (74AHCT125; JP1/JP2 on carrier rev B) |

The second ESC goes the same way on GPIO2 `PIN_ESC_R` (EXT2 5), after its own measurement.

## 2. Wiring

| From (DevKit-Lipo) | To | Wire | Note |
|---|---|---|---|
| GPIO1 `PIN_ESC_L` (EXT2 4) | left ESC yellow (signal) | yellow | only after §1 says ≤ 3.6 V |
| GPIO2 `PIN_ESC_R` (EXT2 5) | right ESC yellow (signal) | yellow | only after its own §1 |
| GND (EXT1 22) | ESC white + bench supply − | black | common ground |
| GPIO14 `PIN_KILL` | rocker **C** | purple | 10 k GPIO14 → 3V3; rocker **KILL** pole → GND. Low = KILL |

KILL is a **software** stop here (the sketch writes 1500 µs). The hardware stop is the bench supply **OUTPUT** button; on the LiPo, the main switch / 20 A fuse slot.

## 3. Flash and first look

Flash `esc`; **monitor on the left USB-C** (`/dev/cu.usbmodem…`, this env keeps `CDC_ON_BOOT=1`; FAILS 171). Banner: `both 1500 us, NOT armed`. CSV shows `l_us` 1500, `r_us` 1500, `armed` 0; `kill` follows the rocker.

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

C006: both signal-wire voltages written down and the connect / level-shifter decision made. C025: `arm` → `# ARMED`, current + direction recorded at 1450 / 1550 / 1600 / 1650, `1700` refused, KILL stops the prop < 0.5 s on video.

Log: `python3 scripts/bench_log.py --port /dev/cu.usbmodem* --card C025 --name esc-bucket` (repo root).

## 7. Photos / video (card folder, `C###_NN.jpg`)

`_01` meter on yellow ↔ black (C006) · `_02` wiring · `_03` meter in series + CSV row at each step · `_04` KILL video, slow-mo, prop in view.
