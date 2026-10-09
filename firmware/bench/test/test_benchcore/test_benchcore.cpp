// Host unit tests for lib/benchcore (pio test -e native). Unity, no Arduino.
#include <unity.h>
#include <math.h>
#include <string.h>

#include "Csv.h"
#include "Deadman.h"
#include "Ramp.h"
#include "SoftLimit.h"

using bench::CsvRow;
using bench::Deadman;
using bench::Ramp;
using bench::SoftLimit;

void setUp() {}
void tearDown() {}

// ------------------------------------------------------------------ 1. Ramp
static void test_ramp_never_exceeds_rate() {
  Ramp r(0.5f, 0.0f);
  r.setTarget(1.0f);
  float prev = r.value();
  for (int i = 0; i < 50; ++i) {  // 50 × 100 ms = 5 s
    const float v = r.update(100);
    const float step = fabsf(v - prev);
    TEST_ASSERT_TRUE_MESSAGE(step <= 0.05f + 1e-5f, "step larger than rate*dt");
    prev = v;
  }
}

static void test_ramp_reaches_target_and_stays() {
  Ramp r(0.5f, 0.0f);
  r.setTarget(0.6f);
  // 0.6 at 0.5/s = 1.2 s = 12 ticks of 100 ms; after 11 ticks not yet there
  for (int i = 0; i < 11; ++i) r.update(100);
  TEST_ASSERT_FALSE(r.atTarget());
  r.update(100);
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, 0.6f, r.value());
  TEST_ASSERT_TRUE(r.atTarget());
  r.update(100);  // no overshoot
  TEST_ASSERT_FLOAT_WITHIN(1e-6f, 0.6f, r.value());
}

static void test_ramp_sign_change_passes_through_zero() {
  Ramp r(0.5f, 0.5f);
  r.setTarget(-0.5f);
  bool seen_zero_or_below = false;
  float prev = r.value();
  for (int i = 0; i < 30; ++i) {
    const float v = r.update(100);
    TEST_ASSERT_TRUE_MESSAGE(v <= prev + 1e-6f, "value must decrease monotonically");
    TEST_ASSERT_TRUE(fabsf(v - prev) <= 0.05f + 1e-5f);
    if (v <= 0.0f) seen_zero_or_below = true;
    prev = v;
  }
  TEST_ASSERT_TRUE(seen_zero_or_below);
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, -0.5f, r.value());
}

static void test_ramp_stop_is_immediate() {
  Ramp r(0.5f, 0.0f);
  r.setTarget(1.0f);
  r.update(1000);
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, 0.5f, r.value());
  r.stop();
  TEST_ASSERT_EQUAL_FLOAT(0.0f, r.value());
  TEST_ASSERT_EQUAL_FLOAT(0.0f, r.target());
  r.update(100);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, r.value());
}

static void test_ramp_rate_change_applies() {
  Ramp r(0.5f, 0.0f);
  r.setRate(2.0f);
  r.setTarget(1.0f);
  r.update(100);
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, 0.2f, r.value());
  TEST_ASSERT_EQUAL_FLOAT(2.0f, r.rate());
}

// ------------------------------------------------------------------ 2. Deadman
static void test_deadman_idle_until_first_feed() {
  Deadman d(2000);
  TEST_ASSERT_FALSE(d.engaged());
  TEST_ASSERT_FALSE(d.update(0));
  TEST_ASSERT_FALSE(d.update(10000));  // never trips without a command
  TEST_ASSERT_FALSE(d.tripped());
}

static void test_deadman_trips_after_timeout_once() {
  Deadman d(2000);
  d.feed(1000);
  TEST_ASSERT_FALSE(d.update(1000));
  TEST_ASSERT_FALSE(d.update(2999));
  TEST_ASSERT_TRUE(d.update(3000));  // edge exactly at timeout
  TEST_ASSERT_TRUE(d.tripped());
  TEST_ASSERT_FALSE(d.update(3100));  // only once
  TEST_ASSERT_FALSE(d.update(9000));
  TEST_ASSERT_TRUE(d.tripped());
}

static void test_deadman_resets_on_any_command() {
  Deadman d(2000);
  d.feed(0);
  TEST_ASSERT_FALSE(d.update(1500));
  d.feed(1500);  // command arrives → window restarts
  TEST_ASSERT_FALSE(d.update(2500));
  TEST_ASSERT_FALSE(d.update(3499));
  TEST_ASSERT_TRUE(d.update(3500));
  d.feed(4000);  // command after a trip re-arms and clears tripped()
  TEST_ASSERT_FALSE(d.tripped());
  TEST_ASSERT_TRUE(d.engaged());
  TEST_ASSERT_TRUE(d.update(6000));
}

static void test_deadman_survives_millis_wraparound() {
  Deadman d(2000);
  d.feed(0xFFFFFF00u);
  TEST_ASSERT_FALSE(d.update(0xFFFFFFF0u));
  TEST_ASSERT_FALSE(d.update(100));  // 0x100 + 0x100 = 512 ms elapsed
  TEST_ASSERT_TRUE(d.update(2000));  // 256 + 2000 ms elapsed
}

static void test_deadman_timeout_configurable() {
  Deadman d(2000);
  d.setTimeout(500);
  d.feed(0);
  TEST_ASSERT_FALSE(d.update(499));
  TEST_ASSERT_TRUE(d.update(500));
}

// ------------------------------------------------------------------ 3. CSV
static void test_csv_row_formatting() {
  char buf[96];
  CsvRow row(buf, sizeof buf);
  row.add(1234UL).add(0.5f, 3).add(128).add(-0.25f, 2).add("x");
  TEST_ASSERT_EQUAL_STRING("1234,0.500,128,-0.25,x", row.c_str());
  TEST_ASSERT_EQUAL_UINT(5, row.fields());
  TEST_ASSERT_FALSE(row.overflow());
  TEST_ASSERT_EQUAL_UINT(strlen(row.c_str()), row.length());
  TEST_ASSERT_NOT_EQUAL(',', buf[row.length() - 1]);  // no trailing comma
}

static void test_csv_fixed_decimals_and_rounding() {
  char buf[96];
  CsvRow row(buf, sizeof buf);
  row.add(0.0f, 3).add(-0.0004f, 3).add(2.5f, 0).add(0.9999f, 2).add(-1.25f, 1).add(12.3456789, 6);
  // -0.0004 rounds to 0.000 and must not print "-0.000"; 2.5 → 3 and -1.25 → -1.3 (half away from zero,
  // both exact in binary); 0.9999 → 1.00 (carry into the integer part)
  TEST_ASSERT_EQUAL_STRING("0.000,0.000,3,1.00,-1.3,12.345679", row.c_str());
}

static void test_csv_reset_and_single_field() {
  char buf[32];
  CsvRow row(buf, sizeof buf);
  row.add(7);
  TEST_ASSERT_EQUAL_STRING("7", row.c_str());
  row.reset();
  TEST_ASSERT_EQUAL_STRING("", row.c_str());
  TEST_ASSERT_EQUAL_UINT(0, row.fields());
  row.add(true).add(false);
  TEST_ASSERT_EQUAL_STRING("1,0", row.c_str());
}

static void test_csv_overflow_is_flagged_and_terminated() {
  char buf[8];
  CsvRow row(buf, sizeof buf);
  row.add(123456L).add(789L);
  TEST_ASSERT_TRUE(row.overflow());
  TEST_ASSERT_EQUAL_UINT(7, strlen(row.c_str()));  // cap - 1, always NUL-terminated
  TEST_ASSERT_EQUAL_STRING("123456,", row.c_str());
}

// ------------------------------------------------------------------ 4. SoftLimit
static void test_softlimit_refuses_until_unlocked() {
  SoftLimit lim;
  TEST_ASSERT_FLOAT_WITHIN(1e-6f, 0.6f, lim.limit());
  TEST_ASSERT_TRUE(lim.accepts(0.6f));
  TEST_ASSERT_TRUE(lim.accepts(-0.6f));
  TEST_ASSERT_TRUE(lim.accepts(0.0f));
  TEST_ASSERT_FALSE(lim.accepts(0.61f));
  TEST_ASSERT_FALSE(lim.accepts(1.0f));
  TEST_ASSERT_FALSE(lim.accepts(-1.0f));
  lim.setLimit(1.0f);  // explicit `limit 1.0`
  TEST_ASSERT_TRUE(lim.accepts(1.0f));
  TEST_ASSERT_TRUE(lim.accepts(-1.0f));
  TEST_ASSERT_FALSE(lim.accepts(1.01f));
}

static void test_softlimit_clamps_to_unit_range() {
  SoftLimit lim(5.0f);
  TEST_ASSERT_EQUAL_FLOAT(1.0f, lim.limit());
  lim.setLimit(-2.0f);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, lim.limit());
  TEST_ASSERT_TRUE(lim.accepts(0.0f));
  TEST_ASSERT_FALSE(lim.accepts(0.1f));
  lim.setLimit(0.3f);
  TEST_ASSERT_FLOAT_WITHIN(1e-6f, 0.3f, lim.clamp(0.9f));
  TEST_ASSERT_FLOAT_WITHIN(1e-6f, -0.3f, lim.clamp(-0.9f));
  TEST_ASSERT_FLOAT_WITHIN(1e-6f, 0.2f, lim.clamp(0.2f));
}

// ------------------------------------------------------------------ Integration: command → limit → ramp → deadman
static void test_pipeline_deadman_stops_ramp() {
  SoftLimit lim;
  Ramp ramp(0.5f, 0.0f);
  Deadman dm(2000);
  uint32_t now = 0;
  // operator: s 0.5
  TEST_ASSERT_TRUE(lim.accepts(0.5f));
  ramp.setTarget(0.5f);
  dm.feed(now);
  for (int i = 0; i < 19; ++i) {
    now += 100;
    ramp.update(100);
    TEST_ASSERT_FALSE(dm.update(now));
  }
  TEST_ASSERT_FLOAT_WITHIN(1e-5f, 0.5f, ramp.value());
  now += 100;  // t = 2000 ms since the command
  ramp.update(100);
  TEST_ASSERT_TRUE(dm.update(now));
  ramp.stop();
  TEST_ASSERT_EQUAL_FLOAT(0.0f, ramp.value());
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_ramp_never_exceeds_rate);
  RUN_TEST(test_ramp_reaches_target_and_stays);
  RUN_TEST(test_ramp_sign_change_passes_through_zero);
  RUN_TEST(test_ramp_stop_is_immediate);
  RUN_TEST(test_ramp_rate_change_applies);
  RUN_TEST(test_deadman_idle_until_first_feed);
  RUN_TEST(test_deadman_trips_after_timeout_once);
  RUN_TEST(test_deadman_resets_on_any_command);
  RUN_TEST(test_deadman_survives_millis_wraparound);
  RUN_TEST(test_deadman_timeout_configurable);
  RUN_TEST(test_csv_row_formatting);
  RUN_TEST(test_csv_fixed_decimals_and_rounding);
  RUN_TEST(test_csv_reset_and_single_field);
  RUN_TEST(test_csv_overflow_is_flagged_and_terminated);
  RUN_TEST(test_softlimit_refuses_until_unlocked);
  RUN_TEST(test_softlimit_clamps_to_unit_range);
  RUN_TEST(test_pipeline_deadman_stops_ramp);
  return UNITY_END();
}
