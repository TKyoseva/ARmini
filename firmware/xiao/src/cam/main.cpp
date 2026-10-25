// AR-Mini · XIAO ESP32-S3 Sense · env `cam` · OV3660 camera node (card C049).
//
// The XIAO is its own WPA2 access point (CAM_AP_SSID / CAM_AP_PASS from include/secrets.h, gitignored) and
// serves the OV3660 at VGA 640x480 JPEG from two HTTP servers (as in the CameraWebServer example), so the page
// and /rec keep answering while a viewer holds the stream open:
//   :80  /            page: <img> of the stream, Rec on / Rec off buttons (fetch, no reload), rec state
//        /jpg         one JPEG snapshot
//        /rec         JSON state {"rec","frames","run","rec_fps"}; /rec?on=1|0 starts / stops and returns the state
//   :81  /stream      multipart MJPEG (one client at a time; the handler returns when the client leaves)
// Serial (USB-C, 115200), commands `rec 1`, `rec 0`, `?`. Every 2 s:
//   `# fps <stream> rec <on|off> frames <n> rec_fps <x> free <MB>`   (+ `# WARN no SD` when no card is mounted)
//
// Recording (microSD in the slot of the Sense expansion board, FAT32, ≤ 32 GB): each run is a new folder
// /C049_<n>/ with ONE video.mjpeg (JPEGs appended back to back) and index.csv (frame,t_ms,offset,len). Both files
// stay open, are flushed every 10 frames (a power cut loses at most 10 frames) and closed on `rec 0`.
// First run 25.10: one file per frame slowed from 15.5 to 8.5 fps over 155 frames, hence the single file.
// Frames are the ones the stream sends (same rate); with no viewer, loop() captures them itself. If recording
// pulls the stream under 8 fps, every 2nd frame is recorded and that is printed.
// A file /autorec on the card starts recording 5 s after boot (water test without the phone).
//
// Decision 0005 (25.10, Teddy): the XIAO Sense = OV3660 camera node only, powered from its own USB-C / 5 V.
// Nothing else is soldered to it; the thermal cameras are on the DevKit-Lipo (bench env `thermal`).
#include <Arduino.h>
#include <FS.h>
#include <SD.h>
#include <SPI.h>
#include <WiFi.h>
#include <esp_camera.h>
#include <esp_http_server.h>

#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

#if __has_include("secrets.h")
#include "secrets.h"
#if !defined(CAM_AP_SSID) || !defined(CAM_AP_PASS)
#error "secrets.h must define CAM_AP_SSID and CAM_AP_PASS (see include/secrets.example.h)"
#endif
#else
#error "firmware/xiao/include/secrets.h missing: copy include/secrets.example.h to include/secrets.h and set CAM_AP_PASS"
#endif

namespace {

// Camera pins. SOURCE: arduino-esp32 2.0.17 libraries/ESP32/examples/Camera/CameraWebServer/camera_pins.h,
// block CAMERA_MODEL_XIAO_ESP32S3 (Seeed Studio XIAO ESP32S3 Sense).
const int kPwdn = -1, kReset = -1, kXclk = 10, kSiod = 40, kSioc = 39;
const int kY9 = 48, kY8 = 11, kY7 = 12, kY6 = 14, kY5 = 16, kY4 = 18, kY3 = 17, kY2 = 15;
const int kVsync = 38, kHref = 47, kPclk = 13;

// microSD on the Sense expansion board: SPI SCK GPIO7 / MISO GPIO8 / MOSI GPIO9 (board variant XIAO_ESP32S3
// pins_arduino.h), CS GPIO21. SOURCE: Seeed wiki "XIAO ESP32S3 Sense – microSD", `SD.begin(21)`.
const int kSdCs = 21;
const uint32_t kSdHz = 20000000;  // VERIFY: 20 MHz SPI; drop to 4 MHz (SD.begin default) if the card does not mount

const int kXclkHz = 20000000;             // SOURCE: CameraWebServer example (20 MHz)
const framesize_t kSize = FRAMESIZE_VGA;  // SOURCE: handoff 25.10 (640x480)
const int kJpegQuality = 12;              // SOURCE: CameraWebServer example (0 = best, 63 = worst); VERIFY: fps vs quality on the phone
const uint8_t kApChannel = 1;             // VERIFY: the DevKit `remote` AP is on channel 6; keep the two apart
const uint32_t kReportMs = 2000;          // SOURCE: handoff (serial every 2 s)
const uint32_t kAutorecDelayMs = 5000;    // SOURCE: handoff (/autorec → start 5 s after boot)
const float kMinStreamFps = 8.0f;         // SOURCE: handoff (recording must not drop the stream below 8 fps at VGA)
const char kRunPrefix[] = "/C049_";
const uint16_t kHttpPort = 80;
const uint16_t kStreamPort = 81;          // SOURCE: CameraWebServer example (stream on its own server, port + 1)
const uint32_t kFlushEvery = 10;          // SOURCE: handoff (flush every 10 frames)

const char kPage[] =
    "<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
    "<title>AR-Mini cam</title><style>html,body{margin:0;background:#111;color:#eee;font:16px -apple-system,sans-serif}"
    "img{width:100%;height:auto;display:block;background:#000}#b{padding:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}"
    "button{font-size:18px;padding:10px 16px;border:0;border-radius:10px;color:#fff}#on{background:#c00}#off{background:#444}"
    "a{color:#9cf;word-break:break-all}</style></head><body>"
    "<img id=\"s\" alt=\"stream\"><div id=\"b\"><button id=\"on\">Rec on</button><button id=\"off\">Rec off</button><span id=\"st\">…</span></div>"
    "<div id=\"b\">stream: <a id=\"l\"></a></div>"
    "<script>var u='http://'+location.hostname+':81/stream';document.getElementById('s').src=u;"
    "var l=document.getElementById('l');l.href=u;l.textContent=u;"
    "function show(j){document.getElementById('st').textContent='rec '+(j.rec?'ON':'off')+' · frames '+j.frames+(j.run?' · '+j.run:'')+' · '+j.rec_fps+' fps';}"
    "function st(){fetch('/rec').then(function(r){return r.json()}).then(show).catch(function(){});}"
    "function rec(o){fetch('/rec?on='+o).then(function(r){return r.json()}).then(show).catch(function(){});}"
    "document.getElementById('on').onclick=function(){rec(1)};document.getElementById('off').onclick=function(){rec(0)};"
    "setInterval(st,2000);st();</script></body></html>";

const char kStreamContentType[] = "multipart/x-mixed-replace;boundary=frame";
const char kStreamBoundary[] = "\r\n--frame\r\n";
const char kStreamPart[] = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

httpd_handle_t server = nullptr;        // :80 page, /jpg, /rec
httpd_handle_t streamServer = nullptr;  // :81 /stream
volatile uint32_t framesSent = 0;
volatile int streamClients = 0;
bool camOk = false;
int frameW = 0, frameH = 0;
float streamFps = 0.0f;

// ---- recording state (guarded by recMutex: loop() task and the httpd task both touch it)
SemaphoreHandle_t recMutex = nullptr;
bool sdOk = false;
bool recOn = false;
int recRun = 0;          // <n> of the current /C049_<n>/
uint32_t recFrames = 0;  // frames written in this run
uint32_t recSeen = 0;    // frames offered to the recorder in this run (for every-2nd)
int recEvery = 1;        // 1 = every frame, 2 = every 2nd (stream fell under kMinStreamFps)
char recDir[24] = "";
File recVideo;           // /C049_<n>/video.mjpeg, open while recording
File recIndex;           // /C049_<n>/index.csv, open while recording
uint32_t recOffset = 0;  // bytes written to video.mjpeg so far
uint32_t recSinceFlush = 0;
float recFps = 0.0f;
uint32_t recFramesAtReport = 0;
float sdFreeMb = 0.0f;
bool autorecPending = false;

struct Lock {
  explicit Lock(SemaphoreHandle_t m) : m_(m) { xSemaphoreTake(m_, portMAX_DELAY); }
  ~Lock() { xSemaphoreGive(m_); }
  SemaphoreHandle_t m_;
};

// ---- SD helpers
void sdUpdateFree() {
  if (!sdOk) return;
  const uint64_t total = SD.totalBytes(), used = SD.usedBytes();
  sdFreeMb = total > used ? (total - used) / 1.0e6f : 0.0f;
}

bool sdMount() {
  if (!SD.begin(kSdCs, SPI, kSdHz)) return false;
  if (SD.cardType() == CARD_NONE) return false;
  sdOk = true;
  sdUpdateFree();
  Serial.printf("# OK microSD %llu MB, %.0f MB free, CS GPIO%d\n", SD.cardSize() / 1000000ULL, sdFreeMb, kSdCs);
  return true;
}

// Highest existing /C049_<n> + 1.
int sdNextRun() {
  int next = 1;
  File root = SD.open("/");
  if (!root) return next;
  for (File f = root.openNextFile(); f; f = root.openNextFile()) {
    const char* name = f.name();
    if (name[0] == '/') ++name;
    if (strncmp(name, kRunPrefix + 1, strlen(kRunPrefix) - 1) == 0) {
      const int n = atoi(name + strlen(kRunPrefix) - 1);
      if (n >= next) next = n + 1;
    }
    f.close();
  }
  root.close();
  return next;
}

// Appends one JPEG to video.mjpeg and one line to index.csv (both already open). Flushes every kFlushEvery
// frames. Returns false on a write error (recording stops).
bool sdWriteFrame(const camera_fb_t* fb, uint32_t t_ms) {
  const size_t n = recVideo.write(fb->buf, fb->len);
  if (n != fb->len) return false;
  recIndex.printf("%lu,%lu,%lu,%u\n", static_cast<unsigned long>(recFrames + 1), static_cast<unsigned long>(t_ms),
                  static_cast<unsigned long>(recOffset), static_cast<unsigned>(fb->len));
  recOffset += fb->len;
  if (++recSinceFlush >= kFlushEvery) {
    recVideo.flush();
    recIndex.flush();
    recSinceFlush = 0;
  }
  return true;
}

// Locked by the caller.
void recCloseFiles() {
  if (recVideo) recVideo.close();
  if (recIndex) recIndex.close();
  recSinceFlush = 0;
}

// ---- recording control (callers hold no lock)
bool recStart(const char* who) {
  Lock l(recMutex);
  if (!sdOk) {
    Serial.println("# WARN no SD — rec refused");
    return false;
  }
  if (recOn) return true;
  recRun = sdNextRun();
  snprintf(recDir, sizeof recDir, "%s%d", kRunPrefix, recRun);
  if (!SD.mkdir(recDir)) {
    Serial.printf("# WARN mkdir %s failed — rec refused\n", recDir);
    return false;
  }
  char path[48];
  snprintf(path, sizeof path, "%s/video.mjpeg", recDir);
  recVideo = SD.open(path, FILE_WRITE);
  snprintf(path, sizeof path, "%s/index.csv", recDir);
  recIndex = SD.open(path, FILE_WRITE);
  if (!recVideo || !recIndex) {
    recCloseFiles();
    Serial.printf("# WARN cannot open files in %s/ — rec refused\n", recDir);
    return false;
  }
  recIndex.println("frame,t_ms,offset,len");
  recFrames = 0;
  recSeen = 0;
  recOffset = 0;
  recSinceFlush = 0;
  recEvery = 1;
  recFps = 0.0f;
  recFramesAtReport = 0;
  recOn = true;
  Serial.printf("# OK rec on (%s) -> %s/video.mjpeg\n", who, recDir);
  return true;
}

void recStop(const char* why) {
  Lock l(recMutex);
  if (!recOn) return;
  recOn = false;
  recCloseFiles();
  Serial.printf("# OK rec off (%s): %lu frames, %lu bytes in %s/\n", why, static_cast<unsigned long>(recFrames),
                static_cast<unsigned long>(recOffset), recDir);
  sdUpdateFree();
}

// Offers a frame to the recorder. Called by the stream handler for every frame it sends, or by loop() when
// nobody is streaming.
void recOffer(const camera_fb_t* fb, uint32_t t_ms) {
  Lock l(recMutex);
  if (!recOn) return;
  ++recSeen;
  if (recEvery == 2 && (recSeen & 1) == 0) return;
  if (!sdWriteFrame(fb, t_ms)) {
    recOn = false;
    recCloseFiles();
    Serial.printf("# WARN SD write failed after %lu frames — rec off\n", static_cast<unsigned long>(recFrames));
    return;
  }
  ++recFrames;
}

// JSON state for the page and /rec.
void recStateJson(char* buf, size_t cap) {
  Lock l(recMutex);
  snprintf(buf, cap, "{\"rec\":%d,\"frames\":%lu,\"run\":\"%s\",\"rec_fps\":%.1f,\"sd\":%d}", recOn ? 1 : 0,
           static_cast<unsigned long>(recFrames), recOn ? recDir : "", recFps, sdOk ? 1 : 0);
}

// Every 2 s: if a viewer is streaming and the stream fell under 8 fps while recording every frame, record every 2nd.
void recAdapt() {
  Lock l(recMutex);
  if (!recOn || streamClients == 0 || recEvery != 1) return;
  if (streamFps > 0.0f && streamFps < kMinStreamFps) {
    recEvery = 2;
    Serial.printf("# WARN stream %.1f fps < %.0f while recording — now recording every 2nd frame\n", streamFps, kMinStreamFps);
  }
}

// ---- HTTP
esp_err_t handleIndex(httpd_req_t* req) {
  httpd_resp_set_type(req, "text/html");
  return httpd_resp_send(req, kPage, HTTPD_RESP_USE_STRLEN);
}

esp_err_t handleJpg(httpd_req_t* req) {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }
  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=armini.jpg");
  const esp_err_t res = httpd_resp_send(req, reinterpret_cast<const char*>(fb->buf), fb->len);
  esp_camera_fb_return(fb);
  return res;
}

// /rec → state; /rec?on=1|0 → start / stop, then state.
esp_err_t handleRec(httpd_req_t* req) {
  char query[32] = "";
  char on[4] = "";
  if (httpd_req_get_url_query_str(req, query, sizeof query) == ESP_OK && httpd_query_key_value(query, "on", on, sizeof on) == ESP_OK) {
    if (on[0] == '1') recStart("http");
    else recStop("http");
  }
  char reply[128];
  recStateJson(reply, sizeof reply);
  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Cache-Control", "no-store");
  return httpd_resp_send(req, reply, HTTPD_RESP_USE_STRLEN);
}

esp_err_t handleStream(httpd_req_t* req) {
  esp_err_t res = httpd_resp_set_type(req, kStreamContentType);
  if (res != ESP_OK) return res;
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  ++streamClients;
  char part[64];
  while (true) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("# WARN frame capture failed");
      res = ESP_FAIL;
      break;
    }
    const uint32_t t = millis();
    const size_t n = snprintf(part, sizeof part, kStreamPart, static_cast<unsigned>(fb->len));
    res = httpd_resp_send_chunk(req, kStreamBoundary, strlen(kStreamBoundary));
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, part, n);
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, reinterpret_cast<const char*>(fb->buf), fb->len);
    frameW = fb->width;
    frameH = fb->height;
    if (res == ESP_OK) recOffer(fb, t);
    esp_camera_fb_return(fb);
    if (res != ESP_OK) break;  // client gone
    ++framesSent;
  }
  --streamClients;
  return res;
}

bool startCamera() {
  camera_config_t c = {};
  c.ledc_channel = LEDC_CHANNEL_0;
  c.ledc_timer = LEDC_TIMER_0;
  c.pin_d0 = kY2;
  c.pin_d1 = kY3;
  c.pin_d2 = kY4;
  c.pin_d3 = kY5;
  c.pin_d4 = kY6;
  c.pin_d5 = kY7;
  c.pin_d6 = kY8;
  c.pin_d7 = kY9;
  c.pin_xclk = kXclk;
  c.pin_pclk = kPclk;
  c.pin_vsync = kVsync;
  c.pin_href = kHref;
  c.pin_sccb_sda = kSiod;
  c.pin_sccb_scl = kSioc;
  c.pin_pwdn = kPwdn;
  c.pin_reset = kReset;
  c.xclk_freq_hz = kXclkHz;
  c.pixel_format = PIXFORMAT_JPEG;
  c.frame_size = kSize;
  c.jpeg_quality = kJpegQuality;
  c.fb_count = psramFound() ? 2 : 1;
  c.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  c.grab_mode = CAMERA_GRAB_LATEST;
  const esp_err_t err = esp_camera_init(&c);
  if (err != ESP_OK) {
    Serial.printf("# WARN camera init failed 0x%x\n", err);
    return false;
  }
  sensor_t* s = esp_camera_sensor_get();
  if (s) {
    Serial.printf("# OK camera PID 0x%02X (OV3660 = 0x36)\n", s->id.PID);
    if (s->id.PID == OV3660_PID) {
      // SOURCE: CameraWebServer example, OV3660 defaults (it comes out of reset upside down and washed out)
      s->set_vflip(s, 1);
      s->set_brightness(s, 1);
      s->set_saturation(s, -2);
    }
    s->set_framesize(s, kSize);
  }
  return true;
}

// Two servers: the stream handler never returns while a viewer is connected and would block every other
// request on the same server (first run 25.10: /rec took the stream to 0 fps). SOURCE: CameraWebServer example.
void startServers() {
  httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
  cfg.server_port = kHttpPort;
  cfg.max_open_sockets = 4;
  if (httpd_start(&server, &cfg) != ESP_OK) {
    Serial.println("# WARN http server :80 failed to start");
  } else {
    httpd_uri_t uri = {};
    uri.method = HTTP_GET;
    uri.uri = "/";
    uri.handler = handleIndex;
    httpd_register_uri_handler(server, &uri);
    uri.uri = "/jpg";
    uri.handler = handleJpg;
    httpd_register_uri_handler(server, &uri);
    uri.uri = "/rec";
    uri.handler = handleRec;
    httpd_register_uri_handler(server, &uri);
  }

  cfg.server_port = kStreamPort;
  cfg.ctrl_port += 1;  // each httpd instance needs its own control socket
  cfg.max_open_sockets = 2;
  if (httpd_start(&streamServer, &cfg) != ESP_OK) {
    Serial.println("# WARN stream server :81 failed to start");
  } else {
    httpd_uri_t uri = {};
    uri.method = HTTP_GET;
    uri.uri = "/stream";
    uri.handler = handleStream;
    httpd_register_uri_handler(streamServer, &uri);
  }
}

// ---- serial CLI: `rec 1`, `rec 0`, `?`
void handleLine(char* line) {
  while (*line == ' ') ++line;
  char* end = line + strlen(line);
  while (end > line && (end[-1] == ' ' || end[-1] == '\r')) *--end = '\0';
  if (strcmp(line, "?") == 0) {
    Serial.println("# cam: `rec 1` start recording to microSD, `rec 0` stop, `?` this help. HTTP :80 /, /jpg, /rec[?on=1|0] · :81 /stream");
    Serial.printf("# state: cam=%s sd=%s rec=%s run=%d frames=%lu every=%d clients=%d\n", camOk ? "ok" : "MISSING",
                  sdOk ? "ok" : "none", recOn ? "on" : "off", recRun, static_cast<unsigned long>(recFrames), recEvery,
                  static_cast<int>(streamClients));
  } else if (strcmp(line, "rec 1") == 0) {
    recStart("serial");
  } else if (strcmp(line, "rec 0") == 0) {
    recStop("serial");
  } else if (*line) {
    Serial.printf("# ERR %s\n", line);
  }
}

void pollSerial() {
  static char buf[32];
  static size_t len = 0;
  while (Serial.available()) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n') {
      buf[len] = '\0';
      handleLine(buf);
      len = 0;
    } else if (len < sizeof buf - 1) {
      buf[len++] = c;
    }
  }
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("# AR-Mini cam · XIAO ESP32-S3 Sense · OV3660 (C049)");
  Serial.printf("# psram %s, heap %u\n", psramFound() ? "found" : "MISSING (fb_count 1, DRAM)", ESP.getFreeHeap());

  recMutex = xSemaphoreCreateMutex();
  camOk = startCamera();

  if (!sdMount()) {
    Serial.println("# WARN no SD — stream only, `rec` refused (card ≤ 32 GB, FAT32, in the Sense board slot)");
  } else if (SD.exists("/autorec")) {
    autorecPending = true;
    Serial.printf("# /autorec found: recording starts %lu ms after boot\n", static_cast<unsigned long>(kAutorecDelayMs));
  }

  if (strlen(CAM_AP_PASS) < 8) {
    Serial.println("# WARN CAM_AP_PASS shorter than 8 characters (WPA2) — AP NOT started; fix include/secrets.h");
  } else {
    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(IPAddress(192, 168, 5, 1), IPAddress(192, 168, 5, 1), IPAddress(255, 255, 255, 0));
    if (WiFi.softAP(CAM_AP_SSID, CAM_AP_PASS, kApChannel, 0, 2)) {
      Serial.printf("# OK WiFi AP \"%s\" ch %u, open http://%s/ (stream on http://%s:%u/stream)\n", CAM_AP_SSID, kApChannel,
                    WiFi.softAPIP().toString().c_str(), WiFi.softAPIP().toString().c_str(), kStreamPort);
    } else {
      Serial.println("# WARN WiFi AP failed to start");
    }
  }
  startServers();
  Serial.println("# fps = frames sent on /stream (0 with no viewer), rec_fps = frames written. Type `?`.");
}

void loop() {
  static uint32_t lastReport = 0;
  static uint32_t lastFrames = 0;
  const uint32_t now = millis();

  pollSerial();

  if (autorecPending && now >= kAutorecDelayMs) {
    autorecPending = false;
    recStart("autorec");
  }

  // Nobody streaming: the recorder captures its own frames at the camera rate.
  if (recOn && streamClients == 0 && camOk) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (fb) {
      frameW = fb->width;
      frameH = fb->height;
      recOffer(fb, millis());
      esp_camera_fb_return(fb);
    }
  } else {
    delay(10);
  }

  if (now - lastReport >= kReportMs) {
    const uint32_t dt = now - lastReport;
    const uint32_t sent = framesSent;
    streamFps = (sent - lastFrames) * 1000.0f / dt;
    lastFrames = sent;
    lastReport = now;
    bool on;
    uint32_t frames;
    int every;
    {
      Lock l(recMutex);
      recFps = recOn ? (recFrames - recFramesAtReport) * 1000.0f / dt : 0.0f;
      recFramesAtReport = recFrames;
      on = recOn;
      frames = recFrames;
      every = recEvery;
    }
    recAdapt();
    if (sdOk && !on) sdUpdateFree();
    Serial.printf("# fps %.1f rec %s frames %lu rec_fps %.1f free %.0f MB%s%s\n", streamFps, on ? "on" : "off",
                  static_cast<unsigned long>(frames), recFps, sdFreeMb, (on && every == 2) ? " (every 2nd frame)" : "",
                  camOk ? "" : " cam=MISSING");
    if (!sdOk) Serial.println("# WARN no SD");
  }
}
