// AR-Mini · host tests for lib/core/Heading.h (heading hold, card C077).
// Entry point (called from test_main.cpp): runHeadingTests().
#include <unity.h>
#include <math.h>
#include <stdio.h>
#include "Heading.h"

using namespace armini;

static const float kDt = 0.02f;   // 50 Hz control loop

// Runs the closed loop for `seconds`; returns the largest |error| seen after `settleS`.
static float worstErrorAfter(YawModel boat, float targetDeg, float seconds, float settleS, float* worstTurn = nullptr) {
  HeadingHold hold;
  float worst = 0.0f, wt = 0.0f;
  for (float t = 0.0f; t < seconds; t += kDt) {
    const float turn = hold.update(targetDeg, boat.headingDeg, kDt);
    boat.step(turn, kDt);
    if (fabsf(turn) > wt) wt = fabsf(turn);
    if (t >= settleS) {
      const float e = fabsf(headingError(targetDeg, boat.headingDeg));
      if (e > worst) worst = e;
    }
  }
  if (worstTurn) *worstTurn = wt;
  return worst;
}

// ---------------------------------------------------------------------------
// angle wrap

void test_heading_error_wraps_the_short_way() {
  TEST_ASSERT_FLOAT_WITHIN(0.001f,  10.0f, headingError(20.0f, 10.0f));
  TEST_ASSERT_FLOAT_WITHIN(0.001f, -10.0f, headingError(10.0f, 20.0f));
  TEST_ASSERT_FLOAT_WITHIN(0.001f,  20.0f, headingError(10.0f, 350.0f));    // across north, turn right
  TEST_ASSERT_FLOAT_WITHIN(0.001f, -20.0f, headingError(350.0f, 10.0f));    // across north, turn left
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 180.0f, headingError(180.0f, 0.0f));     // exactly opposite: +180, not −180
  TEST_ASSERT_FLOAT_WITHIN(0.001f,   0.0f, headingError(720.0f, 0.0f));
  TEST_ASSERT_FLOAT_WITHIN(0.001f,  -5.0f, headingError(-5.0f, 0.0f));
}

// ---------------------------------------------------------------------------
// controller on its own

void test_heading_output_sign_and_clamp() {
  HeadingHold h;
  TEST_ASSERT_TRUE(h.update(100.0f, 90.0f, kDt) > 0.0f);     // target to the right → turn right
  h.reset();
  TEST_ASSERT_TRUE(h.update(80.0f, 90.0f, kDt) < 0.0f);
  h.reset();
  TEST_ASSERT_FLOAT_WITHIN(0.0001f,  1.0f, h.update(180.0f, 90.0f, kDt));   // 90° of error saturates
  h.reset();
  TEST_ASSERT_FLOAT_WITHIN(0.0001f, -1.0f, h.update(0.0f, 90.0f, kDt));
}

void test_heading_integral_does_not_wind_up_in_saturation() {
  HeadingHold h;
  for (int i = 0; i < 500; ++i) h.update(180.0f, 90.0f, kDt);   // 10 s held at full rudder (boat stuck)
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, h.integral());
  // once the error is small the output must follow it at once, not stay pinned by a stored integral
  TEST_ASSERT_TRUE(h.update(90.0f, 91.0f, kDt) < 0.0f);
}

void test_heading_reset_clears_the_integral() {
  HeadingHold h;
  for (int i = 0; i < 100; ++i) h.update(95.0f, 90.0f, kDt);
  TEST_ASSERT_TRUE(h.integral() > 0.0f);
  h.reset();
  TEST_ASSERT_FLOAT_WITHIN(0.0001f, 0.0f, h.integral());
}

void test_heading_bad_samples_are_ignored() {
  HeadingHold h;
  TEST_ASSERT_FLOAT_WITHIN(0.0001f, 0.0f, h.update(90.0f, NAN, kDt));       // IMU not ready
  TEST_ASSERT_FLOAT_WITHIN(0.0001f, 0.0f, h.integral());
  h.update(95.0f, 90.0f, 2.0f);                                             // 2 s gap: stale, integral waits
  TEST_ASSERT_FLOAT_WITHIN(0.0001f, 0.0f, h.integral());
  h.update(95.0f, 90.0f, 0.0f);
  h.update(95.0f, 90.0f, -1.0f);
  TEST_ASSERT_FLOAT_WITHIN(0.0001f, 0.0f, h.integral());
}

// ---------------------------------------------------------------------------
// closed loop on the simulated boat (card C077 pass criterion: ±5° after 10 s, 10° step + constant disturbance)

void test_heading_step_10deg_with_disturbance_nominal_boat() {
  YawModel boat = {30.0f, 0.8f, 5.0f, 90.0f, 0.0f};          // ASSUMED nominal model, 5 °/s push
  TEST_ASSERT_TRUE(worstErrorAfter(boat, 100.0f, 30.0f, 10.0f) < 5.0f);
  TEST_ASSERT_TRUE(worstErrorAfter(boat, 100.0f, 60.0f, 30.0f) < 1.0f);   // the integral removes the offset
}

void test_heading_step_across_north() {
  YawModel boat = {30.0f, 0.8f, -5.0f, 355.0f, 0.0f};
  TEST_ASSERT_TRUE(worstErrorAfter(boat, 5.0f, 30.0f, 10.0f) < 5.0f);
}

// The model is a guess, so the same gains must work on a slower and a faster boat too.
void test_heading_holds_over_the_model_range() {
  const float gains[] = {15.0f, 30.0f, 60.0f};
  const float taus[]  = {0.3f, 0.8f, 1.5f};
  const float pushes[] = {-5.0f, 5.0f};
  for (float g : gains) for (float tau : taus) for (float d : pushes) {
    YawModel boat = {g, tau, d, 90.0f, 0.0f};
    const float worst = worstErrorAfter(boat, 100.0f, 40.0f, 10.0f);
    char msg[80];
    snprintf(msg, sizeof msg, "gain %.0f tau %.1f disturb %.0f → %.2f deg", g, tau, d, worst);
    TEST_ASSERT_TRUE_MESSAGE(worst < 5.0f, msg);
  }
}

void test_heading_large_turn_180_settles() {
  YawModel boat = {30.0f, 0.8f, 5.0f, 0.0f, 0.0f};
  TEST_ASSERT_TRUE(worstErrorAfter(boat, 180.0f, 60.0f, 25.0f) < 5.0f);
}

void test_heading_without_disturbance_stays_put() {
  YawModel boat = {30.0f, 0.8f, 0.0f, 42.0f, 0.0f};
  float worstTurn = 1.0f;
  TEST_ASSERT_TRUE(worstErrorAfter(boat, 42.0f, 10.0f, 0.0f, &worstTurn) < 0.01f);
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, worstTurn);
}

void runHeadingTests() {
  RUN_TEST(test_heading_error_wraps_the_short_way);
  RUN_TEST(test_heading_output_sign_and_clamp);
  RUN_TEST(test_heading_integral_does_not_wind_up_in_saturation);
  RUN_TEST(test_heading_reset_clears_the_integral);
  RUN_TEST(test_heading_bad_samples_are_ignored);
  RUN_TEST(test_heading_step_10deg_with_disturbance_nominal_boat);
  RUN_TEST(test_heading_step_across_north);
  RUN_TEST(test_heading_holds_over_the_model_range);
  RUN_TEST(test_heading_large_turn_180_settles);
  RUN_TEST(test_heading_without_disturbance_stays_put);
}
