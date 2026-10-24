// Vbat — battery voltage from the GPIO4 divider reading. Pure C++11, host-tested.
//
// v_nominal = v_adc × div_gain (130/30 for 100 k / 30 k), then the C027 fit against the meter:
// v_bat = fit_gain × v_nominal + fit_offset_v. The constants live in include/pins_devkit.h.
#pragma once

namespace bench {

inline float vbatCorrected(float v_adc_v, float div_gain, float fit_gain, float fit_offset_v) {
  return fit_gain * (v_adc_v * div_gain) + fit_offset_v;
}

}  // namespace bench
