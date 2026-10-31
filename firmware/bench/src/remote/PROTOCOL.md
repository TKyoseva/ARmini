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

## 6. Env `remote_rudder` · one thruster + rudder (C056, 29.10.2026)

`pio run -e remote_rudder -t upload`. Same page, same safety contract. **thrust** slider → left ESC on GPIO1 (S8050, inverted, dead band 1580 / 1420, 1350–1650). **turn** slider → MG90S rudder on GPIO2, **direct, not inverted**, `rudderUs`: 0 → 1500, ±100 → 1833 / 1167 µs (±30° estimate), ramp 2000 µs/s. Releasing the slider centres the rudder; any SAFE centres it at once.

Wiring: MG90S signal (orange) → the GPIO2 header pin itself (before the 1 k to the S8050 base; pull that 1 k out), red → +5 V (EXT1 pin 21), brown → GND. Never 12 V, never the PCA9685 V+.

**Pass (thruster NOT powered):** turn +100 → `r_us` 1833, horn swings one way; −100 → 1167, the other way; release → 1500 = blade straight. If ±100 hits the stops (buzzing), measure the real ends and lower `kRudderHalfUs`.

### 6.1 Env `remote_rudder_hct` (C058, 29.10.2026)
Same as `remote_rudder`, but GPIO1 (thruster) and GPIO2 (rudder) go through a **74HCT125** powered from +5 V (EXT1-21):
1A = GPIO1 → 1Y = ESC yellow, 2A = GPIO2 → 2Y = MG90S orange, 1OE/2OE to GND, 3A/4A to GND, 3OE/4OE to +5 V,
100 nF across pins 14–7, 10 kΩ from 1A to GND (ESC sees LOW, no pulses, while the ESP32 boots).
The buffer does **not** invert, so `kEscInvert = false` (-DESC_BUFFER). The S8050 stage (1 k, 10 k, S8050) is removed.
**Never flash `remote_rudder` with the 74HCT125 wired, or `remote_rudder_hct` with the S8050 wired:** the ESC would get inverted pulses.

## 7. Env `remote_pool` · thruster + rudder + cradle lift (pool run 31.10.2026)

`pio run -e remote_pool -t upload`. Everything from §6.1 (`remote_rudder_hct`, the 74HCT125 **must** be wired) plus the
two cradle servos of C023 on the PCA9685, driven from a third slider.

| | |
|---|---|
| PCA9685 | I2C-0: SDA GPIO48, SCL GPIO47 (EXT2 16 / 17), VCC 3V3, GND; OE open (module 10 k to GND). Address 0x40, same module as the `pca9685` env |
| servos | TD-8120MG A on **CH12**, B on **CH11**, mirrored (`us_B = 3000 − us_A`, PairMath). Trims 0 — C023 showed trim changes nothing; `-DLIFT_TRIM_A_US=… -DLIFT_TRIM_B_US=…` if ever needed |
| servo power | **5 V** from the QIQIAZI 5 V / 5 A buck (BOM row 80) on fuse F2 into the green **V+** terminal, GND common. **Never 12 V.** C023 at 6.0 V: 0.25 A lifting Pesho, up to 1.1 A holding the empty U (stiction, not fighting). 5 V = ~15 % less torque, enough |
| page | third slider **lift** 50–130°, and it **stays** where released (thrust / turn spring back). 50 = U deployed (down), 130 = raised between the hulls (C023). The bar shows `lift 50°…130°` or `lift off` |
| pulses | OFF at boot and after KILL. **ARM** turns them on with a snap to the slider (`# lift ON at <deg> deg`), so the slider must already show the pose the U is in: deployed = slider at the bottom = 50 (where it is when the page loads). Every later move ramps at 20 °/s |
| SAFE | heartbeat, STOP, disconnect, `0`: thruster 1500, rudder centred, **lift holds** (a ramp in progress stops where it is — the U never drops on a WiFi hiccup). **KILL**: lift pulses off, servos limp, the U settles deployed; before the next ARM slide lift back to 50 |
| serial | `lift <50..130>` moves the pair without the phone (dry test), `lift off` drops both pulses, `?` shows `lift=<deg> (req <slider>, pca ok)` |
| status | JSON `"u"` = pair degree (−1 = off); CSV column `lift_deg` (−1 = off) |

Boot banner: `# OK PCA9685 0x40 (SDA GPIO48, SCL GPIO47): LIFT CH12/CH11 50–130 deg, 50 = deployed, pulses OFF until ARM`.
`# WARN PCA9685 not found` = SDA/SCL swapped or VCC/GND missing; thrust and rudder still work, the lift is disabled.

### 7.1 Dry test (servo 5 V on, thruster NOT powered, U empty, hands clear of the arms)

| # | Action | Expected |
|---|---|---|
| 1 | boot, rocker RUN | banner line above; page bar `lift off` |
| 2 | lift slider at the bottom (50), U resting deployed, ARM | `# ARMED`, `# lift ON at 50 deg`; the arms twitch a few degrees at most |
| 3 | slide lift slowly to the top | the U rises level to 130 in ≈ 4 s; CSV `lift_deg` 50 → 130; current at the buck: `expected: record` |
| 4 | slide back to the bottom | the U comes down to 50 |
| 5 | lift at 130, press STOP | `# SAFE stop`, the U **stays up**. ARM again → nothing moves until the slider moves |
| 6 | lift at 130, phone to airplane mode | `# SAFE heartbeat`, the U stays up |
| 7 | lift at 130, rocker → KILL | `# SAFE kill`, `# lift OFF (KILL) …`, the U drops limp to deployed. Rocker RUN, slider to 50, ARM → snap of a few degrees only |
| 8 | monitor: `lift 90`, `lift 130`, `lift off` | pair moves without the phone; `lift 140` → `# ERR lift (want: lift <50..130> \| lift off)` |

**Pass:** rows 2–8 as written; the U never twists (arms clocked at the same pose, C023 / FAILS 172); a standing current > 0.3 A
only during a stiction stall that a nudge by hand releases (C023), never from the servos fighting.

### 7.2 In the pool

ARM at the edge with the U deployed on its support (lift at 50), then put the robot in; the lift holds 50 while it floats and drives.
Drive over Pesho with thrust / turn, release both, slide **lift** up slowly to 130. Watch `vbat` and the buck: stop at ≤ 10.5 V.
Photos: page with `lift`, the U at 50 and at 130, video of a full pick-up, CSV with `lift_deg`.
