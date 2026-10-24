// EscMath — pulse widths for the two thruster ESCs (C024). Pure C++11, no Arduino.
//
// 1500 µs = stop, above = forward, below = reverse (thruster listing, C002; VERIFY on this unit).
// diff mix: l = 1500 + k·(thrust + turn), r = 1500 + k·(thrust − turn), thrust/turn in −100..100,
// k chosen so 100 reaches the current soft limit, then both clamped into the limit.
// SOURCE: tasks/night/2026-10-23_T10_esc.md (limits 1350–1650 narrow, 1000–2000 wide).
#pragma once
#include <stdint.h>

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

// LEDC duty for a pulse of `us` in a frame of `frame_us`, `bits` resolution. full = 1 << bits (= always on).
// inverted (T11, C006): the pin drives an S8050 NPN that pulls the ESC input low, so the pin must be
// LOW for `us` and HIGH for the rest → duty = full − normal. 0 µs inverted = pin always HIGH = input always LOW.
inline uint32_t escDuty(float us, uint8_t bits, bool inverted, float frame_us = 20000.0f) {
  const uint32_t full = 1UL << bits;
  float d = us / frame_us * static_cast<float>(full);
  if (d < 0.0f) d = 0.0f;
  if (d > static_cast<float>(full)) d = static_cast<float>(full);
  const uint32_t normal = static_cast<uint32_t>(d + 0.5f);
  return inverted ? full - normal : normal;
}

// Dead band (T12, C025 23.10 at 12 V: 1550 µs does not spin, 1600 → 0.22 A, 1650 → 0.58 A, 1400 reverse).
// A command 1..100 maps linearly to db_fwd..hi_us, −1..−100 to db_rev..lo_us, 0 → 1500, so the first
// step of a slider already spins the prop. |cmd| > 100 is clamped.
static const float kEscDeadbandFwdUs = 1580.0f;  // SOURCE: C025 (1550 no spin, 1600 spins); T12
static const float kEscDeadbandRevUs = 1420.0f;  // SOURCE: T12 (mirror of 1580; C025 1400 reverse spins)

inline float escDeadbandUs(float cmd, float lo_us, float hi_us, float db_fwd_us = kEscDeadbandFwdUs,
                           float db_rev_us = kEscDeadbandRevUs) {
  if (cmd > kEscMixMax) cmd = kEscMixMax;
  if (cmd < -kEscMixMax) cmd = -kEscMixMax;
  float us = kEscNeutralUs;
  if (cmd >= 1.0f) {
    us = db_fwd_us + (cmd - 1.0f) * (hi_us - db_fwd_us) / (kEscMixMax - 1.0f);
  } else if (cmd <= -1.0f) {
    us = db_rev_us - (-cmd - 1.0f) * (db_rev_us - lo_us) / (kEscMixMax - 1.0f);
  }
  return escClamp(us, lo_us, hi_us);
}

// Same mix as escDiff (l = thrust + turn, r = thrust − turn, each clamped to ±100), but each side goes
// through the dead-band map instead of the linear gain. Used by the `remote` env.
inline EscPulses escMixDeadband(float thrust, float turn, float lo_us, float hi_us) {
  EscPulses p;
  p.l_us = escDeadbandUs(thrust + turn, lo_us, hi_us);
  p.r_us = escDeadbandUs(thrust - turn, lo_us, hi_us);
  return p;
}

inline EscPulses escDiff(float thrust, float turn, float lo_us, float hi_us) {
  const float k = escMixGain(lo_us, hi_us);
  EscPulses p;
  p.l_us = escClamp(kEscNeutralUs + k * (thrust + turn), lo_us, hi_us);
  p.r_us = escClamp(kEscNeutralUs + k * (thrust - turn), lo_us, hi_us);
  return p;
}

}  // namespace bench
