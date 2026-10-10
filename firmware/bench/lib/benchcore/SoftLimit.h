// SoftLimit — refuses actuator commands whose magnitude exceeds the current limit. Pure C++11.
//
// Starts at `limit` (bench default 0.6 = 150/255, the PWM_MAX of firmware/mega/bench/bench_v1.ino).
// A command above the limit is refused (not clamped) until the limit is raised explicitly
// with setLimit(); the sketch prints the refusal as a warning. Limits are clamped to [0, 1].
#pragma once

namespace bench {

class SoftLimit {
 public:
  static constexpr float kDefaultLimit = 0.6f;  // SOURCE: bench_v1.ino PWM_MAX 150/255 = 0.588 ≈ 60 %

  explicit SoftLimit(float limit = kDefaultLimit) : limit_(clamp01(limit)) {}

  float limit() const { return limit_; }
  void setLimit(float l) { limit_ = clamp01(l); }

  // True if |cmd| <= limit (accepted). Small epsilon so `limit 0.6` then `s 0.6` is accepted.
  bool accepts(float cmd) const {
    const float mag = cmd < 0.0f ? -cmd : cmd;
    return mag <= limit_ + 1e-6f;
  }

  // Clamp helper for callers that prefer saturation (not used for operator commands).
  float clamp(float cmd) const {
    if (cmd > limit_) return limit_;
    if (cmd < -limit_) return -limit_;
    return cmd;
  }

 private:
  static float clamp01(float v) { return v < 0.0f ? 0.0f : (v > 1.0f ? 1.0f : v); }
  float limit_;
};

}  // namespace bench
