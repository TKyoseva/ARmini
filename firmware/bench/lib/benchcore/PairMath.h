// PairMath — one degree for two facing TD-8120MG servos (C023). Pure C++11, no Arduino.
//
// us_A = 500 + deg/180 × 2000
// us_B = 3000 − us_A   (mirror around 1500 µs, so us_A + us_B = 3000)
// A degree outside 0..180 is refused (ok = false). The soft-limit window is a
// separate check: pairInWindow refuses the command when either pulse is outside it.
// SOURCE: card C023 / tasks/night/2026-10-22_T7_pca9685-pair.md (TD-8120MG, 500–2500 µs, 180°).
#pragma once

namespace bench {

static const float kPairUsLo = 500.0f;           // SOURCE: C023, TD-8120MG low pulse
static const float kPairUsHi = 2500.0f;          // SOURCE: C023, TD-8120MG high pulse
static const float kPairDegMax = 180.0f;         // SOURCE: C023, 180° travel
static const float kPairMirrorSumUs = 3000.0f;   // 500 + 2500; mirror around 1500 µs
static const float kPairDefaultDegPerS = 20.0f;  // SOURCE: C023, default ramp

struct PairPulses {
  float us_a;
  float us_b;
  bool ok;
};

inline PairPulses pairFromDeg(float deg) {
  PairPulses p;
  p.us_a = 0.0f;
  p.us_b = 0.0f;
  p.ok = false;
  if (deg < 0.0f || deg > kPairDegMax) return p;
  p.us_a = kPairUsLo + (deg / kPairDegMax) * (kPairUsHi - kPairUsLo);
  p.us_b = kPairMirrorSumUs - p.us_a;
  p.ok = true;
  return p;
}

// 0.5 µs tolerance matches the pca9685 sketch, so a pulse on the window edge is accepted.
inline bool pulseInWindow(float us, float min_us, float max_us) {
  return us >= min_us - 0.5f && us <= max_us + 0.5f;
}

inline bool pairInWindow(const PairPulses& p, float min_us, float max_us) {
  return p.ok && pulseInWindow(p.us_a, min_us, max_us) && pulseInWindow(p.us_b, min_us, max_us);
}

}  // namespace bench
