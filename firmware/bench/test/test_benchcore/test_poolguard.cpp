// Host tests for lib/benchcore/PoolGuard.h (card C076): leak and low-battery stops of env remote_pool.
// Linked into the same executable as test_benchcore.cpp, which calls runPoolGuardTests().
#include <unity.h>

#include "PoolGuard.h"

using bench::GuardStop;
using bench::PoolGuard;

static const float kDry = 3.10f;   // GPIO7 dry (ADC ceiling)
static const float kWet = 1.50f;   // probe in water
static const float kFull = 12.4f;  // pack voltage

// Run the guard for `ms` at a 50 ms tick with constant readings; returns the time after the last tick.
static uint32_t runFor(PoolGuard& g, float leak_v, float vbat_v, uint32_t t0, uint32_t ms) {
  uint32_t t = t0;
  for (; t <= t0 + ms; t += 50) g.tick(leak_v, vbat_v, t);
  return t;
}

static void test_guard_quiet_when_dry_and_full() {
  PoolGuard g;
  runFor(g, kDry, kFull, 0, 10000);
  TEST_ASSERT_TRUE(g.stop() == GuardStop::NONE);
  TEST_ASSERT_TRUE(g.tryClear());
}

static void test_guard_leak_threshold() {
  TEST_ASSERT_FALSE(bench::leakWet(3.10f));
  TEST_ASSERT_FALSE(bench::leakWet(2.60f));  // exactly at the threshold = dry
  TEST_ASSERT_TRUE(bench::leakWet(2.59f));
  TEST_ASSERT_TRUE(bench::leakWet(1.06f));   // probe shorted
  TEST_ASSERT_FALSE(bench::leakWet(-1.0f));  // not read yet
}

static void test_guard_short_splash_does_not_trip() {
  PoolGuard g;
  uint32_t t = runFor(g, kDry, kFull, 0, 1000);
  t = runFor(g, kWet, kFull, t, 150);  // 150 ms wet < 200 ms hold
  runFor(g, kDry, kFull, t, 1000);
  TEST_ASSERT_TRUE(g.stop() == GuardStop::NONE);
}

static void test_guard_leak_trips_after_hold_and_latches_for_good() {
  PoolGuard g;
  uint32_t t = runFor(g, kDry, kFull, 0, 1000);
  t = runFor(g, kWet, kFull, t, 250);
  TEST_ASSERT_TRUE(g.stop() == GuardStop::LEAK);
  TEST_ASSERT_EQUAL_STRING("leak", bench::guardStopName(g.stop()));
  runFor(g, kDry, kFull, t, 60000);   // box dried, a minute later
  TEST_ASSERT_TRUE(g.stop() == GuardStop::LEAK);
  TEST_ASSERT_FALSE(g.tryClear());     // only a power cycle clears it
  TEST_ASSERT_TRUE(g.stop() == GuardStop::LEAK);
}

static void test_guard_lowbatt_needs_5_s_below_10_5() {
  PoolGuard g;
  uint32_t t = runFor(g, kDry, kFull, 0, 1000);
  t = runFor(g, kDry, 10.4f, t, 4800);  // 4.8 s below: not yet
  TEST_ASSERT_TRUE(g.stop() == GuardStop::NONE);
  runFor(g, kDry, 10.4f, t, 300);       // past 5 s
  TEST_ASSERT_TRUE(g.stop() == GuardStop::LOWBATT);
  TEST_ASSERT_EQUAL_STRING("lowbatt", bench::guardStopName(g.stop()));
}

static void test_guard_lowbatt_sag_shorter_than_hold_is_ignored() {
  PoolGuard g;
  uint32_t t = 0;
  for (int i = 0; i < 10; ++i) {        // 3 s sag under thrust, 1 s recovery, ten times
    t = runFor(g, kDry, 10.2f, t, 3000);
    t = runFor(g, kDry, 11.0f, t, 1000);
  }
  TEST_ASSERT_TRUE(g.stop() == GuardStop::NONE);
}

static void test_guard_lowbatt_rearm_only_above_10_8() {
  PoolGuard g;
  uint32_t t = runFor(g, kDry, 10.3f, 0, 6000);
  TEST_ASSERT_TRUE(g.stop() == GuardStop::LOWBATT);
  t = runFor(g, kDry, 10.7f, t, 2000);  // recovered a little: still in the hysteresis band
  TEST_ASSERT_FALSE(g.tryClear());
  TEST_ASSERT_TRUE(g.stop() == GuardStop::LOWBATT);
  runFor(g, kDry, 11.2f, t, 200);       // fresh pack
  TEST_ASSERT_TRUE(g.stop() == GuardStop::LOWBATT);  // still latched until someone presses ARM
  TEST_ASSERT_TRUE(g.tryClear());
  TEST_ASSERT_TRUE(g.stop() == GuardStop::NONE);
}

static void test_guard_no_12v_on_the_divider_trips_lowbatt() {
  PoolGuard g;
  runFor(g, kDry, 0.57f, 0, 6000);      // USB only: 0.965 × 0 + 0.57 V (C027 fit offset)
  TEST_ASSERT_TRUE(g.stop() == GuardStop::LOWBATT);
  TEST_ASSERT_FALSE(g.tryClear());
}

static void test_guard_leak_wins_over_lowbatt() {
  PoolGuard g;
  uint32_t t = runFor(g, kDry, 10.3f, 0, 6000);
  TEST_ASSERT_TRUE(g.stop() == GuardStop::LOWBATT);
  runFor(g, kWet, 10.3f, t, 300);
  TEST_ASSERT_TRUE(g.stop() == GuardStop::LEAK);
  TEST_ASSERT_FALSE(g.tryClear());
}

static void test_guard_survives_millis_wraparound() {
  PoolGuard g;
  const uint32_t t0 = 0xFFFFFFFFu - 100u;
  uint32_t t = t0;
  for (int i = 0; i < 6; ++i, t += 50) g.tick(kWet, kFull, t);  // crosses 2^32 during the 200 ms hold
  TEST_ASSERT_TRUE(g.stop() == GuardStop::LEAK);
}

void runPoolGuardTests() {
  RUN_TEST(test_guard_quiet_when_dry_and_full);
  RUN_TEST(test_guard_leak_threshold);
  RUN_TEST(test_guard_short_splash_does_not_trip);
  RUN_TEST(test_guard_leak_trips_after_hold_and_latches_for_good);
  RUN_TEST(test_guard_lowbatt_needs_5_s_below_10_5);
  RUN_TEST(test_guard_lowbatt_sag_shorter_than_hold_is_ignored);
  RUN_TEST(test_guard_lowbatt_rearm_only_above_10_8);
  RUN_TEST(test_guard_no_12v_on_the_divider_trips_lowbatt);
  RUN_TEST(test_guard_leak_wins_over_lowbatt);
  RUN_TEST(test_guard_survives_millis_wraparound);
}
