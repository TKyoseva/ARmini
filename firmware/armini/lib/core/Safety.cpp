// AR-Mini · safety layer · implementation. See Safety.h and README.md "Safety".
#include "Safety.h"

namespace armini {

Safety::Safety(const SafetyConfig& cfg)
    : cfg_(cfg),
      verdict_(),
      active_(SafetyReason::NONE),
      leak_timing_(false),
      leak_since_ms_(0),
      batt_timing_(false),
      batt_since_ms_(0),
      batt_low_(false),
      hb_timing_(false),
      hb_since_ms_(0) {}

bool Safety::held(bool cond, uint32_t hold_ms, uint32_t now_ms, bool& timing, uint32_t& since_ms) {
  if (!cond) {
    timing = false;
    return false;
  }
  if (!timing) {
    timing = true;
    since_ms = now_ms;
  }
  return (now_ms - since_ms) >= hold_ms;  // unsigned: wrap-safe
}

Verdict Safety::tick(const SafetyInputs& in, uint32_t now_ms) {
  // 1. Merge the two input forms. A ladder reading (>= 0) is decoded and
  //    OR-ed with the booleans, so a board with both still trips on either.
  bool leak_raw = in.leak_raw;
  bool kill_raw = in.kill_raw;
  if (ladderPresent(in.ladder_v)) {
    const LadderState s = decodeLadder(in.ladder_v);
    leak_raw = leak_raw || (s == LadderState::LEAK);
    kill_raw = kill_raw || (s == LadderState::KILL);
  }

  // 2. Per-cause condition after debounce / hysteresis.
  const bool kill = kill_raw;  // immediate, no debounce
  const bool leak = held(leak_raw, cfg_.leak_debounce_ms, now_ms, leak_timing_, leak_since_ms_);
  const bool hb   = held(!in.heartbeat_ok, cfg_.heartbeat_timeout_ms, now_ms, hb_timing_, hb_since_ms_);

  // Battery: debounce the dip, then hold the cause until v_bat climbs above
  // v_reset. A pack that sits between the two thresholds stays "low".
  if (batt_low_) {
    if (in.v_bat > cfg_.v_reset) {
      batt_low_ = false;
      batt_timing_ = false;
    }
  } else if (held(in.v_bat < cfg_.v_trip, cfg_.batt_debounce_ms, now_ms, batt_timing_, batt_since_ms_)) {
    batt_low_ = true;
  }
  const bool batt = batt_low_;

  // 3. Highest-priority active cause this tick.
  if (kill)      active_ = SafetyReason::KILL;
  else if (leak) active_ = SafetyReason::LEAK;
  else if (batt) active_ = SafetyReason::BATTERY;
  else if (hb)   active_ = SafetyReason::HEARTBEAT;
  else           active_ = SafetyReason::NONE;

  // 4. Latch. The first cause to trip is the one reported until reset().
  if (verdict_.safe && active_ != SafetyReason::NONE) {
    verdict_.safe = false;
    verdict_.reason = active_;
  }
  return verdict_;
}

bool Safety::reset() {
  if (verdict_.safe) return false;                  // nothing to reset
  if (active_ != SafetyReason::NONE) return false;  // a cause is still active
  verdict_.safe = true;
  verdict_.reason = SafetyReason::NONE;
  return true;
}

}  // namespace armini
