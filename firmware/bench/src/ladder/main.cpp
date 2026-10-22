// AR-Mini bench · ladder · the DevKit's three "ladder" inputs: VBAT divider, LEAK probe, KILL rocker. No actuators.
//
// On the DevKit-Lipo there is no resistor ladder on one ADC (that is the XIAO design): each signal has
// its own pin (breadboard 2b). The sketch keeps the name so the card / CSV match the XIAO version.
//
//   VBAT  GPIO4  ← 100 k / 30 k divider from the fuse block (F4): v_bat = v_adc × (100 + 30) / 30 ≈ v_adc × 4.33
//   SOURCE: C027 bench, measured 30 k on the bottom leg (carrier rev A keeps 33 k)
//   LEAK  GPIO7  ← 10 k to 3V3, 4.7 k to the probe, probe to GND when wet: ≈ 3.3 V dry, ≈ 1.06 V wet (sheet 2b)
//   KILL  GPIO14 ← 10 k to 3V3, rocker C → GPIO14, KILL → GND: 3.3 V in RUN, 0 V in KILL (sheet 2b)
//
// CSV: t_ms,v_adc_mV,v_bat_V,leak_mV,leak,kill
#include <Arduino.h>

#include "Bench.h"
#include "Cli.h"
#include "Csv.h"

namespace {

const float kDivGain = (VBAT_DIV_R_TOP_OHM + VBAT_DIV_R_BOT_OHM) / VBAT_DIV_R_BOT_OHM;  // 4.33 from the nominal resistors (130/30)
const int kLeakThresholdMv = 2000;  // VERIFY: midpoint between 3.3 V dry and ~1.06 V wet (sheet 2b); `leakth <mV>` to change
const int kAdcSamples = 16;         // average per reading to tame the ESP32 ADC noise

bench::Cli shell(Serial);
bench::KillInput killIn;
bench::Heartbeat heartbeat;
bench::Periodic csvTick(bench::kCsvPeriodMs);
float calGain = 1.0f;  // `cal <V_meter>` sets it from a multimeter reading; not stored
int leakTh = kLeakThresholdMv;

int readMv(int pin) {
  uint32_t sum = 0;
  for (int i = 0; i < kAdcSamples; ++i) sum += analogReadMilliVolts(pin);
  return static_cast<int>(sum / kAdcSamples);
}

void help() {
  bench::msg("ladder commands:");
  bench::msg("  cal <V>       set the gain so v_bat equals the multimeter reading <V> (prints the factor; not stored)");
  bench::msg("  cal 1         reset the gain to the nominal 100k/30k divider");
  bench::msg("  leakth <mV>   leak threshold, default %d mV (leak = 1 when leak_mV < threshold)", kLeakThresholdMv);
  bench::msg("  read          one line with all values now");
  bench::msg("  0             nothing to stop (no actuators)");
  bench::msg("state: gain=%.3f (nominal %.3f) cal=%.4f leakth=%d", kDivGain * calGain, kDivGain, calGain, leakTh);
}

void readAll(int& vAdc, float& vBat, int& leakMv, bool& leak, bool& kill) {
  vAdc = readMv(PIN_VBAT_ADC);
  vBat = vAdc / 1000.0f * kDivGain * calGain;
  leakMv = readMv(PIN_LEAK);
  leak = leakMv < leakTh;
  kill = killIn.active();
}

void handleCommand() {
  if (shell.is("?")) {
    help();
  } else if (shell.is("0")) {
    bench::msg("OK (no actuators)");
  } else if (shell.is("cal")) {
    bool ok = false;
    const float v = shell.argf(1, 0.0f, &ok);
    if (!ok || v <= 0.0f || v > 30.0f) {
      bench::err("cal (want the multimeter voltage in V, or 1 to reset)");
    } else if (v == 1.0f) {
      calGain = 1.0f;
      bench::msg("OK cal reset, gain %.3f", kDivGain);
    } else {
      const int vAdc = readMv(PIN_VBAT_ADC);
      const float nominal = vAdc / 1000.0f * kDivGain;
      if (nominal < 0.1f) {
        bench::msg("WARN v_adc is %d mV — is the divider connected?", vAdc);
      } else {
        calGain = v / nominal;
        bench::msg("OK cal: meter %.3f V, nominal %.3f V → factor %.4f (write it on the card; it is not stored)", v, nominal, calGain);
      }
    }
  } else if (shell.is("leakth")) {
    bool ok = false;
    const long v = shell.argl(1, 0, &ok);
    if (!ok || v < 0 || v > 3300) bench::err("leakth (want 0..3300 mV)");
    else {
      leakTh = static_cast<int>(v);
      bench::msg("OK leakth %d mV", leakTh);
    }
  } else if (shell.is("read")) {
    int vAdc, leakMv;
    float vBat;
    bool leak, kill;
    readAll(vAdc, vBat, leakMv, leak, kill);
    bench::msg("OK v_adc %d mV v_bat %.2f V leak %d mV (%s) kill %s", vAdc, vBat, leakMv, leak ? "WET" : "dry",
               kill ? "KILL" : "run");
  } else {
    bench::err(shell.arg(0));
  }
}

}  // namespace

void setup() {
  killIn.begin();
  heartbeat.begin();
  pinMode(PIN_VBAT_ADC, INPUT);
  pinMode(PIN_LEAK, INPUT);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);  // full 0..~3.1 V range; 12.6 V × 30/130 = 2.91 V. VERIFY the reading still follows a full pack
  bench::begin("ladder", "t_ms,v_adc_mV,v_bat_V,leak_mV,leak,kill");
  bench::msg("pins: VBAT GPIO%d (÷%.2f) · LEAK GPIO%d (th %d mV) · KILL GPIO%d (low = KILL)", PIN_VBAT_ADC, kDivGain, PIN_LEAK,
             leakTh, PIN_KILL);
  bench::msg("rows at 10 Hz. Type `?`.");
}

void loop() {
  const uint32_t now = millis();
  if (shell.poll()) handleCommand();
  heartbeat.update(now);

  if (csvTick.due(now)) {
    int vAdc, leakMv;
    float vBat;
    bool leak, kill;
    readAll(vAdc, vBat, leakMv, leak, kill);
    char buf[64];
    bench::CsvRow row(buf, sizeof buf);
    row.add(static_cast<unsigned long>(now)).add(vAdc).add(vBat, 2).add(leakMv).add(leak).add(kill);
    Serial.println(row.c_str());
  }
  delay(1);
}
