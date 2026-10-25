// AR-Mini bench · thermal · both thermal cameras on the DevKit-Lipo at once (cards C048 + C029).
//
//   d45   MLX90642-D45 (45° x 35°, bom row 76) on Wire  (I2C-0, GPIO48 SDA / GPIO47 SCL), shared with the
//         PCA9685 0x40 and BNO055 0x28. Melexis driver in lib/MLX90642. The address is NOT hard-coded: the bus is
//         scanned at boot, every address is printed, the one that is not 0x40 / 0x28 / 0x70 is taken.
//   w110  MLX90640 110° (bom row 77) on Wire1 (I2C-1, GPIO8 SDA / GPIO9 SCL), 0x33, Adafruit driver — same as
//         src/mlx90640. The board hangs upside down on the arch, so its frame is rotated 180° (FLIP_110).
//
// No actuators: no ramp, no dead-man. 4 Hz each, 400 kHz (`i2c 100` for long wires).
// CSV: t_ms,cam,min_C,max_C,mean_C,hot_x,hot_y   (cam = d45 | w110; hot_x 0..31 from the left, hot_y 0..23 from
//      the top as the camera sees it after the flip: index = y*32 + x)
// Every 2 s one ASCII heat map per camera (`# MAP <cam> …` + 24 `# |…|` lines). `raw 1` streams
// `# RAW <cam> <t_ms> v0 … v767`.
#include <Adafruit_MLX90640.h>
#include <Arduino.h>
#include <Wire.h>

#include "Bench.h"
#include "Cli.h"
#include "Csv.h"
#include "I2cScan.h"
#include "MLX90642_arduino.h"

#ifndef FLIP_110
#define FLIP_110 1  // SOURCE: handoff 25.10 — the 110° board is mounted upside down on the arch
#endif

namespace {

const uint8_t kW110Addr = MLX90640_I2CADDR_DEFAULT;  // 0x33. SOURCE: bom.csv row 77 + breadboard 2b
const uint8_t kKnownOnWire[] = {0x40, 0x28, 0x70};   // PCA9685, BNO055, PCA9685 all-call — anything else is the D45
const uint32_t kI2cFastHz = 400000;  // SOURCE: handoff; datasheet MLX90642 table 25: 400 kHz OK up to 16 Hz
const uint32_t kI2cSlowHz = 100000;  // `i2c 100` for long wires; table 25: 100 kHz OK only at 2 and 4 Hz
const int kW = 32, kH = 24, kN = kW * kH;
const uint32_t kMapPeriodMs = 2000;  // SOURCE: task T3 / handoff (every 2 s one ASCII heat map per camera)
const float kD45Scale = 1.0f / 50.0f;  // SOURCE: datasheet §3.1.5.3 To = RAM / 50 °C (two's complement)

Adafruit_MLX90640 mlx110;
bench::Cli shell(Serial);
bench::Heartbeat heartbeat;
bench::Periodic map110Tick(kMapPeriodMs);
bench::Periodic mapD45Tick(kMapPeriodMs);

float frame110[kN];
float frameD45[kN];
uint16_t rawD45[kN];
bool w110Ok = false;
bool d45Ok = false;
uint8_t d45Addr = 0;
bool rawOn = false;
bool mapOn = true;
long rateHz = 4;        // SOURCE: handoff (4 Hz each)
uint32_t i2cHz = kI2cFastHz;

const char kShades[] = " .:-=+*#%@";  // 10 bands from min to max

struct Stats {
  float mn, mx, mean;
  int hotX, hotY;
};

Stats stats(const float* f) {
  Stats s;
  s.mn = f[0];
  s.mx = f[0];
  float sum = 0.0f;
  int hot = 0;
  for (int i = 0; i < kN; ++i) {
    const float v = f[i];
    sum += v;
    if (v < s.mn) s.mn = v;
    if (v > s.mx) {
      s.mx = v;
      hot = i;
    }
  }
  s.mean = sum / kN;
  s.hotX = hot % kW;
  s.hotY = hot / kW;
  return s;
}

void emitRow(const char* cam, uint32_t t, const Stats& s) {
  char buf[80];
  bench::CsvRow row(buf, sizeof buf);
  row.add(static_cast<unsigned long>(t)).add(cam).add(s.mn, 1).add(s.mx, 1).add(s.mean, 1).add(s.hotX).add(s.hotY);
  Serial.println(row.c_str());
}

void printMap(const char* cam, const float* f, const Stats& s) {
  const float span = (s.mx - s.mn) > 0.01f ? (s.mx - s.mn) : 0.01f;
  bench::msg("MAP %s min %.1f max %.1f C (' ' = min … '@' = max), 32 cols x 24 rows", cam, s.mn, s.mx);
  char line[kW + 1];
  for (int y = 0; y < kH; ++y) {
    for (int x = 0; x < kW; ++x) {
      int b = static_cast<int>((f[y * kW + x] - s.mn) / span * 9.0f + 0.5f);
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

void printRaw(const char* cam, uint32_t t, const float* f) {
  Serial.print("# RAW ");
  Serial.print(cam);
  Serial.print(' ');
  Serial.print(t);
  for (int i = 0; i < kN; ++i) {
    Serial.print(' ');
    Serial.print(f[i], 1);
  }
  Serial.println();
}

void flip180(float* f) {
  for (int i = 0, j = kN - 1; i < j; ++i, --j) {
    const float tmp = f[i];
    f[i] = f[j];
    f[j] = tmp;
  }
}

// ------------------------------------------------------------------ D45
bool isKnownOnWire(uint8_t addr) {
  for (size_t i = 0; i < sizeof kKnownOnWire; ++i)
    if (kKnownOnWire[i] == addr) return true;
  return false;
}

// Scans Wire, prints every address, returns the first that is not a known bus member (0 = none).
uint8_t findD45() {
  uint8_t pick = 0;
  int unknown = 0;
  for (uint8_t addr = 0x08; addr < 0x78; ++addr) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() != 0) continue;
    const bool known = isKnownOnWire(addr);
    bench::msg("I2C Wire found 0x%02X%s", addr, known ? " (PCA9685 / BNO055)" : " <- candidate D45");
    if (!known) {
      if (pick == 0) pick = addr;
      ++unknown;
    }
  }
  if (unknown > 1) bench::msg("WARN %d unknown addresses on Wire, taking the lowest 0x%02X — unplug what is not the D45", unknown, pick);
  return pick;
}

bool d45SetRate(long hz) {
  const uint16_t code = hz == 8 ? MLX90642_REF_RATE_8HZ : MLX90642_REF_RATE_4HZ;
  return MLX90642_SetRefreshRate(d45Addr, code) >= 0;
}

bool d45Begin() {
  mlx90642_arduino_begin(Wire);
  uint16_t id[MLX90642_NUMBER_OF_ID_WORDS] = {0};
  uint8_t fw[3] = {0};
  if (MLX90642_GetID(d45Addr, id) < 0 || MLX90642_GetFWver(d45Addr, fw) < 0) {
    bench::msg("WARN 0x%02X answers but does not read like an MLX90642 (ID / FW read failed)", d45Addr);
    return false;
  }
  bench::msg("OK MLX90642 @0x%02X id %04X%04X%04X%04X fw %u.%u.%u", d45Addr, id[0], id[1], id[2], id[3], fw[0], fw[1], fw[2]);
  int st = MLX90642_SetMeasMode(d45Addr, MLX90642_CONT_MEAS_MODE);
  if (st >= 0) st = MLX90642_SetOutputFormat(d45Addr, MLX90642_TEMPERATURE_OUTPUT);
  if (st >= 0 && !d45SetRate(rateHz)) st = -1;
  if (st < 0) {
    bench::msg("WARN MLX90642 configuration write failed (%d)", st);
    return false;
  }
  int16_t emis = 0;
  MLX90642_GetEmissivity(d45Addr, &emis);
  bench::msg("MLX90642 continuous, temperature output, %ld Hz, emissivity %.2f (EEPROM, not changed here)", rateHz,
             emis / 16384.0f);
  st = MLX90642_Init(d45Addr);  // start/sync and wait for the first frame (blocks ≈ 1 refresh period)
  if (st < 0) {
    bench::msg("WARN MLX90642 init failed (%d) — no first frame", st);
    return false;
  }
  return true;
}

// Reads a D45 frame if one is ready. Returns true when `frameD45` holds new data.
bool d45Poll() {
  const int ready = MLX90642_IsDataReady(d45Addr);
  if (ready != MLX90642_YES) return false;
  if (MLX90642_GetImage(d45Addr, rawD45) < 0) {
    bench::msg("WARN d45 frame read failed");
    return false;
  }
  for (int i = 0; i < kN; ++i) frameD45[i] = static_cast<int16_t>(rawD45[i]) * kD45Scale;
  return true;
}

// ------------------------------------------------------------------ 110°
bool w110SetRate(long hz) {
  if (!w110Ok) return true;
  mlx110.setRefreshRate(hz == 8 ? MLX90640_8_HZ : MLX90640_4_HZ);
  return true;
}

bool w110Begin() {
  if (!mlx110.begin(kW110Addr, &Wire1)) {
    bench::msg("WARN MLX90640 not found at 0x%02X on Wire1 — check SDA GPIO%d / SCL GPIO%d, 3V3, then `scan`", kW110Addr,
               PIN_I2C1_SDA, PIN_I2C1_SCL);
    return false;
  }
  mlx110.setMode(MLX90640_CHESS);
  mlx110.setResolution(MLX90640_ADC_18BIT);
  w110Ok = true;
  w110SetRate(rateHz);
  bench::msg("OK MLX90640 @0x%02X serial %04X%04X%04X, chess, 18 bit, %ld Hz, frame %s", kW110Addr, mlx110.serialNumber[0],
             mlx110.serialNumber[1], mlx110.serialNumber[2], rateHz, FLIP_110 ? "rotated 180° (FLIP_110)" : "as read");
  return true;
}

// ------------------------------------------------------------------ CLI
void setI2c(uint32_t hz) {
  i2cHz = hz;
  Wire.setClock(hz);
  Wire1.setClock(hz);
}

void help() {
  bench::msg("thermal commands:");
  bench::msg("  scan          I2C scan on Wire (SDA GPIO%d, SCL GPIO%d) and Wire1 (SDA GPIO%d, SCL GPIO%d)", PIN_I2C0_SDA,
             PIN_I2C0_SCL, PIN_I2C1_SDA, PIN_I2C1_SCL);
  bench::msg("  rate 4|8      refresh rate of both cameras in Hz (default 4)");
  bench::msg("  raw 0|1       stream all 768 pixels per frame as `# RAW <cam> <t_ms> v0 .. v767`");
  bench::msg("  map 0|1       ASCII heat map every 2 s per camera (default on)");
  bench::msg("  i2c 100|400   bus clock in kHz on both buses (400 default; 100 for long wires, then rate 4 only)");
  bench::msg("  0             raw off, map off");
  bench::msg("state: d45=%s@0x%02X w110=%s rate=%ld Hz i2c=%lu kHz raw=%d map=%d flip110=%d", d45Ok ? "ok" : "MISSING", d45Addr,
             w110Ok ? "ok" : "MISSING", rateHz, static_cast<unsigned long>(i2cHz / 1000), rawOn ? 1 : 0, mapOn ? 1 : 0, FLIP_110);
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
    if (hz != 4 && hz != 8) {
      bench::err("rate (want 4 or 8)");
      return;
    }
    rateHz = hz;
    const bool okD = d45Ok ? d45SetRate(hz) : true;
    w110SetRate(hz);
    bench::msg("%s rate %ld Hz%s", okD ? "OK" : "WARN d45 write failed,", hz,
               (hz == 8 && i2cHz == kI2cSlowHz) ? " — 8 Hz at 100 kHz drops frames (datasheet table 25), use `i2c 400`" : "");
  } else if (shell.is("i2c")) {
    const long k = shell.argl(1, 0);
    if (k != 100 && k != 400) {
      bench::err("i2c (want 100 or 400)");
      return;
    }
    setI2c(k == 100 ? kI2cSlowHz : kI2cFastHz);
    bench::msg("OK i2c %ld kHz on Wire and Wire1%s", k, (k == 100 && rateHz == 8) ? " — rate 8 will drop frames, use `rate 4`" : "");
  } else if (shell.is("scan")) {
    bench::i2cScan(Wire, "Wire");
    bench::i2cScan(Wire1, "Wire1");
  } else {
    bench::err(shell.arg(0));
  }
}

}  // namespace

void setup() {
  heartbeat.begin();
  Wire.begin(PIN_I2C0_SDA, PIN_I2C0_SCL, kI2cFastHz);
  Wire1.begin(PIN_I2C1_SDA, PIN_I2C1_SCL, kI2cFastHz);
  bench::begin("thermal", "t_ms,cam,min_C,max_C,mean_C,hot_x,hot_y");
  bench::msg("d45: Wire SDA GPIO%d SCL GPIO%d (shared with PCA9685 0x40, BNO055 0x28) · w110: Wire1 SDA GPIO%d SCL GPIO%d @0x%02X · 3V3 from EXT1 1/2 only",
             PIN_I2C0_SDA, PIN_I2C0_SCL, PIN_I2C1_SDA, PIN_I2C1_SCL, kW110Addr);

  d45Addr = findD45();
  if (d45Addr == 0) {
    bench::msg("WARN no D45 candidate on Wire (only 0x40 / 0x28 / 0x70 or nothing) — check wiring, then `scan`");
  } else {
    d45Ok = d45Begin();
  }
  w110Begin();

  bench::msg("rows at the frame rate per camera; heat maps every %lu ms. Type `?`.", static_cast<unsigned long>(kMapPeriodMs));
}

void loop() {
  const uint32_t now = millis();
  if (shell.poll()) handleCommand();
  heartbeat.update(now);

  if (!w110Ok && !d45Ok) {
    delay(100);
    return;
  }

  if (w110Ok) {
    // getFrame blocks until both sub-pages are in (≈ 1/rate); the CLI and the D45 are polled between frames.
    if (mlx110.getFrame(frame110) != 0) {
      bench::msg("WARN w110 frame read failed");
      delay(50);
    } else {
      if (FLIP_110) flip180(frame110);
      const uint32_t t = millis();
      const Stats s = stats(frame110);
      emitRow("w110", t, s);
      if (rawOn) printRaw("w110", t, frame110);
      if (mapOn && map110Tick.due(t)) printMap("w110", frame110, s);
    }
  }

  if (d45Ok && d45Poll()) {
    const uint32_t t = millis();
    const Stats s = stats(frameD45);
    emitRow("d45", t, s);
    if (rawOn) printRaw("d45", t, frameD45);
    if (mapOn && mapD45Tick.due(t)) printMap("d45", frameD45, s);
  } else if (!w110Ok) {
    delay(20);  // only the D45: poll its READY flag gently
  }
}
