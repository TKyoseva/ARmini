// EscMath — pulse widths for the two thruster ESCs (C024). Pure C++11, no Arduino.
//
// 1500 µs = stop, above = forward, below = reverse (thruster listing, C002; VERIFY on this unit).
// diff mix: l = 1500 + k·(thrust + turn), r = 1500 + k·(thrust − turn), thrust/turn in −100..100,
// k chosen so 100 reaches the current soft limit, then both clamped into the limit.
// SOURCE: tasks/night/2026-10-23_T10_esc.md (limits 1350–1650 narrow, 1000–2000 wide).
#pragma once

namespace bench {

static const float kEscNeutralUs = 1500.0f;  // SOURCE: C002 thruster listing (1500 µs = stop). VERIFY on this ESC
static const float kEscNarrowLoUs = 1350.0f;  // SOURCE: T10 soft limit
static const float kEscNarrowHiUs = 1650.0f;  // SOURCE: T10 soft limit
static const float kEscWideLoUs = 1000.0f;    // SOURCE: C002 listing (1500 → 1000 reverse), T10 `limit wide`
static const float kEscWideHiUs = 2000.0f;    // SOURCE: C002 listing (1500 → 2000 forward), T10 `limit wide`
static const float kEscMixMax = 100.0f;       // thrust / turn range −100..100

struct EscPulses {
  float l_us;
  float r_us;
};

inline float escClamp(float us, float lo_us, float hi_us) {
  if (us < lo_us) return lo_us;
  if (us > hi_us) return hi_us;
  return us;
}

inline bool escInLimit(float us, float lo_us, float hi_us) { return us >= lo_us - 0.5f && us <= hi_us + 0.5f; }

// µs per unit of thrust/turn, so ±100 reaches the nearer limit on both sides of 1500.
inline float escMixGain(float lo_us, float hi_us) {
  const float up = hi_us - kEscNeutralUs;
  const float down = kEscNeutralUs - lo_us;
  const float span = up < down ? up : down;
  return span > 0.0f ? span / kEscMixMax : 0.0f;
}

inline EscPulses escDiff(float thrust, float turn, float lo_us, float hi_us) {
  const float k = escMixGain(lo_us, hi_us);
  EscPulses p;
  p.l_us = escClamp(kEscNeutralUs + k * (thrust + turn), lo_us, hi_us);
  p.r_us = escClamp(kEscNeutralUs + k * (thrust - turn), lo_us, hi_us);
  return p;
}

}  // namespace bench
