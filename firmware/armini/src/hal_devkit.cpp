// AR-Mini · DRY-RUN HAL · implementation. Arduino only here, never in lib/core.
#include "hal_devkit.h"
#include <Arduino.h>
#include <string.h>
#include <stdlib.h>

namespace armini {

namespace {

// Simulated starting battery voltage: full 3S pack = 3 × 4.2 V.
// SOURCE: README "2 × LiPo 3S". This is a fake input, not a measurement.
const float kSimVbatFullV = 12.6f;

// How long to wait for the USB CDC host before printing anyway.
const uint32_t kUsbWaitMs = 3000;

bool parseBool(const char* s, bool& out) {
  if (s == nullptr) return false;
  if (strcmp(s, "1") == 0 || strcmp(s, "on") == 0 || strcmp(s, "true") == 0) { out = true; return true; }
  if (strcmp(s, "0") == 0 || strcmp(s, "off") == 0 || strcmp(s, "false") == 0) { out = false; return true; }
  return false;
}

bool parseFloat(const char* s, float& out) {
  if (s == nullptr) return false;
  char* end = nullptr;
  const float v = strtof(s, &end);
  if (end == s || *end != '\0') return false;
  out = v;
  return true;
}

}  // namespace

DevkitDryRunHal::DevkitDryRunHal(const Config& cfg, const SafetyConfig& scfg)
    : cfg_(cfg), scfg_(scfg), fake_(), fake_safety_(), reset_requested_(false), line_(), line_len_(0) {
  fake_.target_range_m = 100.0f;  // "far away" until a `see` command arrives
  fake_.arm_deg = cfg_.arm_stow_deg;  // assume the arm starts stowed; use `armdeg` to override
  fake_safety_.v_bat = kSimVbatFullV;  // full pack; use `vbat` to override
  // leak/kill false, heartbeat_ok true, ladder_v -1 (not fitted) from the defaults
}

void DevkitDryRunHal::begin() {
  Serial.begin(115200);
  const uint32_t t0 = millis();
  while (!Serial && (millis() - t0) < kUsbWaitMs) delay(10);
  Serial.println("# AR-Mini dry run · state machine + safety layer · no hardware is driven");
  Serial.println("# type ? for the command list");
  Serial.println("t_ms,state,reason,thrust_l,thrust_r,track_l,track_r,arm_deg,pan_deg,buzzer,flags");
}

uint32_t DevkitDryRunHal::nowMs() { return millis(); }

bool DevkitDryRunHal::takeResetRequest() {
  const bool r = reset_requested_;
  reset_requested_ = false;
  return r;
}

void DevkitDryRunHal::note(const char* msg) {
  Serial.print("# ");
  Serial.println(msg);
}

void DevkitDryRunHal::readInputs(Inputs& in) {
  pollSerial();
  in = fake_;
}

void DevkitDryRunHal::readSafety(SafetyInputs& s) {
  s = fake_safety_;  // serial already polled in readInputs() this tick
}

void DevkitDryRunHal::writeOutputs(const Outputs& out) {
  // flags bitmask: bit0 no_load, bit1 mission_complete, bit2 led_green,
  // bit3 led_yellow, bit4 led_red (documented in README).
  const unsigned flags = (out.flags.no_load ? 1u : 0u) | (out.flags.mission_complete ? 2u : 0u) |
                         (out.led_green ? 4u : 0u) | (out.led_yellow ? 8u : 0u) | (out.led_red ? 16u : 0u);
  Serial.printf("%lu,%s,%s,%.3f,%.3f,%.3f,%.3f,%.1f,%.1f,%d,%u\n",
                static_cast<unsigned long>(millis()), stateName(out.state), reasonName(out.reason),
                static_cast<double>(out.thrust_l), static_cast<double>(out.thrust_r),
                static_cast<double>(out.track_l), static_cast<double>(out.track_r),
                static_cast<double>(out.arm_deg), static_cast<double>(out.pan_deg),
                out.buzzer ? 1 : 0, flags);
}

// ---------------------------------------------------------------------------
// serial command parser

void DevkitDryRunHal::pollSerial() {
  while (Serial.available() > 0) {
    const int c = Serial.read();
    if (c < 0) break;
    if (c == '\n' || c == '\r') {
      if (line_len_ > 0) {
        line_[line_len_] = '\0';
        handleLine(line_);
        line_len_ = 0;
      }
    } else if (line_len_ < kLineMax - 1) {
      line_[line_len_++] = static_cast<char>(c);
    } else {
      line_len_ = 0;  // overflow: drop the line
      note("line too long, dropped");
    }
  }
}

void DevkitDryRunHal::handleLine(char* line) {
  char* save = nullptr;
  const char* cmd = strtok_r(line, " \t", &save);
  if (cmd == nullptr) return;
  const char* a1 = strtok_r(nullptr, " \t", &save);
  const char* a2 = strtok_r(nullptr, " \t", &save);
  const char* a3 = strtok_r(nullptr, " \t", &save);

  bool ok = false;
  if (strcmp(cmd, "?") == 0 || strcmp(cmd, "help") == 0) {
    printHelp();
    printInputs();
    return;
  } else if (strcmp(cmd, "reset") == 0) {
    reset_requested_ = true;
    ok = true;
  } else if (strcmp(cmd, "arm") == 0) {
    ok = parseBool(a1, fake_.armed);
  } else if (strcmp(cmd, "see") == 0) {
    bool s = false;
    ok = parseBool(a1, s);
    if (ok) {
      fake_.target_seen = s;
      float v;
      if (parseFloat(a2, v)) fake_.bearing_deg = v;
      if (parseFloat(a3, v)) fake_.target_range_m = v;
    }
  } else if (strcmp(cmd, "cradle") == 0) {
    ok = parseBool(a1, fake_.cradle_confirmed);
  } else if (strcmp(cmd, "armdeg") == 0) {
    ok = parseFloat(a1, fake_.arm_deg);
  } else if (strcmp(cmd, "load") == 0) {
    ok = parseBool(a1, fake_.load_detected);
  } else if (strcmp(cmd, "tilt") == 0) {
    ok = parseFloat(a1, fake_.tilt_deg);
  } else if (strcmp(cmd, "heading") == 0) {
    ok = parseFloat(a1, fake_.heading_deg);
  } else if (strcmp(cmd, "leak") == 0) {
    ok = parseBool(a1, fake_safety_.leak_raw);
  } else if (strcmp(cmd, "kill") == 0) {
    ok = parseBool(a1, fake_safety_.kill_raw);
  } else if (strcmp(cmd, "vbat") == 0) {
    ok = parseFloat(a1, fake_safety_.v_bat);
  } else if (strcmp(cmd, "hb") == 0) {
    ok = parseBool(a1, fake_safety_.heartbeat_ok);
  } else if (strcmp(cmd, "ladder") == 0) {
    ok = parseFloat(a1, fake_safety_.ladder_v);
  }

  if (ok) {
    Serial.print("# ok: ");
    Serial.println(cmd);
  } else {
    Serial.print("# bad command: ");
    Serial.println(cmd);
  }
}

void DevkitDryRunHal::printHelp() {
  Serial.println("# commands (fake inputs, persist until changed):");
  Serial.println("#   arm 0|1              armed switch");
  Serial.println("#   see 0|1 [bearing_deg] [range_m]   search camera target");
  Serial.println("#   cradle 0|1           cradle camera confirms target");
  Serial.println("#   armdeg <deg>         lift-arm feedback angle");
  Serial.println("#   load 0|1             load detected in cradle");
  Serial.println("#   tilt <deg>           IMU pitch, bow up +");
  Serial.println("#   heading <deg>        IMU yaw 0..360");
  Serial.println("#   leak 0|1  kill 0|1   raw safety inputs (leak debounced, kill immediate)");
  Serial.println("#   vbat <V>             pack voltage (trip < v_trip for batt_debounce_ms, reset > v_reset)");
  Serial.println("#   hb 0|1               heartbeat ok (trip after heartbeat_timeout_ms of 0)");
  Serial.println("#   ladder <V>           A1 ladder voltage, -1 = not fitted (<0.6 KILL, 0.6-2.0 LEAK, >2.0 OK)");
  Serial.println("#   reset                clear the safety latch and leave SAFE -> IDLE (refused while a cause is active)");
  Serial.println("#   ?                    this help + current fake inputs");
}

void DevkitDryRunHal::printInputs() {
  Serial.printf("# inputs: arm=%d see=%d bearing=%.1f range=%.2f cradle=%d armdeg=%.1f load=%d tilt=%.1f heading=%.1f\n",
                fake_.armed ? 1 : 0, fake_.target_seen ? 1 : 0, static_cast<double>(fake_.bearing_deg),
                static_cast<double>(fake_.target_range_m), fake_.cradle_confirmed ? 1 : 0,
                static_cast<double>(fake_.arm_deg), fake_.load_detected ? 1 : 0,
                static_cast<double>(fake_.tilt_deg), static_cast<double>(fake_.heading_deg));
  Serial.printf("# safety: leak=%d kill=%d vbat=%.2f hb=%d ladder=%.2f (%s) | leak %lu ms, batt %lu ms trip<%.2f reset>%.2f V, hb %lu ms\n",
                fake_safety_.leak_raw ? 1 : 0, fake_safety_.kill_raw ? 1 : 0,
                static_cast<double>(fake_safety_.v_bat), fake_safety_.heartbeat_ok ? 1 : 0,
                static_cast<double>(fake_safety_.ladder_v),
                ladderPresent(fake_safety_.ladder_v) ? ladderName(decodeLadder(fake_safety_.ladder_v)) : "none",
                static_cast<unsigned long>(scfg_.leak_debounce_ms), static_cast<unsigned long>(scfg_.batt_debounce_ms),
                static_cast<double>(scfg_.v_trip), static_cast<double>(scfg_.v_reset),
                static_cast<unsigned long>(scfg_.heartbeat_timeout_ms));
}

}  // namespace armini
