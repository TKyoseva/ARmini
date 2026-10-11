// AR-Mini · mission core · shared types.
// Pure C++11. No Arduino, no heap, no time source. Every physical number lives
// in Config with a // SOURCE: or // VERIFY: comment; nothing here is measured.
#pragma once
#include <stdint.h>

namespace armini {

// Mission states. Names fixed by the project (firmware/xiao skeleton + T1);
// IDLE added before SEARCH (powered, not armed).
enum class State : uint8_t { IDLE, SEARCH, APPROACH, DEPLOY, LIFT, STOW, SHORE, SAFE };
static const uint8_t kStateCount = 8;

// Why we are in SAFE. Priority when several trip in one tick:
// KILL > LEAK > BATTERY > HEARTBEAT > DISARM (same order as the T2 Safety module,
// which adds DISARM at the end because it is a mission condition, not a fault).
enum class SafeReason : uint8_t { NONE, LEAK, KILL, BATTERY, HEARTBEAT, DISARM };

inline const char* stateName(State s) {
  switch (s) {
    case State::IDLE:     return "IDLE";
    case State::SEARCH:   return "SEARCH";
    case State::APPROACH: return "APPROACH";
    case State::DEPLOY:   return "DEPLOY";
    case State::LIFT:     return "LIFT";
    case State::STOW:     return "STOW";
    case State::SHORE:    return "SHORE";
    case State::SAFE:     return "SAFE";
  }
  return "?";
}

inline const char* reasonName(SafeReason r) {
  switch (r) {
    case SafeReason::NONE:    return "NONE";
    case SafeReason::LEAK:    return "LEAK";
    case SafeReason::KILL:    return "KILL";
    case SafeReason::BATTERY:   return "BATTERY";
    case SafeReason::HEARTBEAT: return "HEARTBEAT";
    case SafeReason::DISARM:    return "DISARM";
  }
  return "?";
}

// Everything the mission logic reads each tick. The HAL fills it; the core
// never touches hardware. Units in the names.
struct Inputs {
  bool  armed            = false;  // arm switch / operator command
  bool  target_seen      = false;  // search camera (MLX90642-D45 on pan servo) sees a warm target
  float bearing_deg      = 0.0f;   // target bearing relative to the bow, + = starboard (right)
                                   // VERIFY: sign convention once the camera driver exists
  float target_range_m   = 0.0f;   // rough range to target (only meaningful when target_seen)
  bool  cradle_confirmed = false;  // cradle camera (MLX90640 110°) confirms target in cradle zone
  float arm_deg          = 0.0f;   // lift-arm angle from servo feedback (same frame as Config arm_*_deg)
  bool  load_detected    = false;  // something is in the cradle after the lift
  float tilt_deg         = 0.0f;   // IMU pitch, bow up positive (VERIFY: sign on the BNO055 mount)
  float heading_deg      = 0.0f;   // IMU yaw, 0..360
  // Safety causes. On the robot these four are NOT the raw sensors: main.cpp
  // fills them from the debounced, latched Safety verdict (applyVerdict() in
  // Safety.h), exactly one of them true while Safety is tripped. The state
  // machine treats them as plain booleans, so the host tests drive them directly.
  bool  leak             = false;  // Safety: leak probe wet for leak_debounce_ms
  bool  kill             = false;  // Safety: logic kill switch (no debounce)
  bool  battery_low      = false;  // Safety: v_bat < v_trip for batt_debounce_ms, hysteresis to v_reset
  bool  heartbeat_lost   = false;  // Safety: heartbeat_ok false for heartbeat_timeout_ms
};

struct Flags {
  bool no_load          = false;  // LIFT finished but load_detected was false
  bool mission_complete = false;  // SHORE drive finished
};

// Everything the mission logic commands each tick. Clamped before return:
// thrust/track in [-1, 1], angles in [angle_min_deg, angle_max_deg].
struct Outputs {
  State      state  = State::IDLE;
  SafeReason reason = SafeReason::NONE;
  float thrust_l = 0.0f;   // water thruster left,  -1..1
  float thrust_r = 0.0f;   // water thruster right, -1..1
  float track_l  = 0.0f;   // land track left,  -1..1
  float track_r  = 0.0f;   // land track right, -1..1
  float arm_deg  = 0.0f;   // lift-arm target angle
  float pan_deg  = 0.0f;   // search-camera pan target angle
  bool  buzzer   = false;
  bool  led_green  = false;  // status: powered and not in SAFE
  bool  led_yellow = false;  // armed: in a mission state (SEARCH..SHORE)
  bool  led_red    = false;  // fault: SAFE
  Flags flags;
};

// All tunables. Defaults are placeholders unless marked SOURCE.
struct Config {
  // --- SEARCH: pan sweep -------------------------------------------------
  float pan_min_deg    = 45.0f;    // VERIFY: mechanical range of the pan servo on the mast
  float pan_max_deg    = 135.0f;   // VERIFY
  float pan_rate_deg_s = 30.0f;    // VERIFY: sweep speed vs. MLX90642 frame rate

  // --- target confirmation ------------------------------------------------
  uint16_t sightings_to_confirm = 3;     // VERIFY: consecutive ticks with target_seen
  uint32_t loss_timeout_ms      = 2000;  // VERIFY: no target_seen for this long -> back to SEARCH

  // --- APPROACH ----------------------------------------------------------
  float approach_thrust = 0.30f;   // VERIFY: forward thrust while approaching, 0..1
  float k_bearing       = 0.02f;   // VERIFY: differential thrust per degree of bearing
  float deploy_range_m  = 0.50f;   // VERIFY: range at which the cradle can be lowered

  // --- lift arm ----------------------------------------------------------
  float arm_deploy_deg = 215.0f;   // SOURCE: cad/openscad/AR-Mini_v1.scad deploy_a (forward & 35° down)
  float arm_stow_deg   = 45.0f;    // SOURCE: cad/openscad/AR-Mini_v1.scad stow_a (aft & 45° up)
  float arm_tol_deg    = 5.0f;     // VERIFY: ST3215 feedback tolerance under load

  // --- STOW: drive toward shore -----------------------------------------
  float shore_heading_deg = 0.0f;  // VERIFY: compass heading of the ramp at the test site
  float k_heading         = 0.01f; // VERIFY: differential thrust per degree of heading error
  float stow_thrust       = 0.30f; // VERIFY: forward thrust while carrying the load
  float shore_tilt_deg    = 10.0f; // VERIFY: bow-up pitch that means "on the ramp"

  // --- SHORE: tracks -----------------------------------------------------
  float    track_speed    = 0.50f; // VERIFY: ROB0154 speed on the ramp, 0..1
  uint32_t shore_drive_ms = 3000;  // VERIFY: time to drive clear of the water

  // Battery thresholds live in SafetyConfig (Safety.h): v_trip / v_reset.

  // --- output limits -----------------------------------------------------
  float angle_min_deg = 0.0f;      // SOURCE: task T1 ("angles in [0, 270]"); VERIFY against servo range
  float angle_max_deg = 270.0f;
};

}  // namespace armini
