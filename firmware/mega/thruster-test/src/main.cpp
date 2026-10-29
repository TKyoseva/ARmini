// C055 - thruster bench test on Arduino Mega 2560 (Joy-it MEGA 2560-P), PlatformIO
#include <Arduino.h>
// Drives one ESC signal (yellow) straight from a 5 V pin: no S8050, no inversion.
// Serial 115200, LF.  <us> = ramp to target | 0 / s = stop | arm = 1500 for 3 s | limit = 1100-1900 | ? = help
// CSV every 100 ms: t_ms,target_us,out_us. Dead-man: 20 s without a command -> 1500 us.

#include <Servo.h>

const uint8_t ESC_PIN = 9;          // yellow; white (signal GND) -> Mega GND
const int STOP_US = 1500;
const int RAMP_US_PER_S = 200;
const unsigned long DEADMAN_MS = 20000;

int lo = 1350, hi = 1650;
int target = STOP_US;
float out = STOP_US;
unsigned long lastCmd = 0, lastTick = 0, lastPrint = 0;
Servo esc;
String line;

void help() {
  Serial.println(F("# C055 Mega thruster test. <us> | 0/s stop | arm | limit | ?"));
  Serial.print(F("# soft limit ")); Serial.print(lo); Serial.print('-'); Serial.println(hi);
  Serial.println(F("t_ms,target_us,out_us"));
}

void stopNow() { target = STOP_US; out = STOP_US; esc.writeMicroseconds(STOP_US); }

void handle(String c) {
  c.trim();
  lastCmd = millis();
  if (c == "?") { help(); return; }
  if (c == "0" || c == "s") { stopNow(); Serial.println(F("# STOP")); return; }
  if (c == "arm") {
    stopNow(); Serial.println(F("# ARM: 1500 us for 3 s"));
    delay(3000); Serial.println(F("# armed")); lastCmd = millis(); return;
  }
  if (c == "limit") { lo = 1100; hi = 1900; Serial.println(F("# WARN limit 1100-1900, watch the PSU current")); return; }
  int us = c.toInt();
  if (us < 1000 || us > 2000) { Serial.println(F("# ? unknown")); return; }
  target = constrain(us, lo, hi);
  if (target != us) { Serial.print(F("# clamped to ")); Serial.println(target); }
}

void setup() {
  esc.attach(ESC_PIN);
  stopNow();
  Serial.begin(115200);
  help();
  lastCmd = lastTick = millis();
}

void loop() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') { if (line.length()) handle(line); line = ""; }
    else line += ch;
  }
  unsigned long now = millis();
  if (target != STOP_US && now - lastCmd > DEADMAN_MS) {
    stopNow(); Serial.println(F("# DEAD-MAN: 20 s without a command -> 1500"));
  }
  float dt = (now - lastTick) / 1000.0; lastTick = now;
  float step = RAMP_US_PER_S * dt;
  if (out < target) out = min(out + step, (float)target);
  else if (out > target) out = max(out - step, (float)target);
  esc.writeMicroseconds((int)out);
  if (now - lastPrint >= 100) {
    lastPrint = now;
    Serial.print(now); Serial.print(','); Serial.print(target); Serial.print(','); Serial.println((int)out);
  }
}
