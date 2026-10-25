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
// Every line setup() prints (scan, OK/WARN per camera) is kept in a 2 KB buffer; `boot` prints it again — the
// USB-CDC monitor usually reconnects after RST too late to show the banner.
// The D45 never blocks the sketch: start/sync and the READY flag get 500 ms, then `WARN d45 timeout` and the
// 110° carries on alone (the D45 is re-synced and picked up again when it answers).
// Both boards sometimes miss the first probe after power-up (25.10): the 110° probe + init is tried 5 × 300 ms
// apart, the D45 READY read 5 × 200 ms apart; `init` re-runs the init of whatever is still missing, no reset.
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
const uint32_t kD45TimeoutMs = 500;    // SOURCE: handoff 25.10 — 2 frames at 4 Hz; never wait longer for READY
const uint32_t kD45PollMs = 5;         // READY polling step while waiting for the first frame
const int kInitTries = 5;              // SOURCE: handoff 25.10 — both boards sometimes miss the first probe after power-up
const uint32_t kW110RetryMs = 300;     // SOURCE: handoff 25.10 (110° probe + init, 5 × 300 ms)
const uint32_t kD45ReadyRetryMs = 200; // SOURCE: handoff 25.10 (D45 READY read, 5 × 200 ms)

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
uint32_t d45LastFrameMs = 0;  // millis() of the last D45 frame (or of the last re-sync)
bool d45TimedOut = false;     // true while the D45 is silent (WARN printed once per outage)
bool rawOn = false;
bool mapOn = true;
long rateHz = 4;        // SOURCE: handoff (4 Hz each)
uint32_t i2cHz = kI2cFastHz;

const char kShades[] = " .:-=+*#%@";  // 10 bands from min to max

// ------------------------------------------------------------------ boot log
// blog() = bench::msg() that also keeps the line while setup() runs; `boot` replays the buffer.
const size_t kBootLogSize = 2048;  // ≈ 15–20 lines; a full scan with WARNs fits
char bootLog[kBootLogSize];
size_t bootLogLen = 0;
bool bootCapture = true;
bool bootLogFull = false;

void blog(const char* fmt, ...) __attribute__((format(printf, 1, 2)));
void blog(const char* fmt, ...) {
  char buf[160];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(buf, sizeof buf, fmt, ap);
  va_end(ap);
  bench::msg("%s", buf);
  if (!bootCapture) return;
  const size_t n = strlen(buf);
  if (bootLogLen + n + 1 > kBootLogSize) {
    bootLogFull = true;
    return;
  }
  memcpy(bootLog + bootLogLen, buf, n);
  bootLogLen += n;
  bootLog[bootLogLen++] = '\n';
}

void bootReplay() {
  bench::msg("BOOT replay of setup() (thermal, build %s %s, up %lu s)%s", __DATE__, __TIME__,
             static_cast<unsigned long>(millis() / 1000), bootLogFull ? " — buffer was full, tail dropped" : "");
  size_t i = 0;
  while (i < bootLogLen) {
    size_t j = i;
    while (j < bootLogLen && bootLog[j] != '\n') ++j;
    Serial.print("# ");
    Serial.write(reinterpret_cast<const uint8_t*>(bootLog + i), j - i);
    Serial.println();
    i = j + 1;
  }
  bench::msg("BOOT end");
}

struct Stats {
  float mn, mx, mean;
  int hotX, hotY;
  int bad;  // non-finite pixels skipped (MLX90640 gives NaN/inf for a pixel with a bad calibration read, 25.10)
};

// min / max / mean over the finite pixels only; all NaN → every value NaN, hot = (0,0).
Stats stats(const float* f) {
  Stats s;
  s.mn = NAN;
  s.mx = NAN;
  s.mean = NAN;
  s.bad = 0;
  float sum = 0.0f;
  int n = 0;
  int hot = 0;
  for (int i = 0; i < kN; ++i) {
    const float v = f[i];
    if (!isfinite(v)) {
      ++s.bad;
      continue;
    }
    sum += v;
    if (n == 0 || v < s.mn) s.mn = v;
    if (n == 0 || v > s.mx) {
      s.mx = v;
      hot = i;
    }
    ++n;
  }
  if (n > 0) s.mean = sum / n;
  s.hotX = hot % kW;
  s.hotY = hot / kW;
  return s;
}

// `# WARN <cam> <n> non-finite pixels`, at most once per kBadWarnMs per camera.
const uint32_t kBadWarnMs = 10000;  // SOURCE: handoff 25.10 (once per 10 s)
void warnBad(const char* cam, const Stats& s, uint32_t now, uint32_t& lastWarn) {
  if (s.bad == 0) return;
  if (lastWarn != 0 && now - lastWarn < kBadWarnMs) return;
  lastWarn = now;
  bench::msg("WARN %s %d non-finite pixels (skipped in min/max/mean; `raw 1` shows them as nan)", cam, s.bad);
}
uint32_t lastBadWarn110 = 0;
uint32_t lastBadWarnD45 = 0;

void emitRow(const char* cam, uint32_t t, const Stats& s) {
  char buf[80];
  bench::CsvRow row(buf, sizeof buf);
  row.add(static_cast<unsigned long>(t)).add(cam).add(s.mn, 1).add(s.mx, 1).add(s.mean, 1).add(s.hotX).add(s.hotY);
  Serial.println(row.c_str());
}

void printMap(const char* cam, const float* f, const Stats& s) {
  const float span = (s.mx - s.mn) > 0.01f ? (s.mx - s.mn) : 0.01f;
  bench::msg("MAP %s min %.1f max %.1f C (' ' = min … '@' = max, '?' = non-finite), 32 cols x 24 rows", cam, s.mn, s.mx);
  char line[kW + 1];
  for (int y = 0; y < kH; ++y) {
    for (int x = 0; x < kW; ++x) {
      const float v = f[y * kW + x];
      if (!isfinite(v)) {
        line[x] = '?';
        continue;
      }
      int b = static_cast<int>((v - s.mn) / span * 9.0f + 0.5f);
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
    if (isfinite(f[i])) Serial.print(f[i], 1);
    else Serial.print("nan");
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
    blog("I2C Wire found 0x%02X%s", addr, known ? " (PCA9685 / BNO055)" : " <- candidate D45");
    if (!known) {
      if (pick == 0) pick = addr;
      ++unknown;
    }
  }
  if (unknown > 1) blog("WARN %d unknown addresses on Wire, taking the lowest 0x%02X — unplug what is not the D45", unknown, pick);
  return pick;
}

// Polls READY for up to kD45TimeoutMs. Returns MLX90642_YES, MLX90642_NO (timeout) or <0 (I2C error).
int d45WaitReady() {
  const uint32_t t0 = millis();
  for (;;) {
    const int st = MLX90642_IsDataReady(d45Addr);
    if (st != MLX90642_NO) return st;
    if (millis() - t0 >= kD45TimeoutMs) return MLX90642_NO;
    delay(kD45PollMs);
  }
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
    blog("WARN 0x%02X answers but does not read like an MLX90642 (ID / FW read failed)", d45Addr);
    return false;
  }
  // Only the last 4 hex digits of the ID: no serial numbers in logs, chat or CSV.
  blog("OK MLX90642 @0x%02X id …%04X fw %u.%u.%u", d45Addr, id[MLX90642_NUMBER_OF_ID_WORDS - 1], fw[0], fw[1], fw[2]);
  int st = MLX90642_SetMeasMode(d45Addr, MLX90642_CONT_MEAS_MODE);
  if (st >= 0) st = MLX90642_SetOutputFormat(d45Addr, MLX90642_TEMPERATURE_OUTPUT);
  if (st >= 0 && !d45SetRate(rateHz)) st = -1;
  if (st < 0) {
    blog("WARN MLX90642 configuration write failed (%d)", st);
    return false;
  }
  int16_t emis = 0;
  MLX90642_GetEmissivity(d45Addr, &emis);
  blog("MLX90642 continuous, temperature output, %ld Hz, emissivity %.2f (EEPROM, not changed here)", rateHz, emis / 16384.0f);
  // Start/sync, then wait for the first READY ourselves (MLX90642_Init() sleeps a full refresh period first and
  // its own poll loop has no fixed wall-clock bound).
  if (MLX90642_StartSync(d45Addr) < 0) {
    blog("WARN MLX90642 start/sync command NACKed — no frames; `init` retries");
    return false;
  }
  // The READY read NACKed on every boot on 25.10 (-1) and worked a moment later: retry it a few times.
  int ready = -1;
  int attempt = 1;
  for (; attempt <= kInitTries; ++attempt) {
    ready = d45WaitReady();
    if (ready >= 0) break;
    delay(kD45ReadyRetryMs);
  }
  if (ready < 0) {
    blog("WARN d45 READY read failed (%d) %d times, %lu ms apart — carrying on with the 110°; `init` retries", ready, kInitTries,
         static_cast<unsigned long>(kD45ReadyRetryMs));
    return false;
  }
  if (attempt > 1) blog("OK d45 READY read on attempt %d of %d", attempt, kInitTries);
  if (ready != MLX90642_YES) {
    blog("WARN d45 timeout: no READY within %lu ms after start/sync — carrying on with the 110°; `init` retries",
         static_cast<unsigned long>(kD45TimeoutMs));
    return false;
  }
  d45LastFrameMs = millis();
  d45TimedOut = false;
  return true;
}

// Reads a D45 frame if one is ready (never blocks). Returns true when `frameD45` holds new data. When READY stays
// off for kD45TimeoutMs, prints `WARN d45 timeout` once, re-issues start/sync and keeps polling.
bool d45Poll(uint32_t now) {
  const int ready = MLX90642_IsDataReady(d45Addr);
  if (ready != MLX90642_YES) {
    if (now - d45LastFrameMs >= kD45TimeoutMs) {
      if (!d45TimedOut) {
        bench::msg("WARN d45 timeout: no frame for %lu ms (READY read %s) — carrying on with the 110°, re-syncing the D45",
                   static_cast<unsigned long>(now - d45LastFrameMs), ready < 0 ? "failed" : "0");
        d45TimedOut = true;
      }
      MLX90642_StartSync(d45Addr);  // VERIFY: in continuous mode a new start/sync should restart measurements
      d45LastFrameMs = now;         // next timeout check in kD45TimeoutMs
    }
    return false;
  }
  if (MLX90642_GetImage(d45Addr, rawD45) < 0) {
    bench::msg("WARN d45 frame read failed");
    return false;
  }
  for (int i = 0; i < kN; ++i) frameD45[i] = static_cast<int16_t>(rawD45[i]) * kD45Scale;
  d45LastFrameMs = now;
  if (d45TimedOut) {
    d45TimedOut = false;
    bench::msg("OK d45 frames are back");
  }
  return true;
}

// ------------------------------------------------------------------ 110°
bool w110SetRate(long hz) {
  if (!w110Ok) return true;
  mlx110.setRefreshRate(hz == 8 ? MLX90640_8_HZ : MLX90640_4_HZ);
  return true;
}

// Probe + init (begin() reads the 832-word EEPROM), up to kInitTries times kW110RetryMs apart: on 25.10 the board
// was "not found" at boot and answered `scan` a moment later.
bool w110Begin() {
  int attempt = 1;
  for (; attempt <= kInitTries; ++attempt) {
    if (mlx110.begin(kW110Addr, &Wire1)) break;
    delay(kW110RetryMs);
  }
  if (attempt > kInitTries) {
    blog("WARN MLX90640 not found at 0x%02X on Wire1 after %d tries %lu ms apart — check SDA GPIO%d / SCL GPIO%d, 3V3, then `scan`, then `init`",
         kW110Addr, kInitTries, static_cast<unsigned long>(kW110RetryMs), PIN_I2C1_SDA, PIN_I2C1_SCL);
    return false;
  }
  mlx110.setMode(MLX90640_CHESS);
  mlx110.setResolution(MLX90640_ADC_18BIT);
  w110Ok = true;
  w110SetRate(rateHz);
  // Only the last 4 hex digits of the serial: no serial numbers in logs, chat or CSV.
  blog("OK MLX90640 @0x%02X serial …%04X, chess, 18 bit, %ld Hz, frame %s (attempt %d of %d)", kW110Addr, mlx110.serialNumber[2],
       rateHz, FLIP_110 ? "rotated 180° (FLIP_110)" : "as read", attempt, kInitTries);
  return true;
}

// `init`: re-run the init of every camera that is not running (never found, failed, or D45 timed out), no reset.
void initMissing() {
  bool did = false;
  if (!d45Ok || d45TimedOut) {
    did = true;
    if (d45Addr == 0) d45Addr = findD45();
    if (d45Addr == 0) {
      bench::msg("WARN init: still no D45 candidate on Wire");
    } else {
      d45Ok = d45Begin();
    }
  }
  if (!w110Ok) {
    did = true;
    w110Begin();
  }
  if (!did) {
    bench::msg("OK init: both cameras already running");
    return;
  }
  bench::msg("%s init: d45=%s w110=%s", (d45Ok && w110Ok) ? "OK" : "WARN", d45Ok ? "ok" : "MISSING", w110Ok ? "ok" : "MISSING");
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
  bench::msg("  boot          print the boot messages again (scan, OK/WARN per camera)");
  bench::msg("  init          re-run the init of any camera that is not running (no reset)");
  bench::msg("  0             raw off, map off");
  bench::msg("state: d45=%s@0x%02X%s w110=%s rate=%ld Hz i2c=%lu kHz raw=%d map=%d flip110=%d", d45Ok ? "ok" : "MISSING", d45Addr,
             (d45Ok && d45TimedOut) ? " (timeout, no frames)" : "", w110Ok ? "ok" : "MISSING", rateHz,
             static_cast<unsigned long>(i2cHz / 1000), rawOn ? 1 : 0, mapOn ? 1 : 0, FLIP_110);
}

void handleCommand() {
  if (shell.is("?")) {
    help();
  } else if (shell.is("boot")) {
    bootReplay();
  } else if (shell.is("init")) {
    initMissing();
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
  blog("d45: Wire SDA GPIO%d SCL GPIO%d (shared with PCA9685 0x40, BNO055 0x28) · w110: Wire1 SDA GPIO%d SCL GPIO%d @0x%02X · 3V3 from EXT1 1/2 only",
       PIN_I2C0_SDA, PIN_I2C0_SCL, PIN_I2C1_SDA, PIN_I2C1_SCL, kW110Addr);

  d45Addr = findD45();
  if (d45Addr == 0) {
    blog("WARN no D45 candidate on Wire (only 0x40 / 0x28 / 0x70 or nothing) — check wiring, then `scan`, then `init`");
  } else {
    d45Ok = d45Begin();
  }
  w110Begin();

  blog("rows at the frame rate per camera; heat maps every %lu ms. Type `?` (`boot` repeats these lines).",
       static_cast<unsigned long>(kMapPeriodMs));
  bootCapture = false;
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
      warnBad("w110", s, t, lastBadWarn110);
      emitRow("w110", t, s);
      if (rawOn) printRaw("w110", t, frame110);
      if (mapOn && map110Tick.due(t)) printMap("w110", frame110, s);
    }
  }

  if (d45Ok && d45Poll(millis())) {
    const uint32_t t = millis();
    const Stats s = stats(frameD45);
    warnBad("d45", s, t, lastBadWarnD45);
    emitRow("d45", t, s);
    if (rawOn) printRaw("d45", t, frameD45);
    if (mapOn && mapD45Tick.due(t)) printMap("d45", frameD45, s);
  } else if (!w110Ok) {
    delay(20);  // only the D45: poll its READY flag gently
  }
}
