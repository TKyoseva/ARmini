// AR-Mini bench · Olimex ESP32-S3-DevKit-Lipo · the ONE place for GPIO numbers.
//
// SOURCE: hardware/breadboard/AR-Mini_breadboard_2b_devkit-lipo.png, table "AR-Mini pins on the DevKit-Lipo"
//         (sheet 2b, T. Kyoseva, 07.10.2026) and hardware/breadboard/Olimex_DevKit-Lipo_pinout_manual-p7.png
//         (Olimex ESP32-S3-DevKit-Lipo user manual rev 2.0, p7, EXT1/EXT2 = DevKitC-1 compatible).
// Every `// VERIFY` below is also listed at the bottom of hardware/wiring/PINOUT.md and in firmware/bench/README.md.
#pragma once

// ---------------------------------------------------------------- I2C-0 (Wire): D45, BNO055, PCA9685 (= pUEXT pins)
#define PIN_I2C0_SDA 48 // SOURCE: breadboard 2b (I²C-0 SDA GPIO48; also pUEXT / manual p7 "GPIO48\I2C_SDA")
#define PIN_I2C0_SCL 47 // SOURCE: breadboard 2b (I²C-0 SCL GPIO47; also pUEXT / manual p7 "GPIO47\I2C_SCL")

// ---------------------------------------------------------------- I2C-1 (Wire1): MLX90640 110°
#define PIN_I2C1_SDA 8 // SOURCE: breadboard 2b (I²C-1 SDA GPIO8, EXT1 row a)
#define PIN_I2C1_SCL 9 // SOURCE: breadboard 2b (I²C-1 SCL GPIO9, EXT1 row a)

// ---------------------------------------------------------------- UART1: Waveshare bus servo adapter
#define PIN_SRV_TX 17 // SOURCE: breadboard 2b (UART1 TX GPIO17 = U1TXD → adapter RX)
#define PIN_SRV_RX 18 // SOURCE: breadboard 2b (UART1 RX GPIO18 = U1RXD ← adapter TX)

// ---------------------------------------------------------------- UART2 (v2): Raspberry Pi 5 — not used on the bench
#define PIN_PI_TX 15 // SOURCE: breadboard 2b (UART2 TX GPIO15)
#define PIN_PI_RX 16 // SOURCE: breadboard 2b (UART2 RX GPIO16)

// ---------------------------------------------------------------- ESC L / R (LEDC 50 Hz) — no bench sketch (thrusters need water)
#define PIN_ESC_L 1 // SOURCE: breadboard 2b (ESC L GPIO1)
#define PIN_ESC_R 2 // SOURCE: breadboard 2b (ESC R GPIO2)

// ---------------------------------------------------------------- BTS7960 L / R
// Sheet 2b gives the pairs "GPIO39/40 · GPIO41/42" but not which one of a pair is RPWM.
// Chosen here: the lower number is RPWM. If the motor runs the wrong way, swap the two wires, not the code.
// GPIO39-42 each have a 10 k pull-down to GND (C015, 11.10): GPIO39 is weakly HIGH after boot and 39/40 in download mode.
// setup() must drive all four LOW before anything else. The rocker (R_EN/L_EN) stays the hardware stop.
#define PIN_BTS_L_RPWM 39 // VERIFY: sheet 2b "BTS7960 L GPIO39/40" — RPWM/LPWM order chosen, not on the sheet
#define PIN_BTS_L_LPWM 40 // VERIFY: see PIN_BTS_L_RPWM
#define PIN_BTS_R_RPWM 41 // VERIFY: sheet 2b "BTS7960 R GPIO41/42" — order chosen, not on the sheet
#define PIN_BTS_R_LPWM 42 // VERIFY: see PIN_BTS_R_RPWM
// BTS7960 current sense (IS_R, IS_L) is NOT on sheet 2b. Two free analog-capable GPIOs on EXT1 are proposed
// (GPIO10 = ADC1_CH9, GPIO11 = ADC2_CH0; both are SPI pins on the manual, unused here; no WiFi so ADC2 is usable).
// Wiring them is optional — see src/bts7960/PROTOCOL.md (the module's IS pin can exceed 3.3 V in fault mode).
#define PIN_BTS_IS_R 10 // VERIFY: not on sheet 2b; proposed free ADC pin, decide + measure before wiring
#define PIN_BTS_IS_L 11 // VERIFY: not on sheet 2b; proposed free ADC pin, decide + measure before wiring

// ---------------------------------------------------------------- ADC
#define PIN_VBAT_ADC 4 // SOURCE: breadboard 2b (ADC VBAT GPIO4 ← divider from F4). C027 bench, measured 100 k / 30 k.
#define PIN_LEAK 7     // SOURCE: breadboard 2b (ADC LEAK GPIO7 ← 10k to 3V3, 4.7k to the probe → GND)

// ---------------------------------------------------------------- KILL (software kill; the 50 A main switch is the hardware one)
#define PIN_KILL 14 // SOURCE: breadboard 2b (KILL GPIO14, 10k pull-up to 3V3, rocker C → GPIO14, KILL → GND; low = KILL)

// ---------------------------------------------------------------- Used by the board itself — never for modules
#define PIN_ONBOARD_PWR_SENS 5 // SOURCE: manual p7 (GPIO5\PWR_SENS)
#define PIN_ONBOARD_BAT_SENS 6 // SOURCE: manual p7 (GPIO6\BAT_SENS) — the board's own 1S LiPo, not the 3S pack
#define PIN_ONBOARD_LED 38     // SOURCE: manual p7 (GPIO38\LED1), active low (sheet 2b)
#define PIN_ONBOARD_BUTTON 0   // SOURCE: manual p7 (GPIO0\BUT1)
// Do not touch: GPIO35–37 (octal PSRAM), GPIO3/45/46 (strapping), GPIO19/20 (USB D+/D−). SOURCE: breadboard 2b

// ---------------------------------------------------------------- Divider / ladder values (for the ladder sketch)
#define VBAT_DIV_R_TOP_OHM 100000.0f // SOURCE: breadboard 2b + pcb/carrier-revA/SPEC.md (R1 100 k, 1 %)
#define VBAT_DIV_R_BOT_OHM 30000.0f  // SOURCE: C027 bench, measured 30 k
#define LEAK_PULLUP_OHM 10000.0f     // SOURCE: breadboard 2b (10 k to 3V3)
#define LEAK_SERIES_OHM 4700.0f      // SOURCE: breadboard 2b (4.7 k to the probe)
