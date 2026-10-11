// AR-Mini · mission firmware · Olimex ESP32-S3-DevKit-Lipo · DRY RUN.
// Runs the platform-independent Safety layer and StateMachine at 10 Hz.
// Inputs come from serial commands, outputs go to Serial as CSV. No pin is
// driven (T1 + T2). The ESP32 task watchdog is armed so a hung loop reboots.
#include <Arduino.h>
#include <esp_idf_version.h>
#include <esp_task_wdt.h>
#include "Safety.h"
#include "StateMachine.h"
#include "hal_devkit.h"

namespace {

const uint32_t kPeriodMs = 100;  // 10 Hz. SOURCE: AGENTS.md (CSV over serial at 10 Hz), task T1

// Task watchdog: loop() must call esp_task_wdt_reset() at least this often or
// the chip panics and reboots. 20 × the tick period. SOURCE: task T2 ("2 s").
const uint32_t kWatchdogTimeoutS = 2;

armini::Config       cfg;   // defaults from lib/core/Types.h
armini::SafetyConfig scfg;  // defaults from lib/core/Safety.h (all VERIFY)
armini::DevkitDryRunHal hal(cfg, scfg);
armini::Safety       safety(scfg);
armini::StateMachine sm(cfg);

uint32_t next_tick_ms = 0;
uint32_t last_tick_ms = 0;

void armWatchdog() {
#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 0, 0)
  // IDF 5 (arduino-esp32 3.x): the TWDT is usually already initialised by the
  // core, so reconfigure; fall back to init if it was not.
  esp_task_wdt_config_t wdt_cfg = {};
  wdt_cfg.timeout_ms = kWatchdogTimeoutS * 1000;
  wdt_cfg.idle_core_mask = 0;
  wdt_cfg.trigger_panic = true;
  if (esp_task_wdt_reconfigure(&wdt_cfg) != ESP_OK) esp_task_wdt_init(&wdt_cfg);
#else
  // IDF 4.4 (arduino-esp32 2.x): re-initialising with a new timeout is allowed.
  esp_task_wdt_init(kWatchdogTimeoutS, true);
#endif
  esp_task_wdt_add(nullptr);  // subscribe the Arduino loop task
  esp_task_wdt_reset();
}

}  // namespace

void setup() {
  hal.begin();
  armWatchdog();
  hal.note("task watchdog armed: 2 s, panic + reboot if loop() stalls");
  last_tick_ms = hal.nowMs();
  next_tick_ms = last_tick_ms + kPeriodMs;
}

void loop() {
  esp_task_wdt_reset();  // every pass, including the idle wait below

  const uint32_t now = hal.nowMs();
  if (static_cast<int32_t>(now - next_tick_ms) < 0) {
    delay(1);
    return;
  }
  next_tick_ms += kPeriodMs;
  const uint32_t dt = now - last_tick_ms;
  last_tick_ms = now;

  // 1. Raw inputs.
  armini::Inputs in;
  hal.readInputs(in);
  armini::SafetyInputs sin;
  hal.readSafety(sin);

  // 2. Safety verdict for this tick (debounce, hysteresis, latch).
  armini::Verdict verdict = safety.tick(sin, now);

  // 3. Operator reset: clear the safety latch first (refused while any cause
  //    is still active), then let the state machine see one tick without the
  //    cause before its own reset() below.
  const bool want_reset = hal.takeResetRequest();
  if (want_reset && safety.tripped()) {
    if (safety.reset()) {
      hal.note("safety reset: ok");
      verdict = safety.verdict();
    } else {
      hal.note("safety reset: refused (a cause is still active)");
    }
  }

  // 4. The verdict is the only safety input the mission logic ever sees.
  armini::applyVerdict(verdict, in);
  const armini::Outputs out = sm.tick(in, dt);

  if (want_reset) {
    hal.note(sm.reset() ? "reset: ok -> IDLE from the next tick"
                        : "reset: refused (not in SAFE, or the safety layer is still tripped)");
  }

  hal.writeOutputs(out);
}
