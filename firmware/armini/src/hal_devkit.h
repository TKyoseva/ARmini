// AR-Mini · DRY-RUN HAL for the Olimex ESP32-S3-DevKit-Lipo.
// Nothing drives hardware. Inputs are faked from serial commands, outputs are
// printed as CSV. See README.md "Dry run" for the command list.
#pragma once
#include <stdint.h>
#include <stddef.h>
#include "Hal.h"

namespace armini {

class DevkitDryRunHal : public Hal {
 public:
  DevkitDryRunHal(const Config& cfg, const SafetyConfig& scfg);

  // Serial.begin, wait for the USB CDC host (bounded), print banner + CSV header.
  void begin();

  void readInputs(Inputs& in) override;
  void readSafety(SafetyInputs& s) override;
  void writeOutputs(const Outputs& out) override;
  uint32_t nowMs() override;
  bool takeResetRequest() override;

  // Print a `# ...` comment line (ignored by CSV readers).
  void note(const char* msg);

 private:
  void pollSerial();
  void handleLine(char* line);
  void printHelp();
  void printInputs();

  static const size_t kLineMax = 64;

  const Config& cfg_;
  const SafetyConfig& scfg_;
  Inputs fake_;               // mission inputs (safety fields unused here)
  SafetyInputs fake_safety_;  // raw safety inputs: leak/kill/vbat/hb/ladder
  bool reset_requested_;
  char line_[kLineMax];
  size_t line_len_;
};

}  // namespace armini
