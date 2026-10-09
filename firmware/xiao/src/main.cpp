// AR-Mini firmware — skeleton. core 0: perception, core 1: control.
#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
enum State { SEARCH, APPROACH, DEPLOY, LIFT, STOW, SHORE, SAFE };
State state = SEARCH;
void setup() { Serial.begin(115200); }
void loop() { delay(10); }
