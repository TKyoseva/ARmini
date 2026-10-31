// AR-Mini bench · remote · both thruster ESCs from a phone over WiFi (T12, card t-remote-wifi C028).
//
// The DevKit is its own WPA2 access point (channel 6, 192.168.4.1, one client). The phone opens one page
// (served from flash, no CDN) with two sliders (thrust, turn), ARM and a big STOP. Page → board over a
// WebSocket on port 81 every 100 ms: {"t":-100..100,"r":-100..100,"arm":0|1} or {"stop":1}.
// Board → page every 200 ms: {"l":us,"r":us,"armed":0|1,"kill":0|1,"vbat":V,"rssi":dBm,"safe":"<reason>"}.
//
// Same safety contract as the `esc` env:
//   - both ESC outputs at 1500 µs (inverted duty, S8050 NPN, C006) from the first line of setup();
//   - nothing moves until ARM: sliders at 0/0, 1500 µs held 3 s, then armed;
//   - SAFE = both 1500 µs at once (no ramp) + disarm, for: no valid message for > 500 ms ("heartbeat"),
//     KILL rocker ("kill"), page STOP ("stop"), client disconnect ("disconnect"), `0` on serial ("serial").
//     Re-arm needed after any SAFE;
//   - mix + dead band (EscMath escMixDeadband) inside 1350–1650 µs, ramp 200 µs/s.
// KILL is a software stop; the hardware stop is the bench supply OUTPUT button / the main switch.
//
// Env `remote_rudder` (-DREMOTE_RUDDER, C056): left ESC = thrust only (turn ignored); the right channel (GPIO2) drives
// an MG90S rudder directly, NOT inverted, rudder = rudderUs(turn) 1167–1833 µs, own fast ramp; SAFE centres it (1500).
//
// Env `remote_pool` (-DREMOTE_RUDDER -DESC_BUFFER -DREMOTE_LIFT, pool run 31.10.2026): the two cradle servos (TD-8120MG on
// PCA9685 CH12/CH13 over I2C-0, `pair` maths from C023) follow a third slider "lift" 50–130°: 50 = U deployed (down),
// 130 = raised between the hulls. Pulses are OFF at boot, start on ARM with a snap to the slider (the U must already be
// in that pose), then ramp at 20 °/s. They HOLD through every SAFE (heartbeat, STOP, disconnect, serial `0`) so the U
// never drops into the water on a WiFi hiccup, and go OFF only on KILL (servos limp, the U settles deployed).
//
// CSV (serial, 10 Hz): t_ms,l_us,r_us,armed,kill,vbat,clients,last_hb_ms[,lift_deg]   (last_hb_ms = age, −1 = none yet;
// lift_deg only with REMOTE_LIFT, −1 = pulses off)
#include <Arduino.h>
#include <WebServer.h>
#include <WebSocketsServer.h>
#include <WiFi.h>
#include <esp_wifi.h>
#ifdef REMOTE_LIFT
#include <Adafruit_PWMServoDriver.h>
#include <Wire.h>
#endif

#if __has_include("secrets.h")
#include "secrets.h"
#if !defined(AP_SSID) || !defined(AP_PASS)
#error "secrets.h must define AP_SSID and AP_PASS (see include/secrets.example.h)"
#endif
#else
#error "firmware/bench/include/secrets.h missing: copy include/secrets.example.h to include/secrets.h and set AP_PASS"
#endif

#include "Bench.h"
#include "Cli.h"
#include "Csv.h"
#include "EscMath.h"
#include "Ramp.h"
#include "Remote.h"
#include "Vbat.h"
#ifdef REMOTE_LIFT
#include "PairMath.h"
#endif

namespace {

const uint32_t kEscHz = 50;           // SOURCE: C002 thruster listing; esc env (T10)
const uint8_t kEscBits = 14;          // SOURCE: T10
const float kFrameUs = 1000000.0f / kEscHz;
#ifdef ESC_BUFFER
const bool kEscInvert = false;        // SOURCE: C058 (74HCT125 non-inverting buffer at +5 V, S8050 stage removed)
#else
const bool kEscInvert = true;         // SOURCE: C006 (ESC input pulled up to 5 V, driven through S8050 NPN)
#endif
const float kRampUsPerS = 200.0f;     // SOURCE: T10 / T12
const uint32_t kArmHoldMs = 3000;     // SOURCE: T10 (arm holds 1500 µs for 3 s)
const float kLoUs = bench::kEscNarrowLoUs;  // SOURCE: T12 soft limit 1350–1650
const float kHiUs = bench::kEscNarrowHiUs;
#ifdef REMOTE_RUDDER
const bool kRInvert = false;          // SOURCE: RUDDER_SPEC §3 (MG90S on GPIO2 direct, no S8050)
const float kRampRUsPerS = 2000.0f;   // rudder: full swing in ~0.33 s (servo itself is slower)
#else
const bool kRInvert = kEscInvert;
const float kRampRUsPerS = kRampUsPerS;
#endif
const uint8_t kLedcChL = 0;
const uint8_t kLedcChR = 1;
const uint8_t kApChannel = 6;         // SOURCE: T12
const uint32_t kStatusMs = 200;       // SOURCE: T12 (board → page every 200 ms)
const int kAdcSamples = 16;
const float kDivGain = (VBAT_DIV_R_TOP_OHM + VBAT_DIV_R_BOT_OHM) / VBAT_DIV_R_BOT_OHM;

#define LIFT_DEG_LO 50   // SOURCE: C023 result — `pair 10 11 50` = U deployed (down, resting)
#define LIFT_DEG_HI 130  // SOURCE: C023 result — `pair 10 11 130` = U raised between the hulls
#define XSTR(x) STR(x)
#define STR(x) #x
#ifdef REMOTE_LIFT
const uint8_t kPcaAddr = 0x40;        // SOURCE: docs/bom/bom.csv row 72 (I2C address 0x40)
const float kServoHz = 50.0f;         // SOURCE: pca9685 env (C023)
const uint32_t kOscHz = 25000000;     // library default, as the pca9685 env (VERIFY: frame period with the analyser)
const uint32_t kI2cHz = 400000;       // SOURCE: pca9685 env, ran on the breadboard 22–23.10 (C023)
const uint8_t kLiftChA = 12;          // SOURCE: hardware/wiring/PINOUT.md "PCA9685 channels" (C023) // 31.10: CH10 output dead on this module (C059), servo A moved to CH12.
const uint8_t kLiftChB = 13;          // mirrored: us_B = 3000 − us_A (PairMath) // 31.10: CH11 output dead too (0 V on the PWM pin, C059), servo B moved to CH13.
const int kLiftDegLo = LIFT_DEG_LO;
const int kLiftDegHi = LIFT_DEG_HI;
const float kLiftDegPerS = bench::kPairDefaultDegPerS;  // 20 °/s (C023)
const float kLiftMinUs = 1000.0f;     // SOURCE: pca9685 default soft window (45–135°); 50–130° stays inside with zero trim
const float kLiftMaxUs = 2000.0f;
#ifndef LIFT_TRIM_A_US
#define LIFT_TRIM_A_US 0
#endif
#ifndef LIFT_TRIM_B_US
#define LIFT_TRIM_B_US 0
#endif
const float kLiftTrimA = static_cast<float>(LIFT_TRIM_A_US);  // SOURCE: C023 — trim changed nothing, both 0 (build flag)
const float kLiftTrimB = static_cast<float>(LIFT_TRIM_B_US);
// Page pieces that exist only with the lift: the third slider column, its JS hook, the JSON field, the CSV column.
#define LIFT_COL "<div><div class=\"trk\" id=\"ut\"><div class=\"knob\" id=\"uk\"></div></div><div class=\"lbl\">lift <span id=\"uv\">" XSTR(LIFT_DEG_LO) "</span>&deg;</div></div>"
#define LIFT_JS "hold(document.getElementById('ut'),document.getElementById('uk'),document.getElementById('uv')," XSTR(LIFT_DEG_LO) "," XSTR(LIFT_DEG_HI) ",function(v){u=v;});"
#define LIFT_MSG "',\"lift\":'+u+"
#define LIFT_CSV ",lift_deg"
#else
#define LIFT_COL ""
#define LIFT_JS ""
#define LIFT_MSG ""
#define LIFT_CSV ""
#endif

const char kPage[] PROGMEM = R"HTML(<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>AR-Mini</title><style>
*{box-sizing:border-box;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}
html,body{margin:0;height:100%;background:#111;color:#eee;font:16px -apple-system,Helvetica,sans-serif;overflow:hidden;touch-action:none}
#bar{padding:8px;text-align:center;background:#222}#bar.bad{background:#a00}
#row{display:flex;justify-content:space-around;align-items:stretch;height:calc(100% - 200px);padding:12px 0}
#row>div{display:flex;flex-direction:column;align-items:center}
.trk{position:relative;width:90px;flex:1;background:#333;border-radius:45px;touch-action:none}
.knob{position:absolute;left:5px;width:80px;height:80px;border-radius:40px;background:#ccc;top:calc(50% - 40px)}
.lbl{text-align:center;margin-top:4px}
#btns{display:flex;gap:10px;padding:10px;height:150px}
button{flex:1;font-size:28px;font-weight:bold;border:0;border-radius:16px;color:#fff;touch-action:manipulation}
#arm{background:#265}#arm.on{background:#2a4}#stop{background:#c00;flex:2}#stop.on{background:#f33}
</style></head><body>
<div id="bar">connecting…</div>
<div id="row"><div><div class="trk" id="tt"><div class="knob" id="tk"></div></div><div class="lbl">thrust <span id="tv">0</span></div></div>
<div><div class="trk" id="rt"><div class="knob" id="rk"></div></div><div class="lbl">turn <span id="rv">0</span></div></div>)HTML" LIFT_COL R"HTML(</div>
<div id="btns"><button id="arm">ARM</button><button id="stop">STOP</button></div>
<script>
var t=0,r=0,u=0,armReq=0,stopped=1,ws=null,lastRx=0,st={};
function slider(trk,knob,lab,set){var id=null;
 function mv(e){var b=trk.getBoundingClientRect();if(!(b.height>0))return;var y=(e.clientY-b.top)/b.height;y=Math.max(0,Math.min(1,y));
  var v=Math.round((0.5-y)*200);v=Math.max(-100,Math.min(100,v));set(v);lab.textContent=v;knob.style.top=(y*b.height-40)+'px';}
 function up(e){if(e.pointerId!==id)return;id=null;set(0);lab.textContent=0;knob.style.top='calc(50% - 40px)';}
 trk.addEventListener('pointerdown',function(e){id=e.pointerId;trk.setPointerCapture(id);mv(e);e.preventDefault();});
 trk.addEventListener('pointermove',function(e){if(e.pointerId===id)mv(e);e.preventDefault();});
 trk.addEventListener('pointerup',up);trk.addEventListener('pointercancel',up);}
slider(document.getElementById('tt'),document.getElementById('tk'),document.getElementById('tv'),function(v){t=v;});
slider(document.getElementById('rt'),document.getElementById('rk'),document.getElementById('rv'),function(v){r=v;});
function hold(trk,knob,lab,lo,hi,set){var id=null;
 function mv(e){var b=trk.getBoundingClientRect();if(!(b.height>0))return;var y=(e.clientY-b.top)/b.height;y=Math.max(0,Math.min(1,y));
  var v=Math.round(lo+(1-y)*(hi-lo));set(v);lab.textContent=v;knob.style.top=(y*b.height-40)+'px';}
 function up(e){if(e.pointerId===id)id=null;}
 trk.addEventListener('pointerdown',function(e){id=e.pointerId;trk.setPointerCapture(id);mv(e);e.preventDefault();});
 trk.addEventListener('pointermove',function(e){if(e.pointerId===id)mv(e);e.preventDefault();});
 trk.addEventListener('pointerup',up);trk.addEventListener('pointercancel',up);knob.style.top='calc(100% - 80px)';}
)HTML" LIFT_JS R"HTML(
var sb=document.getElementById('stop'),ab=document.getElementById('arm'),bar=document.getElementById('bar');
sb.addEventListener('pointerdown',function(e){stopped=1;e.preventDefault();});
ab.addEventListener('pointerdown',function(e){stopped=0;armReq=1;e.preventDefault();});
function conn(){ws=new WebSocket('ws://'+location.hostname+':81/');
 ws.onmessage=function(e){try{st=JSON.parse(e.data);lastRx=Date.now();}catch(x){}};
 ws.onclose=function(){setTimeout(conn,1000);};}
conn();
setInterval(function(){if(!ws||ws.readyState!==1)return;
 if(stopped){ws.send('{"stop":1}');}else{ws.send('{"t":'+t+',"r":'+r+',"arm":'+armReq+)HTML" LIFT_MSG R"HTML('}');armReq=0;}},100);
setInterval(function(){var age=lastRx?Date.now()-lastRx:-1;
 bar.className=(age<0||age>300)?'bad':'';
 bar.textContent='vbat '+(st.vbat!==undefined?st.vbat.toFixed(2):'?')+' V · kill '+(st.kill?'ON':'off')+' · link '+(age<0?'—':age+' ms')+
  ' · rssi '+(st.rssi!==undefined?st.rssi:'?')+' · l '+(st.l||'?')+' r '+(st.r||'?')+(st.u!==undefined?' · lift '+(st.u>=0?st.u+'°':'off'):'')+(st.safe?' · SAFE '+st.safe:'');
 ab.className=st.armed?'on':'';sb.className=stopped?'on':'';ab.textContent=st.armed?'ARMED':'ARM';},100);
</script></body></html>)HTML";

WebServer http(80);
WebSocketsServer ws(81);
bench::Cli shell(Serial);
bench::Ramp rampL(kRampUsPerS, bench::kEscNeutralUs);
bench::Ramp rampR(kRampRUsPerS, bench::kEscNeutralUs);
bench::KillInput killIn;
bench::Heartbeat heartbeat;
bench::Periodic csvTick(bench::kCsvPeriodMs);
bench::Periodic statusTick(kStatusMs);

bool apOk = false;
bool armed = false;
bool arming = false;
uint32_t armDoneMs = 0;
bool hbSeen = false;  // a valid message arrived since the last SAFE (only then can the link "drop")
uint32_t lastHbMs = 0;
bool everHb = false;
int clients = 0;
int driver = -1;  // WebSocket client number of the one phone allowed to drive
int lastL = -1, lastR = -1;
float vbat = 0.0f;
const char* safeReason = "boot";
uint32_t lastLoopMs = 0;
#ifdef REMOTE_LIFT
Adafruit_PWMServoDriver pca(kPcaAddr, Wire);
bench::Ramp liftRamp(kLiftDegPerS, 0.0f);  // the pair's shared degree
bool pcaOk = false;
bool liftOn = false;       // pulses on CH12/CH13: off at boot and after KILL, on from ARM (or serial `lift`)
int liftReq = kLiftDegLo;  // last slider value from the page (clamped when used)
int lastUsA = 0, lastUsB = 0;
#endif

void writeUs(int pin, uint8_t ch, int us) {
  const uint32_t duty = bench::escDuty(static_cast<float>(us), kEscBits, pin == PIN_ESC_R ? kRInvert : kEscInvert, kFrameUs);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  (void)ch;
  ledcWrite(pin, duty);
#else
  (void)pin;
  ledcWrite(ch, duty);
#endif
}

void attachEsc() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_ESC_L, kEscHz, kEscBits);
  ledcAttach(PIN_ESC_R, kEscHz, kEscBits);
#else
  ledcSetup(kLedcChL, kEscHz, kEscBits);
  ledcSetup(kLedcChR, kEscHz, kEscBits);
  ledcAttachPin(PIN_ESC_L, kLedcChL);
  ledcAttachPin(PIN_ESC_R, kLedcChR);
#endif
  const int n = static_cast<int>(bench::kEscNeutralUs);
  writeUs(PIN_ESC_L, kLedcChL, n);
  writeUs(PIN_ESC_R, kLedcChR, n);
  lastL = lastR = n;
}

void applyOutputs() {
  const int l = static_cast<int>(rampL.value() + 0.5f);
  const int r = static_cast<int>(rampR.value() + 0.5f);
  if (l != lastL) {
    writeUs(PIN_ESC_L, kLedcChL, l);
    lastL = l;
  }
  if (r != lastR) {
    writeUs(PIN_ESC_R, kLedcChR, r);
    lastR = r;
  }
}

#ifdef REMOTE_LIFT
int liftClamp(int deg) { return deg < kLiftDegLo ? kLiftDegLo : (deg > kLiftDegHi ? kLiftDegHi : deg); }
int liftDeg() { return liftOn ? static_cast<int>(liftRamp.value() + 0.5f) : -1; }

void liftWrite(uint8_t ch, int us) {
  if (!pcaOk) return;
  if (us <= 0) pca.setPWM(ch, 0, 0);  // no pulse at all
  else pca.writeMicroseconds(ch, static_cast<uint16_t>(us));
}

// Both pulses off: the servos go limp and the U settles deployed. Only boot, KILL and serial `lift off` do this.
void liftOff() {
  liftOn = false;
  liftRamp.stop(0.0f);
  lastUsA = lastUsB = 0;
  liftWrite(kLiftChA, 0);
  liftWrite(kLiftChB, 0);
}

// First pulse after off: snap to `deg` (nothing to ramp from — the U must already be in that pose, C023).
// While on: ramp there at kLiftDegPerS.
void liftGo(int deg) {
  if (!pcaOk) return;
  deg = liftClamp(deg);
  if (!liftOn) {
    liftRamp.stop(static_cast<float>(deg));
    liftOn = true;
    bench::msg("lift ON at %d deg (snap: the U must already be there)", deg);
  } else {
    liftRamp.setTarget(static_cast<float>(deg));
  }
}

// Every loop: ramp the shared degree, write the two pulses when they change.
void liftUpdate(uint32_t dt) {
  if (!liftOn || !pcaOk) return;
  const float deg = liftRamp.update(dt);
  const bench::PairPulses p = bench::pairFromDegTrim(deg, kLiftTrimA, kLiftTrimB);
  if (!bench::pairInWindow(p, kLiftMinUs, kLiftMaxUs)) return;  // cannot happen inside 50–130° with zero trim
  const int ua = static_cast<int>(p.us_a + 0.5f);
  const int ub = static_cast<int>(p.us_b + 0.5f);
  if (ua != lastUsA) {
    lastUsA = ua;
    liftWrite(kLiftChA, ua);
  }
  if (ub != lastUsB) {
    lastUsB = ub;
    liftWrite(kLiftChB, ub);
  }
}
#endif

// Both 1500 µs at once, disarm. Prints `# SAFE <reason>` only on a change, so a held STOP does not flood serial.
// With REMOTE_LIFT: KILL drops the lift pulses too (limp); every other SAFE holds the lift where it is.
void goSafe(const char* reason) {
  rampL.stop(bench::kEscNeutralUs);
  rampR.stop(bench::kEscNeutralUs);
  applyOutputs();
#ifdef REMOTE_LIFT
  if (strcmp(reason, "kill") == 0) {
    if (liftOn) bench::msg("lift OFF (KILL): servos limp, the U settles deployed — lift slider down to %d before ARM", kLiftDegLo);
    liftOff();
  } else {
    liftRamp.setTarget(liftRamp.value());  // hold: a ramp in progress stops here, nothing drops into the water
  }
#endif
  const bool wasLive = armed || arming;
  armed = false;
  arming = false;
  hbSeen = false;
  if (wasLive || strcmp(reason, safeReason) != 0) bench::msg("SAFE %s", reason);
  safeReason = reason;
}

int readMv(int pin) {
  uint32_t sum = 0;
  for (int i = 0; i < kAdcSamples; ++i) sum += analogReadMilliVolts(pin);
  return static_cast<int>(sum / kAdcSamples);
}

int apRssi() {
  wifi_sta_list_t list;
  if (esp_wifi_ap_get_sta_list(&list) != ESP_OK || list.num == 0) return 0;
  return list.sta[0].rssi;
}

void onMessage(const char* text, uint32_t now) {
  bench::RemoteMsg m;
  if (!bench::parseRemoteMsg(text, &m)) return;  // not a heartbeat
  lastHbMs = now;
  hbSeen = true;
  everHb = true;
#ifdef REMOTE_LIFT
  if (m.lift >= 0) liftReq = m.lift;  // remembered before ARM too: the first pulse snaps to it
#endif
  if (m.stop) {
    goSafe("stop");
    return;
  }
  if (killIn.active()) return;  // KILL holds SAFE; messages keep the link alive but move nothing
  if (m.arm && !armed && !arming) {
    if (m.t != 0 || m.r != 0) {
      bench::msg("WARN arm refused: sliders must be at 0/0 (t=%d r=%d)", m.t, m.r);
    } else {
      rampL.stop(bench::kEscNeutralUs);
      rampR.stop(bench::kEscNeutralUs);
      arming = true;
      armDoneMs = now + kArmHoldMs;
      safeReason = "";
      bench::msg("OK arming: 1500 us for %lu ms", static_cast<unsigned long>(kArmHoldMs));
    }
  }
  if (armed) {
#ifdef REMOTE_RUDDER
    rampL.setTarget(bench::escDeadbandUs(static_cast<float>(m.t), kLoUs, kHiUs));
    rampR.setTarget(bench::rudderUs(static_cast<float>(m.r)));
#else
    const bench::EscPulses p = bench::escMixDeadband(static_cast<float>(m.t), static_cast<float>(m.r), kLoUs, kHiUs);
    rampL.setTarget(p.l_us);
    rampR.setTarget(p.r_us);
#endif
#ifdef REMOTE_LIFT
    if (liftOn) liftRamp.setTarget(static_cast<float>(liftClamp(liftReq)));
#endif
  }
}

void onWsEvent(uint8_t num, WStype_t type, uint8_t* payload, size_t length) {
  const uint32_t now = millis();
  switch (type) {
    case WStype_CONNECTED:
      if (driver >= 0) {  // one driver only
        ws.disconnect(num);
        return;
      }
      driver = num;
      clients = 1;
      bench::msg("OK client %u connected", num);
      break;
    case WStype_DISCONNECTED:
      if (static_cast<int>(num) != driver) return;
      driver = -1;
      clients = 0;
      goSafe("disconnect");
      break;
    case WStype_TEXT: {
      if (static_cast<int>(num) != driver) return;
      char buf[96];
      const size_t n = length < sizeof buf - 1 ? length : sizeof buf - 1;
      memcpy(buf, payload, n);
      buf[n] = '\0';
      onMessage(buf, now);
      break;
    }
    default:
      break;
  }
}

void sendStatus() {
  if (driver < 0) return;
  char buf[192];
#ifdef REMOTE_LIFT
  snprintf(buf, sizeof buf, "{\"l\":%d,\"r\":%d,\"armed\":%d,\"kill\":%d,\"vbat\":%.2f,\"rssi\":%d,\"u\":%d,\"safe\":\"%s\"}",
           lastL, lastR, armed ? 1 : 0, killIn.active() ? 1 : 0, vbat, apRssi(), liftDeg(), (armed || arming) ? "" : safeReason);
#else
  snprintf(buf, sizeof buf, "{\"l\":%d,\"r\":%d,\"armed\":%d,\"kill\":%d,\"vbat\":%.2f,\"rssi\":%d,\"safe\":\"%s\"}", lastL,
           lastR, armed ? 1 : 0, killIn.active() ? 1 : 0, vbat, apRssi(), (armed || arming) ? "" : safeReason);
#endif
  ws.sendTXT(static_cast<uint8_t>(driver), buf);
}

void help() {
  bench::msg("remote: phone page at http://192.168.4.1 on WiFi \"%s\" (password in include/secrets.h)", AP_SSID);
  bench::msg("  serial: `?` this help, `0` SAFE now");
#ifdef REMOTE_LIFT
  bench::msg("  serial: `lift <%d..%d>` move the cradle pair (CH%d/CH%d) without the phone, `lift off` drop its pulses",
             kLiftDegLo, kLiftDegHi, kLiftChA, kLiftChB);
  bench::msg("state: ap=%d clients=%d armed=%d arming=%d kill=%d l=%d r=%d lift=%d (req %d, pca %s) vbat=%.2f safe=%s",
             apOk ? 1 : 0, clients, armed ? 1 : 0, arming ? 1 : 0, killIn.active() ? 1 : 0, lastL, lastR, liftDeg(), liftReq,
             pcaOk ? "ok" : "MISSING", vbat, safeReason);
#else
  bench::msg("state: ap=%d clients=%d armed=%d arming=%d kill=%d l=%d r=%d vbat=%.2f safe=%s", apOk ? 1 : 0, clients,
             armed ? 1 : 0, arming ? 1 : 0, killIn.active() ? 1 : 0, lastL, lastR, vbat, safeReason);
#endif
}

#ifdef REMOTE_LIFT
// `lift <deg>` moves the pair from the monitor (dry test without the phone); `lift off` drops both pulses.
void liftCommand() {
  if (strcmp(shell.arg(1), "off") == 0) {
    liftOff();
    bench::msg("OK lift OFF (both pulses dropped, servos limp)");
    return;
  }
  bool ok = false;
  const float d = shell.argf(1, 0.0f, &ok);
  if (!ok || d < kLiftDegLo || d > kLiftDegHi) {
    bench::msg("ERR lift (want: lift <%d..%d> | lift off)", kLiftDegLo, kLiftDegHi);
  } else if (!pcaOk) {
    bench::msg("WARN PCA9685 missing: lift disabled");
  } else if (killIn.active()) {
    bench::msg("WARN KILL active (GPIO%d low): refused", PIN_KILL);
  } else {
    liftReq = static_cast<int>(d);
    liftGo(liftReq);
    bench::msg("OK lift -> %d deg at %.0f deg/s", liftReq, kLiftDegPerS);
  }
}
#endif

}  // namespace

void setup() {
  attachEsc();  // first: both ESC outputs at 1500 µs before anything else
  killIn.begin();
  heartbeat.begin();
  pinMode(PIN_VBAT_ADC, INPUT);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  bench::begin("remote", "t_ms,l_us,r_us,armed,kill,vbat,clients,last_hb_ms" LIFT_CSV);
#if defined(REMOTE_RUDDER) && defined(ESC_BUFFER)
  bench::msg("ESC_L GPIO%d via 74HCT125, NOT inverted = thrust · RUDDER GPIO%d via 74HCT125, 1167–1833 us · KILL GPIO%d",
             PIN_ESC_L, PIN_ESC_R, PIN_KILL);
#elif defined(REMOTE_RUDDER)
  bench::msg("ESC_L GPIO%d INVERTED (S8050) = thrust · RUDDER GPIO%d direct, not inverted, 1167–1833 us · KILL GPIO%d",
             PIN_ESC_L, PIN_ESC_R, PIN_KILL);
#else
  bench::msg("ESC output INVERTED (NPN level shifter, C006) · ESC_L GPIO%d ESC_R GPIO%d · KILL GPIO%d (software stop)",
             PIN_ESC_L, PIN_ESC_R, PIN_KILL);
#endif
#ifdef REMOTE_LIFT
  Wire.begin(PIN_I2C0_SDA, PIN_I2C0_SCL, kI2cHz);
  pcaOk = pca.begin();
  if (pcaOk) {
    pca.setOscillatorFrequency(kOscHz);
    pca.setPWMFreq(kServoHz);
    for (uint8_t ch = 0; ch < 16; ++ch) pca.setPWM(ch, 0, 0);  // every output silent until ARM
    const bench::PairPulses lo = bench::pairFromDegTrim(static_cast<float>(kLiftDegLo), kLiftTrimA, kLiftTrimB);
    const bench::PairPulses hi = bench::pairFromDegTrim(static_cast<float>(kLiftDegHi), kLiftTrimA, kLiftTrimB);
    if (!bench::pairInWindow(lo, kLiftMinUs, kLiftMaxUs) || !bench::pairInWindow(hi, kLiftMinUs, kLiftMaxUs)) {
      pcaOk = false;
      bench::msg("WARN lift trims %+.0f/%+.0f us push a pulse outside %.0f–%.0f us — lift disabled", kLiftTrimA, kLiftTrimB,
                 kLiftMinUs, kLiftMaxUs);
    } else {
      bench::msg("OK PCA9685 0x%02X (SDA GPIO%d, SCL GPIO%d): LIFT CH%d/CH%d %d–%d deg, %d = deployed, pulses OFF until ARM",
                 kPcaAddr, PIN_I2C0_SDA, PIN_I2C0_SCL, kLiftChA, kLiftChB, kLiftDegLo, kLiftDegHi, kLiftDegLo);
      bench::msg("lift servo V+ = 5 V from the buck on F2 — never 12 V. KILL drops the lift, every other SAFE holds it");
    }
  } else {
    bench::msg("WARN PCA9685 not found at 0x%02X — lift disabled; thrust and rudder still work", kPcaAddr);
  }
#endif

  if (strlen(AP_PASS) < 8) {
    bench::msg("WARN AP_PASS shorter than 8 characters (WPA2) — AP NOT started; fix include/secrets.h");
  } else {
    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(IPAddress(192, 168, 4, 1), IPAddress(192, 168, 4, 1), IPAddress(255, 255, 255, 0));
    apOk = WiFi.softAP(AP_SSID, AP_PASS, kApChannel, 0, 1);
    if (apOk) {
      bench::msg("OK WiFi AP \"%s\" ch %u, open http://%s", AP_SSID, kApChannel, WiFi.softAPIP().toString().c_str());
    } else {
      bench::msg("WARN WiFi AP failed to start");
    }
  }
  http.on("/", []() { http.send_P(200, "text/html", kPage); });
  http.onNotFound([]() { http.send(404, "text/plain", "AR-Mini: open /"); });
  http.begin();
  ws.begin();
  ws.onEvent(onWsEvent);
  bench::msg("both 1500 us, NOT armed. limit %.0f–%.0f us, ramp %.0f us/s, link timeout %lu ms. Type `?`.", kLoUs, kHiUs,
             kRampUsPerS, static_cast<unsigned long>(bench::kLinkTimeoutMs));
  lastLoopMs = millis();
}

void loop() {
  const uint32_t now = millis();
  const uint32_t dt = now - lastLoopMs;
  lastLoopMs = now;

  ws.loop();
  http.handleClient();

  if (shell.poll()) {
    if (shell.is("?")) help();
    else if (shell.is("0")) goSafe("serial");
#ifdef REMOTE_LIFT
    else if (shell.is("lift")) liftCommand();
#endif
    else bench::err(shell.arg(0));
  }

  if (killIn.risingKill() || (killIn.active() && (armed || arming))) goSafe("kill");
  if (hbSeen && bench::linkLost(lastHbMs, now)) goSafe("heartbeat");

  if (arming && static_cast<int32_t>(now - armDoneMs) >= 0) {
    arming = false;
    armed = true;
    bench::msg("ARMED");
#ifdef REMOTE_LIFT
    liftGo(liftReq);  // first ARM: snap to the slider (U already in that pose); later ARMs: ramp from where it holds
#endif
  }

  if (dt > 0) {
    rampL.update(dt);
    rampR.update(dt);
    applyOutputs();
#ifdef REMOTE_LIFT
    liftUpdate(dt);
#endif
  }
  heartbeat.update(now);

  if (statusTick.due(now)) {
    vbat = bench::vbatCorrected(readMv(PIN_VBAT_ADC) / 1000.0f, kDivGain, VBAT_GAIN, VBAT_OFFSET_V);
    sendStatus();
  }
  if (csvTick.due(now)) {
    char buf[96];
    bench::CsvRow row(buf, sizeof buf);
    const long age = everHb ? static_cast<long>(now - lastHbMs) : -1L;
    row.add(static_cast<unsigned long>(now)).add(lastL).add(lastR).add(armed).add(killIn.active()).add(vbat, 2).add(clients).add(age);
#ifdef REMOTE_LIFT
    row.add(liftDeg());
#endif
    Serial.println(row.c_str());
  }
  delay(1);
}
