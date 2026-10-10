// Bench — what every bench sketch shares: serial banner, `#` message lines, periodic ticks,
// the software KILL input (GPIO14) and the on-board LED heartbeat.
//
// Output contract (see firmware/bench/README.md):
//   - exactly one CSV header line (the first line that does not start with `#`), then rows;
//   - everything that is not a CSV row starts with `# ` (`# DEADMAN`, `# ERR <cmd>`, `# WARN …`, `# OK …`),
//     so `pandas.read_csv(path, comment='#')` reads a bench log directly.
#pragma once
#include <Arduino.h>

#include "pins_devkit.h"

namespace bench {

static const unsigned long kBaud = 115200;  // SOURCE: task T3 (CLI over Serial 115200)
static const uint32_t kCsvPeriodMs = 100;   // SOURCE: task T3 (rows at 10 Hz)
static const uint32_t kDeadmanMs = 2000;    // SOURCE: task T3 (dead-man 2 s, configurable)
static const float kRampPerS = 0.5f;        // SOURCE: task T3 (ramp 0.5/s)

// Serial.begin, wait ≤ 2 s for the USB-CDC host, print the banner (as `#` lines) and the CSV header.
inline void begin(const char* sketch, const char* csv_header) {
  Serial.begin(kBaud);
  const uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 2000) delay(10);
  Serial.printf("# AR-Mini bench · %s · build %s %s\r\n", sketch, __DATE__, __TIME__);
  Serial.println("# Olimex ESP32-S3-DevKit-Lipo · pins: firmware/bench/include/pins_devkit.h · `?` = help, `0` = stop");
  Serial.println(csv_header);
}

// `# ` + printf-style message. Keep messages on one line.
inline void msg(const char* fmt, ...) __attribute__((format(printf, 1, 2)));
inline void msg(const char* fmt, ...) {
  char buf[160];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(buf, sizeof buf, fmt, ap);
  va_end(ap);
  Serial.print("# ");
  Serial.println(buf);
}

inline void err(const char* cmd) { msg("ERR %s", cmd); }

// Fires every `period_ms`; drift-free (schedules from the previous due time, catches up if late).
class Periodic {
 public:
  explicit Periodic(uint32_t period_ms) : period_(period_ms), next_(0), started_(false) {}
  bool due(uint32_t now) {
    if (!started_) {
      started_ = true;
      next_ = now + period_;
      return true;
    }
    if (static_cast<int32_t>(now - next_) >= 0) {
      next_ += period_;
      if (static_cast<int32_t>(now - next_) >= 0) next_ = now + period_;  // fell far behind: resync
      return true;
    }
    return false;
  }
  void setPeriod(uint32_t ms) { period_ = ms; }
  uint32_t period() const { return period_; }

 private:
  uint32_t period_;
  uint32_t next_;
  bool started_;
};

// Software KILL: GPIO14 with the board's 10 k pull-up to 3V3; the rocker pulls it to GND in KILL.
// SOURCE: breadboard 2b ("KILL GPIO14 (pull-up, rocker → GND)", "GPIO14: 3.3 V in RUN, 0 V in KILL").
// Without the rocker wired, the pull-up keeps it in RUN.
class KillInput {
 public:
  void begin() {
    pinMode(PIN_KILL, INPUT_PULLUP);
    last_ = active();
  }
  bool active() const { return digitalRead(PIN_KILL) == LOW; }
  // True once when KILL becomes active (falling edge).
  bool risingKill() {
    const bool now = active();
    const bool edge = now && !last_;
    last_ = now;
    return edge;
  }

 private:
  bool last_ = false;
};

// On-board green LED (GPIO38, active low) blinking at 1 Hz = "the sketch is alive". SOURCE: manual p7 + sheet 2b.
class Heartbeat {
 public:
  void begin() {
    pinMode(PIN_ONBOARD_LED, OUTPUT);
    digitalWrite(PIN_ONBOARD_LED, HIGH);  // off
  }
  void update(uint32_t now) {
    const bool on = (now % 1000) < 100;  // 100 ms flash every second
    digitalWrite(PIN_ONBOARD_LED, on ? LOW : HIGH);
  }
};

}  // namespace bench
