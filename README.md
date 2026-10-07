# AR-Mini · AmphiReach

AR-Mini is a ~1:9 physical demonstrator of **AmphiReach**, an autonomous amphibious rescue robot (simulation and paper 2025–2026, Horizon Academic). The robot finds a person in the water by body heat, lifts them onto a cradle between two catamaran hulls and drives out of the water on tracks.

**Status, 7 October 2026:** CAD v1.9, first PCB (XIAO breakout rev 0) DRC-clean, most parts delivered, bench electronics starting. Plan: R1 13.10 (section floats, arm lifts the dummy) · R2 22.10 (full hull swims) · R3 29.10 (search by heat → approach → lift). MIT Maker Portfolio: 1 November 2026.

![AR-Mini 3D model](cad/3d/AR-Mini_3D_renders.png)

| Subsystem | What it is |
|---|---|
| Hulls | 2 × catamaran hull 610 × 100 × 120 mm, PETG, each printed in 2 sections of 305 mm; 250 mm gap; draft 42 mm at 4.7 kg |
| Water drive | 2 × Cuifati 560 KV underwater thrusters (12 V), differential steering |
| Land drive | DFRobot ROB0154 tracked chassis, bolted under two 15 × 15 aluminium cross-beams |
| Rescue lift | parallelogram arms (110 mm) on Waveshare ST3215 bus servos, Ø5 aluminium cradle 220 × 123 mm |
| Sensing | MLX90642-D45 thermal camera on a pan servo (search), MLX90640 110° on the cradle (confirm), BNO055 IMU, leak probe |
| Control | Seeed XIAO ESP32-S3 Sense (FreeRTOS) · PCA9685 PWM · 2 × BTS7960 · serial bus servo driver · Raspberry Pi 5 + ROS 2 in v2 |
| Power | 2 × LiPo 3S 2200 mAh · 30 A inline fuse · 50 A main switch · 6-slot fuse block · logic kill rocker |

## Where to look
- **3D model** — [cad/3d/](cad/3d/): open `AR-Mini_3D.html` in a browser (rotate, run the lift, point at a part to see its name).
- **CAD** — [cad/openscad/AR-Mini_v1.scad](cad/openscad/AR-Mini_v1.scad): the whole robot and every printed part, parametric. Hull script for Fusion 360 in [cad/fusion/](cad/fusion/).
- **Electronics** — architecture: [docs/diagrams/AR-Mini_architecture_v1.png](docs/diagrams/AR-Mini_architecture_v1.png); first board: [pcb/xiao-breakout-rev0/](pcb/xiao-breakout-rev0/) (with all three DRC rounds); next board: [pcb/carrier-revA/SPEC.md](pcb/carrier-revA/SPEC.md); pins: [hardware/wiring/PINOUT.md](hardware/wiring/PINOUT.md).
- **Bill of materials** — [docs/bom/](docs/bom/): the spreadsheet (120 items with photos) and the one-page visual BOM.
- **What went wrong and how it was fixed** — [docs/FAILS_AND_FIXES.md](docs/FAILS_AND_FIXES.md).
- **Build log** — [docs/LOG.md](docs/LOG.md) · **timeline with real dates** — [docs/timeline/TIMELINE.md](docs/timeline/TIMELINE.md) · **design decisions** — [docs/decisions/](docs/decisions/).

## About this repository
The repository was created on **6 October 2026**. Work from 28 September to 6 October was imported in the first commits with its files unchanged; the real dates of that work are in the timeline and in the build log, not in the commit dates. The research manuscript is not part of this repository.

## How it is built: human in the loop
Teddy (Teodora Kyoseva) designs, builds, measures and decides. AI agents (Claude Projects, Cursor, with second opinions from ChatGPT and Gemini) propose CAD changes, wiring, code and test plans; every proposal is reviewed and every result is measured by Teddy before it reaches `main`. Roles and rules: [AGENTS.md](AGENTS.md) · diagrams: [docs/process/](docs/process/).

- `dev` — the AI agent commits here after `scripts/check.sh` passes.
- `main` — Teddy merges after the physical test is logged.
- Every loop has an ID (L001, L002 …) used in the tracker, the iCloud media folder, data files and commit messages.

See [CONTRIBUTORS.md](CONTRIBUTORS.md).
