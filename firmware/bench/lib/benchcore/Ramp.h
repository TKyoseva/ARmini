// Ramp — rate limiter for actuator commands. Pure C++11, no Arduino.
//
// value() moves towards target() by at most rate_per_s * dt each update(); it never jumps,
// never overshoots the target and passes through zero on a sign change.
// stop() is the one deliberate jump: it is the safe direction (dead-man, `0`, kill).
#pragma once
#include <stdint.h>

namespace bench {

class Ramp {
 public:
  explicit Ramp(float rate_per_s = 0.5f, float initial = 0.0f)
      : rate_(rate_per_s < 0.0f ? -rate_per_s : rate_per_s), value_(initial), target_(initial) {}

  void setRate(float rate_per_s) { rate_ = rate_per_s < 0.0f ? -rate_per_s : rate_per_s; }
  float rate() const { return rate_; }

  void setTarget(float t) { target_ = t; }
  float target() const { return target_; }
  float value() const { return value_; }
  bool atTarget() const { return value_ == target_; }

  // Advance by dt_ms. Returns the new value.
  float update(uint32_t dt_ms) {
    const float max_step = rate_ * (static_cast<float>(dt_ms) / 1000.0f);
    const float diff = target_ - value_;
    if (diff > max_step) {
      value_ += max_step;
    } else if (diff < -max_step) {
      value_ -= max_step;
    } else {
      value_ = target_;
    }
    return value_;
  }

  // Immediate stop: value and target both become `v` (default 0). The only allowed jump.
  void stop(float v = 0.0f) {
    value_ = v;
    target_ = v;
  }

 private:
  float rate_;
  float value_;
  float target_;
};

}  // namespace bench
