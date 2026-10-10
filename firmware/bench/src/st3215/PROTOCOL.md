# Bench protocol · st3215 · one ST3215 through the Waveshare Serial Bus Servo Driver

Env `st3215` · CSV `t_ms,id,cmd_deg,pos_deg,load_permille,temp_C,volt_V,ok` at 10 Hz · pins from `include/pins_devkit.h`.
Give the servo ID 1 first with the Waveshare Windows tool + FT232 (bom.csv rows 54, 92), or use `scan` to find it.

## 1. Wiring

| From (DevKit-Lipo) | To (bus servo driver) | Wire | Note |
|---|---|---|---|
| GPIO17 `PIN_SRV_TX` (U1TXD) | RX | orange | sheet 2b step 6 |
| GPIO18 `PIN_SRV_RX` (U1RXD) | TX | yellow | |
| GND (EXT1 pin 22) | GND | black | logic ground; **no 5 V/3V3 wire** between the boards |
| 12 V supply + / − | driver screw terminal + / − | red / black 18 AWG | 6–12.6 V input (bom.csv row 75); bench supply, not the LiPo |
| driver 3-pin servo port | ST3215 5264 cable | — | one servo; the other ports stay empty |
| GPIO14 `PIN_KILL` | rocker C (KILL → GND) | purple | optional: halts the ramp in place |

## 2. Before power

| Check | Probes | Expected |
|---|---|---|
| no short on 12 V | driver + ↔ − | no beep |
| TX/RX not shorted | driver RX ↔ TX, RX ↔ GND, TX ↔ GND | no beep |
| common ground | DevKit GND ↔ driver GND | beep |
| servo cable | 5264 pins seated, polarity as printed on the driver | visual |

## 3. First power

DevKit on USB only → banner `# WARN id 1 does not answer` is normal without 12 V. Then bench supply **12.0 V, current limit 1.0 A**; ST3215 idle current `expected: record`; a stall (30 kg·cm rating, bom.csv row 29) draws more than the limit — that is what the limit is for. Hold the horn free: the servo must be able to turn.

## 4. Steps

| # | Command | Watch | Expected |
|---|---|---|---|
| 0 | `dm 10000` | `# OK dead-man 10000 ms` | steps are human-paced: 10 s between commands before `# DEADMAN`; the 2 s default comes back in step 7 |
| 1 | `scan` | `# OK found id 1` | if nothing: swap TX/RX, check 12 V, `baud 115200` is **not** the default |
| 2 | `read` | `pos`, `load`, `temp`, `volt` | `volt_V` = supply ± 0.3 V; `temp_C` room ± 5; `pos` anything 0–360 |
| 3 | `pos 180` | `cmd_deg` 180, `pos_deg` ramps at 60 °/s | after settling `pos_deg` within **± 2°** of `cmd_deg` (task T3) |
| 4 | `pos 100` | ramp down over ≈ 1.3 s | no overshoot > 2° in the log |
| 5 | `pos 20` | `# WARN 20.0 deg outside the soft window 72-288` | refused |
| 6 | `limit 0 360`, `pos 20` | `# WARN window widened …`; moves | **check nothing is attached to the horn** |
| 7 | `dm 2000` | `# OK dead-man 2000 ms` | (the servo is holding at 20°, nothing moves) |
| 8 | `pos 300`, stop typing | ramp 20 → 300 at 60 °/s would take ≈ 4.7 s; after 2 s `# DEADMAN` → ramp halts in place, torque stays | `pos_deg` stops changing (somewhere near 140°), servo holds |
| 9 | hold the horn gently while `pos 180` | `load_permille` rises (sign = direction) | `expected: record` the value at which you feel it; temp rises `expected: record` |
| 10 | `torque 0` | horn turns by hand, `pos_deg` follows | then `torque 1` |

From step 8 on the dead-man is back at 2 s: type the next command within 2 s of the previous one, or expect `# DEADMAN` in between (harmless — it only halts the ramp in place).

## 5. Pass
ID answers, `pos_deg` settles within ± 2° of `cmd_deg` for steps 3–4, out-of-window command refused, dead-man halts the ramp, `volt_V` matches the supply.

## 6. Photos (card folder, `C###_NN.jpg`)
`_01` driver + DevKit wiring (TX/RX visible) · `_02` meter on driver + ↔ − before power · `_03` supply display at step 3 · `_04` screen with `scan` + `read` lines · `_05` horn at 100° and 180° with a protractor (for the ± 2° claim).
