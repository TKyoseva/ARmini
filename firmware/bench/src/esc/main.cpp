// AR-Mini bench · esc · both thruster ESCs on LEDC, ESC_L GPIO1 and ESC_R GPIO2 (C024).
//
// Both outputs are at 1500 µs (= stop) from the first line of setup(), before the banner. Nothing
// moves until `arm` has held 1500 µs on both for 3 s and printed `# ARMED`. Then `l` / `r` / `both`
// set a pulse target and `diff <thrust> <turn>` mixes both; every change is ramped at 200 µs/s.
// Soft limit 1350–1650 µs; `limit wide` opens 1000–2000 with a warning. Out of range → `# ERR LIMIT`,
// no move. `0`, dead-man (2 s) and KILL (GPIO14 low) → both 1500 µs at once, no ramp, armed = 0.
//
// KILL here is SOFTWARE only (the sketch writes 1500 µs). The hardware stop for the thrusters is the
// bench supply OUTPUT button, later the 20 A fuse slot / main switch.
//
// C006 is open: whether the ESC signal input idles above 3.3 V is not measured yet. PROTOCOL.md
// step 1 measures it BEFORE GPIO1/2 are connected.
//
// CSV: t_ms,l_us,r_us,kill,armed   (l_us/r_us = the ramped pulses on the pins now)
#include <Arduino.h>

#include "Bench.h"
#include "Cli.h"
#include "Csv.h"
#include "Deadman.h"
#include "EscMath.h"
#include "Ramp.h"

namespace {

const uint32_t kEscHz = 50;              // SOURCE: C002 thruster listing (PWM 50 Hz); breadboard 2b "ESC L/R (LEDC 50 Hz)"
const uint8_t kEscBits = 14;             // SOURCE: T10 (≥ 14-bit): 20 ms / 16384 ≈ 1.22 µs per step
const float kFrameUs = 1000000.0f / kEscHz;
const float kRampUsPerS = 200.0f;        // SOURCE: T10 (ramp 200 µs/s)
const uint32_t kArmHoldMs = 3000;        // SOURCE: T10 (arm holds 1500 µs for 3 s). VERIFY: ESC arming not documented (C002)
const uint8_t kLedcChL = 0;
const uint8_t kLedcChR = 1;

bench::Cli shell(Serial);
bench::Ramp rampL(kRampUsPerS, bench::kEscNeutralUs);
bench::Ramp rampR(kRampUsPerS, bench::kEscNeutralUs);
bench::Deadman deadman(bench::kDeadmanMs);
bench::KillInput killIn;
bench::Heartbeat heartbeat;
bench::Periodic csvTick(bench::kCsvPeriodMs);

float loUs = bench::kEscNarrowLoUs, hiUs = bench::kEscNarrowHiUs;  // soft limit
bool wide = false;
bool armed = false;
bool arming = false;
uint32_t armDoneMs = 0;
int lastL = -1, lastR = -1;  // µs last written to the pins
uint32_t lastLoopMs = 0;

uint32_t dutyFromUs(float us) {
  const uint32_t full = (1UL << kEscBits) - 1;
  float d = us / kFrameUs * static_cast<float>(1UL << kEscBits);
  if (d < 0.0f) d = 0.0f;
  if (d > static_cast<float>(full)) d = static_cast<float>(full);
  return static_cast<uint32_t>(d + 0.5f);
}

void writeUs(int pin, uint8_t ch, int us) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  (void)ch;
  ledcWrite(pin, dutyFromUs(static_cast<float>(us)));  // core 3.x: ledcWrite takes the pin
#else
  (void)pin;
  ledcWrite(ch, dutyFromUs(static_cast<float>(us)));
#endif
}

void attachEsc() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_ESC_L, kEscHz, kEscBits);
  ledcAttach(PIN_ESC_R, kEscHz, kEscBits);
#else
  ledcSetup(kLedcChL, kEscHz, kEscBits);
  ledcSetup(kLedcChR, kEscHz, kEscBits);
  ledcAttachPin(PIN_ESC_L, kLedcChL);
  ledcAttachPin(PIN_ESC_R, kLedcChR);
#endif
  const int n = static_cast<int>(bench::kEscNeutralUs);
  writeUs(PIN_ESC_L, kLedcChL, n);
  writeUs(PIN_ESC_R, kLedcChR, n);
  lastL = lastR = n;
}

void applyOutputs() {
  const int l = static_cast<int>(rampL.value() + 0.5f);
  const int r = static_cast<int>(rampR.value() + 0.5f);
  if (l != lastL) {
    writeUs(PIN_ESC_L, kLedcChL, l);
    lastL = l;
  }
  if (r != lastR) {
    writeUs(PIN_ESC_R, kLedcChR, r);
    lastR = r;
  }
}

// Both to 1500 µs now, no ramp; disarm.
void stopAll(const char* why) {
  rampL.stop(bench::kEscNeutralUs);
  rampR.stop(bench::kEscNeutralUs);
  applyOutputs();
  armed = false;
  arming = false;
  if (why) bench::msg("%s", why);
}

// Common gate for l / r / both / diff. Prints the reason when refused.
bool mayMove() {
  if (killIn.active()) {
    bench::msg("WARN KILL active (GPIO%d low): command refused", PIN_KILL);
    return false;
  }
  if (!armed) {
    bench::msg("WARN not armed — send `arm` first (holds 1500 us for %lu ms)", static_cast<unsigned long>(kArmHoldMs));
    return false;
  }
  return true;
}

void help() {
  bench::msg("esc commands:");
  bench::msg("  arm                hold 1500 us on both for %lu ms, then `# ARMED`; nothing moves before", static_cast<unsigned long>(kArmHoldMs));
  bench::msg("  l <us> | r <us>    target pulse for one ESC (ramped at %.0f us/s)", kRampUsPerS);
  bench::msg("  both <us>          same target on both");
  bench::msg("  diff <thrust> <turn>  -100..100 each: l = 1500 + k(thrust+turn), r = 1500 + k(thrust-turn), 100 = limit");
  bench::msg("  limit | limit wide | limit narrow   print / open %.0f–%.0f (WARN) / back to %.0f–%.0f", bench::kEscWideLoUs,
             bench::kEscWideHiUs, bench::kEscNarrowLoUs, bench::kEscNarrowHiUs);
  bench::msg("  dm <ms>            dead-man timeout, default %lu ms (0 = off)", static_cast<unsigned long>(bench::kDeadmanMs));
  bench::msg("  0                  both 1500 us now, disarm");
  bench::msg("state: l=%d r=%d (target %.0f/%.0f) limit=%.0f–%.0f%s armed=%d arming=%d dm=%lu kill=%d", lastL, lastR,
             rampL.target(), rampR.target(), loUs, hiUs, wide ? " (WIDE)" : "", armed ? 1 : 0, arming ? 1 : 0,
             static_cast<unsigned long>(deadman.timeout()), killIn.active() ? 1 : 0);
}

void handleCommand(uint32_t now) {
  deadman.feed(now);
  if (shell.is("?")) {
    help();
  } else if (shell.is("0")) {
    stopAll("OK stop (both 1500 us, disarmed)");
  } else if (shell.is("arm")) {
    if (killIn.active()) {
      bench::msg("WARN KILL active (GPIO%d low): arm refused", PIN_KILL);
    } else {
      rampL.stop(bench::kEscNeutralUs);
      rampR.stop(bench::kEscNeutralUs);
      applyOutputs();
      armed = false;
      arming = true;
      armDoneMs = now + kArmHoldMs;
      bench::msg("OK arming: 1500 us on both for %lu ms — listen for the ESC beeps", static_cast<unsigned long>(kArmHoldMs));
    }
  } else if (shell.is("l") || shell.is("r") || shell.is("both")) {
    bool ok = false;
    const float us = shell.argf(1, 0.0f, &ok);
    if (!ok) {
      bench::err(shell.arg(0));
    } else if (!bench::escInLimit(us, loUs, hiUs)) {
      bench::err("LIMIT");
    } else if (mayMove()) {
      if (!shell.is("r")) rampL.setTarget(us);
      if (!shell.is("l")) rampR.setTarget(us);
      bench::msg("OK %s -> %.0f us (ramping at %.0f us/s)", shell.arg(0), us, kRampUsPerS);
    }
  } else if (shell.is("diff")) {
    bool okT = false, okR = false;
    const float thrust = shell.argf(1, 0.0f, &okT);
    const float turn = shell.argf(2, 0.0f, &okR);
    if (!okT || !okR || thrust < -bench::kEscMixMax || thrust > bench::kEscMixMax || turn < -bench::kEscMixMax ||
        turn > bench::kEscMixMax) {
      bench::err("diff (want: diff <-100..100> <-100..100>)");
    } else if (mayMove()) {
      const bench::EscPulses p = bench::escDiff(thrust, turn, loUs, hiUs);
      rampL.setTarget(p.l_us);
      rampR.setTarget(p.r_us);
      bench::msg("OK diff %.0f %.0f -> l %.0f r %.0f us", thrust, turn, p.l_us, p.r_us);
    }
  } else if (shell.is("limit")) {
    if (shell.argc() == 1) {
      bench::msg("OK limit %.0f–%.0f us%s", loUs, hiUs, wide ? " (WIDE)" : "");
    } else if (strcmp(shell.arg(1), "wide") == 0) {
      wide = true;
      loUs = bench::kEscWideLoUs;
      hiUs = bench::kEscWideHiUs;
      bench::msg("WARN limit widened to %.0f–%.0f us — full thrust allowed; LiPo + fuse only, <= 5 s", loUs, hiUs);
    } else if (strcmp(shell.arg(1), "narrow") == 0) {
      wide = false;
      loUs = bench::kEscNarrowLoUs;
      hiUs = bench::kEscNarrowHiUs;
      rampL.setTarget(bench::escClamp(rampL.target(), loUs, hiUs));
      rampR.setTarget(bench::escClamp(rampR.target(), loUs, hiUs));
      bench::msg("OK limit %.0f–%.0f us (targets clamped, ramping)", loUs, hiUs);
    } else {
      bench::err("limit (want: limit | limit wide | limit narrow)");
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
  attachEsc();  // first: both ESC pins at 1500 µs before anything else
  killIn.begin();
  heartbeat.begin();
  bench::begin("esc", "t_ms,l_us,r_us,kill,armed");
  bench::msg("pins: ESC_L GPIO%d · ESC_R GPIO%d (LEDC %lu Hz, %u bit) · KILL GPIO%d (software stop; supply OUTPUT = hardware)",
             PIN_ESC_L, PIN_ESC_R, static_cast<unsigned long>(kEscHz), kEscBits, PIN_KILL);
  bench::msg("both 1500 us, NOT armed. limit %.0f–%.0f us, ramp %.0f us/s, dead-man %lu ms. C006: measure the signal wire first. Type `?`.",
             loUs, hiUs, kRampUsPerS, static_cast<unsigned long>(deadman.timeout()));
  lastLoopMs = millis();
}

void loop() {
  const uint32_t now = millis();
  const uint32_t dt = now - lastLoopMs;
  lastLoopMs = now;

  if (shell.poll()) handleCommand(now);

  if (killIn.risingKill()) stopAll("KILL (GPIO14 low) — both 1500 us, disarmed");

  if (arming) {
    deadman.feed(now);  // holding neutral is the safe state; the dead-man must not cut the arming hold
    if (static_cast<int32_t>(now - armDoneMs) >= 0) {
      arming = false;
      armed = true;
      bench::msg("ARMED");
    }
  }
  if (deadman.timeout() > 0 && deadman.update(now)) stopAll("DEADMAN");

  if (dt > 0) {
    rampL.update(dt);
    rampR.update(dt);
    applyOutputs();
  }
  heartbeat.update(now);

  if (csvTick.due(now)) {
    char buf[64];
    bench::CsvRow row(buf, sizeof buf);
    row.add(static_cast<unsigned long>(now)).add(lastL).add(lastR).add(killIn.active()).add(armed);
    Serial.println(row.c_str());
  }
  delay(1);
}
