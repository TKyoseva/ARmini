#include "Cli.h"

#include <stdlib.h>

namespace bench {

bool Cli::poll() {
  while (io_.available() > 0) {
    const int c = io_.read();
    if (c < 0) break;
    if (c == '\r' || c == '\n') {
      if (len_ == 0) continue;  // ignore empty lines / CRLF pairs
      line_[len_] = '\0';
      len_ = 0;
      tokenize();
      if (argc_ > 0) return true;
      continue;
    }
    if (c == 0x08 || c == 0x7F) {  // backspace / delete in an interactive terminal
      if (len_ > 0) --len_;
      continue;
    }
    if (len_ < kMaxLine) {
      line_[len_++] = static_cast<char>(c);
    }
    // overlong lines are silently truncated; the terminator still ends them
  }
  return false;
}

void Cli::tokenize() {
  argc_ = 0;
  char* p = line_;
  while (*p != '\0' && argc_ < kMaxArgs) {
    while (*p == ' ' || *p == '\t') ++p;
    if (*p == '\0') break;
    argv_[argc_++] = p;
    while (*p != '\0' && *p != ' ' && *p != '\t') ++p;
    if (*p != '\0') *p++ = '\0';
  }
}

float Cli::argf(int i, float dflt, bool* ok) const {
  if (i < 0 || i >= argc_) {
    if (ok) *ok = false;
    return dflt;
  }
  char* end = nullptr;
  const float v = strtof(argv_[i], &end);
  const bool good = end != argv_[i] && *end == '\0';
  if (ok) *ok = good;
  return good ? v : dflt;
}

long Cli::argl(int i, long dflt, bool* ok) const {
  if (i < 0 || i >= argc_) {
    if (ok) *ok = false;
    return dflt;
  }
  char* end = nullptr;
  const long v = strtol(argv_[i], &end, 10);
  const bool good = end != argv_[i] && *end == '\0';
  if (ok) *ok = good;
  return good ? v : dflt;
}

}  // namespace bench
