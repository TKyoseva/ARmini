// AR-Mini bench · mlx90640 · Waveshare MLX90640 110° thermal camera on I2C-1 (Wire1), 32×24 at 4 Hz.
//
// No actuators: no ramp, no dead-man. CSV at 4 Hz (one row per frame), every 2 s one ASCII heat map
// as `#` lines, and `raw 1` streams all 768 pixel temperatures as `# RAW <t_ms> v0 … v767` lines.
//
// CSV: t_ms,min_C,max_C,mean_C,hot_x,hot_y   (hot_x 0..31 from the left, hot_y 0..23 from the top,
//      as the Adafruit library orders the frame: index = y*32 + x)
#include <Adafruit_MLX90640.h>
#include <Arduino.h>
#include <Wire.h>

#include "Bench.h"
#include "Cli.h"
#include "Csv.h"
#include "I2cScan.h"

namespace {

const uint8_t kMlxAddr = MLX90640_I2CADDR_DEFAULT;  // 0x33. SOURCE: bom.csv row 77 + breadboard 2b ("0x33 on Wire1")
const uint32_t kI2cHz = 400000;  // VERIFY: Adafruit example runs 1 MHz; 400 kHz chosen for breadboard wires (frame read takes longer)
const int kW = 32, kH = 24, kN = kW * kH;
const uint32_t kMapPeriodMs = 2000;  // SOURCE: task T3 (every 2 s one ASCII heat map)

Adafruit_MLX90640 mlx;
bench::Cli shell(Serial);
bench::Heartbeat heartbeat;
bench::Periodic mapTick(kMapPeriodMs);
float frame[kN];
bool mlxOk = false;
bool rawOn = false;
bool mapOn = true;
mlx90640_refreshrate_t rate = MLX90640_4_HZ;  // SOURCE: task T3 (32×24 at 4 Hz)

const char kShades[] = " .:-=+*#%@";  // 10 bands from min to max

void printMap(float mn, float mx) {
  const float span = (mx - mn) > 0.01f ? (mx - mn) : 0.01f;
  bench::msg("MAP min %.1f max %.1f C (' ' = min … '@' = max), 32 cols x 24 rows", mn, mx);
  char line[kW + 1];
  for (int y = 0; y < kH; ++y) {
    for (int x = 0; x < kW; ++x) {
      int b = static_cast<int>((frame[y * kW + x] - mn) / span * 9.0f + 0.5f);
      if (b < 0) b = 0;
      if (b > 9) b = 9;
      line[x] = kShades[b];
    }
    line[kW] = '\0';
    Serial.print("# |");
    Serial.print(line);
    Serial.println("|");
  }
}

void printRaw(uint32_t t) {
  Serial.print("# RAW ");
  Serial.print(t);
  for (int i = 0; i < kN; ++i) {
    Serial.print(' ');
    Serial.print(frame[i], 1);
  }
  Serial.println();
}

bool setRate(long hz) {
  switch (hz) {
    case 1: rate = MLX90640_1_HZ; break;
    case 2: rate = MLX90640_2_HZ; break;
    case 4: rate = MLX90640_4_HZ; break;
    case 8: rate = MLX90640_8_HZ; break;
    default: return false;
  }
  if (mlxOk) mlx.setRefreshRate(rate);
  return true;
}

void help() {
  bench::msg("mlx90640 commands:");
  bench::msg("  raw 0|1     stream all 768 pixel temperatures per frame as `# RAW <t_ms> v0 .. v767`");
  bench::msg("  map 0|1     ASCII heat map every 2 s (default on)");
  bench::msg("  rate 1|2|4|8  refresh rate in Hz (default 4; above 8 the I2C at 400 kHz cannot keep up)");
  bench::msg("  scan        I2C scan on Wire1 (SDA GPIO%d, SCL GPIO%d)", PIN_I2C1_SDA, PIN_I2C1_SCL);
  bench::msg("  0           raw off, map off");
  bench::msg("state: mlx=%s raw=%d map=%d", mlxOk ? "ok" : "MISSING", rawOn ? 1 : 0, mapOn ? 1 : 0);
}

void handleCommand() {
  if (shell.is("?")) {
    help();
  } else if (shell.is("0")) {
    rawOn = false;
    mapOn = false;
    bench::msg("OK raw off, map off");
  } else if (shell.is("raw")) {
    rawOn = shell.argl(1, 0) != 0;
    bench::msg("OK raw %d", rawOn ? 1 : 0);
  } else if (shell.is("map")) {
    mapOn = shell.argl(1, 0) != 0;
    bench::msg("OK map %d", mapOn ? 1 : 0);
  } else if (shell.is("rate")) {
    const long hz = shell.argl(1, 0);
    if (setRate(hz)) bench::msg("OK rate %ld Hz", hz);
    else bench::err("rate (want 1, 2, 4 or 8)");
  } else if (shell.is("scan")) {
    bench::i2cScan(Wire1, "Wire1");
  } else {
    bench::err(shell.arg(0));
  }
}

}  // namespace

void setup() {
  heartbeat.begin();
  Wire1.begin(PIN_I2C1_SDA, PIN_I2C1_SCL, kI2cHz);
  bench::begin("mlx90640", "t_ms,min_C,max_C,mean_C,hot_x,hot_y");
  bench::msg("pins: Wire1 SDA GPIO%d SCL GPIO%d · MLX90640 @0x%02X · 3V3 from the DevKit", PIN_I2C1_SDA, PIN_I2C1_SCL, kMlxAddr);
  mlxOk = mlx.begin(kMlxAddr, &Wire1);
  if (mlxOk) {
    mlx.setMode(MLX90640_CHESS);
    mlx.setResolution(MLX90640_ADC_18BIT);
    mlx.setRefreshRate(rate);
    bench::msg("OK MLX90640 found, serial %04X%04X%04X, chess mode, 18 bit, 4 Hz", mlx.serialNumber[0], mlx.serialNumber[1],
               mlx.serialNumber[2]);
  } else {
    bench::msg("WARN MLX90640 not found at 0x%02X on Wire1 — check SDA/SCL (they are swapped vs. the usual order on the XIAO, not here), then `scan`",
               kMlxAddr);
  }
  bench::msg("rows at the frame rate; heat map every %lu ms. Type `?`.", static_cast<unsigned long>(kMapPeriodMs));
}

void loop() {
  const uint32_t now = millis();
  if (shell.poll()) handleCommand();
  heartbeat.update(now);

  if (!mlxOk) {
    delay(100);
    return;
  }

  // getFrame blocks until both sub-pages are in (≈ 1/rate); the CLI is polled between frames.
  if (mlx.getFrame(frame) != 0) {
    bench::msg("WARN frame read failed");
    delay(50);
    return;
  }
  const uint32_t t = millis();
  float mn = frame[0], mx = frame[0], sum = 0.0f;
  int hot = 0;
  for (int i = 0; i < kN; ++i) {
    const float v = frame[i];
    sum += v;
    if (v < mn) mn = v;
    if (v > mx) {
      mx = v;
      hot = i;
    }
  }
  char buf[80];
  bench::CsvRow row(buf, sizeof buf);
  row.add(static_cast<unsigned long>(t)).add(mn, 1).add(mx, 1).add(sum / kN, 1).add(hot % kW).add(hot / kW);
  Serial.println(row.c_str());

  if (rawOn) printRaw(t);
  if (mapOn && mapTick.due(t)) printMap(mn, mx);
}
