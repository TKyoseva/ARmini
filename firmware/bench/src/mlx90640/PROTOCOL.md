# Bench protocol · mlx90640 · Waveshare MLX90640 110° thermal camera on I2C-1

Env `mlx90640` · CSV `t_ms,min_C,max_C,mean_C,hot_x,hot_y` at 4 Hz · heat map every 2 s · pins from `include/pins_devkit.h`.
Reference thermometer: Laserliner ThermoSpot One (bom.csv row 107, ± 2.5 °C, emissivity 0.95).

## 1. Wiring

| From (DevKit-Lipo) | To (MLX90640 board) | Wire | Note |
|---|---|---|---|
| GPIO8 `PIN_I2C1_SDA` | SDA | green | sheet 2b step 4 — **not swapped** on the DevKit (the swap is a XIAO/rev 0 thing) |
| GPIO9 `PIN_I2C1_SCL` | SCL | teal | |
| 3V3 (EXT1 pin 1) | VCC | red | 3.3 V only (bom.csv row 77) |
| GND (EXT1 pin 22) | GND | black | |

Short wires (< 15 cm): the frame read is 1 500+ bytes at 400 kHz.

## 2. Before power

| Check | Probes | Expected |
|---|---|---|
| no short | VCC ↔ GND | no beep |
| I2C not shorted | SDA ↔ SCL, each ↔ GND | no beep |
| polarity | VCC pin label vs. 3V3 wire | visual, twice — the sensor dies at 5 V |

## 3. First power

USB only (the camera draws ≈ 25 mA from the DevKit 3V3 — `expected: record` on the USB meter if you have one). Banner: `# OK MLX90640 found, serial …, chess mode, 18 bit, 4 Hz`. If `WARN … not found` → `scan` on Wire1 (expect `0x33`).

## 4. Steps

| # | Command / action | Watch | Expected |
|---|---|---|---|
| 1 | nothing, wall at room temperature in front | rows at ≈ 250 ms spacing (`t_ms` deltas 230–270) | `mean_C` = ThermoSpot on the same wall ± 3 °C (sensor ± 1.5 + ThermoSpot ± 2.5 → tolerance set to 3; `expected: record` the two numbers) |
| 2 | hand at 30 cm, centre | `max_C` 30–36, `hot_x` 13–18, `hot_y` 9–14 | map shows a `@` blob in the middle |
| 3 | hand to the right edge of the field (camera's right) | `hot_x` → 0 **or** 31 | **VERIFY** orientation: write down which edge is `x = 0` — needed for the bearing sign in `firmware/armini` |
| 4 | hand to the top | `hot_y` → 0 or 23 | same, record |
| 5 | warm-water bottle (ThermoSpot reading T) at 1 m | `max_C` vs T | `expected: record` the drop with distance (110° / 32 px ≈ 3.4° per pixel: a bottle at 1 m covers only 1–2 pixels) |
| 6 | `rate 8` | `t_ms` deltas ≈ 125 | if `# WARN frame read failed` appears, 400 kHz is too slow — note it, back to `rate 4` |
| 7 | `raw 1` for 3 s, then `raw 0` | `# RAW <t_ms> v0 … v767` lines | 768 values each; save with `scripts/bench_log.py` |
| 8 | `map 0` | no more maps | `0` does the same plus raw off |

## 5. Pass
Sensor found, 4 Hz steady, `mean_C` within ± 3 °C of the ThermoSpot on a uniform wall, hand clearly visible in `max_C`/`hot_x`/`hot_y`, orientation recorded.

## 6. Photos (card folder, `C###_NN.jpg`)
`_01` wiring close-up (VCC pin label visible) · `_02` ThermoSpot display on the wall · `_03` screen with the heat map and your hand · `_04` the hand-at-the-edge test showing `hot_x` (for the orientation note).
