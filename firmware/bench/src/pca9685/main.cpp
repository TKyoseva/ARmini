// AR-Mini bench · pca9685 · 16-channel PWM module on I2C-0, one hobby servo on CH0.
//
// `ch <n> <us>` sets a pulse width; `sweep 1` moves CH0 between the sweep limits at the ramp rate.
// Every pulse-width change goes through the Ramp (µs/s), so a servo never jumps. The soft limit is
// a pulse-width window: 1000–2000 µs by default (the standard hobby range; bench_v1 used 20–160°),
// anything outside is refused until `limit <min_us> <max_us>` widens the window explicitly.
// Dead-man (2 s) or KILL (GPIO14 low) → every channel is set to "no pulse" (servo limp, ESC idle).
//
// OE per pcb/carrier-revA/SPEC.md §5 R10: OE is HARDWARE — 2.2 kΩ pull-up to 3V3, the rocker pulls
// OE to GND in RUN. In KILL (or with a broken wire) OE floats high → all outputs off regardless of
// what this sketch does. This sketch does not drive OE; it only reads the rocker's other pole on GPIO14.
//
// CSV: t_ms,ch,us,sweep,kill   (ch/us = last channel written and the pulse now on it; sweep 0/1)
#include <Adafruit_PWMServoDriver.h>
#include <Arduino.h>
#include <Wire.h>

#include "Bench.h"
#include "Cli.h"
#include "Csv.h"
#include "Deadman.h"
#include "I2cScan.h"
#include "Ramp.h"

namespace {

const uint8_t kPcaAddr = 0x40;          // SOURCE: docs/bom/bom.csv row 72 (I2C address 0x40)
const float kServoHz = 50.0f;           // SOURCE: breadboard 2b "ESC L/R (LEDC 50 Hz)" — same 50 Hz frame for servos/ESCs
const uint32_t kOscHz = 25000000;       // library default. VERIFY: real oscillator is often ~27 MHz; `osc <Hz>` after measuring the frame with the logic analyser
const uint32_t kI2cHz = 400000;         // SOURCE: PCA9685 datasheet supports fast-mode 400 kHz; VERIFY on long breadboard wires
const float kDefaultMinUs = 1000.0f;    // SOURCE: standard hobby-servo range (bench_v1 attached 500–2500 and used 20–160° ≈ 720–2280 µs)
const float kDefaultMaxUs = 2000.0f;
const float kAbsMinUs = 500.0f;         // absolute window that `limit` may open, matches bench_v1 attach(500, 2500)
const float kAbsMaxUs = 2500.0f;
const float kRampUsPerS = 500.0f;       // VERIFY: 500 µs/s (full 1000 µs travel in 2 s) chosen for the bench
const uint8_t kSweepCh = 0;             // SOURCE: task T3 (sweeps a hobby servo on ch0)
const uint32_t kSweepHoldMs = 500;      // pause at each end of the sweep

Adafruit_PWMServoDriver pca(kPcaAddr, Wire);
bench::Cli shell(Serial);
bench::Ramp ramp(kRampUsPerS, 0.0f);  // value in µs; 0 = no pulse
bench::Deadman deadman(bench::kDeadmanMs);
bench::KillInput killIn;
bench::Heartbeat heartbeat;
bench::Periodic csvTick(bench::kCsvPeriodMs);

float minUs = kDefaultMinUs, maxUs = kDefaultMaxUs;  // soft-limit window
int curCh = kSweepCh;
int lastUs = 0;
bool sweeping = false;
bool sweepUp = true;
uint32_t sweepHoldUntil = 0;
bool pcaOk = false;
uint32_t lastLoopMs = 0;

void writeUs(int ch, int us) {
  if (!pcaOk) return;
  if (us <= 0) pca.setPWM(ch, 0, 0);  // no pulse at all
  else pca.writeMicroseconds(ch, us);
}

void allOff() {
  if (!pcaOk) return;
  for (int ch = 0; ch < 16; ++ch) pca.setPWM(ch, 0, 0);
}

void stopAll(const char* why) {
  sweeping = false;
  ramp.stop(0.0f);
  lastUs = 0;
  allOff();
  if (why) bench::msg("%s", why);
}

bool inWindow(float us) { return us >= minUs - 0.5f && us <= maxUs + 0.5f; }

void help() {
  bench::msg("pca9685 commands:");
  bench::msg("  ch <0..15> <us>      pulse width on a channel (ramped at `rate`; refused outside the limit window)");
  bench::msg("  ch <0..15> 0         no pulse on that channel");
  bench::msg("  sweep 0|1            sweep CH%d between the limit window ends", kSweepCh);
  bench::msg("  limit <min_us> <max_us>  window, default %.0f–%.0f; max %.0f–%.0f (prints a warning when widened)",
             kDefaultMinUs, kDefaultMaxUs, kAbsMinUs, kAbsMaxUs);
  bench::msg("  rate <us_per_s>      ramp rate, default %.0f us/s", kRampUsPerS);
  bench::msg("  freq <Hz>            PWM frame rate, default %.0f Hz", kServoHz);
  bench::msg("  osc <Hz>             oscillator calibration, default %lu Hz (measure the frame, then correct)",
             static_cast<unsigned long>(kOscHz));
  bench::msg("  dm <ms>              dead-man timeout, default %lu ms (0 = off)", static_cast<unsigned long>(bench::kDeadmanMs));
  bench::msg("  scan                 I2C scan on Wire (SDA GPIO%d, SCL GPIO%d)", PIN_I2C0_SDA, PIN_I2C0_SCL);
  bench::msg("  0                    all channels off now");
  bench::msg("state: pca=%s ch=%d us=%d window=%.0f–%.0f rate=%.0f sweep=%d kill=%d", pcaOk ? "ok" : "MISSING", curCh,
             lastUs, minUs, maxUs, ramp.rate(), sweeping ? 1 : 0, killIn.active() ? 1 : 0);
}

void handleCommand(uint32_t now) {
  deadman.feed(now);
  if (shell.is("?")) {
    help();
  } else if (shell.is("0")) {
    stopAll("OK all off");
  } else if (shell.is("scan")) {
    bench::i2cScan(Wire, "Wire");
  } else if (shell.is("ch")) {
    bool okCh = false, okUs = false;
    const long ch = shell.argl(1, -1, &okCh);
    const float us = shell.argf(2, -1.0f, &okUs);
    if (!okCh || ch < 0 || ch > 15 || !okUs || us < 0.0f) {
      bench::err("ch (want: ch <0..15> <us>)");
    } else if (killIn.active()) {
      bench::msg("WARN KILL active (GPIO%d low): command refused", PIN_KILL);
    } else if (us == 0.0f) {
      if (ch == curCh) {
        sweeping = false;
        ramp.stop(0.0f);
        lastUs = 0;
      }
      writeUs(static_cast<int>(ch), 0);
      bench::msg("OK ch %ld off", ch);
    } else if (!inWindow(us)) {
      bench::msg("WARN %.0f us outside the soft window %.0f–%.0f — send `limit <min> <max>` first", us, minUs, maxUs);
    } else {
      sweeping = false;
      if (ch != curCh) {
        writeUs(curCh, 0);  // one ramped channel at a time; the previous one goes limp
        curCh = static_cast<int>(ch);
        ramp.stop(0.0f);
      }
      if (ramp.value() <= 0.0f) ramp.stop(us);  // first pulse on this channel: no ramp from "no pulse"
      ramp.setTarget(us);
      bench::msg("OK ch %d -> %.0f us", curCh, us);
    }
  } else if (shell.is("sweep")) {
    const bool on = shell.argl(1, 0) != 0;
    if (on && killIn.active()) {
      bench::msg("WARN KILL active: refused");
    } else if (on) {
      if (curCh != kSweepCh) {
        writeUs(curCh, 0);
        curCh = kSweepCh;
        ramp.stop(0.0f);
      }
      if (ramp.value() <= 0.0f) ramp.stop(minUs);
      sweeping = true;
      sweepUp = true;
      ramp.setTarget(maxUs);
      bench::msg("OK sweep CH%d %.0f<->%.0f us at %.0f us/s", kSweepCh, minUs, maxUs, ramp.rate());
    } else {
      sweeping = false;
      ramp.setTarget(ramp.value());
      bench::msg("OK sweep off (holding %.0f us)", ramp.value());
    }
  } else if (shell.is("limit")) {
    bool okA = false, okB = false;
    const float a = shell.argf(1, 0.0f, &okA);
    const float b = shell.argf(2, 0.0f, &okB);
    if (!okA || !okB || a < kAbsMinUs || b > kAbsMaxUs || a >= b) {
      bench::err("limit (want: limit <min_us> <max_us>, within 500..2500)");
    } else {
      const bool wider = a < kDefaultMinUs || b > kDefaultMaxUs;
      minUs = a;
      maxUs = b;
      if (wider) bench::msg("WARN window widened to %.0f–%.0f us — watch the servo stops", minUs, maxUs);
      else bench::msg("OK limit %.0f–%.0f us", minUs, maxUs);
    }
  } else if (shell.is("rate")) {
    bool ok = false;
    const float v = shell.argf(1, 0.0f, &ok);
    if (!ok || v <= 0.0f || v > 5000.0f) bench::err("rate (want 1..5000 us/s)");
    else {
      ramp.setRate(v);
      bench::msg("OK rate %.0f us/s", v);
    }
  } else if (shell.is("freq")) {
    bool ok = false;
    const float v = shell.argf(1, 0.0f, &ok);
    if (!ok || v < 24.0f || v > 1526.0f) bench::err("freq (want 24..1526 Hz)");
    else if (pcaOk) {
      pca.setPWMFreq(v);
      bench::msg("OK freq %.1f Hz", v);
    }
  } else if (shell.is("osc")) {
    bool ok = false;
    const long v = shell.argl(1, 0, &ok);
    if (!ok || v < 23000000 || v > 27000000) bench::err("osc (want 23e6..27e6 Hz)");
    else if (pcaOk) {
      pca.setOscillatorFrequency(static_cast<uint32_t>(v));
      pca.setPWMFreq(kServoHz);
      bench::msg("OK osc %ld Hz", v);
    }
  } else if (shell.is("dm")) {
    bool ok = false;
    const long v = shell.argl(1, 0, &ok);
    if (!ok || v < 0) bench::err("dm (want ms >= 0)");
    else {
      deadman.setTimeout(static_cast<uint32_t>(v));
      bench::msg("OK dead-man %ld ms%s", v, v == 0 ? " (OFF — bench only)" : "");
    }
  } else {
    bench::err(shell.arg(0));
  }
}

}  // namespace

void setup() {
  killIn.begin();
  heartbeat.begin();
  Wire.begin(PIN_I2C0_SDA, PIN_I2C0_SCL, kI2cHz);
  bench::begin("pca9685", "t_ms,ch,us,sweep,kill");
  bench::msg("pins: SDA GPIO%d SCL GPIO%d · PCA9685 @0x%02X · KILL GPIO%d · OE: 2.2k to 3V3 + rocker to GND (hardware, SPEC §5 R10)",
             PIN_I2C0_SDA, PIN_I2C0_SCL, kPcaAddr, PIN_KILL);
  pcaOk = pca.begin();
  if (pcaOk) {
    pca.setOscillatorFrequency(kOscHz);
    pca.setPWMFreq(kServoHz);
    allOff();
    bench::msg("OK PCA9685 found, %.0f Hz, all channels off", kServoHz);
  } else {
    bench::msg("WARN PCA9685 not found at 0x%02X — check wiring, then `scan`", kPcaAddr);
  }
  bench::msg("soft window %.0f–%.0f us, ramp %.0f us/s, dead-man %lu ms. Type `?`.", minUs, maxUs, ramp.rate(),
             static_cast<unsigned long>(deadman.timeout()));
  lastLoopMs = millis();
}

void loop() {
  const uint32_t now = millis();
  const uint32_t dt = now - lastLoopMs;
  lastLoopMs = now;

  if (shell.poll()) handleCommand(now);

  if (killIn.risingKill()) stopAll("KILL (GPIO14 low) — all channels off");
  if (deadman.timeout() > 0 && deadman.update(now)) stopAll("DEADMAN");

  if (sweeping && ramp.atTarget()) {
    if (sweepHoldUntil == 0) {
      sweepHoldUntil = now + kSweepHoldMs;
    } else if (static_cast<int32_t>(now - sweepHoldUntil) >= 0) {
      sweepHoldUntil = 0;
      sweepUp = !sweepUp;
      ramp.setTarget(sweepUp ? maxUs : minUs);
    }
  }

  if (dt > 0) {
    const float v = ramp.update(dt);
    const int us = static_cast<int>(v + 0.5f);
    if (us != lastUs) {
      lastUs = us;
      writeUs(curCh, us);
    }
  }
  heartbeat.update(now);

  if (csvTick.due(now)) {
    char buf[64];
    bench::CsvRow row(buf, sizeof buf);
    row.add(static_cast<unsigned long>(now)).add(curCh).add(lastUs).add(sweeping).add(killIn.active());
    Serial.println(row.c_str());
  }
  delay(1);
}
