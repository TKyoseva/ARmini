# AR-Mini carrier board — rev A spec (for KiCad + Aisler)

Goal: one 2-layer THT board, 100 × 80 mm, with the modules plugged into female headers. **Only signals and 5 V / 3V3** go through the board. 12 V for the thrusters, the servo bus and the BTS7960s comes directly from the fuse block.

## 1. Board
- Size 100 × 80 mm, R3 corners, 4 × Ø3.2 mounting holes 3.5 mm from the edges (grid 93 × 73).
- 2 layers, 1.6 mm FR-4, 35 µm copper, lead-free HASL (or ENIG with "Beautiful Boards").
- Tracks: signal 0.3 mm, 5 V 0.8 mm, GND as a full pour on the bottom layer.
- Silkscreen: the name of every connector + pin 1 marker; "AR-Mini carrier rev A · <date>".
- Test points (bare Ø1.5 pads): TP1 12V_IN, TP2 5V, TP3 3V3, TP4 SDA0, TP5 SCL0, TP6 GND.

## 2. Modules on headers (all female 2.54 mm; measure with the caliper before fixing the footprint)

| Ref | Module | Footprint | Note |
|---|---|---|---|
| U1 | XIAO ESP32S3 Sense | 2 × 1×7 female headers, 15.24 mm between the rows (6 × 2.54) | camera faces up, USB-C towards the board edge |
| U2 | PCA9685 module (Ardboard) | 2 × 1×6 headers at the ends + a 16×3 field (2.54 pins) | **measure**: board length, distance between the 6-pin rows, position of the 16×3 field |
| U3 | BNO055 breakout | 1 × 1×N header (N = 6 or 8 depending on the board) | **measure after 9.10** |
| U4 | Buck 12→5 V 3 A (MZHOU) | 2-pin screw terminal input + 2-pin output (or 4 pads) | if the module comes with wires, terminals instead of a header |
| U5 | Serial Bus Servo Driver (Waveshare) | not on the board — JST-XH 4-pin (J8) | arrives 9.10 |

## 3. XIAO ESP32S3 — pins

| XIAO pin | GPIO | Function | Net |
|---|---|---|---|
| D0 / A0 | GPIO1 | ADC battery (divider 100k/33k, Vmax 12.6 V → 3.13 V) | VBAT_SENSE |
| D1 / A1 | GPIO2 | ADC ladder: LEAK + KILL (see §5) | LADDER |
| D2 | GPIO3 | I2C-1 SCL (Wire1) → thermal camera 110° | SCL1 |
| D3 | GPIO4 | I2C-1 SDA | SDA1 |
| D4 | GPIO5 | I2C-0 SDA (Wire) → D45, BNO055, PCA9685 | SDA0 |
| D5 | GPIO6 | I2C-0 SCL | SCL0 |
| D6 | GPIO43 | UART1 TX → servo driver RX | SRV_TX |
| D7 | GPIO44 | UART1 RX ← servo driver TX | SRV_RX |
| D8–D10 | GPIO7/8/9 | SPI → built-in microSD (not broken out) | — |
| 5V | — | 5 V input from U4 | +5V |
| 3V3 | — | 3.3 V output (up to ~600 mA) → sensors, PCA9685 VCC, pull-ups | +3V3 |
| USB-C | — | to the Pi 5 (serial) — not on the board | — |

> `Wire1.begin(/*SDA*/4, /*SCL*/3)` — SDA and SCL of I2C-1 are swapped against the "natural" order so the tracks do not cross (the same as on the rev 0 breakout).

## 4. Connectors (JST-XH 2.5 mm, vertical; pin 1 = square pad)

| Ref | Name | Pins | To |
|---|---|---|---|
| J1 | 12V_IN | 1: +12V, 2: GND (screw terminal 5.08 mm) | fuse "5 A logic" |
| J2 | ESC_L | 1: GND, 2: NC, 3: CH0 | left ESC (signal + ground; the ESC is powered from the 20 A fuse) |
| J3 | ESC_R | 1: GND, 2: NC, 3: CH1 | right ESC |
| J4 | BTS_L | 1: RPWM=CH2, 2: LPWM=CH3, 3: +5V (R_EN+L_EN+VCC), 4: GND | left BTS7960 |
| J5 | BTS_R | 1: CH4, 2: CH5, 3: +5V, 4: GND | right BTS7960 |
| J6 | THERM_FWD | 1: +3V3, 2: GND, 3: SDA0, 4: SCL0 | MLX90642-D45 |
| J7 | THERM_POD | 1: +3V3, 2: GND, 3: SDA1, 4: SCL1 | MLX90640-110° |
| J8 | SERVO_BUS | 1: SRV_TX, 2: SRV_RX, 3: GND, 4: NC | Waveshare driver (its 12 V comes separately from the 15 A fuse) |
| J9 | LEAK | 1: LADDER_LEAK, 2: GND | two bare wires |
| J10 | KILL | 1: LADDER_KILL, 2: GND | logic kill (20 A rocker) |
| J11 | IMU_EXT | 1: +3V3, 2: GND, 3: SDA0, 4: SCL0 | spare I2C-0 |
| J12 | BUZZ_LED | not needed — the buzzer and LEDs are on the board | — |

## 5. Discrete parts

| Ref | Part | Value / type | Purpose |
|---|---|---|---|
| Q1 | P-MOSFET | IRF4905 (TO-220) or AO3401 (if SMD) | reverse-polarity protection on J1 |
| D1 | TVS | SMBJ15A | spikes on 12 V |
| C1 | electrolytic | 470 µF / 25 V | 12 V input |
| C2, C3 | ceramic | 100 nF | 5 V and 3V3 at U1 |
| C4 | electrolytic | 100 µF / 10 V | 5 V rail |
| R1, R2 | resistors | 100 kΩ / 33 kΩ, 1 % | VBAT divider (+ C5 100 nF to GND) |
| R3–R6 | resistors | 4.7 kΩ | pull-ups SDA0/SCL0/SDA1/SCL1 to 3V3 |
| R7, R8, R9 | resistors | 10 kΩ / 4.7 kΩ / 1 kΩ | ADC ladder: A1 through R7 to 3V3; LEAK pulls through R8 to GND; KILL pulls through R9 to GND → three different levels |
| R10 | resistor | **2.2 kΩ to 3V3** (changed 07.10, was 10 k to GND) | OE pull-up: in RUN the rocker pulls OE to GND (outputs active); in KILL or with a broken wire OE stays high → all PWM outputs off. 2.2 k because the module has a 10 k pull-down on OE (10 k / 10 k would give 1.65 V — undefined) |
| Q2 | NPN | BC337 + R11 1 kΩ in the base | buzzer |
| BZ1 | buzzer | active 5 V, Ø12 | leak / battery alarm |
| LED1–3 | LED 5 mm | green / yellow / red + 330 Ω | status / arm / fault |
| F1 | polyfuse | 1.1 A | 5 V rail to the logic |
| TP1–6 | test points | Ø1.5 pads | multimeter / logic analyser |

PCA9685 channels: CH0 ESC_L, CH1 ESC_R, CH2/3 BTS_L, CH4/5 BTS_R, CH6 buzzer (through Q2), CH7–9 LED1–3. OE (07.10): R10 2.2 k pull-up to 3V3; the rocker (SPDT): C → GND, RUN → OE, KILL → R9 1 k → A1. So one ON-ON rocker does both: in RUN OE is at GND, in KILL OE stays high (outputs off) and A1 drops to 0.3 V. See breadboard/AR-Mini_breadboard_2.

## 6. Before pressing "Push to AISLER"

1. **DRC** clean in KiCad (clearance 0.2 mm, via 0.6/0.3).
2. **1:1 print** on paper: put the XIAO, PCA9685, BTS connectors and BNO055 on the sheet — every pin in its hole.
3. **Pin 1** of every JST is where it is on the poster; GND always on pin 1 or 2, never in the middle.
4. The XIAO USB-C faces the edge and has 15 mm free for the cable.
5. The mounting holes match the grid in the CAD of the IP65 box (93 × 73).
6. Upload the Gerbers to the **Eurocircuits PCB Visualizer** (free) — if it shows red, fix it before Aisler.
7. Aisler: 2 layers · 1.6 mm · 3 pcs · HASL (or black "Beautiful Boards") · delivery to Bulgaria. Expected price 30–40 €.

## 7. What is NOT on the board (on purpose)
12 V to the ESCs / BTS / servo driver; the BTS7960 modules themselves (on a separate plate next to the motors); the Pi 5 and its 5 A buck; the thruster ESCs (potted, inside the thrusters).
