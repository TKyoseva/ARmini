# C055 - Thrusters on the Arduino Mega 2560 (29.10.2026)

Goal: drive both Cuifati thrusters from a third, independent signal source (Mega, 5 V push-pull)
to confirm FAILS 173 (right thruster faulty) without the ESP32 / S8050 stage in the loop.

## Wiring
| From | To |
|---|---|
| Mega pin 9 | thruster yellow (signal) |
| Mega GND | thruster white (signal GND) **and** PSU minus (common ground) |
| PSU + (12.0 V) | thruster red |
| PSU - | thruster black |
| Mega USB | Mac (power + serial) |

Never power the ESC/thruster from the Mega (5V/VIN pins); the Mega only gives the signal.
PSU: 12.0 V, current limit 2.5 A set **before** connecting. Thruster fully in water.

## Run
Sketch: `firmware/mega/thruster-test/src/main.cpp` (PlatformIO, env `mega`). Wiring drawing: `docs/diagrams/C055_diagram_mega-thruster.png`.
`pio run -t upload`, then `pio device monitor` (115200, LF).
`arm` (wait for beeps) -> then each step, hold 5 s, read PSU current:

| µs | C025 ref, left @12 V (23.10) | left on Mega (A) | right on Mega (A) |
|---|---|---|---|
| 1500 | 0 | | |
| 1550 | no spin (dead band) | | |
| 1600 | 0.22 | | |
| 1650 | 0.58 | | |
| 1400 (reverse) | 0.21 | | |
| 0 / s (stop) | - | | |

Same pin 9, same wires: swap only the thruster. This separates thruster from channel.

## Reading the result
- Left matches C025 (±20 %) and right clicks ~1.1 s at ~0.01 A -> right thruster confirmed faulty, driver not the cause. FAILS 173 stands; seller claim.
- Right spins on the Mega -> the fault was in the ESP32 drive (S8050 / LEDC); reopen FAILS 173.
- Left also misbehaves on the Mega -> check common GND, white wire, PSU limit.

Media: `AR-Mini-Media/01_Loops/C055_2026-10-29_mega-thruster-test/` (photos of the setup = C055_01, C055_02).
