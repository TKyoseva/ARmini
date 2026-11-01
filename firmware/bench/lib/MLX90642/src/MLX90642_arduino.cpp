// Arduino Wire implementation of MLX90642_depends.h (AR-Mini, card C048).
//
// SOURCE: MLX90642 datasheet §3.1.4.1 (I2C protocol):
//   block read      S [SA W] [addr MSB] [addr LSB] Sr [SA R] data … P        — words MSB first      (fig. 7)
//   configuration   S [SA W] 0x3A 0x2E [addr MSB] [addr LSB] [val MSB] [val LSB] P                 (fig. 12)
//   command         S [SA W] 0x01 0x80 [cmd MSB] [cmd LSB] P   (start/sync 0x0001, sleep 0x0007, reset 0x0006; fig. 5/8/10)
//   wake-up         S [SA W] 0x57 P                                                                 (fig. 11)
// The ESP32 Wire buffer is 128 bytes, so a 768-word frame is read in 64-word chunks (24 transactions).
// VERIFY on hardware: that the READY flag is cleared by the first chunk (it starts at 0x342C) and that
// 24 chunked reads at 400 kHz finish inside one 4 Hz frame (datasheet table 25 says 400 kHz is fine up to 16 Hz).
#include "MLX90642_arduino.h"

#include <Arduino.h>

namespace {
TwoWire* g_bus = &Wire;
const size_t kChunkWords = I2C_BUFFER_LENGTH / 2;  // 64 words = 128 bytes
}  // namespace

void mlx90642_arduino_begin(TwoWire& bus) { g_bus = &bus; }

extern "C" {

int MLX90642_I2CRead(uint8_t slaveAddr, uint16_t startAddress, uint16_t nMemAddressRead, uint16_t* rData) {
  size_t left = nMemAddressRead;
  uint16_t addr = startAddress;
  while (left > 0) {
    const size_t n = left < kChunkWords ? left : kChunkWords;
    g_bus->beginTransmission(slaveAddr);
    g_bus->write(static_cast<uint8_t>(addr >> 8));
    g_bus->write(static_cast<uint8_t>(addr & 0xFF));
    if (g_bus->endTransmission(false) != 0) return -MLX90642_NACK_ERR;
    const size_t got = g_bus->requestFrom(slaveAddr, static_cast<size_t>(n * 2), true);
    if (got != n * 2) return -MLX90642_NACK_ERR;
    for (size_t i = 0; i < n; ++i) {
      const uint8_t hi = static_cast<uint8_t>(g_bus->read());
      const uint8_t lo = static_cast<uint8_t>(g_bus->read());
      *rData++ = static_cast<uint16_t>((hi << 8) | lo);
    }
    left -= n;
    addr = static_cast<uint16_t>(addr + n * 2);  // word addresses step by 2 bytes
  }
  return 0;
}

int MLX90642_Config(uint8_t slaveAddr, uint16_t writeAddress, uint16_t wData) {
  g_bus->beginTransmission(slaveAddr);
  g_bus->write(static_cast<uint8_t>(MLX90642_CONFIG_OPCODE >> 8));    // 0x3A
  g_bus->write(static_cast<uint8_t>(MLX90642_CONFIG_OPCODE & 0xFF));  // 0x2E
  g_bus->write(static_cast<uint8_t>(writeAddress >> 8));
  g_bus->write(static_cast<uint8_t>(writeAddress & 0xFF));
  g_bus->write(static_cast<uint8_t>(wData >> 8));
  g_bus->write(static_cast<uint8_t>(wData & 0xFF));
  return g_bus->endTransmission(true) == 0 ? 0 : -MLX90642_NACK_ERR;
}

int MLX90642_I2CCmd(uint8_t slaveAddr, uint16_t i2c_cmd) {
  g_bus->beginTransmission(slaveAddr);
  g_bus->write(static_cast<uint8_t>(MLX90642_CMD_OPCODE >> 8));    // 0x01
  g_bus->write(static_cast<uint8_t>(MLX90642_CMD_OPCODE & 0xFF));  // 0x80
  g_bus->write(static_cast<uint8_t>(i2c_cmd >> 8));
  g_bus->write(static_cast<uint8_t>(i2c_cmd & 0xFF));
  return g_bus->endTransmission(true) == 0 ? 0 : -MLX90642_NACK_ERR;
}

int MLX90642_WakeUp(uint8_t slaveAddr) {
  g_bus->beginTransmission(slaveAddr);
  g_bus->write(static_cast<uint8_t>(0x57));  // SOURCE: datasheet fig. 11
  return g_bus->endTransmission(true) == 0 ? 0 : -MLX90642_NACK_ERR;
}

void MLX90642_Wait_ms(uint16_t time_ms) { delay(time_ms); }

}  // extern "C"
