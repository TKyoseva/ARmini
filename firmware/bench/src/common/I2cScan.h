// I2C bus scan shared by the pca9685 / bno055 / mlx90640 sketches (`scan` command).
// Prints one `# I2C found 0x..` line per responding address, or `# I2C nothing found`.
#pragma once
#include <Arduino.h>
#include <Wire.h>

#include "Bench.h"

namespace bench {

inline int i2cScan(TwoWire& bus, const char* name) {
  int found = 0;
  for (uint8_t addr = 0x08; addr < 0x78; ++addr) {
    bus.beginTransmission(addr);
    if (bus.endTransmission() == 0) {
      msg("I2C %s found 0x%02X", name, addr);
      ++found;
    }
  }
  if (found == 0) msg("I2C %s nothing found (check SDA/SCL, 3V3, pull-ups)", name);
  return found;
}

}  // namespace bench
