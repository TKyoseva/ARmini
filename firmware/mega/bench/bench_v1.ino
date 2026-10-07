// AR-Mini · Breadboard 1 · bench_v1.ino  (Arduino Mega 2560)
// Потенциометър на A0 → скорост/посока на един ROB0154 мотор през BTS7960 (D5 = RPWM, D6 = LPWM)
// и ъгъл на TD-8120MG на D9. Serial 115200 печата CSV: ms,pot,pwm,angle  (10 пъти в секунда).
// Enable на BTS7960 (R_EN + L_EN) е на rocker-а, не на Mega-та → KILL спира мотора хардуерно.
#include <Servo.h>

const int PIN_POT = A0, PIN_RPWM = 5, PIN_LPWM = 6, PIN_SERVO = 9;
const int DEAD = 25;          // ±25 около 512 = стоп
const int PWM_MAX = 150;      // първи тест: ~60 % от 255; вдигни до 255, когато всичко е наред
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
  if (pot > 512 + DEAD) {                   // напред
    pwm = map(pot, 512 + DEAD, 1023, 0, PWM_MAX);
    analogWrite(PIN_LPWM, 0); analogWrite(PIN_RPWM, pwm);
  } else if (pot < 512 - DEAD) {            // назад
    pwm = -map(pot, 512 - DEAD, 0, 0, PWM_MAX);
    analogWrite(PIN_RPWM, 0); analogWrite(PIN_LPWM, -pwm);
  } else {                                  // стоп
    analogWrite(PIN_RPWM, 0); analogWrite(PIN_LPWM, 0);
  }
  int angle = map(pot, 0, 1023, 20, 160);   // пази крайните 20° — не натискай упорите на сервото
  servo.write(angle);

  if (millis() - lastPrint >= 100) {
    lastPrint = millis();
    Serial.print(lastPrint); Serial.print(','); Serial.print(pot); Serial.print(',');
    Serial.print(pwm); Serial.print(','); Serial.println(angle);
  }
}
