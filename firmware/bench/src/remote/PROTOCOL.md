# Bench protocol · remote · both thrusters from a phone over WiFi · C028 (T12)

Env `remote` · CSV `t_ms,l_us,r_us,armed,kill,vbat,clients,last_hb_ms` at 10 Hz (`last_hb_ms` = age of the last valid message, −1 = none yet) · pins from `include/pins_devkit.h`.
Wiring of the ESCs, NPN stages and KILL rocker: exactly as [esc protocol §2](../esc/PROTOCOL.md). Nothing new on the board.
**Not yet run on hardware.**

Safety contract: both outputs 1500 µs from the first line of `setup()`; nothing moves until ARM (sliders at 0/0, 3 s at 1500 µs). SAFE = both 1500 µs at once + disarm, printed as `# SAFE <reason>`:

| reason | trigger |
|---|---|
| `heartbeat` | no valid message for > 500 ms (the page sends every 100 ms) |
| `kill` | rocker in KILL (GPIO14 low) |
| `stop` | page STOP (keeps sending while held) |
| `disconnect` | the phone's WebSocket closed |
| `serial` | `0` in the monitor |

After any SAFE press ARM again. Soft limit 1350–1650 µs, ramp 200 µs/s, dead band: slider ±1 → 1580 / 1420 µs, ±100 → 1650 / 1350 µs.

## 1. Build, flash, page loads (thrusters NOT powered)

```
cd firmware/bench
cp include/secrets.example.h include/secrets.h   # then set AP_PASS (≥ 8 chars) in secrets.h
pio run -e remote -t upload
pio device monitor
```
`git status` must not list `secrets.h`. Rocker in KILL while flashing.
iPhone: Settings → WiFi → `AR-Mini`, password from `secrets.h` → Safari `http://192.168.4.1`, portrait.

**Pass:** banner `# OK WiFi AP "AR-Mini" ch 6, open http://192.168.4.1` (no password on serial); page shows two sliders, ARM, STOP; status line not red; CSV `clients` = 1, `last_hb_ms` < 300.

## 2. ARM and sliders (thrusters NOT powered, only the DevKit on USB)

Rocker RUN. Press ARM with both sliders released. Wait 3 s → `# ARMED`, button turns green. Move thrust to the top, then turn to the top, release.

| Action | Expected `l_us` / `r_us` |
|---|---|
| ARM, sliders 0/0 | 1500 / 1500, `# ARMED` after 3 s |
| ARM with a slider held | `# WARN arm refused: sliders must be at 0/0` |
| thrust ≈ +1 (tiny move) | ≈ 1580 / 1580 (after the ramp) |
| thrust top (+100) | 1650 / 1650, reached in ≈ 0.75 s from 1500 |
| turn top (+100), thrust 0 | 1650 / 1350 (left forward, right reverse) |
| release both | ramps back to 1500 / 1500 |

**Pass:** every row as listed ± 5 µs; never outside 1350–1650.

## 3. SAFE triggers (thrusters NOT powered)

ARM, thrust at +50 (≈ 1615 µs), then for each row re-ARM first:

| Action | Expected |
|---|---|
| phone to airplane mode | `# SAFE heartbeat` and both 1500 within 0.5 s (CSV `last_hb_ms` passes 500, then `l_us`/`r_us` 1500) |
| rocker to KILL | `# SAFE kill`, both 1500 at once; ARM refused while KILL |
| press STOP | `# SAFE stop`, both 1500 at once |
| close the Safari tab | `# SAFE disconnect` (or `heartbeat`, whichever comes first) |
| `0` in the monitor | `# SAFE serial` |

**Pass:** each SAFE line appears, `l_us`/`r_us` = 1500 in the next CSV row (no ramp), `armed` = 0. Heartbeat row: time from airplane mode to `# SAFE heartbeat` ≤ 0.6 s (read from `t_ms`, record it).

## 4. Thrusters in the bucket (Jesverty 12 V, 3 A limit)

Props under water in the bucket, hands clear, someone on the supply OUTPUT button. Rocker KILL → power → RUN → ARM.

| Action | Expected |
|---|---|
| thrust 30, turn 0 | both spin forward, Jesverty current: record (C025: 1600 µs → 0.22 A per ESC) |
| thrust 0, turn +50 | left forward, right reverse |
| thrust 0, turn −50 | right forward, left reverse |
| STOP | both stop at once |

**Pass:** directions as listed; current < 3 A (no limit hit); STOP stops both within 0.5 s (video). If a side spins backwards, swap two of its motor wires — not in code. Record currents on the card.

## 5. Range walk (thrusters NOT powered)

ARM, thrust held at +30. Walk away from the board with the phone; note the RSSI on the page every 5 m.

**Pass:** record the distance and RSSI where the status line turns red or `# SAFE heartbeat` fires; the board must go SAFE every time the link drops (no case where it keeps the last value). Expected: record.

## Photos / video
Page on the phone (screenshot), CSV during step 3, video of step 4 with STOP. Files to iCloud `AR-Mini-Media/01_Loops/C028_…`.
