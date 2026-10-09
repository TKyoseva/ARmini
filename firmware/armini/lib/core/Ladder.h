// AR-Mini · A1 resistor ladder decoder (leak probe + logic kill on one ADC pin).
// Pure C++11, header only, no Arduino, no heap.
//
// Circuit (XIAO carrier). SOURCE: pcb/carrier-revA/SPEC.md §5 (R7/R8/R9),
// hardware/breadboard/AR-Mini_breadboard_2, docs/FAILS_AND_FIXES.md #41/#42:
//
//          3V3 ──[R7 10 kΩ]──┬── A1 (ADC)
//                            ├──[R8 4.7 kΩ]──(leak probe, two bare wires)── GND
//                            └──[R9 1 kΩ]───(KILL rocker, position KILL)── GND
//
//   v_a1 = 3.3 V · R_down / (R7 + R_down),  R_down = parallel of the closed branches
//
//   nothing closed        R_down = ∞            → 3.30 V   OK
//   leak only             R_down = 4.7 kΩ       → 1.055 V  LEAK
//   kill only             R_down = 1 kΩ         → 0.300 V  KILL
//   leak + kill           R_down = 4.7 ∥ 1 = 0.825 kΩ → 0.251 V  KILL
//
// Decode thresholds sit roughly mid-way between the levels:
//   v <  0.6 V         → KILL
//   0.6 V ≤ v ≤ 2.0 V  → LEAK
//   v >  2.0 V         → OK
// A negative value means "no ladder on this board" (DevKit-Lipo breadboard
// 2b has leak and kill on separate GPIOs) and decodes as OK; Safety then uses
// only the boolean inputs.
//
// The ladder tells the firmware *that* the rocker is in KILL. It does not
// stop the motors: the same rocker pulls PCA9685 OE high in hardware
// (SPEC.md R10), which switches all 16 PWM outputs off before any code runs.
#pragma once
#include <stdint.h>

namespace armini {

enum class LadderState : uint8_t { OK, LEAK, KILL };

// Resistor values. SOURCE: pcb/carrier-revA/SPEC.md (R7, R8, R9).
static const float kLadderVrefV     = 3.3f;   // pull-up rail
static const float kLadderPullupOhm = 10000.0f;  // R7
static const float kLadderLeakOhm   = 4700.0f;   // R8
static const float kLadderKillOhm   = 1000.0f;   // R9

// Decode thresholds. SOURCE: tasks/night/2026-10-08_T2_safety.md
// (< 0.6 V → KILL, 0.6–2.0 V → LEAK, > 2.0 V → OK). VERIFY on the breadboard
// with the real resistors and the ESP32 ADC (its non-linearity near 0 V and
// above ~2.5 V is known; the levels have ≥ 0.75 V margin to each threshold).
static const float kLadderKillBelowV = 0.6f;
static const float kLadderLeakUpToV  = 2.0f;

// true if the voltage comes from a real ladder (negative = not fitted).
inline bool ladderPresent(float v) { return v >= 0.0f; }

// Pure decode. Both thresholds are inclusive on the LEAK side:
// exactly 0.6 V → LEAK, exactly 2.0 V → LEAK.
inline LadderState decodeLadder(float v) {
  if (!ladderPresent(v)) return LadderState::OK;
  if (v < kLadderKillBelowV) return LadderState::KILL;
  if (v <= kLadderLeakUpToV) return LadderState::LEAK;
  return LadderState::OK;
}

// Expected A1 voltage for a given switch state (the formula above). Used by
// the host tests and handy for checking the breadboard with a multimeter.
inline float ladderVoltage(bool leak, bool kill) {
  if (!leak && !kill) return kLadderVrefV;
  float g = 0.0f;  // conductance of the closed branches
  if (leak) g += 1.0f / kLadderLeakOhm;
  if (kill) g += 1.0f / kLadderKillOhm;
  const float r_down = 1.0f / g;
  return kLadderVrefV * r_down / (kLadderPullupOhm + r_down);
}

inline const char* ladderName(LadderState s) {
  switch (s) {
    case LadderState::OK:   return "OK";
    case LadderState::LEAK: return "LEAK";
    case LadderState::KILL: return "KILL";
  }
  return "?";
}

}  // namespace armini
