// AR-Mini bench · bts7960 · one BTS7960 H-bridge driving one ROB0154 track motor.
//
// Same spirit as firmware/mega/bench/bench_v1.ino (PWM_MAX 150/255 ≈ 60 %, CSV 10 Hz), but the
// command comes from the CLI instead of a potentiometer, it is rate-limited (Ramp), refused above
// the soft limit (SoftLimit) and dropped to zero when no command arrives for 2 s (Deadman) or when
// the rocker pulls KILL (GPIO14) low. R_EN + L_EN of the module stay on the rocker/5 V, not on a
// GPIO: KILL also stops the motor in hardware, exactly like on breadboard 1.
//
// CSV: t_ms,cmd,pwm_r,pwm_l,is_r_mV,is_l_mV,kill
//   cmd    accepted target (−1..1), pwm_r/pwm_l the ramped 8-bit duties actually on the pins,
//   is_*   BTS7960 IS pins in mV (only meaningful if wired, see PROTOCOL.md), kill 0/1.
#include <Arduino.h>

#include "Bench.h"
#include "Cli.h"
#include "Csv.h"
#include "Deadman.h"
#include "Ramp.h"
#include "SoftLimit.h"

namespace {

// PWM: 8-bit so the duties read like bench_v1 (150/255); 1 kHz.
// VERIFY: 1 kHz chosen for the bench (the Mega ran analogWrite at its default ~490 Hz; the BTS7960 accepts up to 25 kHz).
const uint32_t kPwmHz = 1000;
const uint8_t kPwmBits = 8;
const int kPwmMax = 255;
const uint8_t kLedcChR = 0;
const uint8_t kLedcChL = 1;

struct Side {
  const char* name;
  int rpwm;
  int lpwm;
  int is_r;
  int is_l;
};
const Side kLeft = {"L", PIN_BTS_L_RPWM, PIN_BTS_L_LPWM, PIN_BTS_IS_R, PIN_BTS_IS_L};
const Side kRight = {"R", PIN_BTS_R_RPWM, PIN_BTS_R_LPWM, PIN_BTS_IS_R, PIN_BTS_IS_L};
const Side* side = &kLeft;

bench::Cli shell(Serial);
bench::Ramp ramp(bench::kRampPerS, 0.0f);
bench::SoftLimit limit;  // 0.6 by default
bench::Deadman deadman(bench::kDeadmanMs);
bench::KillInput killIn;
bench::Heartbeat heartbeat;
bench::Periodic csvTick(bench::kCsvPeriodMs);
bool isWired = false;  // `is 1` enables the current-sense columns (ADC reads of floating pins are noise)

float cmd = 0.0f;
int pwmR = 0, pwmL = 0;
uint32_t lastLoopMs = 0;

void ledcWriteDuty(uint8_t ch, int duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  // core 3.x: ledcWrite takes the pin, not the channel
  ledcWrite(ch == kLedcChR ? side->rpwm : side->lpwm, duty);
#else
  ledcWrite(ch, duty);
#endif
}

void attachPins() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(side->rpwm, kPwmHz, kPwmBits);
  ledcAttach(side->lpwm, kPwmHz, kPwmBits);
#else
  ledcSetup(kLedcChR, kPwmHz, kPwmBits);
  ledcSetup(kLedcChL, kPwmHz, kPwmBits);
  ledcAttachPin(side->rpwm, kLedcChR);
  ledcAttachPin(side->lpwm, kLedcChL);
#endif
  ledcWriteDuty(kLedcChR, 0);
  ledcWriteDuty(kLedcChL, 0);
}

void detachPins() {
  ledcWriteDuty(kLedcChR, 0);
  ledcWriteDuty(kLedcChL, 0);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcDetach(side->rpwm);
  ledcDetach(side->lpwm);
#else
  ledcDetachPin(side->rpwm);
  ledcDetachPin(side->lpwm);
#endif
  pinMode(side->rpwm, OUTPUT);
  digitalWrite(side->rpwm, LOW);
  pinMode(side->lpwm, OUTPUT);
  digitalWrite(side->lpwm, LOW);
}

void applyOutput(float out) {
  int duty = static_cast<int>(fabsf(out) * kPwmMax + 0.5f);
  if (duty > kPwmMax) duty = kPwmMax;
  if (out > 0.0f) {
    pwmR = duty;
    pwmL = 0;
  } else if (out < 0.0f) {
    pwmR = 0;
    pwmL = duty;
  } else {
    pwmR = pwmL = 0;
  }
  // never both high: write the zero first
  if (pwmR == 0) ledcWriteDuty(kLedcChR, 0);
  if (pwmL == 0) ledcWriteDuty(kLedcChL, 0);
  if (pwmR) ledcWriteDuty(kLedcChR, pwmR);
  if (pwmL) ledcWriteDuty(kLedcChL, pwmL);
}

void stopAll(const char* why) {
  ramp.stop();
  cmd = 0.0f;
  applyOutput(0.0f);
  if (why) bench::msg("%s", why);
}

void help() {
  bench::msg("bts7960 commands:");
  bench::msg("  s <-1..1>     speed/direction target (ramped at `rate`, refused above `limit`)");
  bench::msg("  0             stop now (no ramp)");
  bench::msg("  limit <0..1>  soft limit, default 0.60 (= 150/255 of bench_v1); `limit 1.0` unlocks full PWM");
  bench::msg("  rate <per_s>  ramp rate, default 0.50/s");
  bench::msg("  dm <ms>       dead-man timeout, default 2000 ms (0 = off)");
  bench::msg("  side L|R      which BTS7960 pin pair (L = GPIO%d/%d, R = GPIO%d/%d), stops first", PIN_BTS_L_RPWM,
             PIN_BTS_L_LPWM, PIN_BTS_R_RPWM, PIN_BTS_R_LPWM);
  bench::msg("  is 0|1        read the IS_R/IS_L current-sense pins (GPIO%d/%d) — only after they are wired", PIN_BTS_IS_R,
             PIN_BTS_IS_L);
  bench::msg("  ?             this help");
  bench::msg("state: side=%s limit=%.2f rate=%.2f/s dm=%lu ms is=%d kill=%d", side->name, limit.limit(), ramp.rate(),
             static_cast<unsigned long>(deadman.timeout()), isWired ? 1 : 0, killIn.active() ? 1 : 0);
}

void handleCommand(uint32_t now) {
  deadman.feed(now);
  if (shell.is("?")) {
    help();
  } else if (shell.is("0")) {
    stopAll("OK stop");
  } else if (shell.is("s")) {
    bool ok = false;
    const float v = shell.argf(1, 0.0f, &ok);
    if (!ok || v < -1.0f || v > 1.0f) {
      bench::err("s (want -1..1)");
    } else if (killIn.active()) {
      bench::msg("WARN KILL active (GPIO%d low): command refused", PIN_KILL);
    } else if (!limit.accepts(v)) {
      bench::msg("WARN |s|=%.2f above soft limit %.2f — send `limit %.2f` first", fabsf(v), limit.limit(), fabsf(v));
    } else {
      cmd = v;
      ramp.setTarget(v);
      bench::msg("OK s %.2f (ramping at %.2f/s)", v, ramp.rate());
    }
  } else if (shell.is("limit")) {
    bool ok = false;
    const float v = shell.argf(1, 0.0f, &ok);
    if (!ok || v < 0.0f || v > 1.0f) {
      bench::err("limit (want 0..1)");
    } else {
      limit.setLimit(v);
      if (v > bench::SoftLimit::kDefaultLimit) bench::msg("WARN soft limit raised to %.2f — full PWM allowed", v);
      else bench::msg("OK limit %.2f", v);
      if (!limit.accepts(cmd)) {
        cmd = limit.clamp(cmd);
        ramp.setTarget(cmd);
        bench::msg("OK target reduced to %.2f", cmd);
      }
    }
  } else if (shell.is("rate")) {
    bool ok = false;
    const float v = shell.argf(1, 0.0f, &ok);
    if (!ok || v <= 0.0f || v > 10.0f) bench::err("rate (want 0..10 per s)");
    else {
      ramp.setRate(v);
      bench::msg("OK rate %.2f/s", v);
    }
  } else if (shell.is("dm")) {
    bool ok = false;
    const long v = shell.argl(1, 0, &ok);
    if (!ok || v < 0) bench::err("dm (want ms >= 0)");
    else {
      deadman.setTimeout(static_cast<uint32_t>(v));
      bench::msg("OK dead-man %ld ms%s", v, v == 0 ? " (OFF — bench only)" : "");
    }
  } else if (shell.is("side")) {
    const char* a = shell.arg(1);
    const Side* s = (a[0] == 'L' || a[0] == 'l') ? &kLeft : (a[0] == 'R' || a[0] == 'r') ? &kRight : nullptr;
    if (!s) bench::err("side (want L or R)");
    else {
      stopAll(nullptr);
      detachPins();
      side = s;
      attachPins();
      bench::msg("OK side %s: RPWM GPIO%d, LPWM GPIO%d", side->name, side->rpwm, side->lpwm);
    }
  } else if (shell.is("is")) {
    isWired = shell.argl(1, 0) != 0;
    bench::msg("OK is %d", isWired ? 1 : 0);
  } else {
    bench::err(shell.arg(0));
  }
}

}  // namespace

void setup() {
  attachPins();
  killIn.begin();
  heartbeat.begin();
  pinMode(PIN_BTS_IS_R, INPUT);
  pinMode(PIN_BTS_IS_L, INPUT);
  analogReadResolution(12);
  bench::begin("bts7960", "t_ms,cmd,pwm_r,pwm_l,is_r_mV,is_l_mV,kill");
  bench::msg("pins: side %s RPWM GPIO%d LPWM GPIO%d · KILL GPIO%d · R_EN+L_EN on the rocker (5 V), not on a GPIO",
             side->name, side->rpwm, side->lpwm, PIN_KILL);
  bench::msg("soft limit %.2f, ramp %.2f/s, dead-man %lu ms. Type `?`.", limit.limit(), ramp.rate(),
             static_cast<unsigned long>(deadman.timeout()));
  lastLoopMs = millis();
}

void loop() {
  const uint32_t now = millis();
  const uint32_t dt = now - lastLoopMs;
  lastLoopMs = now;

  if (shell.poll()) handleCommand(now);

  if (killIn.risingKill()) stopAll("KILL (GPIO14 low) — outputs off");
  if (deadman.timeout() > 0 && deadman.update(now)) stopAll("DEADMAN");

  if (dt > 0) applyOutput(ramp.update(dt));
  heartbeat.update(now);

  if (csvTick.due(now)) {
    const int isR = isWired ? static_cast<int>(analogReadMilliVolts(side->is_r)) : -1;
    const int isL = isWired ? static_cast<int>(analogReadMilliVolts(side->is_l)) : -1;
    char buf[96];
    bench::CsvRow row(buf, sizeof buf);
    row.add(static_cast<unsigned long>(now)).add(cmd, 3).add(pwmR).add(pwmL).add(isR).add(isL).add(killIn.active());
    Serial.println(row.c_str());
  }
  delay(1);
}
