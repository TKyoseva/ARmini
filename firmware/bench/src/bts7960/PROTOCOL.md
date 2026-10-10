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

**VERIFY (logic level):** the DevKit drives RPWM/LPWM with 3.3 V PWM into the module's 5 V input buffer. If the motor stutters, misses pulses or the module LEDs flicker, record it on the card (which `cmd`, which direction, supply voltage) — the module's input threshold is not in the repo, so the measurement decides whether a level shifter is needed.

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

**Rocker in KILL whenever you flash or press reset; switch to RUN only after the banner.** GPIO39 (L RPWM) may be pulled up during ESP32-S3 boot, so RPWM can be high until `setup()` runs — with R_EN/L_EN high that would be full forward for a fraction of a second. The rocker (R_EN/L_EN through the RUN pole) is what makes this safe; do not bypass it.

| Measurement | Probes | Expected |
|---|---|---|
| GPIO39 level during boot | meter (DC V) on GPIO39 ↔ GND, rocker in KILL, hold RST pressed (board held in reset, then release and watch until the banner) | `expected: record` — in reset and before `setup()`; ~0 V once the banner is out. If it reads ≈ 3.3 V: the boot pull-up is real → PINOUT.md VERIFY item 4 (10 k pull-downs on GPIO39–42) |

## 4. Steps

| # | Command | Watch (CSV / instrument) | Expected |
|---|---|---|---|
| 0 | `dm 10000` | `# OK dead-man 10000 ms` | steps are human-paced: 10 s between commands before `# DEADMAN`; the 2 s default comes back in step 3 |
| 1 | `?` | help + `state: side=L limit=0.60 …` | — |
| 2 | rocker → RUN, `s 0.2` | `cmd` 0.200; `pwm_r` ramps 0 → 51 in ≈ 0.4 s, `pwm_l` 0 | motor turns slowly; supply current `expected: record` |
| 3 | `dm 2000` (within 10 s of step 2; if `# DEADMAN` already came, send `s 0.2` again first) | `# OK dead-man 2000 ms`; motor still turning | |
| 4 | wait 2 s without typing | `# DEADMAN`, `pwm_r` → 0 | motor stops |
| 4b | `dm 10000` | `# OK dead-man 10000 ms` | back to human pace for steps 5–9 |
| 5 | `s -0.3` | `pwm_l` ramps to 77, `pwm_r` 0 | other direction |
| 6 | `s 0.8` | `# WARN |s|=0.80 above soft limit 0.60 …` | **refused**, no change |
| 7 | `limit 0.8` then `s 0.8` | `# WARN soft limit raised …`; `pwm_r` ramps to 204 over ≈ 1.6 s | current `expected: record` |
| 8 | rocker → KILL while running | motor stops at once (hardware); if GPIO14 wired: `# KILL …`, `kill` 1 | |
| 9 | `0` | `pwm_r`/`pwm_l` 0 | |

The 2 s dead-man is only in force between steps 3 and 4b; step 4b puts it back to 10 s, so steps 5–9 can be typed at human pace. A `# DEADMAN` that still appears in between is harmless — it only zeroes the outputs; send the command again.

Ramp check in the log: no two consecutive rows differ by more than 13 PWM counts (0.5/s × 0.1 s × 255 = 12.75).

## 5. Pass
Motor follows `s` in both directions with the ramp visible in the CSV, `s 0.8` is refused at the default limit, dead-man and rocker both stop it.

## 6. Photos (card folder, `C###_NN.jpg`)
`_01` wiring overview with the rocker · `_02` multimeter B+↔B− before power · `_03` supply display at step 2 (voltage + current) · `_04` screen with the `# DEADMAN` row · `_05` (if IS wired) meter on IS_R at full command.
