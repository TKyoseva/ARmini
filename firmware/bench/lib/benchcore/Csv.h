// CsvRow — builds one CSV line in a caller-owned buffer. Pure C++11, no heap, no Arduino.
//
//   char buf[128]; bench::CsvRow row(buf, sizeof buf);
//   row.add(t_ms).add(cmd, 3).add(pwm).add("DEADMAN");  ->  "1234,0.500,128,DEADMAN"
//
// Fixed decimals for floats (no exponent, no "-0.000"), no trailing comma, no units in values. A NaN or ±inf
// prints as "nan" (pandas reads it as NaN); casting it to an integer gave "922337203685477580.7" (thermal, 25.10).
// If the buffer is too small the row is truncated and overflow() is true.
#pragma once
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

namespace bench {

class CsvRow {
 public:
  CsvRow(char* buf, size_t cap) : buf_(buf), cap_(cap), len_(0), fields_(0), overflow_(false) { reset(); }

  void reset() {
    len_ = 0;
    fields_ = 0;
    overflow_ = false;
    if (cap_ > 0) buf_[0] = '\0';
  }

  CsvRow& add(const char* s) {
    sep();
    append(s);
    return *this;
  }

  CsvRow& add(long v) {
    char tmp[24];
    snprintf(tmp, sizeof tmp, "%ld", v);
    return add(tmp);
  }
  CsvRow& add(unsigned long v) {
    char tmp[24];
    snprintf(tmp, sizeof tmp, "%lu", v);
    return add(tmp);
  }
  // (uint32_t is `unsigned int` on both the ESP32 and the host, so no separate overload.)
  CsvRow& add(int v) { return add(static_cast<long>(v)); }
  CsvRow& add(unsigned int v) { return add(static_cast<unsigned long>(v)); }
  CsvRow& add(bool v) { return add(v ? "1" : "0"); }

  // Fixed-point: `decimals` digits after the point (0..6), round-half-away-from-zero, no "-0".
  CsvRow& add(float v, int decimals) { return add(static_cast<double>(v), decimals); }
  CsvRow& add(double v, int decimals) {
    if (!isfinite(v)) return add("nan");
    if (decimals < 0) decimals = 0;
    if (decimals > 6) decimals = 6;
    long scale = 1;
    for (int i = 0; i < decimals; ++i) scale *= 10;
    const double scaled = v * static_cast<double>(scale);
    long long r = static_cast<long long>(scaled >= 0.0 ? scaled + 0.5 : scaled - 0.5);
    const bool neg = r < 0;
    if (neg) r = -r;
    const long long ip = r / scale;
    const long long fp = r % scale;
    char tmp[48];
    if (decimals == 0) {
      snprintf(tmp, sizeof tmp, "%s%lld", neg ? "-" : "", ip);
    } else {
      snprintf(tmp, sizeof tmp, "%s%lld.%0*lld", neg ? "-" : "", ip, decimals, fp);
    }
    return add(tmp);
  }

  const char* c_str() const { return buf_; }
  size_t length() const { return len_; }
  size_t fields() const { return fields_; }
  bool overflow() const { return overflow_; }

 private:
  void sep() {
    if (fields_ > 0) append(",");
    ++fields_;
  }
  void append(const char* s) {
    if (cap_ == 0) {
      overflow_ = true;
      return;
    }
    const size_t n = strlen(s);
    const size_t room = cap_ - 1 - len_;
    const size_t take = n <= room ? n : room;
    memcpy(buf_ + len_, s, take);
    len_ += take;
    buf_[len_] = '\0';
    if (take < n) overflow_ = true;
  }

  char* buf_;
  size_t cap_;
  size_t len_;
  size_t fields_;
  bool overflow_;
};

}  // namespace bench
