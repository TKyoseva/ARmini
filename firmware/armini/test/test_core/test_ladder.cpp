// AR-Mini · host tests for lib/core/Ladder.h (A1 leak + kill ladder decoder).
// Entry point (called from test_main.cpp): runLadderTests().
#include <unity.h>
#include "Ladder.h"

using namespace armini;

// ---------------------------------------------------------------------------
// the four physical levels (SPEC.md: open 3.30, leak 1.06, kill 0.30, both 0.25)

void test_ladder_four_levels() {
  TEST_ASSERT_EQUAL(LadderState::OK,   decodeLadder(3.30f));
  TEST_ASSERT_EQUAL(LadderState::LEAK, decodeLadder(1.06f));
  TEST_ASSERT_EQUAL(LadderState::KILL, decodeLadder(0.30f));
  TEST_ASSERT_EQUAL(LadderState::KILL, decodeLadder(0.25f));
}

// The formula in the header reproduces the SPEC.md numbers from the resistors.
void test_ladder_formula_matches_spec() {
  TEST_ASSERT_FLOAT_WITHIN(0.005f, 3.30f, ladderVoltage(false, false));
  TEST_ASSERT_FLOAT_WITHIN(0.005f, 1.06f, ladderVoltage(true,  false));   // 3.3·4.7/14.7 = 1.055
  TEST_ASSERT_FLOAT_WITHIN(0.005f, 0.30f, ladderVoltage(false, true));    // 3.3·1/11   = 0.300
  TEST_ASSERT_FLOAT_WITHIN(0.005f, 0.25f, ladderVoltage(true,  true));    // 3.3·0.825/10.825 = 0.251

  TEST_ASSERT_EQUAL(LadderState::OK,   decodeLadder(ladderVoltage(false, false)));
  TEST_ASSERT_EQUAL(LadderState::LEAK, decodeLadder(ladderVoltage(true,  false)));
  TEST_ASSERT_EQUAL(LadderState::KILL, decodeLadder(ladderVoltage(false, true)));
  TEST_ASSERT_EQUAL(LadderState::KILL, decodeLadder(ladderVoltage(true,  true)));
}

// ---------------------------------------------------------------------------
// thresholds exactly at the boundary: 0.6 V and 2.0 V belong to LEAK

void test_ladder_boundaries() {
  TEST_ASSERT_EQUAL(LadderState::KILL, decodeLadder(0.59f));
  TEST_ASSERT_EQUAL(LadderState::LEAK, decodeLadder(0.6f));
  TEST_ASSERT_EQUAL(LadderState::LEAK, decodeLadder(2.0f));
  TEST_ASSERT_EQUAL(LadderState::OK,   decodeLadder(2.01f));
  TEST_ASSERT_EQUAL(LadderState::LEAK, decodeLadder(kLadderKillBelowV));
  TEST_ASSERT_EQUAL(LadderState::LEAK, decodeLadder(kLadderLeakUpToV));
}

// ---------------------------------------------------------------------------
// negative = ladder not fitted: decodes as OK and reports "not present"

void test_ladder_negative_is_not_present() {
  TEST_ASSERT_FALSE(ladderPresent(-1.0f));
  TEST_ASSERT_FALSE(ladderPresent(-0.001f));
  TEST_ASSERT_TRUE(ladderPresent(0.0f));
  TEST_ASSERT_EQUAL(LadderState::OK, decodeLadder(-1.0f));
  TEST_ASSERT_EQUAL(LadderState::KILL, decodeLadder(0.0f));  // 0 V is a real reading: shorted = KILL
}

// ---------------------------------------------------------------------------

void runLadderTests() {
  RUN_TEST(test_ladder_four_levels);
  RUN_TEST(test_ladder_formula_matches_spec);
  RUN_TEST(test_ladder_boundaries);
  RUN_TEST(test_ladder_negative_is_not_present);
}
