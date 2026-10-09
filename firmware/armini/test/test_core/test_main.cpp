// AR-Mini · host test entry point (Unity, `pio test -e native`).
// All files in test/test_core/ are linked into ONE executable, so Unity's
// setUp / tearDown / main live here and each suite exposes a runner.
#include <unity.h>

void stateMachineSetUp();
void runStateMachineTests();   // test_state_machine.cpp (T1)
void runLadderTests();         // test_ladder.cpp (T2)
void safetySetUp();
void runSafetyTests();         // test_safety.cpp (T2)

void setUp() {
  stateMachineSetUp();
  safetySetUp();
}
void tearDown() {}

int main(int, char**) {
  UNITY_BEGIN();
  runStateMachineTests();
  runLadderTests();
  runSafetyTests();
  return UNITY_END();
}
