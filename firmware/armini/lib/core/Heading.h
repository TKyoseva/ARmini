// AR-Mini · heading hold: PI controller from the BNO055 heading to a turn command (card C077).
// Pure C++11, header only, no Arduino, no heap. SIMULATION ONLY so far: not wired into any firmware env.
// Wiring it in (behind -DHEADING_HOLD, off by default) waits for C066 (BNO055 on the robot); water test = C067.
//
//   error  = shortest way from the heading to the target, wrapped to −180…+180°
//   turn   = Kp · error + Ki · ∫error dt        clamped to −1…+1
//   rudder = bench::rudderUs(turn) = 1500 ± 333 µs  (the existing phone-slider path, unchanged)
//
// Sign convention: heading grows clockwise seen from above (BNO055 Euler heading, 0…360°);
// turn > 0 = turn right (heading grows). VERIFY the sign on the robot in C066 step C: if the boat turns
// away from the target, swap the rudder horn side or negate kp and ki together.
//
// Anti-windup: the integral stops growing while the output is saturated in the same direction, and it is
// cleared on reset() (controller switched on, SAFE, new target far away).
//
// Gains. SOURCE: sim/heading/ (first-order yaw model, ASSUMED 30 °/s at full rudder, time constant 0.8 s —
// NOT measured; C067 replaces them). With these gains the simulated boat stays inside ±5° after 10 s for
// every model in the tested range (see sim/heading/README.md).
#pragma once
#include <math.h>

namespace armini {

static const float kHeadingKp = 0.04f;      // turn per degree: full rudder at 25° of error
static const float kHeadingKi = 0.008f;     // turn per degree-second
static const float kHeadingMaxDtS = 0.5f;   // a longer gap between samples = stale data, the integral waits

// Shortest signed angle from `fromDeg` to `toDeg`, in (−180, +180].
inline float headingError(float toDeg, float fromDeg) {
  float e = fmodf(toDeg - fromDeg, 360.0f);
  if (e > 180.0f) e -= 360.0f;
  if (e <= -180.0f) e += 360.0f;
  return e;
}

class HeadingHold {
 public:
  explicit HeadingHold(float kp = kHeadingKp, float ki = kHeadingKi) : kp_(kp), ki_(ki), i_(0.0f) {}

  void reset() { i_ = 0.0f; }
  float integral() const { return i_; }

  // One control step. targetDeg and headingDeg in degrees (any range), dtS = time since the last step.
  // Returns turn in −1…+1. A NaN heading (IMU not ready) returns 0 and keeps the integral.
  float update(float targetDeg, float headingDeg, float dtS) {
    if (isnan(targetDeg) || isnan(headingDeg)) return 0.0f;
    const float e = headingError(targetDeg, headingDeg);
    const float p = kp_ * e;
    const float raw = p + ki_ * i_;
    const bool sat_hi = raw >= 1.0f, sat_lo = raw <= -1.0f;
    const bool winding = (sat_hi && e > 0.0f) || (sat_lo && e < 0.0f);
    if (dtS > 0.0f && dtS <= kHeadingMaxDtS && !winding) i_ += e * dtS;
    float u = p + ki_ * i_;
    if (u > 1.0f) u = 1.0f;
    if (u < -1.0f) u = -1.0f;
    return u;
  }

 private:
  float kp_, ki_, i_;
};

// The simulated boat used by the host tests and by sim/heading/: first-order yaw rate, then heading.
//   tau · d(rate)/dt + rate = gain · turn + disturbance,   d(heading)/dt = rate
// gain = yaw rate at full rudder (°/s), disturbance = constant push (°/s), e.g. wind or the off-centre thruster.
struct YawModel {
  float gainDps, tauS, disturbDps;
  float headingDeg, rateDps;
  void step(float turn, float dtS) {
    rateDps += (gainDps * turn + disturbDps - rateDps) * dtS / tauS;
    headingDeg += rateDps * dtS;
    headingDeg = fmodf(headingDeg, 360.0f);
    if (headingDeg < 0.0f) headingDeg += 360.0f;
  }
};

}  // namespace armini
