// AR-Mini · safety layer: decides every tick whether the robot may run.
// Pure C++11: no Arduino, no heap, no clock access. Time is passed in as an
// absolute now_ms; the module keeps timestamps, so the tick period is free.
//
// Second line of defence. The first is hardware: the KILL rocker pulls
// PCA9685 OE high and switches all PWM outputs off without the MCU
// (pcb/carrier-revA/SPEC.md R10, docs/FAILS_AND_FIXES.md #42). This module
// makes the firmware *agree* with the hardware, adds the causes the hardware
// cannot see (leak, battery, heartbeat) and latches so nothing restarts on
// its own.
//
// Causes and their timing (defaults in SafetyConfig, all VERIFY):
//   KILL       first tick seen → trip. The only cause without debounce.
//   LEAK       probe continuously wet for leak_debounce_ms → trip.
//   BATTERY    v_bat < v_trip continuously for batt_debounce_ms → trip;
//              the cause stays active until v_bat > v_reset (hysteresis).
//   HEARTBEAT  heartbeat_ok continuously false for heartbeat_timeout_ms → trip.
// Priority if several trip in the same tick: KILL > LEAK > BATTERY > HEARTBEAT.
// Latch: once tripped, verdict.safe == false and verdict.reason keep their
// value until reset() is called while no cause is active.
#pragma once
#include <stdint.h>
#include "Ladder.h"
#include "Types.h"

namespace armini {

enum class SafetyReason : uint8_t { NONE, LEAK, KILL, BATTERY, HEARTBEAT };

inline const char* safetyReasonName(SafetyReason r) {
  switch (r) {
    case SafetyReason::NONE:      return "NONE";
    case SafetyReason::LEAK:      return "LEAK";
    case SafetyReason::KILL:      return "KILL";
    case SafetyReason::BATTERY:   return "BATTERY";
    case SafetyReason::HEARTBEAT: return "HEARTBEAT";
  }
  return "?";
}

struct SafetyConfig {
  // --- debounce / timeout --------------------------------------------------
  uint32_t leak_debounce_ms     = 100;  // VERIFY: a 50 ms splash must not trip; task T2 default
  uint32_t batt_debounce_ms     = 500;  // VERIFY: one bad ADC sample must not trip; task T2 default
  uint32_t heartbeat_timeout_ms = 500;  // VERIFY: task T2 default

  // --- battery, 2 × LiPo 3S (README) ---------------------------------------
  // v_bat is the pack voltage after the HAL has undone the VBAT divider
  // 100 kΩ / 33 kΩ (hardware/wiring/PINOUT.md): v_bat = v_adc × 133 / 33.
  float v_trip  = 9.9f;   // VERIFY: Teddy decides. 3.3 V/cell × 3 (task T2 proposal)
  float v_reset = 10.5f;  // VERIFY: Teddy decides. 3.5 V/cell × 3; must be > v_trip
};

// VBAT divider ratio, (100 k + 33 k) / 33 k. SOURCE: hardware/wiring/PINOUT.md.
static const float kVbatDividerGain = 133.0f / 33.0f;
inline float vbatFromAdc(float v_adc) { return v_adc * kVbatDividerGain; }

struct SafetyInputs {
  bool  leak_raw     = false;  // leak probe wet (boolean form, e.g. DevKit-Lipo GPIO)
  bool  kill_raw     = false;  // logic kill switch (boolean form)
  float v_bat        = 0.0f;   // pack voltage in V. 0 V (unknown) trips BATTERY after the debounce: fail-safe
  bool  heartbeat_ok = true;   // the watched link / loop reported in time
  float ladder_v     = -1.0f;  // A1 ladder voltage, < 0 = no ladder fitted. Decoded and OR-ed into leak/kill
};

struct Verdict {
  bool         safe   = true;
  SafetyReason reason = SafetyReason::NONE;
};

class Safety {
 public:
  explicit Safety(const SafetyConfig& cfg);

  // Evaluate one tick at absolute time now_ms (wrap-safe, uint32 arithmetic).
  Verdict tick(const SafetyInputs& in, uint32_t now_ms);

  // Clear the latch. Allowed only while tripped and no cause was active in
  // the most recent tick. Returns true if it acted; false changes nothing.
  bool reset();

  Verdict verdict() const { return verdict_; }
  bool tripped() const { return !verdict_.safe; }
  // Highest-priority cause active in the most recent tick (after debounce
  // and hysteresis), independent of the latch. NONE when nothing is active.
  SafetyReason active() const { return active_; }
  const SafetyConfig& config() const { return cfg_; }

 private:
  SafetyConfig cfg_;
  Verdict      verdict_;
  SafetyReason active_;

  // leak debounce
  bool     leak_timing_;
  uint32_t leak_since_ms_;
  // battery debounce + hysteresis
  bool     batt_timing_;
  uint32_t batt_since_ms_;
  bool     batt_low_;       // tripped state with hysteresis
  // heartbeat
  bool     hb_timing_;
  uint32_t hb_since_ms_;

  // Debounce helper: `cond` must be continuously true for `hold_ms`.
  // Returns true once the time has elapsed; resets when cond is false.
  static bool held(bool cond, uint32_t hold_ms, uint32_t now_ms, bool& timing, uint32_t& since_ms);
};

// ---------------------------------------------------------------------------
// Glue: feed the verdict into the StateMachine inputs. While tripped exactly
// one of leak / kill / battery_low / heartbeat_lost is true; when safe all
// four are false. The raw sensors never reach the state machine.
inline void applyVerdict(const Verdict& v, Inputs& in) {
  in.leak           = !v.safe && v.reason == SafetyReason::LEAK;
  in.kill           = !v.safe && v.reason == SafetyReason::KILL;
  in.battery_low    = !v.safe && v.reason == SafetyReason::BATTERY;
  in.heartbeat_lost = !v.safe && v.reason == SafetyReason::HEARTBEAT;
}

}  // namespace armini
