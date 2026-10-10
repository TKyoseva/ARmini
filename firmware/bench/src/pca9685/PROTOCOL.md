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
| 3V3 → 2.2 kΩ → OE | OE | — | SPEC §5 R10: pull-up; rocker RUN pole → OE → GND when in RUN. OE high = outputs off |
| GPIO14 `PIN_KILL` | rocker KILL pole | purple | so one rocker does hardware OE and software kill |
| CH0 pins (PWM/V+/GND) | servo lead (signal / red / brown) | — | signal to the yellow/white pin row |

## 2. Before power

| Check | Probes | Expected |
|---|---|---|
| no short | V+ ↔ GND, VCC ↔ GND | no beep |
| I2C not shorted | SDA ↔ SCL, SDA ↔ GND, SCL ↔ GND | no beep; pull-ups read ≈ 10 kΩ-ish to VCC (`expected: record`) |
| OE pull-up | OE ↔ 3V3 (rocker in KILL) | ≈ 2.2 kΩ; OE ↔ GND with rocker in RUN: beep |
| common ground | DevKit GND ↔ module GND ↔ servo brown | beep |

## 3. First power

DevKit on USB first (no servo power): the banner must say `# OK PCA9685 found, 50 Hz, all channels off`; if `WARN … not found` → `scan` (expect `0x40`). Then servo power from the bench supply at **5.0 V, current limit 1.0 A** (TD-8120MG stall is higher — raise only after the idle current is known, `expected: record`).

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
| 9 | `sweep 1`, rocker → KILL | servo stops at once (OE high = hardware); `# KILL …`, `kill` 1 | |
| 10 | optional: logic analyser on CH0 | frame period | 20.0 ms ± 0.5 ms; if off, `osc <Hz>` until it is (library default 25 MHz; VERIFY) |

From step 8 on the dead-man is back at 2 s: type the next command within 2 s of the previous one, or expect `# DEADMAN` in between (harmless — it only drops the pulses).

## 5. Pass
Servo follows `ch 0 <us>` with a visible ramp, out-of-window values are refused, sweep runs, dead-man and OE/rocker both drop the pulse.

## 6. Photos (card folder, `C###_NN.jpg`)
`_01` wiring with the OE pull-up and rocker · `_02` meter OE↔3V3 (2.2 k) · `_03` supply at step 3 · `_04` servo at 1000 / 2000 µs (two frames, ruler for the horn angle) · `_05` analyser screenshot if step 10 done.
