// AR-Mini · mission state machine.
// Pure C++11: no Arduino, no heap, no clock access. Time is passed in as dt_ms.
// tick() is deterministic: same Config + same input sequence -> same outputs.
#pragma once
#include "Types.h"

namespace armini {

class StateMachine {
 public:
  explicit StateMachine(const Config& cfg);

  // Advance one tick. dt_ms = time since the previous tick.
  // Transitions decided in this tick take effect from the next tick, except
  // the jump to SAFE, which applies immediately (outputs of this tick are
  // already the SAFE outputs).
  Outputs tick(const Inputs& in, uint32_t dt_ms);

  // Leave SAFE -> IDLE. Only allowed while no hard cause (leak, kill,
  // battery_low) was active in the most recent tick. Returns true if it acted.
  // Disarm is not a blocking cause here: IDLE is itself the "not armed" state.
  bool reset();

  State state() const { return state_; }
  SafeReason reason() const { return reason_; }
  const Config& config() const { return cfg_; }

 private:
  void enter(State next);
  void stepIdle(const Inputs& in, Outputs& out);
  void stepSearch(const Inputs& in, uint32_t dt_ms, Outputs& out);
  void stepApproach(const Inputs& in, uint32_t dt_ms, Outputs& out);
  void stepDeploy(const Inputs& in, Outputs& out);
  void stepLift(const Inputs& in, Outputs& out);
  void stepStow(const Inputs& in, Outputs& out);
  void stepShore(uint32_t dt_ms, Outputs& out);
  void stepSafe(Outputs& out);
  void clampOutputs(Outputs& out) const;

  static SafeReason hardCause(const Inputs& in);
  static float clampf(float v, float lo, float hi);
  static float wrapDeg(float d);
  static uint32_t addSat(uint32_t a, uint32_t b);

  Config     cfg_;
  State      state_;
  SafeReason reason_;
  bool       cause_active_;      // hard cause seen in the last tick (for reset())
  uint16_t   sightings_;         // consecutive target_seen ticks in SEARCH
  uint32_t   since_seen_ms_;     // time without target_seen in APPROACH
  uint32_t   shore_elapsed_ms_;  // time spent driving in SHORE
  float      pan_deg_;           // current pan sweep position
  float      pan_dir_;           // +1 / -1
  float      arm_hold_deg_;      // arm angle latched on entering SAFE
  bool       no_load_;
  bool       mission_complete_;
};

}  // namespace armini
