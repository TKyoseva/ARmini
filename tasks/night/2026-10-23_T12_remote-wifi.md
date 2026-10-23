# T12 · bench `remote` env: drive both thrusters from a phone over WiFi · card t-remote-wifi (C028)

**Branch** `night/remote` → PR to `dev` (Teddy reviews and merges in the morning)
**Budget** two to three hours

## Goal
G1 "swims on remote" (30.10). The DevKit makes its own WiFi access point; the phone opens one page with two sliders (thrust, turn) and a big STOP. Same safety contract as the `esc` env.

## Context (measured)
- Thruster ESCs: GPIO1 (L) / GPIO2 (R), LEDC 50 Hz, each through an S8050 NPN → output INVERTED (C006, T11 730317a). Reuse `bench::escDuty`, `bench::escDiff`, `Ramp`, `Deadman`, `KillInput` from `lib/benchcore` and the `esc` env; do not duplicate the maths.
- C025 (23.10, 12 V): 1550 µs does not spin (dead band), 1600 → 0.22 A, 1650 → 0.58 A, 1400 reverse → 0.21 A.
- Battery (C027, 23.10): `v_bat = 0.965 × v_nominal + 0.57`, v_nominal = v_adc × 130/30 (100 k / 30 k on GPIO4). Add `VBAT_GAIN 0.965f` / `VBAT_OFFSET_V 0.57f` with `// SOURCE: C027` where the bench reads VBAT (shared header, so `ladder` uses it too).
- KILL rocker: GPIO14 low = KILL (10 k to 3V3).
- Safety rule T2: no heartbeat for **500 ms → SAFE** (both 1500 µs, disarm).

## Change
1. `platformio.ini`: `[env:remote]` extends `esp32s3`, `build_src_filter = +<common/> +<remote/>`, pinned lib versions (e.g. `links2004/WebSockets@<exact>`; the core `WiFi` + `WebServer` are fine). CDC_ON_BOOT=1 (monitor on the left USB-C).
2. `firmware/bench/include/secrets.example.h` (in git): `#define AP_SSID "AR-Mini"`, `#define AP_PASS "change-me-8+chars"`. Real `firmware/bench/include/secrets.h` is **gitignored** → add the line `firmware/bench/include/secrets.h` to `.gitignore` (the existing `include/secrets.h` line only covers the repo root). Build fails with a clear `#error` if secrets.h is missing. Never print the password on serial.
3. `firmware/bench/src/remote/main.cpp`:
   - Both ESC outputs at 1500 µs (inverted duty) as the first thing in `setup()`.
   - WiFi soft-AP (WPA2, channel 6), IP 192.168.4.1. One HTML page served from flash (inline CSS/JS, no CDN — the phone has no internet on this AP).
   - WebSocket on port 81. Page → board every **100 ms**: `{"t":<thrust -100..100>,"r":<turn -100..100>,"arm":0|1}`. Board → page every 200 ms: `{"l":us,"r":us,"armed":0|1,"kill":0|1,"vbat":V,"rssi":dBm,"safe":"<reason>"}`.
   - Heartbeat = any valid message. **> 500 ms without one → both 1500 µs at once (no ramp), disarm, `safe:"heartbeat"`.** Same for KILL (`safe:"kill"`), page STOP (`safe:"stop"`), and a client disconnect.
   - Arming: page button ARM → 1500 µs held 3 s (like `arm` in `esc`), then armed; sliders must be at 0/0 to arm. Re-arm needed after any SAFE.
   - Mix with `escDiff` inside the soft limit **1350–1650 µs**; ramp 200 µs/s; stops are immediate.
   - Dead band: map |thrust| 1..100 to 1580..1650 (and 1420..1350 reverse) so small slider moves already spin the prop (C025: 1550 does nothing). Put the mapping in `EscMath.h` with host tests.
   - Serial CSV at 10 Hz: `t_ms,l_us,r_us,armed,kill,vbat,clients,last_hb_ms` + `# SAFE <reason>` lines.
4. Page: two vertical sliders (thrust left, turn right) that spring back to 0 on release, big red STOP (sends stop and keeps sending), ARM button, a line with v_bat / kill / link age / RSSI; turns red when the link age > 300 ms. Works on iPhone Safari in portrait. Touch, not mouse only.
5. `firmware/bench/src/remote/PROTOCOL.md`: bench test without water first (props in the bucket only at step 4): (1) build with secrets.h, flash, phone joins `AR-Mini`, page loads; (2) ARM, sliders, watch `l_us/r_us` in the CSV, thrusters NOT powered; (3) heartbeat test: phone to airplane mode → `# SAFE heartbeat` within 0.5 s; KILL rocker → `# SAFE kill`; (4) thrusters powered 12 V / 3 A in the bucket, thrust 30 / turn ±50, STOP; (5) range walk with the phone, note RSSI where the link drops. Pass lines for each.

## Tests (host, `pio test -e native`)
- dead-band map: 0 → 1500; +1 → 1580; +100 → 1650; −1 → 1420; −100 → 1350; clamp.
- diff + map: thrust 50 turn 0 → both equal; thrust 0 turn 100 → l forward, r reverse.
- heartbeat timeout logic as a pure function (last_hb, now, 500) → safe/unsafe.

## Do not touch
`main`, other envs except the shared VBAT constants, `include/secrets.h` contents, the armini firmware.

## Definition of done
- [ ] `pio test -e native` green
- [ ] `pio run -e remote` builds (with a local secrets.h copied from the example)
- [ ] `scripts/check.sh` green; `git status` shows no secrets.h
- [ ] PROTOCOL.md + `firmware/bench/README.md` env list + PINOUT note
- PR title: `fw: bench remote env (none → WiFi AP, phone sliders, 500 ms heartbeat) · C028`
