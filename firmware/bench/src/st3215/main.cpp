// AR-Mini bench · st3215 · Waveshare ST3215 bus servo through the Waveshare Serial Bus Servo Driver.
//
// UART1 (GPIO17 TX → adapter RX, GPIO18 RX ← adapter TX), 1 000 000 baud (ST3215 factory default,
// SOURCE: SCServo library example "passed the test in ST3215 Servo"). The adapter does the
// half-duplex direction switching; the 12 V for the servo comes from the adapter's terminal, never from the DevKit.
//
// `pos <deg>` is ramped in degrees (Ramp, default 60 °/s) and refused outside the soft window.
// Soft window default: 60 % of the 360° range centred on 180° → 72°–288°; `limit <min> <max>` opens it.
// Dead-man (2 s) and `0` HALT the motion in place (goal = present position) — the servo keeps torque,
// so an arm does not drop; `torque 0` is the explicit way to make it limp.
//
// CSV: t_ms,id,cmd_deg,pos_deg,load_permille,temp_C,volt_V,ok
//   load_permille: library ReadLoad (0..±1000 = output voltage share to the motor; sign = direction);
//   volt_V: ReadVoltage / 10; ok 0/1 = the feedback packet was received this tick.
#include <Arduino.h>
#include <SCServo.h>

#include "Bench.h"
#include "Cli.h"
#include "Csv.h"
#include "Deadman.h"
#include "Ramp.h"

namespace {

const unsigned long kBusBaud = 1000000;  // SOURCE: SCServo example (ST3215 default 1 Mbps); `baud <n>` to change
const int kStepsPerRev = 4096;           // SOURCE: SCServo SMS_STS position range 0..4095 for one 360° turn (12-bit encoder, bom.csv row 29)
const float kDegPerStep = 360.0f / kStepsPerRev;
const float kDefaultMinDeg = 72.0f;      // 60 % of 360° centred on 180° (soft-limit rule of task T3)
const float kDefaultMaxDeg = 288.0f;
const float kRampDegPerS = 60.0f;        // VERIFY: 60 °/s chosen for the bench (ST3215 can do far more)
const uint16_t kDefaultSpeed = 1000;     // steps/s sent with every goal. VERIFY: Waveshare examples use 1500–3400
const uint8_t kDefaultAcc = 50;          // acceleration (×100 steps/s²). VERIFY: Waveshare examples use 50
const int kScanMaxId = 20;

SMS_STS st;
bench::Cli shell(Serial);
bench::Ramp ramp(kRampDegPerS, 180.0f);
bench::Deadman deadman(bench::kDeadmanMs);
bench::KillInput killIn;
bench::Heartbeat heartbeat;
bench::Periodic csvTick(bench::kCsvPeriodMs);

int servoId = 1;  // SOURCE: breadboard 2b ("ST3215 ID 1 answers a ping"); `id <n>` to change
float minDeg = kDefaultMinDeg, maxDeg = kDefaultMaxDeg;
uint16_t speed = kDefaultSpeed;
uint8_t acc = kDefaultAcc;
bool moving = false;    // true while ramp target differs from what we last wrote
int lastGoalSteps = -1;
float cmdDeg = 180.0f;  // accepted target
float posDeg = 0.0f;
int load = 0, tempC = 0;
float voltV = 0.0f;
bool fbOk = false;
uint32_t lastLoopMs = 0;

int degToSteps(float deg) {
  int s = static_cast<int>(deg / kDegPerStep + 0.5f);
  if (s < 0) s = 0;
  if (s > kStepsPerRev - 1) s = kStepsPerRev - 1;
  return s;
}

bool readFeedback() {
  if (st.FeedBack(servoId) == -1) return false;
  const int p = st.ReadPos(-1);
  posDeg = p * kDegPerStep;
  load = st.ReadLoad(-1);
  tempC = st.ReadTemper(-1);
  voltV = st.ReadVoltage(-1) / 10.0f;
  return true;
}

void writeGoal(float deg) {
  const int steps = degToSteps(deg);
  if (steps == lastGoalSteps) return;
  lastGoalSteps = steps;
  st.WritePosEx(static_cast<u8>(servoId), static_cast<s16>(steps), speed, acc);
}

// Halt in place: the present position becomes the goal, torque stays on.
void haltInPlace(const char* why) {
  if (readFeedback()) {
    ramp.stop(posDeg);
    cmdDeg = posDeg;
    lastGoalSteps = -1;
    writeGoal(posDeg);
  } else {
    ramp.stop(ramp.value());
  }
  moving = false;
  if (why) bench::msg("%s", why);
}

void help() {
  bench::msg("st3215 commands:");
  bench::msg("  id <1..253>          select servo (default 1)");
  bench::msg("  ping                 ping the selected id");
  bench::msg("  scan                 ping ids 1..%d", kScanMaxId);
  bench::msg("  pos <deg>            move (ramped at `rate`), refused outside the soft window");
  bench::msg("  read                 one feedback line now: pos, load, temp, volt");
  bench::msg("  torque 0|1           torque off (limp) / on");
  bench::msg("  speed <steps_s>      goal speed sent with each position, default %u", kDefaultSpeed);
  bench::msg("  acc <0..254>         acceleration, default %u", kDefaultAcc);
  bench::msg("  rate <deg_s>         ramp rate, default %.0f deg/s", kRampDegPerS);
  bench::msg("  limit <min> <max>    soft window in deg, default %.0f-%.0f; `limit 0 360` opens it (warning)", kDefaultMinDeg,
             kDefaultMaxDeg);
  bench::msg("  baud <n>             reopen the bus at another baud (default %lu)", kBusBaud);
  bench::msg("  dm <ms>              dead-man timeout, default %lu ms (0 = off)", static_cast<unsigned long>(bench::kDeadmanMs));
  bench::msg("  0                    halt in place (torque stays on)");
  bench::msg("state: id=%d cmd=%.1f pos=%.1f window=%.0f-%.0f rate=%.0f speed=%u acc=%u fb=%s kill=%d", servoId, cmdDeg,
             posDeg, minDeg, maxDeg, ramp.rate(), speed, acc, fbOk ? "ok" : "none", killIn.active() ? 1 : 0);
}

void openBus(unsigned long baud) {
  Serial1.end();
  Serial1.begin(baud, SERIAL_8N1, PIN_SRV_RX, PIN_SRV_TX);
  st.pSerial = &Serial1;
}

void handleCommand(uint32_t now) {
  deadman.feed(now);
  if (shell.is("?")) {
    help();
  } else if (shell.is("0")) {
    haltInPlace("OK halt");
  } else if (shell.is("id")) {
    bool ok = false;
    const long v = shell.argl(1, 0, &ok);
    if (!ok || v < 1 || v > 253) bench::err("id (want 1..253)");
    else {
      haltInPlace(nullptr);
      servoId = static_cast<int>(v);
      lastGoalSteps = -1;
      if (readFeedback()) {
        ramp.stop(posDeg);
        cmdDeg = posDeg;
        bench::msg("OK id %d (pos %.1f deg)", servoId, posDeg);
      } else {
        bench::msg("WARN id %d does not answer", servoId);
      }
    }
  } else if (shell.is("ping")) {
    const int r = st.Ping(static_cast<u8>(servoId));
    bench::msg("%s ping id %d", r == -1 ? "WARN no answer:" : "OK", servoId);
  } else if (shell.is("scan")) {
    int found = 0;
    for (int id = 1; id <= kScanMaxId; ++id) {
      if (st.Ping(static_cast<u8>(id)) != -1) {
        bench::msg("OK found id %d", id);
        ++found;
      }
    }
    if (found == 0) bench::msg("WARN no servo answered on ids 1..%d (12 V on the adapter? TX/RX swapped? baud?)", kScanMaxId);
  } else if (shell.is("pos")) {
    bool ok = false;
    const float v = shell.argf(1, 0.0f, &ok);
    if (!ok || v < 0.0f || v > 360.0f) {
      bench::err("pos (want 0..360 deg)");
    } else if (killIn.active()) {
      bench::msg("WARN KILL active (GPIO%d low): command refused", PIN_KILL);
    } else if (v < minDeg || v > maxDeg) {
      bench::msg("WARN %.1f deg outside the soft window %.0f-%.0f — send `limit <min> <max>` first", v, minDeg, maxDeg);
    } else {
      // Not mid-ramp → resync the ramp to the real horn position first (it may have been moved by hand
      // after `torque 0`, halted by KILL/dead-man, or never read if the servo was silent at boot).
      if (!moving && readFeedback()) ramp.stop(posDeg);
      cmdDeg = v;
      ramp.setTarget(v);
      moving = true;
      bench::msg("OK pos %.1f (from %.1f at %.0f deg/s)", v, ramp.value(), ramp.rate());
    }
  } else if (shell.is("read")) {
    if (readFeedback()) {
      bench::msg("OK id %d pos %.1f deg load %d temp %d C volt %.1f V move %d", servoId, posDeg, load, tempC, voltV,
                 st.ReadMove(servoId));
    } else {
      bench::msg("WARN id %d: no feedback", servoId);
    }
  } else if (shell.is("torque")) {
    const bool on = shell.argl(1, 0) != 0;
    moving = false;
    if (st.EnableTorque(static_cast<u8>(servoId), on ? 1 : 0) == -1) bench::msg("WARN torque: no answer");
    else bench::msg("OK torque %d%s", on ? 1 : 0, on ? "" : " (limp — hold the arm)");
    if (!on) lastGoalSteps = -1;
  } else if (shell.is("speed")) {
    bool ok = false;
    const long v = shell.argl(1, 0, &ok);
    if (!ok || v < 1 || v > 4000) bench::err("speed (want 1..4000 steps/s)");
    else {
      speed = static_cast<uint16_t>(v);
      bench::msg("OK speed %u", speed);
    }
  } else if (shell.is("acc")) {
    bool ok = false;
    const long v = shell.argl(1, 0, &ok);
    if (!ok || v < 0 || v > 254) bench::err("acc (want 0..254)");
    else {
      acc = static_cast<uint8_t>(v);
      bench::msg("OK acc %u", acc);
    }
  } else if (shell.is("rate")) {
    bool ok = false;
    const float v = shell.argf(1, 0.0f, &ok);
    if (!ok || v <= 0.0f || v > 720.0f) bench::err("rate (want 1..720 deg/s)");
    else {
      ramp.setRate(v);
      bench::msg("OK rate %.0f deg/s", v);
    }
  } else if (shell.is("limit")) {
    bool okA = false, okB = false;
    const float a = shell.argf(1, 0.0f, &okA);
    const float b = shell.argf(2, 0.0f, &okB);
    if (!okA || !okB || a < 0.0f || b > 360.0f || a >= b) bench::err("limit (want: limit <min> <max> within 0..360)");
    else {
      const bool wider = a < kDefaultMinDeg || b > kDefaultMaxDeg;
      minDeg = a;
      maxDeg = b;
      if (wider) bench::msg("WARN window widened to %.0f-%.0f deg — check the mechanical stops first", minDeg, maxDeg);
      else bench::msg("OK limit %.0f-%.0f deg", minDeg, maxDeg);
    }
  } else if (shell.is("baud")) {
    bool ok = false;
    const long v = shell.argl(1, 0, &ok);
    if (!ok || v < 9600 || v > 1000000) bench::err("baud (want 9600..1000000)");
    else {
      openBus(static_cast<unsigned long>(v));
      bench::msg("OK bus reopened at %ld baud", v);
    }
  } else if (shell.is("dm")) {
    bool ok = false;
    const long v = shell.argl(1, 0, &ok);
    if (!ok || v < 0) bench::err("dm (want ms >= 0)");
    else {
      deadman.setTimeout(static_cast<uint32_t>(v));
      bench::msg("OK dead-man %ld ms%s", v, v == 0 ? " (OFF — bench only)" : "");
    }
  } else {
    bench::err(shell.arg(0));
  }
}

}  // namespace

void setup() {
  killIn.begin();
  heartbeat.begin();
  openBus(kBusBaud);
  bench::begin("st3215", "t_ms,id,cmd_deg,pos_deg,load_permille,temp_C,volt_V,ok");
  bench::msg("pins: UART1 TX GPIO%d -> adapter RX, RX GPIO%d <- adapter TX, GND common · %lu baud · KILL GPIO%d",
             PIN_SRV_TX, PIN_SRV_RX, kBusBaud, PIN_KILL);
  delay(200);
  if (readFeedback()) {
    ramp.stop(posDeg);
    cmdDeg = posDeg;
    fbOk = true;
    bench::msg("OK id %d answers: pos %.1f deg, %.1f V, %d C", servoId, posDeg, voltV, tempC);
  } else {
    bench::msg("WARN id %d does not answer — `scan`, check 12 V on the adapter and TX/RX", servoId);
  }
  bench::msg("soft window %.0f-%.0f deg, ramp %.0f deg/s, dead-man %lu ms (halts in place). Type `?`.", minDeg, maxDeg,
             ramp.rate(), static_cast<unsigned long>(deadman.timeout()));
  lastLoopMs = millis();
}

void loop() {
  const uint32_t now = millis();
  const uint32_t dt = now - lastLoopMs;
  lastLoopMs = now;

  if (shell.poll()) handleCommand(now);

  if (killIn.risingKill()) haltInPlace("KILL (GPIO14 low) — halted in place");
  if (deadman.timeout() > 0 && deadman.update(now)) {
    if (moving) haltInPlace("DEADMAN");
    else bench::msg("DEADMAN");
  }

  if (moving && dt > 0) {
    writeGoal(ramp.update(dt));
    if (ramp.atTarget()) moving = false;
  }
  heartbeat.update(now);

  if (csvTick.due(now)) {
    fbOk = readFeedback();
    char buf[96];
    bench::CsvRow row(buf, sizeof buf);
    row.add(static_cast<unsigned long>(now)).add(servoId).add(cmdDeg, 1);
    if (fbOk) row.add(posDeg, 1).add(load).add(tempC).add(voltV, 1);
    else row.add("nan").add("nan").add("nan").add("nan");
    row.add(fbOk);
    Serial.println(row.c_str());
  }
  delay(1);
}
