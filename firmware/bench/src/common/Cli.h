// Cli — line-oriented serial command reader shared by every bench sketch.
//
// Reads characters from a Stream, collects one line (CR/LF terminated, max kMaxLine chars),
// splits it on spaces into argv. poll() returns true once per complete line; then argc()/arg(i)/
// argf(i)/argl(i) describe it until the next poll() that returns true.
#pragma once
#include <Arduino.h>

namespace bench {

class Cli {
 public:
  static const int kMaxLine = 96;
  static const int kMaxArgs = 8;

  explicit Cli(Stream& io) : io_(io), len_(0), argc_(0) { line_[0] = '\0'; }

  // Returns true when a complete non-empty line has been parsed.
  bool poll();

  int argc() const { return argc_; }
  const char* arg(int i) const { return (i >= 0 && i < argc_) ? argv_[i] : ""; }
  bool is(const char* cmd) const { return argc_ > 0 && strcmp(argv_[0], cmd) == 0; }

  // Numeric arguments; `ok` (optional) tells whether the text parsed completely.
  float argf(int i, float dflt = 0.0f, bool* ok = nullptr) const;
  long argl(int i, long dflt = 0, bool* ok = nullptr) const;

 private:
  void tokenize();

  Stream& io_;
  char line_[kMaxLine + 1];
  int len_;
  char* argv_[kMaxArgs];
  int argc_;
};

}  // namespace bench
