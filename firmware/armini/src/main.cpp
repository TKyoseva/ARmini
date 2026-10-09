// AR-Mini · mission firmware · Olimex ESP32-S3-DevKit-Lipo · DRY RUN.
// Runs the platform-independent StateMachine at 10 Hz. Inputs come from serial
// commands, outputs go to Serial as CSV. No pin is driven (T1).
#include <Arduino.h>
#include "StateMachine.h"
#include "hal_devkit.h"

namespace {

const uint32_t kPeriodMs = 100;  // 10 Hz. SOURCE: AGENTS.md (CSV по serial с 10 Hz), task T1

armini::Config cfg;                  // defaults from lib/core/Types.h
armini::DevkitDryRunHal hal(cfg);
armini::StateMachine sm(cfg);

uint32_t next_tick_ms = 0;
uint32_t last_tick_ms = 0;

}  // namespace

void setup() {
  hal.begin();
  last_tick_ms = hal.nowMs();
  next_tick_ms = last_tick_ms + kPeriodMs;
}

void loop() {
  const uint32_t now = hal.nowMs();
  if (static_cast<int32_t>(now - next_tick_ms) < 0) {
    delay(1);
    return;
  }
  next_tick_ms += kPeriodMs;
  const uint32_t dt = now - last_tick_ms;
  last_tick_ms = now;

  armini::Inputs in;
  hal.readInputs(in);

  if (hal.takeResetRequest()) {
    hal.note(sm.reset() ? "reset: ok -> IDLE" : "reset: refused (not in SAFE, or a cause is still active)");
  }

  const armini::Outputs out = sm.tick(in, dt);
  hal.writeOutputs(out);
}
