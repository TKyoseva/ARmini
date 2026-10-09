// AR-Mini · host tests for lib/core/StateMachine (Unity, `pio test -e native`).
// Entry points (called from test_main.cpp): stateMachineSetUp(), runStateMachineTests().
#include <unity.h>
#include <stdint.h>
#include "StateMachine.h"

using namespace armini;

// ---------------------------------------------------------------------------
// fixtures

static const uint32_t DT = 100;  // ms per tick (10 Hz, same as main.cpp)
static Config cfg;               // default Config, fresh for every test

void stateMachineSetUp() { cfg = Config(); }

// Nominal inputs: armed, arm stowed, no target, no faults.
static Inputs base() {
  Inputs in;
  in.armed = true;
  in.arm_deg = cfg.arm_stow_deg;
  in.target_range_m = 100.0f;  // far away
  return in;
}

static Inputs seen(float bearing = 0.0f, float range = 10.0f) {
  Inputs in = base();
  in.target_seen = true;
  in.bearing_deg = bearing;
  in.target_range_m = range;
  return in;
}

static Outputs run(StateMachine& sm, const Inputs& in, int ticks) {
  Outputs out;
  for (int i = 0; i < ticks; ++i) out = sm.tick(in, DT);
  return out;
}

// Script the inputs so that `sm` (fresh, in IDLE) ends in `target`.
// Each transition takes effect at the end of the tick that decides it.
static void driveTo(StateMachine& sm, State target) {
  if (target == State::IDLE) return;
  sm.tick(base(), DT);  // IDLE -> SEARCH
  if (target == State::SEARCH) return;
  run(sm, seen(), cfg.sightings_to_confirm);  // SEARCH -> APPROACH
  if (target == State::APPROACH) return;
  Inputs in = seen(0.0f, cfg.deploy_range_m);
  in.cradle_confirmed = true;
  sm.tick(in, DT);  // APPROACH -> DEPLOY
  if (target == State::DEPLOY) return;
  in = base();
  in.arm_deg = cfg.arm_deploy_deg;
  sm.tick(in, DT);  // DEPLOY -> LIFT
  if (target == State::LIFT) return;
  in = base();
  in.arm_deg = cfg.arm_stow_deg;
  in.load_detected = true;
  sm.tick(in, DT);  // LIFT -> STOW
  if (target == State::STOW) return;
  in = base();
  in.tilt_deg = cfg.shore_tilt_deg;
  sm.tick(in, DT);  // STOW -> SHORE
  if (target == State::SHORE) return;
  in = base();
  in.leak = true;
  sm.tick(in, DT);  // -> SAFE
}

static void assertActuatorsZero(const Outputs& o) {
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.thrust_l);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.thrust_r);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.track_l);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.track_r);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.pan_deg);
}

static bool outputsEqual(const Outputs& a, const Outputs& b) {
  return a.state == b.state && a.reason == b.reason && a.thrust_l == b.thrust_l &&
         a.thrust_r == b.thrust_r && a.track_l == b.track_l && a.track_r == b.track_r &&
         a.arm_deg == b.arm_deg && a.pan_deg == b.pan_deg && a.buzzer == b.buzzer &&
         a.led_green == b.led_green && a.led_yellow == b.led_yellow && a.led_red == b.led_red &&
         a.flags.no_load == b.flags.no_load && a.flags.mission_complete == b.flags.mission_complete;
}

// ---------------------------------------------------------------------------
// 1. starts in IDLE; armed -> SEARCH

void test_starts_idle_and_arms_to_search() {
  StateMachine sm(cfg);
  TEST_ASSERT_EQUAL(State::IDLE, sm.state());

  Inputs in = base();
  in.armed = false;
  Outputs o = run(sm, in, 5);
  TEST_ASSERT_EQUAL(State::IDLE, sm.state());
  TEST_ASSERT_EQUAL(State::IDLE, o.state);
  assertActuatorsZero(o);
  TEST_ASSERT_FALSE(o.buzzer);

  sm.tick(base(), DT);
  TEST_ASSERT_EQUAL(State::SEARCH, sm.state());
}

// ---------------------------------------------------------------------------
// 2. SEARCH -> APPROACH after exactly N consecutive sightings; a miss resets

void test_search_needs_n_consecutive_sightings() {
  const uint16_t N = cfg.sightings_to_confirm;
  TEST_ASSERT_TRUE_MESSAGE(N >= 2, "test needs sightings_to_confirm >= 2");

  StateMachine sm(cfg);
  driveTo(sm, State::SEARCH);

  run(sm, seen(), N - 1);
  TEST_ASSERT_EQUAL(State::SEARCH, sm.state());  // N-1 is not enough
  sm.tick(base(), DT);                           // miss -> counter resets
  run(sm, seen(), N - 1);
  TEST_ASSERT_EQUAL(State::SEARCH, sm.state());  // still N-1 after the reset
  sm.tick(seen(), DT);                           // the N-th consecutive one
  TEST_ASSERT_EQUAL(State::APPROACH, sm.state());
}

void test_search_exactly_n_sightings() {
  StateMachine sm(cfg);
  driveTo(sm, State::SEARCH);
  for (uint16_t i = 1; i < cfg.sightings_to_confirm; ++i) {
    sm.tick(seen(), DT);
    TEST_ASSERT_EQUAL(State::SEARCH, sm.state());
  }
  Outputs o = sm.tick(seen(), DT);
  TEST_ASSERT_EQUAL(State::APPROACH, sm.state());
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.thrust_l);  // thrust 0 while still in SEARCH
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.thrust_r);
}

void test_search_pan_sweeps_within_limits() {
  StateMachine sm(cfg);
  driveTo(sm, State::SEARCH);
  float lo = 1e9f, hi = -1e9f;
  for (int i = 0; i < 400; ++i) {  // 40 s, several sweeps at 30 deg/s
    Outputs o = sm.tick(base(), DT);
    if (o.pan_deg < lo) lo = o.pan_deg;
    if (o.pan_deg > hi) hi = o.pan_deg;
  }
  TEST_ASSERT_FLOAT_WITHIN(0.01f, cfg.pan_min_deg, lo);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, cfg.pan_max_deg, hi);
}

// ---------------------------------------------------------------------------
// 3. APPROACH -> SEARCH after loss timeout; sighting counter resets

void test_approach_loss_timeout_back_to_search() {
  StateMachine sm(cfg);
  driveTo(sm, State::APPROACH);

  const int lossTicks = static_cast<int>(cfg.loss_timeout_ms / DT);
  run(sm, base(), lossTicks - 1);
  TEST_ASSERT_EQUAL(State::APPROACH, sm.state());  // one tick short
  sm.tick(base(), DT);
  TEST_ASSERT_EQUAL(State::SEARCH, sm.state());

  // Counter was reset: N-1 sightings are not enough again.
  run(sm, seen(), cfg.sightings_to_confirm - 1);
  TEST_ASSERT_EQUAL(State::SEARCH, sm.state());
  sm.tick(seen(), DT);
  TEST_ASSERT_EQUAL(State::APPROACH, sm.state());
}

void test_approach_sighting_resets_loss_timer() {
  StateMachine sm(cfg);
  driveTo(sm, State::APPROACH);
  const int lossTicks = static_cast<int>(cfg.loss_timeout_ms / DT);
  run(sm, base(), lossTicks - 1);
  sm.tick(seen(), DT);  // one sighting resets the timer
  run(sm, base(), lossTicks - 1);
  TEST_ASSERT_EQUAL(State::APPROACH, sm.state());
}

// ---------------------------------------------------------------------------
// 4. APPROACH -> DEPLOY needs both range and cradle confirmation

void test_deploy_needs_range_and_cradle() {
  // a) in range, no cradle confirmation
  {
    StateMachine sm(cfg);
    driveTo(sm, State::APPROACH);
    Inputs in = seen(0.0f, cfg.deploy_range_m);
    in.cradle_confirmed = false;
    run(sm, in, 5);
    TEST_ASSERT_EQUAL(State::APPROACH, sm.state());
  }
  // b) cradle confirmed, still too far
  {
    StateMachine sm(cfg);
    driveTo(sm, State::APPROACH);
    Inputs in = seen(0.0f, cfg.deploy_range_m * 2.0f + 1.0f);
    in.cradle_confirmed = true;
    run(sm, in, 5);
    TEST_ASSERT_EQUAL(State::APPROACH, sm.state());
  }
  // c) both
  {
    StateMachine sm(cfg);
    driveTo(sm, State::APPROACH);
    Inputs in = seen(0.0f, cfg.deploy_range_m);
    in.cradle_confirmed = true;
    sm.tick(in, DT);
    TEST_ASSERT_EQUAL(State::DEPLOY, sm.state());
  }
}

// ---------------------------------------------------------------------------
// 5. full happy path with scripted inputs

void test_happy_path() {
  StateMachine sm(cfg);
  Outputs o;

  TEST_ASSERT_EQUAL(State::IDLE, sm.state());
  sm.tick(base(), DT);
  TEST_ASSERT_EQUAL(State::SEARCH, sm.state());

  run(sm, seen(), cfg.sightings_to_confirm);
  TEST_ASSERT_EQUAL(State::APPROACH, sm.state());

  // approach thrust: forward + differential from bearing
  o = sm.tick(seen(10.0f, 5.0f), DT);
  TEST_ASSERT_EQUAL(State::APPROACH, o.state);
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, cfg.approach_thrust + cfg.k_bearing * 10.0f, o.thrust_l);
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, cfg.approach_thrust - cfg.k_bearing * 10.0f, o.thrust_r);
  TEST_ASSERT_EQUAL_FLOAT(cfg.arm_stow_deg, o.arm_deg);

  Inputs in = seen(0.0f, cfg.deploy_range_m);
  in.cradle_confirmed = true;
  sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::DEPLOY, sm.state());

  // DEPLOY: thrust 0, arm commanded to deploy; stays until the arm gets there
  in = base();
  in.arm_deg = cfg.arm_stow_deg;
  o = run(sm, in, 3);
  TEST_ASSERT_EQUAL(State::DEPLOY, sm.state());
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.thrust_l);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.thrust_r);
  TEST_ASSERT_EQUAL_FLOAT(cfg.arm_deploy_deg, o.arm_deg);
  in.arm_deg = cfg.arm_deploy_deg - cfg.arm_tol_deg;  // just inside tolerance
  sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::LIFT, sm.state());

  // LIFT: arm commanded to stow
  o = sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::LIFT, o.state);
  TEST_ASSERT_EQUAL_FLOAT(cfg.arm_stow_deg, o.arm_deg);
  in.arm_deg = cfg.arm_stow_deg;
  in.load_detected = true;
  sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::STOW, sm.state());

  // STOW: hold arm, drive toward shore heading, no no_load flag
  in = base();
  in.heading_deg = cfg.shore_heading_deg;
  o = sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::STOW, o.state);
  TEST_ASSERT_FALSE(o.flags.no_load);
  TEST_ASSERT_EQUAL_FLOAT(cfg.arm_stow_deg, o.arm_deg);
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, cfg.stow_thrust, o.thrust_l);
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, cfg.stow_thrust, o.thrust_r);
  in.tilt_deg = cfg.shore_tilt_deg;
  sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::SHORE, sm.state());

  // SHORE: thrust 0, tracks on for shore_drive_ms, then off + mission_complete
  in = base();
  const int driveTicks = static_cast<int>(cfg.shore_drive_ms / DT);
  for (int i = 0; i < driveTicks; ++i) {
    o = sm.tick(in, DT);
    TEST_ASSERT_EQUAL(State::SHORE, o.state);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, o.thrust_l);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, o.thrust_r);
    TEST_ASSERT_EQUAL_FLOAT(cfg.track_speed, o.track_l);
    TEST_ASSERT_EQUAL_FLOAT(cfg.track_speed, o.track_r);
    TEST_ASSERT_FALSE(o.flags.mission_complete);
  }
  o = sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::SHORE, sm.state());
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.track_l);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.track_r);
  TEST_ASSERT_TRUE(o.flags.mission_complete);
  o = run(sm, in, 20);  // stays
  TEST_ASSERT_EQUAL(State::SHORE, o.state);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, o.track_l);
  TEST_ASSERT_TRUE(o.flags.mission_complete);
}

void test_lift_without_load_sets_no_load_flag() {
  StateMachine sm(cfg);
  driveTo(sm, State::LIFT);
  Inputs in = base();
  in.arm_deg = cfg.arm_stow_deg;
  in.load_detected = false;
  sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::STOW, sm.state());  // goes to STOW anyway
  Outputs o = sm.tick(in, DT);
  TEST_ASSERT_TRUE(o.flags.no_load);
}

// ---------------------------------------------------------------------------
// 6. SAFE from each of the 7 states on leak

void test_safe_on_leak_from_every_state() {
  const State states[] = {State::IDLE,  State::SEARCH, State::APPROACH, State::DEPLOY,
                          State::LIFT,  State::STOW,   State::SHORE};
  for (size_t i = 0; i < sizeof(states) / sizeof(states[0]); ++i) {
    StateMachine sm(cfg);
    driveTo(sm, states[i]);
    TEST_ASSERT_EQUAL_MESSAGE(states[i], sm.state(), stateName(states[i]));

    Inputs in = base();
    in.armed = (states[i] != State::IDLE);
    in.leak = true;
    Outputs o = sm.tick(in, DT);
    TEST_ASSERT_EQUAL_MESSAGE(State::SAFE, sm.state(), stateName(states[i]));
    TEST_ASSERT_EQUAL_MESSAGE(State::SAFE, o.state, stateName(states[i]));
    TEST_ASSERT_EQUAL_MESSAGE(SafeReason::LEAK, o.reason, stateName(states[i]));
    TEST_ASSERT_TRUE(o.buzzer);
  }
}

// ---------------------------------------------------------------------------
// 7. SAFE on kill / battery_low / disarm with the right reason

void test_safe_reasons() {
  {
    StateMachine sm(cfg);
    driveTo(sm, State::SEARCH);
    Inputs in = base();
    in.kill = true;
    sm.tick(in, DT);
    TEST_ASSERT_EQUAL(State::SAFE, sm.state());
    TEST_ASSERT_EQUAL(SafeReason::KILL, sm.reason());
  }
  {
    StateMachine sm(cfg);
    driveTo(sm, State::APPROACH);
    Inputs in = base();
    in.battery_low = true;
    sm.tick(in, DT);
    TEST_ASSERT_EQUAL(State::SAFE, sm.state());
    TEST_ASSERT_EQUAL(SafeReason::BATTERY, sm.reason());
  }
  {
    StateMachine sm(cfg);
    driveTo(sm, State::LIFT);
    Inputs in = base();
    in.heartbeat_lost = true;  // T2: fed from the Safety verdict
    sm.tick(in, DT);
    TEST_ASSERT_EQUAL(State::SAFE, sm.state());
    TEST_ASSERT_EQUAL(SafeReason::HEARTBEAT, sm.reason());
  }
  {
    StateMachine sm(cfg);
    driveTo(sm, State::STOW);
    Inputs in = base();
    in.armed = false;
    sm.tick(in, DT);
    TEST_ASSERT_EQUAL(State::SAFE, sm.state());
    TEST_ASSERT_EQUAL(SafeReason::DISARM, sm.reason());
  }
  {
    // priority when several trip at once: KILL > LEAK > BATTERY > HEARTBEAT > DISARM
    StateMachine sm(cfg);
    driveTo(sm, State::SEARCH);
    Inputs in = base();
    in.kill = in.leak = in.battery_low = in.heartbeat_lost = true;
    in.armed = false;
    sm.tick(in, DT);
    TEST_ASSERT_EQUAL(SafeReason::KILL, sm.reason());
  }
  {
    StateMachine sm(cfg);
    driveTo(sm, State::SEARCH);
    Inputs in = base();
    in.heartbeat_lost = true;
    in.armed = false;
    sm.tick(in, DT);
    TEST_ASSERT_EQUAL(SafeReason::HEARTBEAT, sm.reason());  // HEARTBEAT beats DISARM
  }
  {
    // IDLE is the not-armed state: !armed alone does not trip SAFE there
    StateMachine sm(cfg);
    Inputs in = base();
    in.armed = false;
    run(sm, in, 10);
    TEST_ASSERT_EQUAL(State::IDLE, sm.state());
  }
}

// ---------------------------------------------------------------------------
// 8. outputs zero in SAFE, buzzer on, arm held

void test_safe_outputs() {
  StateMachine sm(cfg);
  driveTo(sm, State::SHORE);  // tracks were running
  Inputs in = base();
  in.arm_deg = 123.0f;  // whatever the arm reads when the fault hits
  in.leak = true;
  Outputs o = sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::SAFE, o.state);
  assertActuatorsZero(o);
  TEST_ASSERT_TRUE(o.buzzer);
  TEST_ASSERT_TRUE(o.led_red);
  TEST_ASSERT_FALSE(o.led_green);
  TEST_ASSERT_EQUAL_FLOAT(123.0f, o.arm_deg);  // hold where it was

  in.arm_deg = 90.0f;  // arm sags: target stays latched
  o = run(sm, in, 10);
  assertActuatorsZero(o);
  TEST_ASSERT_TRUE(o.buzzer);
  TEST_ASSERT_EQUAL_FLOAT(123.0f, o.arm_deg);
}

// ---------------------------------------------------------------------------
// 9. reset() ignored while a cause is active; works after it clears -> IDLE

void test_reset_latch() {
  StateMachine sm(cfg);
  driveTo(sm, State::APPROACH);
  Inputs in = base();
  in.leak = true;
  sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::SAFE, sm.state());

  TEST_ASSERT_FALSE(sm.reset());  // leak still active
  TEST_ASSERT_EQUAL(State::SAFE, sm.state());
  TEST_ASSERT_EQUAL(SafeReason::LEAK, sm.reason());

  in.leak = false;
  Outputs o = sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::SAFE, o.state);  // cause cleared, still latched
  TEST_ASSERT_TRUE(o.buzzer);

  TEST_ASSERT_TRUE(sm.reset());
  TEST_ASSERT_EQUAL(State::IDLE, sm.state());
  TEST_ASSERT_EQUAL(SafeReason::NONE, sm.reason());
  o = sm.tick(in, DT);  // armed -> SEARCH again, fresh mission
  TEST_ASSERT_EQUAL(State::SEARCH, sm.state());
  TEST_ASSERT_FALSE(o.flags.no_load);
  TEST_ASSERT_FALSE(o.flags.mission_complete);

  TEST_ASSERT_FALSE(sm.reset());  // reset outside SAFE does nothing
  TEST_ASSERT_EQUAL(State::SEARCH, sm.state());
}

// ---------------------------------------------------------------------------
// 10. clamping

void test_clamping_absurd_gains() {
  cfg.k_bearing = 1000.0f;
  cfg.approach_thrust = 50.0f;
  cfg.k_heading = -1000.0f;
  cfg.stow_thrust = -50.0f;
  cfg.track_speed = 7.0f;
  cfg.arm_deploy_deg = 999.0f;
  cfg.arm_tol_deg = 1e6f;  // so DEPLOY/LIFT still pass with any arm reading
  cfg.pan_max_deg = 1e4f;
  cfg.pan_rate_deg_s = 1e6f;

  StateMachine sm(cfg);
  driveTo(sm, State::SEARCH);
  Outputs o = sm.tick(base(), DT);
  TEST_ASSERT_TRUE(o.pan_deg <= 270.0f && o.pan_deg >= 0.0f);

  run(sm, seen(90.0f), cfg.sightings_to_confirm);
  o = sm.tick(seen(-90.0f), DT);
  TEST_ASSERT_EQUAL(State::APPROACH, o.state);
  TEST_ASSERT_TRUE(o.thrust_l >= -1.0f && o.thrust_l <= 1.0f);
  TEST_ASSERT_TRUE(o.thrust_r >= -1.0f && o.thrust_r <= 1.0f);

  Inputs in = seen(0.0f, cfg.deploy_range_m);
  in.cradle_confirmed = true;
  sm.tick(in, DT);
  o = sm.tick(base(), DT);  // DEPLOY output, then -> LIFT
  TEST_ASSERT_EQUAL(State::DEPLOY, o.state);
  TEST_ASSERT_TRUE(o.arm_deg <= 270.0f && o.arm_deg >= 0.0f);
  sm.tick(base(), DT);  // LIFT -> STOW
  in = base();
  in.heading_deg = 179.0f;
  o = sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::STOW, o.state);
  TEST_ASSERT_TRUE(o.thrust_l >= -1.0f && o.thrust_l <= 1.0f);
  TEST_ASSERT_TRUE(o.thrust_r >= -1.0f && o.thrust_r <= 1.0f);
  in.tilt_deg = cfg.shore_tilt_deg;
  sm.tick(in, DT);
  o = sm.tick(base(), DT);
  TEST_ASSERT_EQUAL(State::SHORE, o.state);
  TEST_ASSERT_EQUAL_FLOAT(1.0f, o.track_l);
  TEST_ASSERT_EQUAL_FLOAT(1.0f, o.track_r);
}

// ---------------------------------------------------------------------------
// 11. determinism: two instances, same input sequence -> identical outputs

void test_determinism() {
  StateMachine a(cfg), b(cfg);
  uint32_t lcg = 12345u;  // deterministic pseudo-random inputs
  for (int i = 0; i < 2000; ++i) {
    lcg = lcg * 1664525u + 1013904223u;
    Inputs in;
    in.armed = ((lcg >> 3) % 50) != 0;
    in.target_seen = ((lcg >> 7) % 3) != 0;
    in.bearing_deg = static_cast<float>((lcg >> 9) % 181) - 90.0f;
    in.target_range_m = static_cast<float>((lcg >> 11) % 40) / 10.0f;
    in.cradle_confirmed = ((lcg >> 13) % 4) == 0;
    in.arm_deg = static_cast<float>((lcg >> 15) % 271);
    in.load_detected = ((lcg >> 17) & 1u) != 0;
    in.tilt_deg = static_cast<float>((lcg >> 19) % 30);
    in.heading_deg = static_cast<float>((lcg >> 21) % 360);
    in.leak = ((lcg >> 23) % 97) == 0;
    in.kill = ((lcg >> 25) % 131) == 0;
    in.battery_low = ((lcg >> 27) % 113) == 0;
    in.heartbeat_lost = ((lcg >> 29) % 7) == 0;
    const uint32_t dt = 50 + ((lcg >> 2) % 100);

    Outputs oa = a.tick(in, dt);
    Outputs ob = b.tick(in, dt);
    TEST_ASSERT_TRUE_MESSAGE(outputsEqual(oa, ob), "outputs diverged");
    if ((i % 37) == 0) {
      bool ra = a.reset();
      bool rb = b.reset();
      TEST_ASSERT_EQUAL(ra, rb);
    }
  }
  TEST_ASSERT_EQUAL(a.state(), b.state());
}

// ---------------------------------------------------------------------------

void runStateMachineTests() {
  RUN_TEST(test_starts_idle_and_arms_to_search);
  RUN_TEST(test_search_needs_n_consecutive_sightings);
  RUN_TEST(test_search_exactly_n_sightings);
  RUN_TEST(test_search_pan_sweeps_within_limits);
  RUN_TEST(test_approach_loss_timeout_back_to_search);
  RUN_TEST(test_approach_sighting_resets_loss_timer);
  RUN_TEST(test_deploy_needs_range_and_cradle);
  RUN_TEST(test_happy_path);
  RUN_TEST(test_lift_without_load_sets_no_load_flag);
  RUN_TEST(test_safe_on_leak_from_every_state);
  RUN_TEST(test_safe_reasons);
  RUN_TEST(test_safe_outputs);
  RUN_TEST(test_reset_latch);
  RUN_TEST(test_clamping_absurd_gains);
  RUN_TEST(test_determinism);
}
