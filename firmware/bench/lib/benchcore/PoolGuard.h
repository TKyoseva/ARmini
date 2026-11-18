// PoolGuard — the two automatic stops of env `remote_pool` (card C076): leak probe wet, battery low.
// Pure C++11, host-tested. A thin wrapper over armini::Safety (firmware/armini/lib/core/Safety.h), so the
// bench boat and the mission firmware use one rule set (debounce, hysteresis, latch) instead of two copies.
// KILL and the heartbeat stay in remote_pool's own code (bench::KillInput, bench::linkLost); this class
// never sees them.
//
//   LEAK     GPIO7 below kLeakWetBelowV for kLeakHoldMs → stop "leak". Never clears: dry the box, power-cycle.
//   LOWBATT  VBAT below kLowBattTripV for kLowBattHoldMs → stop "lowbatt". Clears only on an ARM request
//            (tryClear) once VBAT is back above kLowBattRearmV. VBAT 0 V (no 12 V on the divider) also trips:
//            fail-safe. Bench without the battery chain: serial `lowbatt off` (one boot only, never LEAK).
//
// Leak divider (include/pins_devkit.h, breadboard 2b): 3V3 — 10 k — GPIO7 — 4.7 k — probe — water — GND.
// Dry: 3.3 V (the ADC reads ≈3.1 V at 11 dB). Probe shorted: 3.3 × 4.7 / 14.7 = 1.06 V.
// Water across a 5–10 mm gap R_w: V = 3.3 × (4.7 k + R_w) / (14.7 k + R_w) → 2.60 V at R_w ≈ 28 k.
#pragma once
#include <stdint.h>

#include "Safety.h"

namespace bench {

const float kLeakWetBelowV = 2.60f;     // VERIFY in C068: probe in tap and lake water, log leak_v (CSV column)
const uint32_t kLeakHoldMs = 200;       // a splash shorter than this does not stop the boat
const float kLowBattTripV = 10.50f;     // SOURCE: project rule "stop the run at VBAT ≤ 10.5 V" (3.5 V/cell, FINAL 2)
const float kLowBattRearmV = 10.80f;    // ARM allowed again only above this (0.3 V hysteresis)
const uint32_t kLowBattHoldMs = 5000;   // VERIFY in C062: sag under full thrust must not trip on its own

enum class GuardStop : uint8_t { NONE, LEAK, LOWBATT };

// Names as the page and serial show them (`# SAFE leak`, `"safe":"lowbatt"`).
inline const char* guardStopName(GuardStop s) {
  switch (s) {
    case GuardStop::LEAK:    return "leak";
    case GuardStop::LOWBATT: return "lowbatt";
    case GuardStop::NONE:    return "";
  }
  return "";
}

// leak_v < 0 = not read yet → dry.
inline bool leakWet(float leak_v) { return leak_v >= 0.0f && leak_v < kLeakWetBelowV; }

class PoolGuard {
 public:
  PoolGuard() : safety_(config()), leak_latched_(false) {}

  static armini::SafetyConfig config() {
    armini::SafetyConfig c;
    c.leak_debounce_ms = kLeakHoldMs;
    c.batt_debounce_ms = kLowBattHoldMs;
    c.v_trip = kLowBattTripV;
    c.v_reset = kLowBattRearmV;
    return c;
  }

  // Call every few tens of ms with the latest readings. Returns the stop that holds now.
  GuardStop tick(float leak_v, float vbat_v, uint32_t now_ms) {
    armini::SafetyInputs in;
    in.leak_raw = leakWet(leak_v);
    in.kill_raw = false;      // remote_pool handles KILL itself
    in.v_bat = vbat_v;
    in.heartbeat_ok = true;   // remote_pool handles the link itself
    safety_.tick(in, now_ms);
    if (safety_.active() == armini::SafetyReason::LEAK) leak_latched_ = true;
    return stop();
  }

  GuardStop stop() const {
    if (leak_latched_) return GuardStop::LEAK;
    if (safety_.tripped()) return GuardStop::LOWBATT;
    return GuardStop::NONE;
  }

  // On an ARM request: true = may arm. Clears a low-battery stop once VBAT is above kLowBattRearmV
  // (and no leak). A leak never clears.
  bool tryClear() {
    if (leak_latched_) return false;
    if (!safety_.tripped()) return true;
    return safety_.reset();
  }

 private:
  armini::Safety safety_;
  bool leak_latched_;
};

}  // namespace bench
