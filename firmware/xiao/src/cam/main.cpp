// AR-Mini · XIAO ESP32-S3 Sense · env `cam` · OV3660 camera node (card C049).
//
// The XIAO is its own WPA2 access point (CAM_AP_SSID / CAM_AP_PASS from include/secrets.h, gitignored) and
// serves the OV3660 at VGA 640x480 JPEG:
//   /        one page with <img src="/stream">
//   /stream  multipart MJPEG (one client at a time; the handler returns when the client leaves)
//   /jpg     one JPEG snapshot
// Serial (USB-C, 115200) every 2 s: `# fps <n> size <WxH> heap <n> psram <n>`; fps = frames sent on /stream.
//
// Decision 0005 (25.10, Teddy): the XIAO Sense = OV3660 camera node only, powered from its own USB-C / 5 V.
// Nothing else is soldered to it; the thermal cameras are on the DevKit-Lipo (bench env `thermal`).
#include <Arduino.h>
#include <WiFi.h>
#include <esp_camera.h>
#include <esp_http_server.h>

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

const int kXclkHz = 20000000;             // SOURCE: CameraWebServer example (20 MHz)
const framesize_t kSize = FRAMESIZE_VGA;  // SOURCE: handoff 25.10 (640x480)
const int kJpegQuality = 12;              // SOURCE: CameraWebServer example (0 = best, 63 = worst); VERIFY: fps vs quality on the phone
const uint8_t kApChannel = 1;             // VERIFY: the DevKit `remote` AP is on channel 6; keep the two apart
const uint32_t kReportMs = 2000;          // SOURCE: handoff (serial every 2 s)

const char kPage[] =
    "<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
    "<title>AR-Mini cam</title><style>html,body{margin:0;background:#111;height:100%}img{width:100%;height:auto;display:block}</style>"
    "</head><body><img src=\"/stream\"></body></html>";

const char kStreamContentType[] = "multipart/x-mixed-replace;boundary=frame";
const char kStreamBoundary[] = "\r\n--frame\r\n";
const char kStreamPart[] = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

httpd_handle_t server = nullptr;
volatile uint32_t framesSent = 0;
bool camOk = false;
int frameW = 0, frameH = 0;

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

esp_err_t handleStream(httpd_req_t* req) {
  esp_err_t res = httpd_resp_set_type(req, kStreamContentType);
  if (res != ESP_OK) return res;
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  char part[64];
  while (true) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("# WARN frame capture failed");
      res = ESP_FAIL;
      break;
    }
    const size_t n = snprintf(part, sizeof part, kStreamPart, static_cast<unsigned>(fb->len));
    res = httpd_resp_send_chunk(req, kStreamBoundary, strlen(kStreamBoundary));
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, part, n);
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, reinterpret_cast<const char*>(fb->buf), fb->len);
    frameW = fb->width;
    frameH = fb->height;
    esp_camera_fb_return(fb);
    if (res != ESP_OK) break;  // client gone
    ++framesSent;
  }
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

void startServer() {
  httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
  cfg.server_port = 80;
  cfg.max_open_sockets = 4;
  if (httpd_start(&server, &cfg) != ESP_OK) {
    Serial.println("# WARN http server failed to start");
    return;
  }
  httpd_uri_t uri = {};
  uri.method = HTTP_GET;
  uri.uri = "/";
  uri.handler = handleIndex;
  httpd_register_uri_handler(server, &uri);
  uri.uri = "/stream";
  uri.handler = handleStream;
  httpd_register_uri_handler(server, &uri);
  uri.uri = "/jpg";
  uri.handler = handleJpg;
  httpd_register_uri_handler(server, &uri);
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("# AR-Mini cam · XIAO ESP32-S3 Sense · OV3660 (C049)");
  Serial.printf("# psram %s, heap %u\n", psramFound() ? "found" : "MISSING (fb_count 1, DRAM)", ESP.getFreeHeap());

  camOk = startCamera();

  if (strlen(CAM_AP_PASS) < 8) {
    Serial.println("# WARN CAM_AP_PASS shorter than 8 characters (WPA2) — AP NOT started; fix include/secrets.h");
  } else {
    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(IPAddress(192, 168, 5, 1), IPAddress(192, 168, 5, 1), IPAddress(255, 255, 255, 0));
    if (WiFi.softAP(CAM_AP_SSID, CAM_AP_PASS, kApChannel, 0, 2)) {
      Serial.printf("# OK WiFi AP \"%s\" ch %u, open http://%s/ (also /stream, /jpg)\n", CAM_AP_SSID, kApChannel,
                    WiFi.softAPIP().toString().c_str());
    } else {
      Serial.println("# WARN WiFi AP failed to start");
    }
  }
  startServer();
  Serial.println("# fps counts frames sent on /stream (0 with no viewer). Nothing to type here.");
}

void loop() {
  static uint32_t lastReport = 0;
  static uint32_t lastFrames = 0;
  const uint32_t now = millis();
  if (now - lastReport >= kReportMs) {
    const uint32_t sent = framesSent;
    const float fps = (sent - lastFrames) * 1000.0f / (now - lastReport);
    lastFrames = sent;
    lastReport = now;
    Serial.printf("# fps %.1f size %dx%d heap %u psram %u%s\n", fps, frameW, frameH, ESP.getFreeHeap(), ESP.getFreePsram(),
                  camOk ? "" : " cam=MISSING");
  }
  delay(10);
}
