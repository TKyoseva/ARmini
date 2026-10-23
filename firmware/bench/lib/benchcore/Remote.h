// Remote — pure helpers for the `remote` env (T12, C028): link timeout and the phone's JSON message.
// Pure C++11, no Arduino, host-tested.
#pragma once
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

namespace bench {

static const uint32_t kLinkTimeoutMs = 500;  // SOURCE: safety rule T2 (no heartbeat for 500 ms → SAFE)

// True when more than `timeout_ms` have passed since the last heartbeat. Survives millis() wrap-around.
inline bool linkLost(uint32_t last_hb_ms, uint32_t now_ms, uint32_t timeout_ms = kLinkTimeoutMs) {
  return static_cast<uint32_t>(now_ms - last_hb_ms) > timeout_ms;
}

// Page → board, every 100 ms:  {"t":<-100..100>,"r":<-100..100>,"arm":0|1}   or   {"stop":1}
struct RemoteMsg {
  bool stop;
  int t;
  int r;
  bool arm;
};

// Finds `"key"`, then `:` and an integer. Returns false if the key is missing or the value is not a number.
inline bool remoteInt(const char* s, const char* key, long* out) {
  char pat[16];
  const size_t n = strlen(key);
  if (n + 3 > sizeof pat) return false;
  pat[0] = '"';
  memcpy(pat + 1, key, n);
  pat[n + 1] = '"';
  pat[n + 2] = '\0';
  const char* p = strstr(s, pat);
  if (!p) return false;
  p += n + 2;
  while (*p == ' ') ++p;
  if (*p != ':') return false;
  ++p;
  while (*p == ' ') ++p;
  char* end = nullptr;
  const long v = strtol(p, &end, 10);
  if (end == p) return false;
  *out = v;
  return true;
}

// A valid message is a heartbeat. Out-of-range or missing t/r → false (the board ignores it, no heartbeat).
inline bool parseRemoteMsg(const char* s, RemoteMsg* m) {
  m->stop = false;
  m->t = 0;
  m->r = 0;
  m->arm = false;
  if (!s) return false;
  long v = 0;
  if (remoteInt(s, "stop", &v)) {
    if (v != 1) return false;
    m->stop = true;
    return true;
  }
  long t = 0, r = 0;
  if (!remoteInt(s, "t", &t) || !remoteInt(s, "r", &r)) return false;
  if (t < -100 || t > 100 || r < -100 || r > 100) return false;
  long a = 0;
  if (remoteInt(s, "arm", &a) && a != 0 && a != 1) return false;
  m->t = static_cast<int>(t);
  m->r = static_cast<int>(r);
  m->arm = a == 1;
  return true;
}
}  // namespace bench
