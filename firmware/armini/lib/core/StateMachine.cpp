// AR-Mini · mission state machine · implementation. See README.md for the diagram.
#include "StateMachine.h"
#include <math.h>

namespace armini {

StateMachine::StateMachine(const Config& cfg)
    : cfg_(cfg),
      state_(State::IDLE),
      reason_(SafeReason::NONE),
      cause_active_(false),
      sightings_(0),
      since_seen_ms_(0),
      shore_elapsed_ms_(0),
      pan_deg_(cfg.pan_min_deg),
      pan_dir_(1.0f),
      arm_hold_deg_(0.0f),
      no_load_(false),
      mission_complete_(false) {}

// ---------------------------------------------------------------------------
// helpers

float StateMachine::clampf(float v, float lo, float hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

// Wrap an angle difference into (-180, 180].
float StateMachine::wrapDeg(float d) {
  d = fmodf(d, 360.0f);
  if (d > 180.0f) d -= 360.0f;
  if (d <= -180.0f) d += 360.0f;
  return d;
}

uint32_t StateMachine::addSat(uint32_t a, uint32_t b) {
  return (a > UINT32_MAX - b) ? UINT32_MAX : a + b;
}

SafeReason StateMachine::hardCause(const Inputs& in) {
  if (in.kill) return SafeReason::KILL;
  if (in.leak) return SafeReason::LEAK;
  if (in.battery_low) return SafeReason::BATTERY;
  if (in.heartbeat_lost) return SafeReason::HEARTBEAT;
  return SafeReason::NONE;
}

void StateMachine::clampOutputs(Outputs& out) const {
  out.thrust_l = clampf(out.thrust_l, -1.0f, 1.0f);
  out.thrust_r = clampf(out.thrust_r, -1.0f, 1.0f);
  out.track_l  = clampf(out.track_l, -1.0f, 1.0f);
  out.track_r  = clampf(out.track_r, -1.0f, 1.0f);
  out.arm_deg  = clampf(out.arm_deg, cfg_.angle_min_deg, cfg_.angle_max_deg);
  out.pan_deg  = clampf(out.pan_deg, cfg_.angle_min_deg, cfg_.angle_max_deg);
}

// ---------------------------------------------------------------------------
// transitions

void StateMachine::enter(State next) {
  state_ = next;
  switch (next) {
    case State::SEARCH:
      sightings_ = 0;
      since_seen_ms_ = 0;
      break;
    case State::APPROACH:
      since_seen_ms_ = 0;
      break;
    case State::SHORE:
      shore_elapsed_ms_ = 0;
      break;
    default:
      break;
  }
}

bool StateMachine::reset() {
  if (state_ != State::SAFE) return false;
  if (cause_active_) return false;
  state_ = State::IDLE;
  reason_ = SafeReason::NONE;
  sightings_ = 0;
  since_seen_ms_ = 0;
  shore_elapsed_ms_ = 0;
  no_load_ = false;
  mission_complete_ = false;
  return true;
}

// ---------------------------------------------------------------------------
// tick

Outputs StateMachine::tick(const Inputs& in, uint32_t dt_ms) {
  Outputs out;

  // Safety first: leak / kill / battery from every state; disarm from every
  // mission state (IDLE is the not-armed state, so !armed is normal there).
  SafeReason cause = hardCause(in);
  cause_active_ = (cause != SafeReason::NONE);
  if (state_ != State::SAFE) {
    if (cause == SafeReason::NONE && !in.armed && state_ != State::IDLE) cause = SafeReason::DISARM;
    if (cause != SafeReason::NONE) {
      reason_ = cause;
      arm_hold_deg_ = in.arm_deg;
      enter(State::SAFE);
    }
  }

  switch (state_) {
    case State::IDLE:     stepIdle(in, out); break;
    case State::SEARCH:   stepSearch(in, dt_ms, out); break;
    case State::APPROACH: stepApproach(in, dt_ms, out); break;
    case State::DEPLOY:   stepDeploy(in, out); break;
    case State::LIFT:     stepLift(in, out); break;
    case State::STOW:     stepStow(in, out); break;
    case State::SHORE:    stepShore(dt_ms, out); break;
    case State::SAFE:     stepSafe(out); break;
  }

  // Indicators (SPEC.md LED1–3: green = status, yellow = arm, red = fault).
  // Computed on the state the outputs were produced for.
  const State produced = out.state;
  out.led_green  = (produced != State::SAFE);
  out.led_yellow = (produced != State::IDLE && produced != State::SAFE);
  out.led_red    = (produced == State::SAFE);
  out.reason = reason_;
  out.flags.no_load = no_load_;
  out.flags.mission_complete = mission_complete_;

  clampOutputs(out);
  return out;
}

// ---------------------------------------------------------------------------
// per-state logic. Each step() fills out for the *current* state and may call
// enter() for the next tick. out.state is the state the outputs belong to.

void StateMachine::stepIdle(const Inputs& in, Outputs& out) {
  out.state = State::IDLE;
  // Thrust, tracks and pan are zero. The arm target mirrors the measured arm
  // angle instead of 0: commanding 0° at power-on would swing a stowed arm
  // (45°) into the hull. Deviation from T1 "outputs zero", flagged in the PR.
  out.arm_deg = in.arm_deg;
  if (in.armed) {
    no_load_ = false;
    mission_complete_ = false;
    enter(State::SEARCH);
  }
}

void StateMachine::stepSearch(const Inputs& in, uint32_t dt_ms, Outputs& out) {
  out.state = State::SEARCH;

  // Pan sweep between pan_min_deg and pan_max_deg at pan_rate_deg_s.
  pan_deg_ += pan_dir_ * cfg_.pan_rate_deg_s * (static_cast<float>(dt_ms) / 1000.0f);
  if (pan_deg_ >= cfg_.pan_max_deg) {
    pan_deg_ = cfg_.pan_max_deg;
    pan_dir_ = -1.0f;
  } else if (pan_deg_ <= cfg_.pan_min_deg) {
    pan_deg_ = cfg_.pan_min_deg;
    pan_dir_ = 1.0f;
  }
  out.pan_deg = pan_deg_;
  out.arm_deg = cfg_.arm_stow_deg;  // arm stays stowed while searching

  // N consecutive sightings confirm the target; one miss resets the count.
  if (in.target_seen) {
    if (sightings_ < UINT16_MAX) ++sightings_;
    if (sightings_ >= cfg_.sightings_to_confirm) enter(State::APPROACH);
  } else {
    sightings_ = 0;
  }
}

void StateMachine::stepApproach(const Inputs& in, uint32_t dt_ms, Outputs& out) {
  out.state = State::APPROACH;

  if (in.target_seen) {
    since_seen_ms_ = 0;
  } else {
    since_seen_ms_ = addSat(since_seen_ms_, dt_ms);
  }

  // Differential thrust: + bearing (target to starboard) -> more left thrust -> turn right.
  const float diff = cfg_.k_bearing * in.bearing_deg;
  out.thrust_l = cfg_.approach_thrust + diff;
  out.thrust_r = cfg_.approach_thrust - diff;
  out.pan_deg = pan_deg_;
  out.arm_deg = cfg_.arm_stow_deg;

  if (since_seen_ms_ >= cfg_.loss_timeout_ms) {
    enter(State::SEARCH);
    return;
  }
  if (in.target_range_m <= cfg_.deploy_range_m && in.cradle_confirmed) {
    enter(State::DEPLOY);
  }
}

void StateMachine::stepDeploy(const Inputs& in, Outputs& out) {
  out.state = State::DEPLOY;
  out.arm_deg = cfg_.arm_deploy_deg;
  out.pan_deg = pan_deg_;
  if (fabsf(in.arm_deg - cfg_.arm_deploy_deg) <= cfg_.arm_tol_deg) enter(State::LIFT);
}

void StateMachine::stepLift(const Inputs& in, Outputs& out) {
  out.state = State::LIFT;
  out.arm_deg = cfg_.arm_stow_deg;
  out.pan_deg = pan_deg_;
  if (fabsf(in.arm_deg - cfg_.arm_stow_deg) <= cfg_.arm_tol_deg) {
    if (!in.load_detected) no_load_ = true;  // Teddy decides later what to do with it
    enter(State::STOW);
  }
}

void StateMachine::stepStow(const Inputs& in, Outputs& out) {
  out.state = State::STOW;
  out.arm_deg = cfg_.arm_stow_deg;
  out.pan_deg = pan_deg_;

  // Steer toward the shore heading. + error (shore to starboard) -> turn right.
  const float err = wrapDeg(cfg_.shore_heading_deg - in.heading_deg);
  const float diff = cfg_.k_heading * err;
  out.thrust_l = cfg_.stow_thrust + diff;
  out.thrust_r = cfg_.stow_thrust - diff;

  if (in.tilt_deg >= cfg_.shore_tilt_deg) enter(State::SHORE);
}

void StateMachine::stepShore(uint32_t dt_ms, Outputs& out) {
  out.state = State::SHORE;
  out.arm_deg = cfg_.arm_stow_deg;
  out.pan_deg = pan_deg_;
  if (shore_elapsed_ms_ < cfg_.shore_drive_ms) {
    out.track_l = cfg_.track_speed;
    out.track_r = cfg_.track_speed;
    shore_elapsed_ms_ = addSat(shore_elapsed_ms_, dt_ms);
  } else {
    mission_complete_ = true;  // tracks stay at 0; we stay in SHORE
  }
}

void StateMachine::stepSafe(Outputs& out) {
  out.state = State::SAFE;
  out.arm_deg = arm_hold_deg_;  // hold the angle the arm had when SAFE was entered
  out.buzzer = true;
}

}  // namespace armini
