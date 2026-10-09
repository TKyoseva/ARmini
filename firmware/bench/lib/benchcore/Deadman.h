// Deadman — stops an actuator when no command has arrived for `timeout_ms`. Pure C++11.
//
// Starts disengaged: nothing is watched until the first feed() (an actuator can only be
// non-zero after a command, and every command feeds). update(now) returns true exactly once,
// on the tick the timeout expires, so the sketch prints `# DEADMAN` a single time and stops
// its outputs. Any later feed() re-engages the watchdog.
#pragma once
#include <stdint.h>

namespace bench {

class Deadman {
 public:
  explicit Deadman(uint32_t timeout_ms = 2000) : timeout_ms_(timeout_ms), last_feed_ms_(0), engaged_(false), tripped_(false) {}

  void setTimeout(uint32_t ms) { timeout_ms_ = ms; }
  uint32_t timeout() const { return timeout_ms_; }

  // Call on every received command.
  void feed(uint32_t now_ms) {
    last_feed_ms_ = now_ms;
    engaged_ = true;
    tripped_ = false;
  }

  // Call every loop. Returns true only on the tick the dead-man trips (rising edge).
  bool update(uint32_t now_ms) {
    if (!engaged_ || tripped_) return false;
    if (static_cast<uint32_t>(now_ms - last_feed_ms_) >= timeout_ms_) {
      tripped_ = true;
      engaged_ = false;  // wait for the next command
      return true;
    }
    return false;
  }

  bool tripped() const { return tripped_; }
  bool engaged() const { return engaged_; }

 private:
  uint32_t timeout_ms_;
  uint32_t last_feed_ms_;
  bool engaged_;
  bool tripped_;
};

}  // namespace bench
