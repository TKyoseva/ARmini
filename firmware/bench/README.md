# firmware/bench · one known-good test sketch per module (DevKit-Lipo) — night task T3

Plug **one** module at a time into the Olimex ESP32-S3-DevKit-Lipo (breadboard sheet 2b), flash the matching
env, open the serial monitor at 115200, type `?`. Every sketch prints CSV at 10 Hz (MLX90640: 4 Hz), takes a
few commands, ramps actuators slowly, refuses commands above a soft limit and stops outputs on a 2 s dead-man
or when the rocker pulls KILL (GPIO14) low. Each module has a one-page `PROTOCOL.md`: wiring, what to measure
before power, expected numbers, pass criterion, photos.

**Status:** compiles (7 envs, 0 warnings) and the host tests pass. **Nothing has run on hardware yet** —
every number in a PROTOCOL marked `expected: record` or `VERIFY` is Teddy's to measure.

```
cd firmware/bench
pio run                            # build all seven module envs
pio test -e native                 # host unit tests of lib/benchcore (Unity, 29 cases)
pio run -e bts7960 -t upload       # flash one sketch over USB-C (hold BUT1 + RST if the port does not appear)
pio device monitor                 # 115200; `?` help, `0` stop
python3 scripts/bench_log.py --port /dev/tty.usbmodem* --card C005 --name bts-bench   # from the repo root: save the CSV
```

**Rocker in KILL whenever you flash or press reset; switch to RUN only after the banner.** GPIO39 (L RPWM) may be
pulled up during ESP32-S3 boot, so RPWM can be high until `setup()` runs. The hardware kill (R_EN/L_EN or OE through
the rocker) is what covers that window — the sketch cannot. Measurement to settle it: meter on GPIO39, rocker in KILL,
hold RST → `expected: record` ([bts7960 protocol §3](src/bts7960/PROTOCOL.md), PINOUT.md VERIFY item 4).

## Env → module → protocol

| env | module (bom.csv row) | bus / pins | CSV columns | protocol |
|---|---|---|---|---|
| `bts7960` | BTS7960 H-bridge (74) + ROB0154 motor (27) | LEDC PWM GPIO39/40 (L) or 41/42 (R) | `t_ms,cmd,pwm_r,pwm_l,is_r_mV,is_l_mV,kill` | [src/bts7960/PROTOCOL.md](src/bts7960/PROTOCOL.md) |
| `pca9685` | PCA9685 16-ch PWM (72) + hobby servo (30/31) | I2C-0 GPIO48/47 @0x40 | `t_ms,ch,us,sweep,kill` | [src/pca9685/PROTOCOL.md](src/pca9685/PROTOCOL.md) |
| `st3215` | ST3215 bus servo (29) via Waveshare driver (75) | UART1 GPIO17 TX / 18 RX, 1 Mbps | `t_ms,id,cmd_deg,pos_deg,load_permille,temp_C,volt_V,ok` | [src/st3215/PROTOCOL.md](src/st3215/PROTOCOL.md) |
| `mlx90640` | MLX90640 110° thermal camera (77) | I2C-1 GPIO8/9 @0x33 | `t_ms,min_C,max_C,mean_C,hot_x,hot_y` (4 Hz) | [src/mlx90640/PROTOCOL.md](src/mlx90640/PROTOCOL.md) |
| `bno055` | BNO055 IMU breakout (78) | I2C-0 GPIO48/47 @0x28 | `t_ms,heading_deg,roll_deg,pitch_deg,cal_sys,cal_gyro,cal_acc,cal_mag` | [src/bno055/PROTOCOL.md](src/bno055/PROTOCOL.md) |
| `ladder` | VBAT divider, LEAK probe, KILL rocker | ADC GPIO4, GPIO7; GPIO14 | `t_ms,v_adc_mV,v_bat_V,leak_mV,leak,kill` | [src/ladder/PROTOCOL.md](src/ladder/PROTOCOL.md) |
| `esc` | 2 × thruster ESC (C002, C024) | LEDC 50 Hz GPIO1 (L) / GPIO2 (R) | `t_ms,l_us,r_us,kill,armed` | [src/esc/PROTOCOL.md](src/esc/PROTOCOL.md) |

`pair <chA> <chB> <deg> [deg_per_s]` (pca9685, C023): both TD-8120MG move together from one degree, chB mirrored (`us_B = 3000 − us_A`), default 20 °/s. First lift 22–23.10 (empty U, level). `trim <ch> <us>` (T9): ±200 µs per-channel offset after the mirror, RAM only, to match arms clocked a tooth apart on the splines — not yet run on hardware.

`esc` (T10, C024): both outputs at 1500 µs from the first line of `setup()`; `arm` (3 s at 1500) before anything moves; `l` / `r` / `both` / `diff`, ramped at 200 µs/s; soft limit 1350–1650, `limit wide` 1000–2000. C006 (23.10): the ESC input idles at 5 V, so each pin drives an S8050 NPN and the output is **inverted** (T11, [protocol §1–2](src/esc/PROTOCOL.md)). Not yet run on hardware.

Pins: **only** in [include/pins_devkit.h](include/pins_devkit.h) (every line `// SOURCE: breadboard 2b` or `// VERIFY`).
The same table is in [hardware/wiring/PINOUT.md](../../hardware/wiring/PINOUT.md) ("DevKit-Lipo").

## Output contract (every sketch)

- Serial 115200. Banner lines start with `# `; then **one** CSV header (the first line without `#`); then rows.
- `t_ms` is always the first column (ms since boot). No units inside values; units live in the header name (`is_r_mV`).
- Everything that is not a CSV row starts with `# `: `# DEADMAN`, `# KILL …`, `# ERR <cmd>`, `# WARN …`, `# OK …`,
  the MLX heat map (`# |…|`) and raw frames (`# RAW <t_ms> v0 … v767`). So `pandas.read_csv(path, comment='#')`
  reads a bench log as is. (Task T3 spelled these as bare `ERR <cmd>` / `DEADMAN`; the `# ` prefix keeps the CSV parseable.)
- Commands: `?` help, `0` stop everything, unknown → `# ERR <cmd>`. Numbers are parsed strictly (`s 0.5x` → `# ERR`).
- **Dead-man** (actuator sketches): no command for 2 s (`dm <ms>` to change, `0` = off) → outputs stop, `# DEADMAN` printed once.
  Starts disengaged, so an idle board does not nag; the first command arms it.
- **Ramp**: actuator targets never jump (`bench::Ramp`, default 0.5/s for the BTS, 500 µs/s for the PCA, 60 °/s for the ST3215).
  Stopping (`0`, dead-man, KILL) is the one immediate action.
- **Soft limit**: starts at 60 % (BTS: 0.60 = 150/255 like `bench_v1.ino`; PCA: 1000–2000 µs window; ST3215: 72–288° = 60 % of 360°
  centred on 180°). Anything beyond is **refused** with a `# WARN` until `limit …` raises it explicitly, which also prints a warning.
- **KILL**: GPIO14 read with the internal pull-up in every actuator sketch (low = KILL) → stop + refuse commands.
  It is the software half of the kill; the hardware half is the rocker on R_EN/L_EN (BTS) or OE (PCA9685), see the protocols.
- No WiFi, no secrets, nothing stored on the board (calibration factors are printed for the card).
- On-board green LED (GPIO38) flashes once a second = sketch alive.

## Layout

| Path | What |
|---|---|
| `platformio.ini` | one env per module (`build_src_filter = +<common/> +<module/>`), `[env:native]` for the host tests, exact library pins |
| `include/pins_devkit.h` | every GPIO, with SOURCE/VERIFY |
| `lib/benchcore/` | `Ramp.h`, `Deadman.h`, `SoftLimit.h`, `Csv.h`, `PairMath.h`, `EscMath.h` — pure C++11, no Arduino, tested on the host |
| `src/common/` | `Cli.h/.cpp` (line parser), `Bench.h` (banner, `# ` messages, `Periodic`, `KillInput`, `Heartbeat`), `I2cScan.h` |
| `src/<module>/main.cpp` + `PROTOCOL.md` | the sketch and its one-page test protocol |
| `test/test_benchcore/` | Unity tests: Ramp rate/target/sign change/stop, Deadman trip once/reset/wrap-around, CSV formatting, SoftLimit refuse-until-unlocked, pipeline, PairMath mirror / 4.5 s ramp / trim, EscMath diff mix / clamp / 0.75 s ramp / inverted duty |

Task T3 listed `Csv.h`, `Ramp.h`, `Deadman.h` under `src/common/`; they live in `lib/benchcore/` instead so that the
`native` env can test them without Arduino (the task's "Tests" section asks for exactly that).

## Libraries (pinned, exact)

| env | library | version |
|---|---|---|
| pca9685 | adafruit/Adafruit PWM Servo Driver Library | 3.0.3 |
| pca9685, mlx90640, bno055 | adafruit/Adafruit BusIO | 1.17.4 |
| st3215 | workloads/SCServo (Waveshare SMS_STS, registry mirror of `waveshareteam/ugv_base_general`) | 1.0.1 |
| mlx90640 | adafruit/Adafruit MLX90640 | 1.1.2 |
| bno055 | adafruit/Adafruit BNO055 | 1.6.4 |
| bno055 | adafruit/Adafruit Unified Sensor | 1.1.15 |
| native | throwtheswitch/Unity (test framework, pulled by PlatformIO) | ^2.6.1 |

Platform: `espressif32` (built with 7.1.3, Arduino core 2.0.17), board id `esp32-s3-devkitc-1` with
`memory_type = qio_opi` for the N8R8 module — same reasoning as `firmware/armini/platformio.ini`. The LEDC
calls in `bts7960` are guarded for both Arduino core 2.x and 3.x.

## VERIFY list (pins and values that are not on sheet 2b)

| Where | What | How to settle it |
|---|---|---|
| `PIN_BTS_L_RPWM/LPWM` 39/40, `PIN_BTS_R_RPWM/LPWM` 41/42 | sheet 2b gives the pairs, not which pin is RPWM; lower = RPWM chosen | bts7960 protocol step 2: if the track runs backwards, swap the wires and note it on sheet 2b |
| `PIN_BTS_IS_R` 10, `PIN_BTS_IS_L` 11 | IS pins are not on sheet 2b; two free analog pins proposed | measure IS voltage first (protocol §2); decide whether to wire them at all |
| bts7960 PWM 1 kHz | chosen (Mega ran ~490 Hz; BTS7960 allows ≤ 25 kHz) | listen for whine; change `kPwmHz` if needed |
| pca9685 oscillator 25 MHz | library default; real chips are often ~27 MHz | logic analyser on CH0: 20.0 ms frame → `osc <Hz>` |
| pca9685 I2C 400 kHz, mlx90640 I2C 400 kHz, bno055 I2C 100 kHz | bench choices | `scan` finds the device; raise/lower on errors |
| st3215 speed 1000 steps/s, acc 50, ramp 60 °/s | bench choices from the Waveshare examples | protocol steps 3–4 (± 2°) |
| bno055 `xtal 0` default, which pin is VIN vs 3V3, roll/pitch column | breakout from GoTo (bom row 78) is unknown | protocol steps 2, 7 |
| ladder `leakth` 2000 mV | midpoint of 3.3 V dry / ≈ 1.06 V wet from sheet 2b | protocol step 7 |
| ladder ADC at 12.6 V | 2.91 V (100 k / 30 k, C027); the 11 dB range is characterised to ≈ 3.1 V | protocol step 4 |
| mlx90640 `hot_x`/`hot_y` orientation | which edge is x = 0 | protocol steps 3–4 |

## Not done / open

- Thruster ESCs (GPIO1/2): env `esc` (T10) runs one thruster in a bucket on the Jesverty (C025); full power stays on the LiPo + 20 A slot, ≤ 5 s.
- No sketch for the MLX90642-D45 (bom row 76): the Melexis driver is not in the repo (`firmware/xiao/lib/MLX90642` mentioned
  in `firmware/xiao/platformio.ini` is empty); the Adafruit MLX90640 library does not speak to the 90642.
- `scripts/bench_log.py` needs `pyserial` for a real port (`pip install pyserial`); `--fake` works without it.
