# T1 · Mission state machine (platform-independent, unit-tested)

**Branch:** `night/state-machine` → PR to `dev`
**Budget:** ~3 h agent time, or 3 failed attempts at one step.

## Goal
In the morning there is a new PlatformIO project `firmware/armini/` with a pure C++ mission state machine (no Arduino dependency), a hardware abstraction interface, Unity tests that run on the host (`pio test -e native`), and a `main.cpp` for the Olimex ESP32-S3-DevKit-Lipo that runs the state machine in **dry-run mode**: all outputs go to Serial as CSV, nothing drives hardware yet. `scripts/check.sh` runs the native tests.

## Context
Read first: `.cursor/rules/ar-mini.mdc`, `AGENTS.md`, `README.md`, `firmware/xiao/src/main.cpp` (the old skeleton with the state names), `hardware/wiring/PINOUT.md`, `pcb/carrier-revA/SPEC.md`, `docs/FAILS_AND_FIXES.md` (search "state", "SAFE", "leak", "kill").

Mission (from README): find a person in the water by body heat → approach → lower the cradle → lift → stow → drive onto the shore on tracks.

States (keep these names): `SEARCH, APPROACH, DEPLOY, LIFT, STOW, SHORE, SAFE`. Add `IDLE` (powered, not armed) before SEARCH.

Actuators: 2 thrusters (water, differential), 2 tracks (land, differential), lift arm (parallelogram: deploy 215°, stow 45°, from the CAD comments), pan servo for the search camera, buzzer, 3 LEDs.
Sensors: search thermal camera 32×24 on the pan servo (target seen, bearing, rough range), cradle thermal camera 110° (confirms the target is in the cradle zone), IMU (tilt), leak probe, battery voltage, kill switch, arm angle (servo feedback).

Known unknowns, **do not guess, make them config parameters with `// VERIFY` comments**: approach range threshold, sightings needed to confirm a target, loss timeout, thrust gains, arm angle tolerance, tilt that means "on shore", battery thresholds (take the defaults from T2 if it is merged, else leave `// VERIFY`).

## Files to create
```
firmware/armini/platformio.ini
firmware/armini/lib/core/StateMachine.h / .cpp     pure C++11, no Arduino, no heap, no millis()
firmware/armini/lib/core/Types.h                    Inputs, Outputs, Config structs
firmware/armini/lib/hal/Hal.h                       abstract interface: readInputs(), writeOutputs(), nowMs()
firmware/armini/src/hal_devkit.cpp                  DRY-RUN implementation: inputs from serial commands, outputs to CSV
firmware/armini/src/main.cpp                        10 Hz loop, CSV header + rows
firmware/armini/test/test_core/test_state_machine.cpp   Unity tests
firmware/armini/README.md                           state diagram (mermaid), config table, CSV format, serial commands
```
Also: edit `scripts/check.sh` so section 5 runs `pio run -e devkit_lipo` and `pio test -e native` for `firmware/armini` (keep the existing loop for other projects).

### platformio.ini
- `[env:native]`: `platform = native`, `test_framework = unity`, `build_flags = -std=c++11 -Wall -Wextra -Werror`, `build_src_filter = -<*>` so `pio run` never compiles Arduino code for native.
- `[env:devkit_lipo]`: `platform = espressif32`, `framework = arduino`, board: use the Olimex ESP32-S3-DevKit-Lipo board id if PlatformIO has one, otherwise `esp32-s3-devkitc-1` with `board_build.arduino.memory_type = qio_opi` (WROOM-1-N8R8); `monitor_speed = 115200`; `build_flags = -DARDUINO_USB_CDC_ON_BOOT=1`. Comment which choice you made and why.
- Keep `firmware/xiao/` untouched.

### Behaviour (implement exactly; everything numeric comes from `Config`)
- `tick(const Inputs&, uint32_t dt_ms) -> Outputs`, deterministic, no side effects besides the internal state.
- `IDLE`: outputs zero; `armed` input true → `SEARCH`.
- `SEARCH`: pan sweeps between `cfg.pan_min_deg` and `cfg.pan_max_deg`; thrust 0. `target_seen` for `cfg.sightings_to_confirm` **consecutive** ticks → `APPROACH` (N−1 is not enough).
- `APPROACH`: thrust differential = `cfg.k_bearing * bearing_deg`, forward = `cfg.approach_thrust`; clamp to [−1, 1]. `target_range_m <= cfg.deploy_range_m` **and** `cradle_confirmed` → `DEPLOY`. No `target_seen` for `cfg.loss_timeout_ms` → `SEARCH`.
- `DEPLOY`: thrust 0, arm target `cfg.arm_deploy_deg`; `|arm_deg − target| <= cfg.arm_tol_deg` → `LIFT`.
- `LIFT`: arm target `cfg.arm_stow_deg`; arm within tolerance → `STOW`. If `load_detected` is false at that point, go to `STOW` anyway but set `outputs.flags.no_load = true` (Teddy decides later what to do with it).
- `STOW`: hold arm, thrust toward shore heading `cfg.shore_heading_deg` using `heading_deg` input; `tilt_deg >= cfg.shore_tilt_deg` (bow on the ramp) → `SHORE`.
- `SHORE`: thrust 0, tracks forward `cfg.track_speed` for `cfg.shore_drive_ms`, then tracks 0 and stay (mission complete flag).
- **From every state**: `leak || kill || battery_low || !armed` → `SAFE`. In `SAFE` all outputs are zero, arm target = current arm angle (hold), buzzer on, `reason` recorded. Leaving `SAFE` only via explicit `reset()` while no cause is active.
- All outputs clamped: thrust/track in [−1, 1], angles in [0, 270].

### CSV (dry run, 10 Hz)
`t_ms,state,reason,thrust_l,thrust_r,track_l,track_r,arm_deg,pan_deg,buzzer,flags`
Serial commands to fake inputs in dry run: `arm 1`, `see 1 12.5 1.8` (seen, bearing, range), `cradle 1`, `armdeg 215`, `load 1`, `tilt 12`, `leak 1`, `kill 1`, `vbat 11.1`, `reset`, `?`.

## Do not touch
`cad/`, `pcb/`, `interfaces/`, `docs/bom/`, `firmware/xiao/`, `firmware/mega/`, `.github/`, `main` branch.

## Tests (Unity, native) — minimum
1. starts in IDLE; `armed` → SEARCH
2. SEARCH → APPROACH after exactly N consecutive sightings; N−1 then a miss resets the count
3. APPROACH → SEARCH after loss timeout; counter resets
4. APPROACH → DEPLOY needs **both** range and cradle confirmation (three cases)
5. full happy path IDLE → SEARCH → APPROACH → DEPLOY → LIFT → STOW → SHORE with scripted inputs; SHORE stops tracks after `shore_drive_ms`
6. SAFE from each of the 7 states on leak (loop over states)
7. SAFE on kill, SAFE on battery_low, SAFE on disarm; reason is correct
8. outputs all zero in SAFE; buzzer on
9. `reset()` ignored while a cause is active; works after it clears → IDLE
10. clamping: absurd gains never produce |thrust| > 1
11. determinism: two instances fed the same input sequence produce identical output sequences

## Definition of done
- [ ] `cd firmware/armini && pio test -e native` → all tests pass, 0 warnings
- [ ] `cd firmware/armini && pio run -e devkit_lipo` → builds
- [ ] `bash scripts/check.sh` → `check: OK` (with the native tests included)
- [ ] `README.md` has the mermaid state diagram and a table: parameter · default · unit · `VERIFY` / `SOURCE`
- [ ] no `millis()`, `delay()`, `new`, `malloc`, `String` in `lib/core`
- [ ] PR to `dev` with title `fw: mission state machine + native tests (T1)`

## PR description must include
- the list of config parameters marked `VERIFY` (Teddy will measure or decide each one)
- which board id you used and why
- anything you could not finish
