# Bench protocol · bts7960 · one BTS7960 + one ROB0154 track motor

Env `bts7960` · CSV `t_ms,cmd,pwm_r,pwm_l,is_r_mV,is_l_mV,kill` at 10 Hz · pins from `include/pins_devkit.h`.
Wire colours follow the legend of breadboard sheet 2b (red = power, black = GND, blue = PWM, purple = kill, yellow = ADC).

## 1. Wiring

| From (DevKit-Lipo) | To (BTS7960 module) | Wire | Note |
|---|---|---|---|
| GPIO39 `PIN_BTS_L_RPWM` | RPWM | blue | **VERIFY** which of 39/40 is RPWM — if the track runs backwards, swap these two wires |
| GPIO40 `PIN_BTS_L_LPWM` | LPWM | blue | |
| GND (EXT1 pin 22) | GND | black | common ground with the 12 V supply |
| — | R_EN + L_EN | red | **not on a GPIO**: both to +5 V through the rocker (RUN position), as on breadboard 1 → KILL stops the motor in hardware |
| — | VCC | red | +5 V (buck output / EXT1 pin 21) |
| 12 V supply + | B+ | red 18 AWG | through the bench supply, not the LiPo |
| 12 V supply − | B− | black 18 AWG | |
| M+ / M− | ROB0154 motor | 18 AWG | one motor only |
| GPIO14 `PIN_KILL` | rocker C | purple | rocker KILL → GND; 10 k pull-up to 3V3 (sheet 2b) — optional on this bench |
| GPIO10 / GPIO11 `PIN_BTS_IS_R/L` | IS_R / IS_L | yellow | **optional, VERIFY first** — see step 2; enable with `is 1` |

## 2. Before power (multimeter, everything off)

| Check | Probes | Expected |
|---|---|---|
| no short on 12 V | B+ ↔ B− | no beep; kΩ or OL |
| no short on 5 V | VCC ↔ GND | no beep |
| PWM lines not shorted to power | RPWM ↔ VCC, LPWM ↔ VCC, RPWM ↔ LPWM | no beep |
| ground is common | DevKit GND ↔ module GND ↔ supply − | beep, < 1 Ω |
| IS pins (only if you want them) | IS_R ↔ GND with 5 V on VCC and the motor running | **must stay < 3.3 V in every case you test**; in fault mode the chip can push ≈ 4.5 V into the module's IS resistor → **do not connect to the ESP32 unless measured safe or divided**. Expected: record |

## 3. First power

Bench supply (Jesverty) 12.0 V, current limit **1.0 A** to start; rocker in KILL (R_EN/L_EN low), DevKit on USB only. Watch: supply current < 50 mA with the motor stopped (`expected: record`), module LEDs, no warm parts.

## 4. Steps

| # | Command | Watch (CSV / instrument) | Expected |
|---|---|---|---|
| 1 | `?` | help + `state: side=L limit=0.60 …` | — |
| 2 | rocker → RUN, `s 0.2` | `cmd` 0.200; `pwm_r` ramps 0 → 51 in ≈ 0.4 s, `pwm_l` 0 | motor turns slowly; supply current `expected: record` |
| 3 | wait 2 s without typing | `# DEADMAN`, `pwm_r` → 0 | motor stops |
| 4 | `s -0.3` | `pwm_l` ramps to 77, `pwm_r` 0 | other direction |
| 5 | `s 0.8` | `# WARN |s|=0.80 above soft limit 0.60 …` | **refused**, no change |
| 6 | `limit 0.8` then `s 0.8` | `# WARN soft limit raised …`; `pwm_r` ramps to 204 over ≈ 1.6 s | current `expected: record` |
| 7 | rocker → KILL while running | motor stops at once (hardware); if GPIO14 wired: `# KILL …`, `kill` 1 | |
| 8 | `0` | `pwm_r`/`pwm_l` 0 | |

Ramp check in the log: no two consecutive rows differ by more than 13 PWM counts (0.5/s × 0.1 s × 255 = 12.75).

## 5. Pass
Motor follows `s` in both directions with the ramp visible in the CSV, `s 0.8` is refused at the default limit, dead-man and rocker both stop it.

## 6. Photos (card folder, `C###_NN.jpg`)
`_01` wiring overview with the rocker · `_02` multimeter B+↔B− before power · `_03` supply display at step 2 (voltage + current) · `_04` screen with the `# DEADMAN` row · `_05` (if IS wired) meter on IS_R at full command.
