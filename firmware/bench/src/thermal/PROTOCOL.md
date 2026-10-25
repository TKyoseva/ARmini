# Bench protocol · thermal · MLX90642-D45 + MLX90640 110° on the DevKit-Lipo · C048 → C029

Env `thermal` · CSV `t_ms,cam,min_C,max_C,mean_C,hot_x,hot_y` at 4 Hz per camera (`cam` = `d45` | `w110`) · heat map every 2 s per camera · pins from `include/pins_devkit.h`.
Reference thermometer: Laserliner ThermoSpot One (bom.csv row 107, ± 2.5 °C, emissivity 0.95).
Decision 25.10 (Teddy, 0005): both thermal boards on the DevKit; the XIAO Sense is the OV3660 node only.
**Not yet run on hardware.** The D45 driver (lib/MLX90642, Melexis + our Wire glue) has never talked to a real part: step 3 is the first time.

## 1. Wiring

Both boards are **3.3 V only** (the D45 dies at 5 V, datasheet abs. max 5 V < 24 h). 3V3 from **EXT1 pin 1 or 2 only**, never from a 5 V pin.

| From (DevKit-Lipo) | To | Wire | Note |
|---|---|---|---|
| GPIO48 `PIN_I2C0_SDA` (EXT2 16) | **D45** SDA | green | Wire (I2C-0), the same two pins as the PCA9685 and BNO055 |
| GPIO47 `PIN_I2C0_SCL` (EXT2 17) | **D45** SCL | teal | |
| 3V3 (EXT1 1) | **D45** VDD | red | |
| GND (EXT1 22) | **D45** GND | black | |
| GPIO8 `PIN_I2C1_SDA` (EXT1 12) | **110°** SDA | green | Wire1 (I2C-1) — not swapped on the DevKit (the swap was a XIAO thing) |
| GPIO9 `PIN_I2C1_SCL` (EXT1 15) | **110°** SCL | teal | |
| 3V3 (EXT1 2) | **110°** VCC | red | |
| GND (EXT1 22) | **110°** GND | black | |

D45 TO39 pins: **1 SDA · 2 VDD · 3 GND · 4 SCL** (SOURCE: MLX90642 datasheet table 2). Which physical leg is pin 1 → datasheet figure 1 / the breakout's silkscreen — **check before power**.
Short wires (< 15 cm) at 400 kHz; `i2c 100` for longer ones (then `rate 4` only).
The 110° board hangs upside down on the arch → the sketch rotates its frame 180° (`FLIP_110 1`); the D45 is mounted upright.

## 2. Before power

| Check | Probes | Expected |
|---|---|---|
| no short | 3V3 ↔ GND | no beep |
| I2C not shorted | SDA ↔ SCL, each ↔ GND, on both buses | no beep |
| polarity, twice | VDD / VCC pin label vs. the red wire | visual — both sensors die at 5 V |
| pull-ups | Wire SDA ↔ 3V3 | ≈ 2–5 kΩ (the PCA9685 breakout carries them); if > 10 kΩ add 4.7 k on SDA and SCL |

## 3. First power

USB only. Banner, in order:
- `# I2C Wire found 0x40 (PCA9685 / BNO055)`, `0x28 …`, and **one** `… <- candidate D45` (datasheet default **0x66**; the sketch takes whatever is not 0x40 / 0x28 / 0x70 — `expected: record` the address).
- `# OK MLX90642 @0x66 id … fw <a>.<b>.<c>` → record the FW version (features differ by FW, datasheet §3.1.4.3).
- `# MLX90642 continuous, temperature output, 4 Hz, emissivity <e>` → `expected: record` e (EEPROM default; not changed by the sketch).
- `# OK MLX90640 @0x33 serial …, chess, 18 bit, 4 Hz, frame rotated 180° (FLIP_110)`.

If `WARN 0x.. answers but does not read like an MLX90642`, the I2C byte format in `lib/MLX90642/src/MLX90642_arduino.cpp` is wrong for this part → FAILS entry + logic analyser on SDA/SCL.
If `WARN no D45 candidate`, `scan` and look at Wire; a D45 at 0x40 or 0x28 would hide behind the known list — then unplug the PCA9685/BNO055 and `scan` again.

## 4. Steps

| # | Command / action | Watch | Expected |
|---|---|---|---|
| 1 | nothing, wall at room temperature in front of both | two kinds of rows, each at ≈ 250 ms spacing | `mean_C` of **both** = ThermoSpot on the wall ± 3 °C; `d45` and `w110` within 2 °C of each other (`expected: record` all three) |
| 2 | hand at 30 cm, centre of both | `max_C` 30–36 on both | `hot_x` 13–18, `hot_y` 9–14 on both; maps show a `@` blob in the middle |
| 3 | hand to the **right** edge of the field (your right, facing the cameras) | `hot_x` of each camera → 0 or 31 | **VERIFY** orientation per camera: write down which edge is `x = 0` for `d45` and for `w110` (with the flip the 110° should agree with the D45) |
| 4 | hand to the top | `hot_y` → 0 or 23 | same, record for both |
| 5 | `rate 8` | `t_ms` deltas ≈ 125 for both | `# WARN … frame read failed` on either → 400 kHz with 24 chunked reads is too slow for that camera; note it, `rate 4` |
| 6 | `i2c 100`, `rate 4` | rows keep coming | both still at ≈ 250 ms; `expected: record` if the D45 drops frames (datasheet table 25 says 100 kHz is OK at 4 Hz) |
| 7 | `i2c 400`, `raw 1` for 3 s, `raw 0` | `# RAW d45 …` and `# RAW w110 …` | 768 values each; save with `scripts/bench_log.py` |
| 8 | `map 0` | no more maps | `0` does the same plus raw off |

## 5. Pesho at 1 / 2 / 3 m (card C029)

Pesho's head (the warmer, ThermoSpot on the forehead → `T_pesho`, `expected: record`, target ≈ 37 °C) in front of both cameras at room temperature, nothing else warm in the field.

| Distance | Expected `d45` | Expected `w110` |
|---|---|---|
| 1 m | `max_C` ≥ T_pesho − 5, blob ≥ 2×2 px (45° / 32 px ≈ 1.4° per pixel → a 15 cm head covers ≈ 6 px) | `max_C` ≥ T_pesho − 10, 1–2 px (110° / 32 px ≈ 3.4° per pixel) |
| 2 m | `max_C` ≥ T_pesho − 10, ≈ 3 px | blob likely 1 px, `max_C` `expected: record` |
| 3 m | `max_C` `expected: record`; still the hottest pixel? | `expected: record` |

Pass for C029: at **1 m** the D45's `hot_x`/`hot_y` sit on Pesho in every row for 10 s (no jumps to another pixel), and `max_C` − `mean_C` ≥ 3 °C. Record the 2 m and 3 m numbers for the search range in `firmware/armini`.

## 6. Pass (C048)
Both sensors found at boot without a hard-coded D45 address, 4 Hz steady on both, `mean_C` of both within ± 3 °C of the ThermoSpot on a uniform wall, hand visible in `max_C`/`hot_x`/`hot_y` on both, orientation recorded for both, D45 FW version and emissivity recorded.

## 7. Photos (card folder, `C###_NN.jpg`)
`_01` wiring close-up with both boards (VDD labels visible) · `_02` ThermoSpot on the wall · `_03` screen with the two heat maps and your hand · `_04` the hand-at-the-edge test (`hot_x` of both) · `_05` Pesho at 1 m with the `d45` map.
