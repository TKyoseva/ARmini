// Host unit tests for lib/benchcore (pio test -e native). Unity, no Arduino.
#include <unity.h>
#include <math.h>
#include <string.h>

#include "Csv.h"
#include "Deadman.h"
#include "EscMath.h"
#include "PairMath.h"
#include "Ramp.h"
#include "Remote.h"
#include "SoftLimit.h"
#include "Vbat.h"

using bench::CsvRow;
using bench::Deadman;
using bench::PairPulses;
using bench::Ramp;
using bench::SoftLimit;
using bench::pairFromDeg;
using bench::pairFromDegTrim;
using bench::pairInWindow;
using bench::trimInRange;

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

static void test_csv_non_finite_prints_nan() {
  char buf[64];
  CsvRow row(buf, sizeof buf);
  row.add(NAN, 1).add(static_cast<double>(INFINITY), 3).add(-INFINITY, 2).add(1.5f, 1);
  TEST_ASSERT_EQUAL_STRING("nan,nan,nan,1.5", row.c_str());
  TEST_ASSERT_FALSE(row.overflow());
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

// ------------------------------------------------------------------ 5. Pair (C023): mirrored TD-8120MG, one shared degree
static void test_pair_endpoints_and_out_of_range() {
  const PairPulses z = pairFromDeg(0.0f);
  TEST_ASSERT_TRUE(z.ok);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 500.0f, z.us_a);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 2500.0f, z.us_b);

  const PairPulses mid = pairFromDeg(90.0f);
  TEST_ASSERT_TRUE(mid.ok);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, mid.us_a);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, mid.us_b);

  const PairPulses full = pairFromDeg(180.0f);
  TEST_ASSERT_TRUE(full.ok);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 2500.0f, full.us_a);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 500.0f, full.us_b);

  TEST_ASSERT_FALSE(pairFromDeg(215.0f).ok);
  TEST_ASSERT_FALSE(pairFromDeg(-0.1f).ok);
  TEST_ASSERT_FALSE(pairFromDeg(180.1f).ok);
}

static void test_pair_sum_is_3000_for_every_degree() {
  for (int deg = 0; deg <= 180; ++deg) {
    const PairPulses p = pairFromDeg(static_cast<float>(deg));
    TEST_ASSERT_TRUE(p.ok);
    TEST_ASSERT_FLOAT_WITHIN(1e-3f, 3000.0f, p.us_a + p.us_b);
  }
}

static void test_pair_ramp_0_to_90_at_20_deg_per_s() {
  // 90° at 20 °/s = 4.5 s. Tick is 100 ms, so 45 ticks, tolerance ± 1 tick.
  // Both pulses come from that one degree (lock-step), not from two ramps.
  Ramp deg(20.0f, 0.0f);
  deg.setTarget(90.0f);
  int ticks = 0;
  while (!deg.atTarget() && ticks < 60) {
    const float now = deg.update(100);
    const PairPulses p = pairFromDeg(now);
    TEST_ASSERT_TRUE(p.ok);
    TEST_ASSERT_FLOAT_WITHIN(1e-3f, 3000.0f, p.us_a + p.us_b);
    ++ticks;
  }
  TEST_ASSERT_INT_WITHIN(1, 45, ticks);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 90.0f, deg.value());
  const PairPulses end = pairFromDeg(deg.value());
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, end.us_a);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, end.us_b);
}

static void test_pair_window_refuses_a_pulse_outside_it() {
  const PairPulses centre = pairFromDeg(90.0f);
  TEST_ASSERT_TRUE(pairInWindow(centre, 1000.0f, 2000.0f));
  const PairPulses ends = pairFromDeg(0.0f);  // 500 / 2500, outside the default window
  TEST_ASSERT_FALSE(pairInWindow(ends, 1000.0f, 2000.0f));
  const PairPulses edge = pairFromDeg(45.0f);  // 1000 / 2000, on the edge
  TEST_ASSERT_TRUE(pairInWindow(edge, 1000.0f, 2000.0f));
  TEST_ASSERT_FALSE(pairInWindow(pairFromDeg(215.0f), 500.0f, 2500.0f));
}

// ------------------------------------------------------------------ 6. Pair trim (T9): offset after the mirror
static void test_pair_trim_zero_is_identity() {
  const float degs[] = {0.0f, 90.0f, 180.0f, 37.5f};
  for (int i = 0; i < 4; ++i) {
    const PairPulses a = pairFromDeg(degs[i]);
    const PairPulses b = pairFromDegTrim(degs[i], 0.0f, 0.0f);
    TEST_ASSERT_TRUE(b.ok);
    TEST_ASSERT_FLOAT_WITHIN(1e-3f, a.us_a, b.us_a);
    TEST_ASSERT_FLOAT_WITHIN(1e-3f, a.us_b, b.us_b);
  }
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 500.0f, pairFromDegTrim(0.0f, 0.0f, 0.0f).us_a);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 2500.0f, pairFromDegTrim(0.0f, 0.0f, 0.0f).us_b);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, pairFromDegTrim(90.0f, 0.0f, 0.0f).us_a);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, pairFromDegTrim(90.0f, 0.0f, 0.0f).us_b);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 2500.0f, pairFromDegTrim(180.0f, 0.0f, 0.0f).us_a);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 500.0f, pairFromDegTrim(180.0f, 0.0f, 0.0f).us_b);
}

static void test_pair_trim_b_minus_60_at_90() {
  const PairPulses p = pairFromDegTrim(90.0f, 0.0f, -60.0f);
  TEST_ASSERT_TRUE(p.ok);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, p.us_a);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1440.0f, p.us_b);
  const PairPulses q = pairFromDegTrim(90.0f, 25.0f, -60.0f);  // A trimmed too, independent of B
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1525.0f, q.us_a);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1440.0f, q.us_b);
}

static void test_pair_trim_out_of_range_refused() {
  TEST_ASSERT_TRUE(trimInRange(200.0f));
  TEST_ASSERT_TRUE(trimInRange(-200.0f));
  TEST_ASSERT_FALSE(trimInRange(200.5f));
  TEST_ASSERT_FALSE(trimInRange(-201.0f));
  TEST_ASSERT_FALSE(pairFromDegTrim(90.0f, 201.0f, 0.0f).ok);
  TEST_ASSERT_FALSE(pairFromDegTrim(90.0f, 0.0f, -201.0f).ok);
  TEST_ASSERT_FALSE(pairFromDegTrim(215.0f, 0.0f, 0.0f).ok);  // degree check still first
}

static void test_pair_trim_pushes_pulse_out_of_window() {
  // 45° → 1000 / 2000, on the default window edge. Any trim outward leaves the window.
  TEST_ASSERT_TRUE(pairInWindow(pairFromDegTrim(45.0f, 0.0f, 0.0f), 1000.0f, 2000.0f));
  TEST_ASSERT_FALSE(pairInWindow(pairFromDegTrim(45.0f, -10.0f, 0.0f), 1000.0f, 2000.0f));
  TEST_ASSERT_FALSE(pairInWindow(pairFromDegTrim(45.0f, 0.0f, 10.0f), 1000.0f, 2000.0f));
  TEST_ASSERT_TRUE(pairInWindow(pairFromDegTrim(45.0f, 10.0f, -10.0f), 1000.0f, 2000.0f));  // inward is fine
  TEST_ASSERT_TRUE(pairInWindow(pairFromDegTrim(45.0f, -10.0f, 10.0f), 500.0f, 2500.0f));   // wider window accepts
}

// ------------------------------------------------------------------ 7. ESC (T10): diff mix, clamp, ramp
static void test_esc_diff_mix_narrow() {
  const float lo = bench::kEscNarrowLoUs, hi = bench::kEscNarrowHiUs;
  bench::EscPulses p = bench::escDiff(0.0f, 0.0f, lo, hi);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, p.l_us);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, p.r_us);
  p = bench::escDiff(100.0f, 0.0f, lo, hi);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1650.0f, p.l_us);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1650.0f, p.r_us);
  p = bench::escDiff(0.0f, 100.0f, lo, hi);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1650.0f, p.l_us);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1350.0f, p.r_us);
  p = bench::escDiff(100.0f, 100.0f, lo, hi);  // l would be 1800 → clamped
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1650.0f, p.l_us);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, p.r_us);
}

static void test_esc_clamp_narrow_and_wide() {
  const float nlo = bench::kEscNarrowLoUs, nhi = bench::kEscNarrowHiUs;
  const float wlo = bench::kEscWideLoUs, whi = bench::kEscWideHiUs;
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1650.0f, bench::escClamp(1700.0f, nlo, nhi));
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1350.0f, bench::escClamp(1200.0f, nlo, nhi));
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 2000.0f, bench::escClamp(2100.0f, wlo, whi));
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1000.0f, bench::escClamp(900.0f, wlo, whi));
  TEST_ASSERT_TRUE(bench::escInLimit(1650.0f, nlo, nhi));
  TEST_ASSERT_FALSE(bench::escInLimit(1700.0f, nlo, nhi));
  TEST_ASSERT_TRUE(bench::escInLimit(1700.0f, wlo, whi));
  bench::EscPulses p = bench::escDiff(100.0f, 0.0f, wlo, whi);  // 100 = the wide limit
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 2000.0f, p.l_us);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 2000.0f, p.r_us);
  p = bench::escDiff(-100.0f, -100.0f, wlo, whi);  // l would be 500 → clamped
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1000.0f, p.l_us);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, p.r_us);
}

static void test_esc_ramp_1500_to_1650_in_0_75_s() {
  Ramp r(200.0f, 1500.0f);
  r.setTarget(1650.0f);
  for (int i = 0; i < 14; ++i) r.update(50);  // 0.70 s
  TEST_ASSERT_FALSE(r.atTarget());
  r.update(50);  // 0.75 s
  TEST_ASSERT_TRUE(r.atTarget());
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1650.0f, r.value());
}

static void test_esc_duty_normal_and_inverted() {
  TEST_ASSERT_EQUAL_UINT32(1229, bench::escDuty(1500.0f, 14, false));          // 1500 / 20000 × 16384 = 1228.8
  TEST_ASSERT_EQUAL_UINT32(16384 - 1229, bench::escDuty(1500.0f, 14, true));   // 15155
  TEST_ASSERT_EQUAL_UINT32(16384, bench::escDuty(0.0f, 14, true));             // pin always HIGH → ESC input always LOW
  TEST_ASSERT_EQUAL_UINT32(0, bench::escDuty(0.0f, 14, false));
  TEST_ASSERT_EQUAL_UINT32(16384, bench::escDuty(20000.0f, 14, false) + bench::escDuty(0.0f, 14, false));
  for (int us = 1000; us <= 2000; us += 50) {
    TEST_ASSERT_EQUAL_UINT32(16384, bench::escDuty(static_cast<float>(us), 14, false) +
                                        bench::escDuty(static_cast<float>(us), 14, true));
  }
}

// ------------------------------------------------------------------ Remote (T12): dead band, mix, link, message
static void test_remote_deadband_map() {
  const float lo = bench::kEscNarrowLoUs, hi = bench::kEscNarrowHiUs;
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, bench::escDeadbandUs(0.0f, lo, hi));
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1580.0f, bench::escDeadbandUs(1.0f, lo, hi));
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1650.0f, bench::escDeadbandUs(100.0f, lo, hi));
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1420.0f, bench::escDeadbandUs(-1.0f, lo, hi));
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1350.0f, bench::escDeadbandUs(-100.0f, lo, hi));
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1650.0f, bench::escDeadbandUs(250.0f, lo, hi));   // clamped
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1350.0f, bench::escDeadbandUs(-250.0f, lo, hi));  // clamped
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, bench::escDeadbandUs(0.5f, lo, hi));     // below one step → neutral
  for (int c = -100; c <= 100; ++c) {
    const float us = bench::escDeadbandUs(static_cast<float>(c), lo, hi);
    TEST_ASSERT_TRUE(bench::escInLimit(us, lo, hi));
  }
}

static void test_remote_mix() {
  const float lo = bench::kEscNarrowLoUs, hi = bench::kEscNarrowHiUs;
  bench::EscPulses p = bench::escMixDeadband(50.0f, 0.0f, lo, hi);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, p.l_us, p.r_us);
  TEST_ASSERT_TRUE(p.l_us > 1580.0f && p.l_us < 1650.0f);
  p = bench::escMixDeadband(0.0f, 100.0f, lo, hi);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1650.0f, p.l_us);  // left forward
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1350.0f, p.r_us);  // right reverse
  p = bench::escMixDeadband(100.0f, 100.0f, lo, hi);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1650.0f, p.l_us);
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 1500.0f, p.r_us);
}

static void test_remote_link_timeout() {
  TEST_ASSERT_FALSE(bench::linkLost(1000, 1000));
  TEST_ASSERT_FALSE(bench::linkLost(1000, 1500));  // exactly 500 ms: still alive
  TEST_ASSERT_TRUE(bench::linkLost(1000, 1501));
  TEST_ASSERT_FALSE(bench::linkLost(0xFFFFFF00u, 0x000000F0u));  // 496 ms across millis() wrap
  TEST_ASSERT_TRUE(bench::linkLost(0xFFFFFF00u, 0x00000200u));   // 768 ms across wrap
  TEST_ASSERT_FALSE(bench::linkLost(1001, 1000));  // heartbeat stamped 1 ms after loop()'s now (bench 23.10)
}

static void test_remote_parse_message() {
  bench::RemoteMsg m;
  TEST_ASSERT_TRUE(bench::parseRemoteMsg("{\"t\":-100,\"r\":100,\"arm\":0}", &m));
  TEST_ASSERT_EQUAL_INT(-100, m.t);
  TEST_ASSERT_EQUAL_INT(100, m.r);
  TEST_ASSERT_FALSE(m.arm);
  TEST_ASSERT_FALSE(m.stop);
  TEST_ASSERT_TRUE(bench::parseRemoteMsg("{\"t\": 5, \"r\": -3, \"arm\": 1}", &m));
  TEST_ASSERT_EQUAL_INT(5, m.t);
  TEST_ASSERT_EQUAL_INT(-3, m.r);
  TEST_ASSERT_TRUE(m.arm);
  TEST_ASSERT_TRUE(bench::parseRemoteMsg("{\"stop\":1}", &m));
  TEST_ASSERT_TRUE(m.stop);
  TEST_ASSERT_FALSE(bench::parseRemoteMsg("{\"t\":101,\"r\":0,\"arm\":0}", &m));  // out of range
  TEST_ASSERT_FALSE(bench::parseRemoteMsg("{\"t\":0}", &m));                      // no r
  TEST_ASSERT_FALSE(bench::parseRemoteMsg("{\"t\":x,\"r\":0}", &m));              // not a number
  TEST_ASSERT_FALSE(bench::parseRemoteMsg("{\"t\":0,\"r\":0,\"arm\":2}", &m));
  TEST_ASSERT_FALSE(bench::parseRemoteMsg("hello", &m));
  TEST_ASSERT_FALSE(bench::parseRemoteMsg(nullptr, &m));
}

static void test_vbat_corrected() {
  const float div = (100000.0f + 30000.0f) / 30000.0f;
  TEST_ASSERT_FLOAT_WITHIN(1e-4f, 2.769f * div, bench::vbatCorrected(2.769f, div, 1.0f, 0.0f));
  TEST_ASSERT_FLOAT_WITHIN(1e-3f, 0.965f * 2.769f * div + 0.57f, bench::vbatCorrected(2.769f, div, 0.965f, 0.57f));
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
  RUN_TEST(test_csv_non_finite_prints_nan);
  RUN_TEST(test_csv_reset_and_single_field);
  RUN_TEST(test_csv_overflow_is_flagged_and_terminated);
  RUN_TEST(test_softlimit_refuses_until_unlocked);
  RUN_TEST(test_softlimit_clamps_to_unit_range);
  RUN_TEST(test_pipeline_deadman_stops_ramp);
  RUN_TEST(test_pair_endpoints_and_out_of_range);
  RUN_TEST(test_pair_sum_is_3000_for_every_degree);
  RUN_TEST(test_pair_ramp_0_to_90_at_20_deg_per_s);
  RUN_TEST(test_pair_window_refuses_a_pulse_outside_it);
  RUN_TEST(test_pair_trim_zero_is_identity);
  RUN_TEST(test_pair_trim_b_minus_60_at_90);
  RUN_TEST(test_pair_trim_out_of_range_refused);
  RUN_TEST(test_pair_trim_pushes_pulse_out_of_window);
  RUN_TEST(test_esc_diff_mix_narrow);
  RUN_TEST(test_esc_clamp_narrow_and_wide);
  RUN_TEST(test_esc_ramp_1500_to_1650_in_0_75_s);
  RUN_TEST(test_esc_duty_normal_and_inverted);
  RUN_TEST(test_remote_deadband_map);
  RUN_TEST(test_remote_mix);
  RUN_TEST(test_remote_link_timeout);
  RUN_TEST(test_remote_parse_message);
  RUN_TEST(test_vbat_corrected);
  return UNITY_END();
}
