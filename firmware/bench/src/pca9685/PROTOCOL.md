# Bench protocol · pca9685 · PCA9685 module + one hobby servo (TD-8120MG or MG90S) on CH0

Env `pca9685` · CSV `t_ms,ch,us,sweep,kill` at 10 Hz · pins from `include/pins_devkit.h`.

## 1. Wiring

| From (DevKit-Lipo) | To (PCA9685) | Wire | Note |
|---|---|---|---|
| GPIO48 `PIN_I2C0_SDA` | SDA | green | I2C-0 = pUEXT pins; module has its own pull-ups |
| GPIO47 `PIN_I2C0_SCL` | SCL | teal | |
| 3V3 (EXT1 pin 1) | VCC | red | logic supply of the chip (3.3 V keeps SDA/SCL at 3.3 V) |
| GND (EXT1 pin 22) | GND | black | |
| 5 V (buck / EXT1 pin 21) | V+ screw terminal | red 18 AWG | **servo power**, never from the DevKit 3V3 (600 mA max) |
| OE | — (left open) | — | the module has 10 k OE → GND, so outputs are **enabled**. No hardware OE kill on the breadboard; that comes with carrier rev B (Q2 inverter from EN) |
| GPIO14 `PIN_KILL` | rocker **C** (common) | purple | 10 k GPIO14 → 3V3; rocker **KILL** pole → GND. Low = KILL (software stop: the sketch drops every pulse). Same as PINOUT / breadboard 2b. Bench wiring used 22.10 (C023) |
| CH0 pins (PWM/V+/GND) | servo lead (signal / red / brown) | — | signal to the yellow/white pin row |

On the breadboard the rocker is a **software** stop only. The hardware stop is the bench supply **OUTPUT** button (servo power off). Keep a finger near it. The earlier text here ("rocker RUN pole → OE → GND" plus "GPIO14 → rocker KILL pole") asked one SPDT to do two things and contradicted PINOUT; it was never wired that way.

## 2. Before power

| Check | Probes | Expected |
|---|---|---|
| no short | V+ ↔ GND, VCC ↔ GND | no beep |
| I2C not shorted | SDA ↔ SCL, SDA ↔ GND, SCL ↔ GND | no beep; pull-ups read ≈ 10 kΩ-ish to VCC (`expected: record`) |
| OE | OE ↔ GND | ≈ 10 kΩ (module pull-down); nothing else on OE |
| kill pull-up | GPIO14 ↔ 3V3 | ≈ 10 kΩ; GPIO14 ↔ GND with rocker in KILL: beep; in RUN: no beep |
| common ground | DevKit GND ↔ module GND ↔ servo brown ↔ bench supply − | beep |

## 3. First power

DevKit on USB first (no servo power). Flash through either port, but **monitor on the left USB-C** (`/dev/cu.usbmodem…`): this env keeps `ARDUINO_USB_CDC_ON_BOOT=1`, so `Serial` is the native USB, not the CH340 (`/dev/cu.usbserial-…`, right port) — FAILS 171. The banner must say `# OK PCA9685 found, 50 Hz, all channels off`; if `WARN … not found` → `scan` (expect `0x40`); if `scan` finds nothing, read the pin numbers printed on the DevKit next to the SDA/SCL wires (48 / 47), not the breadboard row. Then servo power from the bench supply at **5.0 V, current limit 1.0 A** (TD-8120MG stall is higher — raise only after the idle current is known, `expected: record`).

## 4. Steps

| # | Command | Watch | Expected |
|---|---|---|---|
| 0 | `dm 10000` | `# OK dead-man 10000 ms` | steps are human-paced: 10 s between commands before `# DEADMAN`; the 2 s default comes back in step 7 |
| 1 | `scan` | `# I2C Wire found 0x40` | address from bom.csv row 72 |
| 2 | rocker → RUN, `ch 0 1500` | `ch` 0, `us` 1500 | servo moves to the middle |
| 3 | `ch 0 1000` | `us` ramps 1500 → 1000 over ≈ 1 s (500 µs/s) | smooth, no jump; current `expected: record` |
| 4 | `ch 0 2300` | `# WARN 2300 us outside the soft window 1000–2000` | refused |
| 5 | `limit 700 2300` then `ch 0 2300` | `# WARN window widened …`; `us` ramps to 2300 | **listen**: a servo buzzing at the end = it hit the mechanical stop → `0` and narrow the window |
| 6 | `sweep 1` | `us` goes end-to-end, 0.5 s hold at each end, `sweep` 1 | |
| 7 | `dm 2000` (while the sweep runs) | `# OK dead-man 2000 ms`; sweep continues | |
| 8 | stop typing for 2 s | `# DEADMAN`, `us` 0, servo goes limp | |
| 9 | `sweep 1`, rocker → KILL | `# KILL …`, `kill` 1, `us` 0; servo goes limp within one row (software stop; OE is not switched on the breadboard) | |
| 10 | optional: logic analyser on CH0 | frame period | 20.0 ms ± 0.5 ms; if off, `osc <Hz>` until it is (library default 25 MHz; VERIFY) |

From step 8 on the dead-man is back at 2 s: type the next command within 2 s of the previous one, or expect `# DEADMAN` in between (harmless — it only drops the pulses).

## 5. Pass
Servo follows `ch 0 <us>` with a visible ramp, out-of-window values are refused, sweep runs, dead-man and the rocker both drop the pulse.

## 6. Photos (card folder, `C###_NN.jpg`)
`_01` wiring with the rocker on GPIO14 · `_02` meter GPIO14↔3V3 (10 k) · `_03` supply at step 3 · `_04` servo at 1000 / 2000 µs (two frames, ruler for the horn angle) · `_05` analyser screenshot if step 10 done.

## 7. Pair (C023)

Two TD-8120MG, facing each other, on **CH10** and **CH11** (see `hardware/wiring/PINOUT.md`). chB is the mirror of chA around 1500 µs: `us_A = 500 + deg/180 × 2000`, `us_B = 3000 − us_A`. Both channels follow **one** degree ramp (default 20 °/s). The first `pair` after boot, `0`, dead-man or KILL snaps (no pulse to ramp from); the next `pair` ramps. `dm` and the rocker drop **both** pulses, same as `ch` / `sweep`.

Servo power for this section: Jesverty bench supply at **6.0 V, current limit 3 A**. That is not the 5.0 V / 1 A of §3.

The default soft window is 1000–2000 µs, which is about 45°–135° on this map. `pair 10 11 90` and `pair 10 11 45` fit. A command whose either pulse falls outside the window is refused (`limit 500 2500` opens the full TD-8120MG range). `215` is refused (outside 0–180).

**Trim (T9).** `trim <ch> <us>` adds a signed offset, −200..+200 µs (≈ ±18°), to that channel **after** the mirror: `us_A' = us_A + trim[chA]`, `us_B' = us_B + trim[chB]`. The window check uses the trimmed pulses. Trims live in RAM only (gone at reset) — **write them on the card**. A trim on a running pair applies at once as a step, so change it in ≤ 20 µs steps while the pair holds. `trim` alone prints both. `?` shows `trimA=… trimB=…`.

**Rule from FAILS 172:** the two arms sit on 25T splines (≈ 14.4° per tooth) and never line up by themselves. **Clock both arms at `pair 10 11 90` before anything joins them.** With the U in both couplers, current **> 0.3 A while nothing moves = the servos are fighting → KILL** (22.10: 0.53 A standing still, 0.09 A with the U out; two arm screws sheared). The first `pair` after KILL / dead-man / `0` snaps — keep hands and the U clear of the arms for it.

CSV `ch` / `us` follow channel A while the pair runs. `?` prints `pair=<chA>/<chB> deg=… usA=… usB=… trimA=… trimB=…`. First lift done 22–23.10 (C023_15, empty U, level); trim not yet run on hardware.

| # | Action / command | Watch | Expected |
|---|---|---|---|
| 1 | Arms OFF the servos. `dm 10000`, then `pair 10 11 90` | both horns | centre (1500 / 1500 µs). Then `pair 10 11 45` → mirrored (1000 / 2000 µs), ramped. Rocker → KILL drops both pulses |
| 2 | Back to `pair 10 11 90`. Fit both arms in the **same pose** on the splines, screws tight. No U yet | arms | both at the same angle by eye / ruler against the bracket; `expected: record` the residual difference in degrees |
| 3 | `trim 11 <us>` in ≤ 20 µs steps (−200..+200; ≈ 11 µs per degree) until the two arms match. `trim` to print | arms, `?` line | match within ± 1° at 90°; then `pair 10 11 60` and `pair 10 11 120` — still matched at both ends (if not, the mismatch is not a pure offset → tell Desk 1) |
| 4 | U ON, empty. `pair 10 11 <lift>` slowly | Jesverty current | moves at 20 °/s (or the rate you pass); standing current `expected: record`; **> 0.3 A still = fighting → KILL**, back to step 2 |
| 5 | Pesho (C021) in the U. Same `pair` | current, photos | `expected: record` current and photos |
