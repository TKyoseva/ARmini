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
| 1500 | 0 | 0.010 (idle) | — |
| 1550 | no spin (dead band) | not recorded | — |
| 1600 | 0.22 | **0.217** | no spin: ~0.9 s loop, C.C, 1.1–2.1 A pulses, 12 → 8.75 V |
| 1650 | 0.58 | **0.570** | not run (stopped after 1600) |
| 1400 (reverse) | 0.21 | **0.202** | not run |
| 0 / s (stop) | - | 1500 at once | 1500 at once |

Same pin 9, same wires: swap only the thruster. This separates thruster from channel.

## Reading the result
- Left matches C025 (±20 %) and right clicks ~1.1 s at ~0.01 A -> right thruster confirmed faulty, driver not the cause. FAILS 173 stands; seller claim.
- Right spins on the Mega -> the fault was in the ESP32 drive (S8050 / LEDC); reopen FAILS 173.
- Left also misbehaves on the Mega -> check common GND, white wire, PSU limit.

## Result 29.10.2026 (C055, pass)
Left on the Mega repeats C025 within 5 %; right on the same pin and wires fails exactly as on the ESP32 (24.10).
**FAILS 173 confirmed with a third, independent driver: the right thruster's built-in ESC/motor is faulty.**
Do not run the right thruster again: the stalled start pulses reach 2 A.

Media: `AR-Mini-Media/01_Loops/C055_2026-10-29_mega-thruster-test/` — C055_01–03 setup, ★04 left spinning (MOV), 05–10 serial + supply at 1600 / 1400 / 1650 µs, ★11 right failing (MOV).
