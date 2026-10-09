// AR-Mini · host tests for lib/core/Safety (Unity, `pio test -e native`).
// Entry points (called from test_main.cpp): safetySetUp(), runSafetyTests().
#include <unity.h>
#include <stdint.h>
#include "Safety.h"
#include "StateMachine.h"

using namespace armini;

// ---------------------------------------------------------------------------
// fixtures

static const uint32_t DT = 100;      // ms per tick (10 Hz, same as main.cpp)
static const uint32_t T0 = 5000;     // first tick time; not 0 so "since" maths is exercised
static const float    kVfull = 12.6f;  // simulated full 3S pack (3 × 4.2 V). Fake value, not a measurement.
static SafetyConfig scfg;            // fresh defaults for every test

void safetySetUp() { scfg = SafetyConfig(); }

// Nominal inputs: dry, not killed, full battery, heartbeat alive, no ladder.
static SafetyInputs nominal() {
  SafetyInputs s;
  s.v_bat = kVfull;
  return s;
}

// Tick `ms` worth of time in DT steps, starting at *t (advanced on return).
// Returns the last verdict.
static Verdict runFor(Safety& s, const SafetyInputs& in, uint32_t ms, uint32_t* t) {
  Verdict v;
  for (uint32_t done = 0; done < ms; done += DT) {
    *t += DT;
    v = s.tick(in, *t);
  }
  return v;
}

static void assertSafe(const Verdict& v) {
  TEST_ASSERT_TRUE(v.safe);
  TEST_ASSERT_EQUAL(SafetyReason::NONE, v.reason);
}

static void assertTripped(const Verdict& v, SafetyReason why) {
  TEST_ASSERT_FALSE(v.safe);
  TEST_ASSERT_EQUAL(why, v.reason);
}

// ---------------------------------------------------------------------------
// 1. leak debounce: 50 ms splash does not trip, 100 ms does

void test_leak_splash_no_trip_then_100ms_trips() {
  Safety s(scfg);
  uint32_t t = T0;
  SafetyInputs wet = nominal();
  wet.leak_raw = true;

  // t=T0 wet (timer starts), t=T0+50 wet (50 ms elapsed), then dry.
  assertSafe(s.tick(wet, t));
  t += 50;
  assertSafe(s.tick(wet, t));
  t += 50;
  assertSafe(s.tick(nominal(), t));
  assertSafe(runFor(s, nominal(), 1000, &t));

  // Continuous wet: 0, 50 → safe; 100 ms → trip, reason LEAK.
  t += DT;
  assertSafe(s.tick(wet, t));
  t += 50;
  assertSafe(s.tick(wet, t));
  t += 50;
  assertTripped(s.tick(wet, t), SafetyReason::LEAK);
  TEST_ASSERT_TRUE(s.tripped());
  TEST_ASSERT_EQUAL(SafetyReason::LEAK, s.active());
}

void test_leak_debounce_restarts_after_dry_tick() {
  Safety s(scfg);
  uint32_t t = T0;
  SafetyInputs wet = nominal();
  wet.leak_raw = true;
  // wet 90 ms, dry one tick, wet 90 ms: never continuously wet for 100 ms.
  for (int rep = 0; rep < 5; ++rep) {
    s.tick(wet, t); t += 45;
    s.tick(wet, t); t += 45;
    assertSafe(s.tick(wet, t)); t += 10;
    assertSafe(s.tick(nominal(), t)); t += DT;
  }
  assertSafe(s.verdict());
}

// ---------------------------------------------------------------------------
// 2. kill trips on the first tick it is seen (no debounce)

void test_kill_trips_immediately() {
  {
    Safety s(scfg);
    SafetyInputs k = nominal();
    k.kill_raw = true;
    assertTripped(s.tick(k, T0), SafetyReason::KILL);  // very first tick
  }
  {
    Safety s(scfg);
    uint32_t t = T0;
    assertSafe(runFor(s, nominal(), 1000, &t));
    SafetyInputs k = nominal();
    k.kill_raw = true;
    t += 1;  // 1 ms later, not even a full tick
    assertTripped(s.tick(k, t), SafetyReason::KILL);
  }
}

// ---------------------------------------------------------------------------
// 3. priority in the same tick: KILL > LEAK > BATTERY > HEARTBEAT

void test_priority_same_tick() {
  // kill + leak (+ everything else) in one tick → KILL
  {
    Safety s(scfg);
    SafetyInputs in = nominal();
    in.kill_raw = true;
    in.leak_raw = true;
    in.v_bat = 0.0f;
    in.heartbeat_ok = false;
    assertTripped(s.tick(in, T0), SafetyReason::KILL);
  }
  // Make all debounces equal so leak, battery and heartbeat trip in the same tick.
  scfg.leak_debounce_ms = scfg.batt_debounce_ms = scfg.heartbeat_timeout_ms = 100;
  {
    Safety s(scfg);
    SafetyInputs in = nominal();
    in.leak_raw = true;
    in.v_bat = scfg.v_trip - 0.1f;
    in.heartbeat_ok = false;
    assertSafe(s.tick(in, T0));
    assertTripped(s.tick(in, T0 + 100), SafetyReason::LEAK);
  }
  {
    Safety s(scfg);
    SafetyInputs in = nominal();
    in.v_bat = scfg.v_trip - 0.1f;
    in.heartbeat_ok = false;
    assertSafe(s.tick(in, T0));
    assertTripped(s.tick(in, T0 + 100), SafetyReason::BATTERY);
  }
  {
    Safety s(scfg);
    SafetyInputs in = nominal();
    in.heartbeat_ok = false;
    assertSafe(s.tick(in, T0));
    assertTripped(s.tick(in, T0 + 100), SafetyReason::HEARTBEAT);
  }
}

// ---------------------------------------------------------------------------
// 4. battery: one sample no trip; 600 ms trips; hysteresis blocks reset at 10.2 V

void test_battery_debounce_latch_hysteresis() {
  TEST_ASSERT_TRUE_MESSAGE(scfg.v_trip < 9.9f + 1e-3f && scfg.v_trip > 9.9f - 1e-3f, "test assumes v_trip 9.9 V");
  TEST_ASSERT_TRUE_MESSAGE(scfg.v_reset < 10.5f + 1e-3f && scfg.v_reset > 10.5f - 1e-3f, "test assumes v_reset 10.5 V");

  Safety s(scfg);
  uint32_t t = T0;
  SafetyInputs low = nominal();
  low.v_bat = 9.8f;

  // one bad sample, then back to full → nothing
  assertSafe(s.tick(low, t));
  assertSafe(runFor(s, nominal(), 1000, &t));

  // 9.8 V for 600 ms → trip, reason BATTERY (exactly at 500 ms elapsed)
  t += DT;
  assertSafe(s.tick(low, t));                 // elapsed 0
  assertSafe(runFor(s, low, 400, &t));        // elapsed 400
  assertTripped(runFor(s, low, DT, &t), SafetyReason::BATTERY);  // elapsed 500
  runFor(s, low, 100, &t);                    // 600 ms total, still tripped
  assertTripped(s.verdict(), SafetyReason::BATTERY);

  // rises to 10.2 V (between trip and reset) → still tripped, reset refused
  SafetyInputs mid = nominal();
  mid.v_bat = 10.2f;
  assertTripped(runFor(s, mid, 1000, &t), SafetyReason::BATTERY);
  TEST_ASSERT_EQUAL(SafetyReason::BATTERY, s.active());  // hysteresis keeps the cause alive
  TEST_ASSERT_FALSE(s.reset());
  assertTripped(s.verdict(), SafetyReason::BATTERY);

  // 10.6 V → cause clears, latch still holds, reset accepted
  SafetyInputs high = nominal();
  high.v_bat = 10.6f;
  assertTripped(runFor(s, high, 300, &t), SafetyReason::BATTERY);
  TEST_ASSERT_EQUAL(SafetyReason::NONE, s.active());
  TEST_ASSERT_TRUE(s.reset());
  assertSafe(s.verdict());
  assertSafe(runFor(s, high, 300, &t));

  // after the reset the debounce starts from zero again
  t += DT;
  assertSafe(s.tick(low, t));
  assertSafe(runFor(s, low, 400, &t));
  assertTripped(runFor(s, low, DT, &t), SafetyReason::BATTERY);
}

void test_battery_dip_between_thresholds_before_trip_resets_debounce() {
  // Not yet tripped: hysteresis does not apply, a sample >= v_trip restarts the timer.
  Safety s(scfg);
  uint32_t t = T0;
  SafetyInputs low = nominal();
  low.v_bat = scfg.v_trip - 0.2f;
  SafetyInputs mid = nominal();
  mid.v_bat = scfg.v_trip;  // not below v_trip
  for (int rep = 0; rep < 5; ++rep) {
    assertSafe(runFor(s, low, 400, &t));
    assertSafe(runFor(s, mid, DT, &t));
  }
}

// ---------------------------------------------------------------------------
// 5. heartbeat: false 400 ms ok, 500 ms trips

void test_heartbeat_timeout() {
  Safety s(scfg);
  uint32_t t = T0;
  SafetyInputs dead = nominal();
  dead.heartbeat_ok = false;

  assertSafe(s.tick(dead, t));                 // elapsed 0
  assertSafe(runFor(s, dead, 400, &t));        // elapsed 400 → ok
  assertTripped(runFor(s, dead, DT, &t), SafetyReason::HEARTBEAT);  // elapsed 500

  // A heartbeat that returns in time never trips.
  Safety s2(scfg);
  t = T0;
  for (int rep = 0; rep < 10; ++rep) {
    assertSafe(runFor(s2, dead, 400, &t));
    assertSafe(runFor(s2, nominal(), DT, &t));
  }
}

// ---------------------------------------------------------------------------
// 6. latch: cause clears, verdict stays unsafe until reset(); reason is frozen

void test_latch_until_reset() {
  Safety s(scfg);
  uint32_t t = T0;
  SafetyInputs wet = nominal();
  wet.leak_raw = true;

  assertTripped(runFor(s, wet, 200, &t), SafetyReason::LEAK);
  TEST_ASSERT_FALSE(s.reset());  // cause still active

  // dry for 5 s: still unsafe, reason LEAK
  assertTripped(runFor(s, nominal(), 5000, &t), SafetyReason::LEAK);
  TEST_ASSERT_EQUAL(SafetyReason::NONE, s.active());

  // a later, higher-priority cause does not rewrite the latched reason
  SafetyInputs k = nominal();
  k.kill_raw = true;
  assertTripped(runFor(s, k, DT, &t), SafetyReason::LEAK);
  TEST_ASSERT_EQUAL(SafetyReason::KILL, s.active());
  TEST_ASSERT_FALSE(s.reset());  // kill active → refused

  assertTripped(runFor(s, nominal(), DT, &t), SafetyReason::LEAK);
  TEST_ASSERT_TRUE(s.reset());
  assertSafe(s.verdict());
  TEST_ASSERT_FALSE(s.reset());  // nothing to reset
  assertSafe(runFor(s, nominal(), 1000, &t));
}

// ---------------------------------------------------------------------------
// 7. integration: Safety verdict drives the StateMachine (SEARCH + leak → SAFE)

void test_verdict_feeds_state_machine() {
  Config mcfg;
  StateMachine sm(mcfg);
  Safety s(scfg);
  uint32_t t = T0;

  Inputs in;
  in.armed = true;
  in.arm_deg = mcfg.arm_stow_deg;
  in.target_range_m = 100.0f;

  // one tick dry: IDLE → SEARCH
  applyVerdict(s.tick(nominal(), t), in);
  sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::SEARCH, sm.state());

  // leak 50 ms: still SEARCH
  SafetyInputs wet = nominal();
  wet.leak_raw = true;
  t += DT;
  applyVerdict(s.tick(wet, t), in);
  sm.tick(in, DT);
  t += 50;
  applyVerdict(s.tick(wet, t), in);
  Outputs o = sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::SEARCH, o.state);
  TEST_ASSERT_FALSE(in.leak);

  // leak 100 ms: SAFE, reason LEAK, in the same tick
  t += 50;
  applyVerdict(s.tick(wet, t), in);
  TEST_ASSERT_TRUE(in.leak);
  TEST_ASSERT_FALSE(in.kill || in.battery_low || in.heartbeat_lost);
  o = sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::SAFE, o.state);
  TEST_ASSERT_EQUAL(SafeReason::LEAK, o.reason);
  TEST_ASSERT_TRUE(o.buzzer);

  // dry again: both stay latched; reset order as in main.cpp
  // (safety.reset() before the state-machine tick, sm.reset() after it).
  t += DT;
  applyVerdict(s.tick(nominal(), t), in);
  TEST_ASSERT_TRUE(in.leak);  // still latched → the state machine keeps seeing the cause
  sm.tick(in, DT);
  TEST_ASSERT_FALSE(sm.reset());

  t += DT;
  Verdict v = s.tick(nominal(), t);
  TEST_ASSERT_TRUE(s.reset());
  v = s.verdict();
  applyVerdict(v, in);
  TEST_ASSERT_FALSE(in.leak);
  o = sm.tick(in, DT);
  TEST_ASSERT_EQUAL(State::SAFE, o.state);  // this tick's outputs are still SAFE
  TEST_ASSERT_TRUE(sm.reset());
  TEST_ASSERT_EQUAL(State::IDLE, sm.state());

  // heartbeat path reaches the state machine with its own reason
  SafetyInputs dead = nominal();
  dead.heartbeat_ok = false;
  for (int i = 0; i < 6; ++i) {  // 0..500 ms
    t += DT;
    applyVerdict(s.tick(dead, t), in);
    o = sm.tick(in, DT);
  }
  TEST_ASSERT_EQUAL(State::SAFE, o.state);
  TEST_ASSERT_EQUAL(SafeReason::HEARTBEAT, o.reason);
}

// ---------------------------------------------------------------------------
// 8. ladder path and boolean path give the same verdicts

void test_ladder_and_boolean_paths_agree() {
  Safety viaBool(scfg), viaLadder(scfg), viaBoth(scfg);
  uint32_t lcg = 777u;
  uint32_t t = T0;
  int trips = 0;
  for (int i = 0; i < 3000; ++i) {
    lcg = lcg * 1664525u + 1013904223u;
    const bool leak = ((lcg >> 5) % 4) == 0;
    const bool kill = ((lcg >> 9) % 60) == 0;
    const float v_bat = kVfull - static_cast<float>((lcg >> 13) % 40) / 10.0f;  // 8.7..12.6
    const bool hb = ((lcg >> 19) % 9) != 0;
    const uint32_t dt = 20 + ((lcg >> 2) % 150);
    t += dt;

    SafetyInputs b = nominal();
    b.leak_raw = leak;
    b.kill_raw = kill;
    b.v_bat = v_bat;
    b.heartbeat_ok = hb;

    SafetyInputs l = b;
    l.leak_raw = false;
    l.kill_raw = false;
    l.ladder_v = ladderVoltage(leak, kill);

    SafetyInputs both = b;          // booleans AND the ladder say the same thing
    both.ladder_v = l.ladder_v;

    const Verdict vb = viaBool.tick(b, t);
    const Verdict vl = viaLadder.tick(l, t);
    const Verdict v2 = viaBoth.tick(both, t);
    TEST_ASSERT_EQUAL_MESSAGE(vb.safe, vl.safe, "ladder vs bool: safe diverged");
    TEST_ASSERT_EQUAL_MESSAGE(vb.reason, vl.reason, "ladder vs bool: reason diverged");
    TEST_ASSERT_EQUAL(vb.safe, v2.safe);
    TEST_ASSERT_EQUAL(vb.reason, v2.reason);
    TEST_ASSERT_EQUAL(viaBool.active(), viaLadder.active());

    if (!vb.safe) ++trips;
    if ((i % 23) == 0) {
      const bool rb = viaBool.reset();
      const bool rl = viaLadder.reset();
      const bool r2 = viaBoth.reset();
      TEST_ASSERT_EQUAL(rb, rl);
      TEST_ASSERT_EQUAL(rb, r2);
    }
  }
  TEST_ASSERT_TRUE_MESSAGE(trips > 0, "random sequence never tripped; test is vacuous");
}

void test_ladder_ors_into_booleans() {
  // ladder says LEAK while leak_raw is false → leak (debounced) trips
  {
    Safety s(scfg);
    uint32_t t = T0;
    SafetyInputs in = nominal();
    in.ladder_v = 1.06f;
    assertSafe(s.tick(in, t));
    assertTripped(runFor(s, in, DT, &t), SafetyReason::LEAK);
  }
  // ladder says KILL → immediate
  {
    Safety s(scfg);
    SafetyInputs in = nominal();
    in.ladder_v = 0.30f;
    assertTripped(s.tick(in, T0), SafetyReason::KILL);
  }
  // ladder open but boolean kill → still KILL (OR, not override)
  {
    Safety s(scfg);
    SafetyInputs in = nominal();
    in.ladder_v = 3.30f;
    in.kill_raw = true;
    assertTripped(s.tick(in, T0), SafetyReason::KILL);
  }
  // ladder not fitted (negative) is ignored
  {
    Safety s(scfg);
    uint32_t t = T0;
    SafetyInputs in = nominal();
    in.ladder_v = -1.0f;
    assertSafe(runFor(s, in, 2000, &t));
  }
}

// ---------------------------------------------------------------------------
// extras: determinism, VBAT divider helper, time wrap

void test_safety_determinism() {
  Safety a(scfg), b(scfg);
  uint32_t lcg = 4242u;
  uint32_t t = T0;
  for (int i = 0; i < 3000; ++i) {
    lcg = lcg * 1664525u + 1013904223u;
    SafetyInputs in;
    in.leak_raw = ((lcg >> 4) % 5) == 0;
    in.kill_raw = ((lcg >> 8) % 80) == 0;
    in.v_bat = 8.0f + static_cast<float>((lcg >> 12) % 50) / 10.0f;
    in.heartbeat_ok = ((lcg >> 18) % 8) != 0;
    in.ladder_v = (((lcg >> 22) & 1u) != 0) ? -1.0f : static_cast<float>((lcg >> 23) % 34) / 10.0f;
    t += 20 + ((lcg >> 1) % 150);
    const Verdict va = a.tick(in, t);
    const Verdict vb = b.tick(in, t);
    TEST_ASSERT_EQUAL(va.safe, vb.safe);
    TEST_ASSERT_EQUAL(va.reason, vb.reason);
    if ((i % 31) == 0) TEST_ASSERT_EQUAL(a.reset(), b.reset());
  }
}

void test_vbat_divider() {
  // 100 k / 33 k: 12.6 V at the pack → 12.6 × 33 / 133 = 3.126 V at the ADC.
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 12.6f, vbatFromAdc(3.126f));
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 9.9f, vbatFromAdc(9.9f * 33.0f / 133.0f));
}

void test_time_wrap_does_not_break_debounce() {
  Safety s(scfg);
  uint32_t t = UINT32_MAX - 150;  // millis() about to wrap
  SafetyInputs wet = nominal();
  wet.leak_raw = true;
  assertSafe(s.tick(wet, t));
  t += 100;  // 0xFFFFFFCD
  assertTripped(s.tick(wet, t), SafetyReason::LEAK);

  Safety s2(scfg);
  t = UINT32_MAX - 30;
  assertSafe(s2.tick(wet, t));
  t += 60;  // wrapped to 29
  assertSafe(s2.tick(wet, t));   // 60 ms elapsed
  t += 40;
  assertTripped(s2.tick(wet, t), SafetyReason::LEAK);  // 100 ms elapsed across the wrap
}

// ---------------------------------------------------------------------------

void runSafetyTests() {
  RUN_TEST(test_leak_splash_no_trip_then_100ms_trips);
  RUN_TEST(test_leak_debounce_restarts_after_dry_tick);
  RUN_TEST(test_kill_trips_immediately);
  RUN_TEST(test_priority_same_tick);
  RUN_TEST(test_battery_debounce_latch_hysteresis);
  RUN_TEST(test_battery_dip_between_thresholds_before_trip_resets_debounce);
  RUN_TEST(test_heartbeat_timeout);
  RUN_TEST(test_latch_until_reset);
  RUN_TEST(test_verdict_feeds_state_machine);
  RUN_TEST(test_ladder_and_boolean_paths_agree);
  RUN_TEST(test_ladder_ors_into_booleans);
  RUN_TEST(test_safety_determinism);
  RUN_TEST(test_vbat_divider);
  RUN_TEST(test_time_wrap_does_not_break_debounce);
}
