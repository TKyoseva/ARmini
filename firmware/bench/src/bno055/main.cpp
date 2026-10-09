// AR-Mini bench · bno055 · 9-DOF IMU breakout on I2C-0 (Wire), Euler angles + calibration status at 10 Hz.
//
// No actuators: no ramp, no dead-man. `cal` prints the sensor offsets once the fusion reports full
// calibration (sys/gyro/acc/mag all 3) — move the board in figure-8s and rest it on its 6 faces to get there.
//
// CSV: t_ms,heading_deg,roll_deg,pitch_deg,cal_sys,cal_gyro,cal_acc,cal_mag
//   heading = orientation.x, roll = orientation.y, pitch = orientation.z as the Adafruit library maps the
//   BNO055 Euler vector. VERIFY by tilting the board: which column moves when you roll about the long axis?
#include <Adafruit_BNO055.h>
#include <Adafruit_Sensor.h>
#include <Arduino.h>
#include <Wire.h>

#include "Bench.h"
#include "Cli.h"
#include "Csv.h"
#include "I2cScan.h"

namespace {

const uint8_t kBnoAddr = BNO055_ADDRESS_A;  // 0x28. SOURCE: bom.csv row 78 + breadboard 2b ("0x28 on Wire")
const uint32_t kI2cHz = 100000;  // VERIFY: the BNO055 I2C is specified to 400 kHz but is known to clock-stretch; 100 kHz is the safe bench value
const bool kExtCrystalDefault = false;  // VERIFY: Adafruit boards have a 32 kHz crystal (use true); the GoTo breakout is unknown → off

Adafruit_BNO055 bno(55, kBnoAddr, &Wire);
bench::Cli shell(Serial);
bench::Heartbeat heartbeat;
bench::Periodic csvTick(bench::kCsvPeriodMs);
bool bnoOk = false;

void printStatus() {
  uint8_t sys = 0, selftest = 0, syserr = 0;
  bno.getSystemStatus(&sys, &selftest, &syserr);
  bench::msg("OK status sys=%u selftest=0x%02X (0x0F = all passed) error=%u temp=%d C", sys, selftest, syserr, bno.getTemp());
}

void printCal() {
  uint8_t s = 0, g = 0, a = 0, m = 0;
  bno.getCalibration(&s, &g, &a, &m);
  adafruit_bno055_offsets_t o;
  if (!bno.getSensorOffsets(o)) {
    bench::msg("WARN not fully calibrated yet (sys %u gyro %u acc %u mag %u; all must be 3) — figure-8s + rest on 6 faces", s, g,
               a, m);
    return;
  }
  bench::msg("OK offsets acc %d %d %d | gyro %d %d %d | mag %d %d %d | radius acc %d mag %d", o.accel_offset_x,
             o.accel_offset_y, o.accel_offset_z, o.gyro_offset_x, o.gyro_offset_y, o.gyro_offset_z, o.mag_offset_x,
             o.mag_offset_y, o.mag_offset_z, o.accel_radius, o.mag_radius);
  bench::msg("OK copy the line above into the card; nothing is stored on the board");
}

void help() {
  bench::msg("bno055 commands:");
  bench::msg("  cal         print calibration offsets (needs sys/gyro/acc/mag = 3/3/3/3)");
  bench::msg("  status      system status, self-test, error, chip temperature");
  bench::msg("  xtal 0|1    external 32 kHz crystal use (default %d) — re-inits the sensor", kExtCrystalDefault ? 1 : 0);
  bench::msg("  scan        I2C scan on Wire (SDA GPIO%d, SCL GPIO%d)", PIN_I2C0_SDA, PIN_I2C0_SCL);
  bench::msg("  0           nothing to stop (no actuators)");
  bench::msg("state: bno=%s", bnoOk ? "ok" : "MISSING");
}

bool initBno(bool xtal) {
  if (!bno.begin(OPERATION_MODE_NDOF)) return false;
  delay(50);
  bno.setExtCrystalUse(xtal);
  return true;
}

void handleCommand() {
  if (shell.is("?")) {
    help();
  } else if (shell.is("0")) {
    bench::msg("OK (no actuators)");
  } else if (shell.is("cal")) {
    if (bnoOk) printCal();
    else bench::msg("WARN no sensor");
  } else if (shell.is("status")) {
    if (bnoOk) printStatus();
    else bench::msg("WARN no sensor");
  } else if (shell.is("xtal")) {
    const bool on = shell.argl(1, 0) != 0;
    bnoOk = initBno(on);
    bench::msg("%s xtal %d (sensor re-initialised, calibration restarts)", bnoOk ? "OK" : "WARN init failed:", on ? 1 : 0);
  } else if (shell.is("scan")) {
    bench::i2cScan(Wire, "Wire");
  } else {
    bench::err(shell.arg(0));
  }
}

}  // namespace

void setup() {
  heartbeat.begin();
  Wire.begin(PIN_I2C0_SDA, PIN_I2C0_SCL, kI2cHz);
  bench::begin("bno055", "t_ms,heading_deg,roll_deg,pitch_deg,cal_sys,cal_gyro,cal_acc,cal_mag");
  bench::msg("pins: Wire SDA GPIO%d SCL GPIO%d · BNO055 @0x%02X · 3V3 from the DevKit", PIN_I2C0_SDA, PIN_I2C0_SCL, kBnoAddr);
  bnoOk = initBno(kExtCrystalDefault);
  if (bnoOk) {
    bench::msg("OK BNO055 found, NDOF mode, ext crystal %d", kExtCrystalDefault ? 1 : 0);
    printStatus();
  } else {
    bench::msg("WARN BNO055 not found at 0x%02X — check wiring (ADR pin low = 0x28), then `scan`", kBnoAddr);
  }
  bench::msg("rows at 10 Hz. Type `?`.");
}

void loop() {
  const uint32_t now = millis();
  if (shell.poll()) handleCommand();
  heartbeat.update(now);

  if (csvTick.due(now)) {
    char buf[96];
    bench::CsvRow row(buf, sizeof buf);
    row.add(static_cast<unsigned long>(now));
    if (bnoOk) {
      sensors_event_t ev;
      bno.getEvent(&ev, Adafruit_BNO055::VECTOR_EULER);
      uint8_t s = 0, g = 0, a = 0, m = 0;
      bno.getCalibration(&s, &g, &a, &m);
      row.add(ev.orientation.x, 1).add(ev.orientation.y, 1).add(ev.orientation.z, 1).add(s).add(g).add(a).add(m);
    } else {
      row.add("nan").add("nan").add("nan").add(0).add(0).add(0).add(0);
    }
    Serial.println(row.c_str());
  }
  delay(1);
}
