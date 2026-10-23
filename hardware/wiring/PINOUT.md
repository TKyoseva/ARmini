# XIAO ESP32S3 — pins (AR-Mini)

| XIAO | GPIO | Net | To |
|---|---|---|---|
| D0/A0 | 1 | VBAT_S | divider 100k/33k |
| D1/A1 | 2 | LADDER | leak + kill (ladder) |
| D2 | 3 | SCL1 | MLX90640-110° |
| D3 | 4 | SDA1 | MLX90640-110° |
| D4 | 5 | SDA0 | D45, BNO055, PCA9685 |
| D5 | 6 | SCL0 | D45, BNO055, PCA9685 |
| D6 | 43 | SRV_TX | servo driver RX |
| D7 | 44 | SRV_RX | servo driver TX |
| USB-C | — | — | Raspberry Pi 5 (serial) |

I2C-1: `Wire1.begin(/*SDA*/ 4, /*SCL*/ 3)` — SDA and SCL are swapped against the usual order so the tracks do not cross on rev 0 and on the carrier board.

# Olimex ESP32-S3-DevKit-Lipo — pins (bench, breadboard 2b)

Source: `hardware/breadboard/AR-Mini_breadboard_2b_devkit-lipo.png` (table "AR-Mini pins on the DevKit-Lipo") and the
Olimex manual p7 (`Olimex_DevKit-Lipo_pinout_manual-p7.png`). The firmware copy is `firmware/bench/include/pins_devkit.h`;
change it there and here together. EXT1/EXT2 are pin-compatible with the Espressif ESP32-S3-DevKitC-1.

| GPIO | Header | Net / `pins_devkit.h` | To | Status |
|---|---|---|---|---|
| 48 | EXT2 16 | SDA0 `PIN_I2C0_SDA` (Wire) | MLX90642-D45, BNO055, PCA9685 — same pins as pUEXT | SOURCE 2b |
| 47 | EXT2 17 | SCL0 `PIN_I2C0_SCL` (Wire) | " | SOURCE 2b |
| 8 | EXT1 12 | SDA1 `PIN_I2C1_SDA` (Wire1) | MLX90640 110° (not swapped here, unlike the XIAO) | SOURCE 2b |
| 9 | EXT1 15 | SCL1 `PIN_I2C1_SCL` (Wire1) | " | SOURCE 2b |
| 17 | EXT1 10 | SRV_TX `PIN_SRV_TX` (U1TXD) | bus servo driver RX | SOURCE 2b |
| 18 | EXT1 11 | SRV_RX `PIN_SRV_RX` (U1RXD) | bus servo driver TX | SOURCE 2b |
| 15 | EXT1 8 | PI_TX `PIN_PI_TX` (UART2, v2) | Raspberry Pi 5 — not used on the bench | SOURCE 2b |
| 16 | EXT1 9 | PI_RX `PIN_PI_RX` (UART2, v2) | " | SOURCE 2b |
| 1 | EXT2 4 | ESC_L `PIN_ESC_L` (LEDC 50 Hz) | left thruster ESC — bench env `esc` (C024) via S8050 NPN, inverted (C006); rev B: JP1/JP2 → B + 74AHCT125 | SOURCE 2b · C006 |
| 2 | EXT2 5 | ESC_R `PIN_ESC_R` (LEDC 50 Hz) | right thruster ESC — bench env `esc` (C024) via S8050 NPN, inverted (C006); rev B: JP1/JP2 → B + 74AHCT125 | SOURCE 2b · C006 |
| 39 | EXT2 9 | BTS_L_RPWM `PIN_BTS_L_RPWM` | left BTS7960 RPWM · **10 k to GND** | pull-down DECIDED (C015) · order **VERIFY** (item 1) |
| 40 | EXT2 8 | BTS_L_LPWM `PIN_BTS_L_LPWM` | left BTS7960 LPWM · **10 k to GND** | pull-down DECIDED (C015) · order **VERIFY** (item 1) |
| 41 | EXT2 7 | BTS_R_RPWM `PIN_BTS_R_RPWM` | right BTS7960 RPWM · **10 k to GND** | pull-down DECIDED (C015) · order **VERIFY** (item 1) |
| 42 | EXT2 6 | BTS_R_LPWM `PIN_BTS_R_LPWM` | right BTS7960 LPWM · **10 k to GND** | pull-down DECIDED (C015) · order **VERIFY** (item 1) |
| 10 | EXT1 16 | `PIN_BTS_IS_R` (ADC1_CH9) | BTS7960 IS_R, optional | **VERIFY** (not on the sheet, proposed) |
| 11 | EXT1 17 | `PIN_BTS_IS_L` (ADC2_CH0) | BTS7960 IS_L, optional | **VERIFY** (not on the sheet, proposed) |
| 4 | EXT1 4 | VBAT_S `PIN_VBAT_ADC` | divider 100k/30k from F4 | SOURCE C027 (measured 30 k; sheet 2b and carrier rev A say 33 k) |
| 7 | EXT1 7 | LEAK `PIN_LEAK` | 10k to 3V3, 4.7k to the probe → GND | SOURCE 2b |
| 14 | EXT1 20 | KILL `PIN_KILL` | 10k to 3V3, rocker C → GPIO14, KILL → GND (low = KILL) | SOURCE 2b |
| 5 | EXT1 5 | PWR_SENS (board) | — never for modules | SOURCE manual p7 |
| 6 | EXT1 6 | BAT_SENS (board) | the board's own 1S LiPo — never the 3S pack | SOURCE manual p7 |
| 38 | EXT2 10 | LED1 (board, active low) | heartbeat in the bench sketches | SOURCE manual p7 |
| 0 | EXT2 14 | BUT1 (board) | boot button | SOURCE manual p7 |
| 35–37, 3/45/46, 19/20 | — | PSRAM · strapping · USB D+/D− | do not use | SOURCE 2b |
| EXT1 1 / 2 | — | 3V3 out (≤ 600 mA) | sensors, PCA9685 VCC | SOURCE manual p7 |
| EXT1 21 | — | +5 V in/out | from the MZHOU buck when running; USB only when programming | SOURCE 2b |
| EXT1 22, EXT2 1 / 22 | — | GND | common ground | SOURCE manual p7 |

Header pin numbers are from the manual drawing (EXT1 pin 1 = 3V3 at the antenna end, pin 22 = GND; EXT2 pin 1 = GND) and were **confirmed on the board 11.10 (C030)**: continuity EXT1 1↔2 (3V3), EXT1 22 ↔ EXT2 1 ↔ EXT2 22 (GND), no 3V3–GND short; GPIO38 (LED1) found on EXT2 10 with the meter. Rows 25.40 apart, 22 pins at 2.54 per row.

## PCA9685 channels

These are the 16 PWM outputs on the PCA9685 module. They are not ESP32 GPIO numbers: GPIO10 and GPIO11 in the table above are the optional BTS7960 current-sense pins.

| CH | Function | Source |
|---|---|---|
| 0 | ESC_L | carrier rev A SPEC §5. On the DevKit bench and carrier rev B the ESC signal is GPIO1, not this output. |
| 1 | ESC_R | rev A SPEC §5. Bench and rev B: GPIO2. |
| 2, 3 | BTS_L RPWM, LPWM | rev A SPEC §5. Rev B drives the BTS from GPIO39/40. |
| 4, 5 | BTS_R RPWM, LPWM | rev A SPEC §5. Rev B: GPIO41/42. |
| 6 | buzzer | rev A SPEC §5; rev B SPEC (Q3 from CH6) |
| 7–9 | LED1–3 (status / armed / fault) | rev A SPEC §5; rev B SPEC |
| 10 | cradle servo A, TD-8120MG | C023; rev B SPEC (U2): the two cradle servos plug into CH10 / CH11 |
| 11 | cradle servo B, TD-8120MG, mirrored (`us_B = 3000 − us_A`) | C023; rev B SPEC |
| 12–15 | not assigned | — |

`pair` in the pca9685 bench sketch uses CH10 and CH11 (C023). Not yet run on hardware.

## VERIFY (DevKit-Lipo)

1. **BTS7960 RPWM/LPWM order** — sheet 2b lists "GPIO39/40 · GPIO41/42" as pairs; the lower number is taken as RPWM.
   Test: `firmware/bench/src/bts7960/PROTOCOL.md` step 2 — if the track runs backwards, swap the two wires and correct sheet 2b.
2. **BTS7960 IS_R / IS_L** — not on sheet 2b; GPIO10/11 proposed. Measure the module's IS voltage under load and in fault
   before connecting (can exceed 3.3 V). Decide whether to use them at all.
3. ~~Header pin numbers~~ → **MEASURED 11.10 (C030)**, see the note under the table.
4. **GPIO39–42 at boot → DECIDED 11.10 (C015): 10 kΩ pull-down to GND on each of GPIO39, 40, 41, 42** on the
   breadboard, the perfboard (C031) and carrier rev B (C032). Measured with the `ladder` sketch (does not touch 39–42), meter
   to GND: in reset (EN low) all four ≈ 0.02 V; after boot GPIO39 = 3.15 V (40–42 ≈ 0.02 V) until the code drives it; in
   download mode GPIO39 = 3.23 V and GPIO40 = 3.24 V. With 10 kΩ to GND, 39 (running and download) and 40 (download) read
   ≈ 0 V, so the HIGH is very weak and the pull-down wins. Without a pull-down the left BTS7960 would see RPWM = 1, LPWM = 0
   (full forward) from reset until `setup()`. Layers: pull-downs + firmware drives 39–42 LOW first in `setup()` + the rocker
   (R_EN/L_EN through its RUN pole) stays the hardware stop. Rule unchanged: rocker in KILL when flashing or pressing reset.
