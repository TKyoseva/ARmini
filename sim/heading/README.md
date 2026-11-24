# sim/heading · heading hold in simulation (card C077)

Question: can a PI controller on the BNO055 heading hold a commanded heading with the rudder, within ±5°
10 s after a 10° step, while something pushes the boat sideways all the time?

    python3 sim/heading/run.py      # seconds; needs a C++ compiler and matplotlib

`run.py` compiles `step.cpp` against `firmware/armini/lib/core/Heading.h`, so the plot shows the same
controller code the firmware will use. Only the boat is simulated. The host tests of the controller are in
`firmware/armini/test/test_core/test_heading.cpp` (`pio test -e native`).

## Inputs and where they come from

| Input | Value | Source |
|---|---|---|
| Controller | Kp 0.04 turn/°, Ki 0.008 turn/(°·s), 50 Hz | chosen in this simulation (`Heading.h`) |
| Rudder | turn −1…+1 → 1500 ± 333 µs | `bench::rudderUs`, RUDDER_SPEC §3 |
| Boat | yaw rate follows the rudder with a first-order lag: 30 °/s at full rudder, time constant 0.8 s | **ASSUMED, not measured.** To measure in C067 (or from the C059 lake video) |
| Push | constant 5 °/s (wind, the single off-centre thruster) | **ASSUMED** |

Because the boat numbers are guesses, the same gains are tested on a boat twice slower and twice faster
(15…60 °/s, time constant 0.3…1.5 s). Results: `results/results.md`, plot `results/C077_heading_step.png`.

## What the simulation says

- The criterion is met for every tested boat.
- A PI controller alone overshoots: 5.4° on the nominal boat, 9.5° on the slow one. A yaw-rate term from the
  BNO055 gyro would damp it. Add it in C067 if the real boat overshoots like this.

## Limits

1. The model has no sideslip, no speed dependence (a rudder does nothing at zero speed) and no servo lag or
   rate limit. The MG90S and the 2000 µs/s ramp in `remote/main.cpp` add delay the model ignores.
2. No sensor noise, no magnetic disturbance from the bucks, battery or thruster (C066 step C checks that).
3. Nothing here runs on the robot: `Heading.h` is not included by any firmware environment yet.
