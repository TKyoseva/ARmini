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
// CSV (serial, 10 Hz): t_ms,l_us,r_us,armed,kill,vbat,clients,last_hb_ms   (last_hb_ms = age, −1 = none yet)
#include <Arduino.h>
#include <WebServer.h>
#include <WebSocketsServer.h>
#include <WiFi.h>
#include <esp_wifi.h>

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

namespace {

const uint32_t kEscHz = 50;           // SOURCE: C002 thruster listing; esc env (T10)
const uint8_t kEscBits = 14;          // SOURCE: T10
const float kFrameUs = 1000000.0f / kEscHz;
const bool kEscInvert = true;         // SOURCE: C006 (ESC input pulled up to 5 V, driven through S8050 NPN)
const float kRampUsPerS = 200.0f;     // SOURCE: T10 / T12
const uint32_t kArmHoldMs = 3000;     // SOURCE: T10 (arm holds 1500 µs for 3 s)
const float kLoUs = bench::kEscNarrowLoUs;  // SOURCE: T12 soft limit 1350–1650
const float kHiUs = bench::kEscNarrowHiUs;
const uint8_t kLedcChL = 0;
const uint8_t kLedcChR = 1;
const uint8_t kApChannel = 6;         // SOURCE: T12
const uint32_t kStatusMs = 200;       // SOURCE: T12 (board → page every 200 ms)
const int kAdcSamples = 16;
const float kDivGain = (VBAT_DIV_R_TOP_OHM + VBAT_DIV_R_BOT_OHM) / VBAT_DIV_R_BOT_OHM;

const char kPage[] PROGMEM = R"HTML(<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>AR-Mini</title><style>
*{box-sizing:border-box;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}
html,body{margin:0;height:100%;background:#111;color:#eee;font:16px -apple-system,Helvetica,sans-serif;overflow:hidden;touch-action:none}
#bar{padding:8px;text-align:center;background:#222}#bar.bad{background:#a00}
#row{display:flex;justify-content:space-around;align-items:center;height:calc(100% - 200px)}
.trk{position:relative;width:90px;height:90%;background:#333;border-radius:45px;touch-action:none}
.knob{position:absolute;left:5px;width:80px;height:80px;border-radius:40px;background:#ccc;top:calc(50% - 40px)}
.lbl{text-align:center;margin-top:4px}
#btns{display:flex;gap:10px;padding:10px;height:150px}
button{flex:1;font-size:28px;font-weight:bold;border:0;border-radius:16px;color:#fff;touch-action:manipulation}
#arm{background:#265}#arm.on{background:#2a4}#stop{background:#c00;flex:2}#stop.on{background:#f33}
</style></head><body>
<div id="bar">connecting…</div>
<div id="row"><div><div class="trk" id="tt"><div class="knob" id="tk"></div></div><div class="lbl">thrust <span id="tv">0</span></div></div>
<div><div class="trk" id="rt"><div class="knob" id="rk"></div></div><div class="lbl">turn <span id="rv">0</span></div></div></div>
<div id="btns"><button id="arm">ARM</button><button id="stop">STOP</button></div>
<script>
var t=0,r=0,armReq=0,stopped=1,ws=null,lastRx=0,st={};
function slider(trk,knob,lab,set){var id=null;
 function mv(e){var b=trk.getBoundingClientRect();var y=(e.clientY-b.top)/b.height;y=Math.max(0,Math.min(1,y));
  var v=Math.round((0.5-y)*200);v=Math.max(-100,Math.min(100,v));set(v);lab.textContent=v;knob.style.top=(y*b.height-40)+'px';}
 function up(e){if(e.pointerId!==id)return;id=null;set(0);lab.textContent=0;knob.style.top='calc(50% - 40px)';}
 trk.addEventListener('pointerdown',function(e){id=e.pointerId;trk.setPointerCapture(id);mv(e);e.preventDefault();});
 trk.addEventListener('pointermove',function(e){if(e.pointerId===id)mv(e);e.preventDefault();});
 trk.addEventListener('pointerup',up);trk.addEventListener('pointercancel',up);}
slider(document.getElementById('tt'),document.getElementById('tk'),document.getElementById('tv'),function(v){t=v;});
slider(document.getElementById('rt'),document.getElementById('rk'),document.getElementById('rv'),function(v){r=v;});
var sb=document.getElementById('stop'),ab=document.getElementById('arm'),bar=document.getElementById('bar');
sb.addEventListener('pointerdown',function(e){stopped=1;e.preventDefault();});
ab.addEventListener('pointerdown',function(e){stopped=0;armReq=1;e.preventDefault();});
function conn(){ws=new WebSocket('ws://'+location.hostname+':81/');
 ws.onmessage=function(e){try{st=JSON.parse(e.data);lastRx=Date.now();}catch(x){}};
 ws.onclose=function(){setTimeout(conn,1000);};}
conn();
setInterval(function(){if(!ws||ws.readyState!==1)return;
 if(stopped){ws.send('{"stop":1}');}else{ws.send('{"t":'+t+',"r":'+r+',"arm":'+armReq+'}');armReq=0;}},100);
setInterval(function(){var age=lastRx?Date.now()-lastRx:-1;
 bar.className=(age<0||age>300)?'bad':'';
 bar.textContent='vbat '+(st.vbat!==undefined?st.vbat.toFixed(2):'?')+' V · kill '+(st.kill?'ON':'off')+' · link '+(age<0?'—':age+' ms')+
  ' · rssi '+(st.rssi!==undefined?st.rssi:'?')+' · l '+(st.l||'?')+' r '+(st.r||'?')+(st.safe?' · SAFE '+st.safe:'');
 ab.className=st.armed?'on':'';sb.className=stopped?'on':'';ab.textContent=st.armed?'ARMED':'ARM';},100);
</script></body></html>)HTML";

WebServer http(80);
WebSocketsServer ws(81);
bench::Cli shell(Serial);
bench::Ramp rampL(kRampUsPerS, bench::kEscNeutralUs);
bench::Ramp rampR(kRampUsPerS, bench::kEscNeutralUs);
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

void writeUs(int pin, uint8_t ch, int us) {
  const uint32_t duty = bench::escDuty(static_cast<float>(us), kEscBits, kEscInvert, kFrameUs);
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

// Both 1500 µs at once, disarm. Prints `# SAFE <reason>` only on a change, so a held STOP does not flood serial.
void goSafe(const char* reason) {
  rampL.stop(bench::kEscNeutralUs);
  rampR.stop(bench::kEscNeutralUs);
  applyOutputs();
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
    const bench::EscPulses p = bench::escMixDeadband(static_cast<float>(m.t), static_cast<float>(m.r), kLoUs, kHiUs);
    rampL.setTarget(p.l_us);
    rampR.setTarget(p.r_us);
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
  char buf[160];
  snprintf(buf, sizeof buf, "{\"l\":%d,\"r\":%d,\"armed\":%d,\"kill\":%d,\"vbat\":%.2f,\"rssi\":%d,\"safe\":\"%s\"}", lastL,
           lastR, armed ? 1 : 0, killIn.active() ? 1 : 0, vbat, apRssi(), (armed || arming) ? "" : safeReason);
  ws.sendTXT(static_cast<uint8_t>(driver), buf);
}

void help() {
  bench::msg("remote: phone page at http://192.168.4.1 on WiFi \"%s\" (password in include/secrets.h)", AP_SSID);
  bench::msg("  serial: `?` this help, `0` SAFE now");
  bench::msg("state: ap=%d clients=%d armed=%d arming=%d kill=%d l=%d r=%d vbat=%.2f safe=%s", apOk ? 1 : 0, clients,
             armed ? 1 : 0, arming ? 1 : 0, killIn.active() ? 1 : 0, lastL, lastR, vbat, safeReason);
}

}  // namespace

void setup() {
  attachEsc();  // first: both ESC outputs at 1500 µs before anything else
  killIn.begin();
  heartbeat.begin();
  pinMode(PIN_VBAT_ADC, INPUT);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  bench::begin("remote", "t_ms,l_us,r_us,armed,kill,vbat,clients,last_hb_ms");
  bench::msg("ESC output INVERTED (NPN level shifter, C006) · ESC_L GPIO%d ESC_R GPIO%d · KILL GPIO%d (software stop)",
             PIN_ESC_L, PIN_ESC_R, PIN_KILL);

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
    else bench::err(shell.arg(0));
  }

  if (killIn.risingKill() || (killIn.active() && (armed || arming))) goSafe("kill");
  if (hbSeen && bench::linkLost(lastHbMs, now)) goSafe("heartbeat");

  if (arming && static_cast<int32_t>(now - armDoneMs) >= 0) {
    arming = false;
    armed = true;
    bench::msg("ARMED");
  }

  if (dt > 0) {
    rampL.update(dt);
    rampR.update(dt);
    applyOutputs();
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
    Serial.println(row.c_str());
  }
  delay(1);
}
