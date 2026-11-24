// AR-Mini C077 · closed-loop step response of the real controller code (firmware/armini/lib/core/Heading.h)
// on the simulated boat. Prints CSV: model, t, target, heading, turn. Built and plotted by run.py.
#include <stdio.h>
#include "Heading.h"

using namespace armini;

static void run(const char* name, float gain, float tau, float disturb) {
  YawModel boat = {gain, tau, disturb, 90.0f, 0.0f};
  HeadingHold hold;
  const float dt = 0.02f;                       // 50 Hz
  for (int i = 0; i <= 2000; ++i) {             // 40 s
    const float t = i * dt;
    const float target = t < 2.0f ? 90.0f : 100.0f;   // 10° step at t = 2 s; the push acts from t = 0
    const float turn = hold.update(target, boat.headingDeg, dt);
    printf("%s,%.2f,%.1f,%.3f,%.4f\n", name, t, target, boat.headingDeg, turn);
    boat.step(turn, dt);
  }
}

int main() {
  printf("model,t_s,target_deg,heading_deg,turn\n");
  run("nominal: 30 deg/s · tau 0.8 s", 30.0f, 0.8f, 5.0f);
  run("slow: 15 deg/s · tau 1.5 s", 15.0f, 1.5f, 5.0f);
  run("fast: 60 deg/s · tau 0.3 s", 60.0f, 0.3f, 5.0f);
  return 0;
}
