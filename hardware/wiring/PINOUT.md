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
