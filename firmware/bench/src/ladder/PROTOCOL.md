# Bench protocol · ladder · VBAT divider + LEAK probe + KILL rocker (inputs only, no actuators)

Env `ladder` · CSV `t_ms,v_adc_mV,v_bat_V,leak_mV,leak,kill` at 10 Hz · pins from `include/pins_devkit.h`.
Resistors from the MOGAOPI kit (bom.csv rows 56, 59), 1 % metal film. Bench supply stands in for the LiPo.

## 1. Wiring

| From (DevKit-Lipo) | Through | To | Wire | Note |
|---|---|---|---|---|
| GPIO4 `PIN_VBAT_ADC` | 100 kΩ up / 30 kΩ down | "VBAT" = bench supply +, divider bottom to GND | yellow | C027 measured 30 k on the bottom leg (carrier rev A keeps 33 k); v_bat = v_adc × 130/30 = × 4.33 |
| GPIO7 `PIN_LEAK` | 10 kΩ to 3V3, 4.7 kΩ to the probe | probe = two bare wire ends; other end GND | purple | sheet 2b step 8 |
| GPIO14 `PIN_KILL` | 10 kΩ to 3V3 | rocker C; rocker KILL pole → GND | purple | sheet 2b: 3.3 V in RUN, 0 V in KILL |
| GND (EXT1 pin 22) | — | bench supply − | black | common ground |

## 2. Before power

| Check | Probes | Expected |
|---|---|---|
| divider values | 100 k leg, 30 k leg (out of circuit) | 100 ± 1 kΩ, 30 ± 0.30 kΩ (C027 measured 30 kΩ) |
| divider assembled | VBAT node ↔ GPIO4 node | ≈ 100 kΩ; GPIO4 node ↔ GND ≈ 30 kΩ |
| nothing on GPIO4 above 3.3 V | VBAT node ↔ GPIO4 **direct** continuity | **no beep** (a direct short would put 12 V on the ESP32) |
| leak pull-up | GPIO7 node ↔ 3V3 | ≈ 10 kΩ |
| kill pull-up | GPIO14 node ↔ 3V3 | ≈ 10 kΩ; GPIO14 ↔ GND with rocker in KILL: beep |

## 3. First power

USB first, **supply off**: `v_adc_mV` ≈ 0, `leak_mV` ≈ 3300 dry, `kill` follows the rocker. Then bench supply **12.0 V, current limit 0.1 A** (the divider draws 92 µA) to the VBAT node.

## 4. Steps

| # | Action / command | Watch | Expected |
|---|---|---|---|
| 1 | supply 12.00 V (meter on the VBAT node) | `v_adc_mV` ≈ 2769, `v_bat_V` | 12.0 ± 0.3 V (1 % resistors + ESP32 ADC ≈ ± 2.5 %); 12.00 × 30/130 = 2.769 V |
| 2 | `cal 12.00` (type the meter value) | `# OK cal: … factor …` | factor between 0.95 and 1.05 — **write it on the card**; it is not stored |
| 3 | supply 9.9 V (the T2 low-battery proposal) | `v_bat_V` | 9.9 ± 0.1 after cal |
| 4 | supply 12.6 V (full 3S) | `v_adc_mV` | ≈ 2908 — 12.6 × 30/130 = 2.91 V, under the ≈ 3.1 V 11 dB range. **VERIFY** the row still follows the meter |
| 5 | supply 11.0, 10.5, 10.0 V | `v_bat_V` | each ± 0.1 V after cal → table for the card |
| 6 | probe wires dry | `leak_mV` ≈ 3300, `leak` 0 | |
| 7 | probe wires in a cup of tap water | `leak_mV` | sheet 2b says ≈ 1060 mV; `expected: record`; `leak` 1 if below 2000 (`leakth` to move the threshold) |
| 8 | probe wires touched together | `leak_mV` ≈ 1055 (4.7 k / 14.7 k × 3300) | `leak` 1 |
| 9 | rocker RUN → KILL → RUN | `kill` 0 → 1 → 0 within one row (100 ms) | |

## 5. Pass
`v_bat_V` within ± 0.1 V of the meter at 9.9 / 10 / 10.5 / 11 / 12 V after one `cal`, the 12.6 V row follows the meter (2.91 V at the ADC; record if it flattens), leak reads dry/wet/short as three distinct levels, kill toggles with the rocker.

## 6. Photos (card folder, `C###_NN.jpg`)
`_01` breadboard with the three resistor groups labelled · `_02` meter on the VBAT node + the CSV row (same instant) · `_03` probe in the cup + the row · `_04` supply display at 12.6 V + the row (saturation question).
