// AR-Mini · hardware abstraction interface.
// The mission core never includes Arduino. A Hal implementation reads sensors
// into Inputs, pushes Outputs to actuators (or to a CSV log in dry run) and
// provides the clock. Pure virtual, no heap.
#pragma once
#include <stdint.h>
#include "Types.h"

namespace armini {

class Hal {
 public:
  virtual ~Hal() {}

  // Fill `in` with the current sensor / operator state.
  virtual void readInputs(Inputs& in) = 0;

  // Apply `out` to the actuators (or log it).
  virtual void writeOutputs(const Outputs& out) = 0;

  // Monotonic milliseconds since boot.
  virtual uint32_t nowMs() = 0;

  // Operator asked for StateMachine::reset() since the last call. Returns the
  // request and clears it. Default: never.
  virtual bool takeResetRequest() { return false; }
};

}  // namespace armini
