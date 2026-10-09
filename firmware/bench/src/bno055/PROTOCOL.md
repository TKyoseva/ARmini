# Bench protocol · bno055 · BNO055 9-DOF IMU breakout on I2C-0

Env `bno055` · CSV `t_ms,heading_deg,roll_deg,pitch_deg,cal_sys,cal_gyro,cal_acc,cal_mag` at 10 Hz · pins from `include/pins_devkit.h`.

## 1. Wiring

| From (DevKit-Lipo) | To (BNO055 breakout) | Wire | Note |
|---|---|---|---|
| GPIO48 `PIN_I2C0_SDA` | SDA | green | I2C-0 (shared later with the PCA9685 and the D45) |
| GPIO47 `PIN_I2C0_SCL` | SCL | teal | |
| 3V3 (EXT1 pin 1) | VIN / 3V3 | red | **VERIFY** which pin the GoTo breakout wants (some have a 5 V regulator on VIN, 3V3 pin bypasses it) |
| GND (EXT1 pin 22) | GND | black | |
| — | ADR | — | leave open/low → address 0x28 (bom.csv row 78); high = 0x29 |
| — | PS0 / PS1 | — | both low = I2C mode (board default — do not touch) |

## 2. Before power

| Check | Probes | Expected |
|---|---|---|
| no short | 3V3 ↔ GND | no beep |
| I2C not shorted | SDA ↔ SCL, each ↔ GND | no beep |
| regulator question | board markings / seller page | note "VIN 5 V?" / "3V3 only?" on the card before plugging in |

## 3. First power

USB only. Banner `# OK BNO055 found, NDOF mode, ext crystal 0` and `# OK status sys=5 selftest=0x0F …` (0x0F = accelerometer, magnetometer, gyro and MCU all passed). If `WARN … not found` → `scan` (expect `0x28`).

## 4. Steps

| # | Command / action | Watch | Expected |
|---|---|---|---|
| 1 | board flat on the table, still | `roll_deg`, `pitch_deg` | both within **± 2°** of 0 after 5 s (`expected: record`) |
| 2 | tilt the board about its long axis by ≈ 30° (phone level or a protractor) | one of `roll_deg` / `pitch_deg` changes by ≈ 30 | **VERIFY** which column is "roll" for our mounting — write it on the card; Adafruit maps y = roll, z = pitch |
| 3 | tilt about the short axis | the other column moves | |
| 4 | rotate flat through 90° (table edge as reference) | `heading_deg` changes by 90 ± 5 | needs `cal_mag` ≥ 2; magnets, the bench supply and the motor nearby spoil it |
| 5 | figure-8s in the air for 30 s, then rest on all 6 faces for 3 s each | `cal_*` climb to 3 3 3 3 | `expected: record` how long it took |
| 6 | `cal` | `# OK offsets acc … gyro … mag … radius …` | copy the line into the card (it is **not** stored on the board) |
| 7 | `xtal 1` | banner again; wait 10 s; `status` | if `sys` stays 5 and the Euler values still update, the board has a crystal — note it; if the values freeze → `xtal 0` (no crystal) |
| 8 | `status` | chip temperature | room ± 5 °C |

## 5. Pass
Sensor found with self-test 0x0F, flat board reads roll/pitch within ± 2°, a 30° tilt shows ≈ 30° in one column (which one is recorded), heading turns 90 ± 5° once `cal_mag` ≥ 2, `cal` printed full offsets.

## 6. Photos (card folder, `C###_NN.jpg`)
`_01` breakout wiring (ADR/PS pins visible) · `_02` board flat with the CSV row (roll/pitch ≈ 0) · `_03` board tilted against a protractor + the CSV row · `_04` screen with the `# OK offsets` line.
