// Arduino glue for the Melexis MLX90642 driver (AR-Mini). Include this, not MLX90642.h directly.
#pragma once
#include <Wire.h>

extern "C" {
#include "MLX90642.h"
}

// Selects the TwoWire bus every MLX90642_* call goes through. Call once before MLX90642_Init(). The bus must
// already be begun (pins, clock) by the sketch.
void mlx90642_arduino_begin(TwoWire& bus);
