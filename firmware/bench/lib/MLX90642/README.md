# MLX90642 driver (Melexis) + Arduino glue

- `inc/MLX90642.h`, `inc/MLX90642_depends.h`, `src/MLX90642.c`, `LICENSE` — **unchanged** copies from
  https://github.com/melexis/mlx90642-library, commit `140705e16bafa4118e772a6b777c2d1cc5de53de` (2025-04-10),
  Apache License 2.0 (© Melexis N.V.).
- `src/MLX90642_arduino.cpp` — AR-Mini's implementation of the five functions Melexis leaves to the MCU
  (`MLX90642_depends.h`): block read, configuration write, command, wake-up, wait — on an Arduino `TwoWire`.
  Byte formats from the MLX90642 datasheet §3.1.4.1 (block read: address MSB/LSB + repeated START; configuration:
  opcode `0x3A 0x2E` + address + value; commands: opcode `0x01 0x80` + command; wake-up: single byte `0x57`).
- `inc/MLX90642_arduino.h` — `mlx90642_arduino_begin(TwoWire&)` to pick the bus, and C++ linkage for the C headers.

The Melexis headers have no `extern "C"` guards: include them through `MLX90642_arduino.h`, not directly.

Used by `firmware/bench/src/thermal` (card C048). Not run on hardware yet — see `src/thermal/PROTOCOL.md`.
