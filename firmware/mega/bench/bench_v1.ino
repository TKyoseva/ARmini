// AR-Mini · Breadboard 1 · bench_v1.ino  (Arduino Mega 2560)
// Potentiometer on A0 → speed/direction of one ROB0154 motor through a BTS7960 (D5 = RPWM, D6 = LPWM)
// and the angle of a TD-8120MG on D9. Serial 115200 prints CSV: ms,pot,pwm,angle  (10 times per second).
// BTS7960 enable (R_EN + L_EN) is on the rocker, not on the Mega → KILL stops the motor in hardware.
#include <Servo.h>

const int PIN_POT = A0, PIN_RPWM = 5, PIN_LPWM = 6, PIN_SERVO = 9;
const int DEAD = 25;          // ±25 around 512 = stop
const int PWM_MAX = 150;      // first test: ~60 % of 255; raise to 255 when everything is fine
Servo servo;
unsigned long lastPrint = 0;

void setup() {
  pinMode(PIN_RPWM, OUTPUT); pinMode(PIN_LPWM, OUTPUT);
  analogWrite(PIN_RPWM, 0); analogWrite(PIN_LPWM, 0);
  servo.attach(PIN_SERVO, 500, 2500);
  Serial.begin(115200);
  Serial.println("ms,pot,pwm,angle");
}

void loop() {
  int pot = analogRead(PIN_POT);            // 0..1023
  int pwm = 0;
  if (pot > 512 + DEAD) {                   // forward
    pwm = map(pot, 512 + DEAD, 1023, 0, PWM_MAX);
    analogWrite(PIN_LPWM, 0); analogWrite(PIN_RPWM, pwm);
  } else if (pot < 512 - DEAD) {            // reverse
    pwm = -map(pot, 512 - DEAD, 0, 0, PWM_MAX);
    analogWrite(PIN_RPWM, 0); analogWrite(PIN_LPWM, -pwm);
  } else {                                  // stop
    analogWrite(PIN_RPWM, 0); analogWrite(PIN_LPWM, 0);
  }
  int angle = map(pot, 0, 1023, 20, 160);   // keep 20° away from the ends — do not push the servo against its stops
  servo.write(angle);

  if (millis() - lastPrint >= 100) {
    lastPrint = millis();
    Serial.print(lastPrint); Serial.print(','); Serial.print(pot); Serial.print(',');
    Serial.print(pwm); Serial.print(','); Serial.println(angle);
  }
}
