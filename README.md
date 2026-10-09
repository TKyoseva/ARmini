# AR-Mini · AmphiReach

AR-Mini is a ~1:9 physical demonstrator of **AmphiReach**, an autonomous amphibious rescue robot (simulation and paper 2025–2026, Horizon Academic). The robot finds a person in the water by body heat, lifts them onto a cradle between two catamaran hulls and drives out of the water on tracks.

**Status, 9 October 2026:** CAD v2.0 (thruster mount redesigned from measured parts), first PCB (XIAO breakout rev 0) DRC-clean, bench electronics started, mission state machine with host tests on a branch. Cards C001–C003 closed with measurements. Next releases: r1a 11.10 (front hull section floats) · r2a 16.10 (thruster spins in a bucket) · r2c 22.10 (swims on remote) · r3a 26.10 (thermal camera finds the dummy) · r3b 29.10 (full rescue cycle). MIT Maker Portfolio: 1 November 2026.

![AR-Mini 3D model](cad/3d/AR-Mini_3D_renders.png)

| Subsystem | What it is |
|---|---|
| Hulls | 2 × catamaran hull 610 × 100 × 120 mm, PETG, each printed in 2 sections of 305 mm; 250 mm gap; draft 42 mm at 4.7 kg |
| Water drive | 2 × Cuifati underwater thrusters (12 V, ESC inside), differential steering, kick-up mount on the transom ([decision 0004](docs/decisions/0004-kick-up-thruster-mount.md)) |
| Land drive | DFRobot ROB0154 tracked chassis, bolted under two 15 × 15 aluminium cross-beams |
| Rescue lift | parallelogram arms (110 mm) on Waveshare ST3215 bus servos, Ø5 aluminium cradle 220 × 123 mm |
| Sensing | MLX90642-D45 thermal camera on a pan servo (search), MLX90640 110° on the cradle (confirm), BNO055 IMU, leak probe |
| Control | Seeed XIAO ESP32-S3 Sense (FreeRTOS) · PCA9685 PWM · 2 × BTS7960 · serial bus servo driver · Raspberry Pi 5 + ROS 2 in v2 |
| Power | 2 × LiPo 3S 2200 mAh · 30 A inline fuse · 50 A main switch · 6-slot fuse block · logic kill rocker |

## Where to look
- **3D model** — [cad/3d/](cad/3d/): open `AR-Mini_3D.html` in a browser (rotate, run the lift, point at a part to see its name).
- **CAD** — [cad/openscad/AR-Mini_v1.scad](cad/openscad/AR-Mini_v1.scad): the whole robot and every printed part, parametric. Hull script for Fusion 360 in [cad/fusion/](cad/fusion/).
- **Electronics** — architecture: [docs/diagrams/AR-Mini_architecture_v1.png](docs/diagrams/AR-Mini_architecture_v1.png); first board: [pcb/xiao-breakout-rev0/](pcb/xiao-breakout-rev0/) (with all three DRC rounds); next board: [pcb/carrier-revA/SPEC.md](pcb/carrier-revA/SPEC.md); pins: [hardware/wiring/PINOUT.md](hardware/wiring/PINOUT.md); breadboard sheets: [hardware/breadboard/](hardware/breadboard/).
- **Firmware** — [firmware/](firmware/): PlatformIO projects for the XIAO and the DevKit-Lipo, bench sketches for the Mega.
- **Bill of materials** — [docs/bom/](docs/bom/): the spreadsheet (with photos) and the one-page visual BOM.
- **What went wrong and how it was fixed** — [docs/FAILS_AND_FIXES.md](docs/FAILS_AND_FIXES.md).
- **Design decisions** — [docs/decisions/](docs/decisions/) · **build log** — [docs/LOG.md](docs/LOG.md) · **timeline with real dates** — [docs/timeline/TIMELINE.md](docs/timeline/TIMELINE.md) · **current state on one page** — [docs/STATE.md](docs/STATE.md).
- **Every test card** — [data/board/board.json](data/board/board.json): hypothesis, result, Pass / Partial / Fail, link to the photos.

## How it is built: human in the loop
I (Teddy, Teodora Kyoseva) design, build, measure and decide. I work alone, with AI tools:

- **Claude** (workshop chat and the AR-Mini Board) proposes CAD changes, wiring, test plans and documentation, and writes them as files into this repository.
- **Cursor** writes most of the code and makes the commits; its background agents work on night tasks ([tasks/night/](tasks/night/)) and open pull requests.
- **Gemini** reads test videos and long datasheets; **ChatGPT** gives a second opinion before risky steps (first power-up, LiPo, long prints).

Every proposal is reviewed by me, and every result is measured by me on the real robot before it reaches `main`. Most of the code and the CAD and PCB scripts in this repository were written by AI agents under my direction; the physical work, the measurements and the decisions are mine. Roles and rules: [AGENTS.md](AGENTS.md) · diagrams: [docs/process/](docs/process/).

- `dev` — AI agents commit here after [scripts/check.sh](scripts/check.sh) passes (OpenSCAD render, KiCad ERC/DRC, PlatformIO builds, host tests).
- `night/*` — background agents, each ends with a pull request to `dev`.
- `main` — I merge after the physical test is logged.
- Every test is a card with an ID (C001, C002 …). The same ID names the photo folder, the data files and the commit message.

## About this repository
The repository was created on **6 October 2026**. Work from 28 September to 6 October was imported in the first commits with its files unchanged; the real dates of that work are in the timeline and in the build log, not in the commit dates. Photos and videos are kept outside git (iCloud), indexed in [media/LINKS.md](media/LINKS.md). The research manuscript is not part of this repository.

## License
Code: MIT. CAD, PCB, documentation and images: CC BY 4.0. See [LICENSE](LICENSE) and [decision 0001](docs/decisions/0001-license.md).

See [CONTRIBUTORS.md](CONTRIBUTORS.md).
