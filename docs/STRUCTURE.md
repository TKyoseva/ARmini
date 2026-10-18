# Repository structure

```
ARmini/
├── README.md                 what it is, status, picture, subsystems, how it is built
├── AGENTS.md                 human in the loop: who does what, rules for every AI
├── CONTRIBUTORS.md           who did what
├── LICENSE                   MIT (code) + CC BY 4.0 (CAD, PCB, docs, images)
├── .cursor/rules/            rules the Cursor agent reads in every chat
├── .github/workflows/        check.yml (every push) · parts.yml (hourly parts agent)
│
├── docs/
│   ├── STATE.md              the current state on one page
│   ├── LOG.md                build log: date · what I tried · what happened · what I change
│   ├── STRUCTURE.md          this file
│   ├── FAILS_AND_FIXES.md    every failure and how it was fixed (numbered, dated)
│   ├── timeline/TIMELINE.md  timeline from 9/2025 with REAL dates (including work before the repo)
│   ├── decisions/            short "why" records: 0001-license, 0002-chassis-on-beams, …
│   ├── bom/                  BOM spreadsheet + bom.csv (diff-friendly copy) + visual BOM (+ src/, history/)
│   ├── diagrams/             hardware poster, architecture, mechanism drawings (+ src/ that draws them, history/ first sketches)
│   ├── process/              how the work is organised: lab protocol, information flow, setup, GOALS_AND_ROADMAP.md, CLAUDE_PROJECT.md (+ src/, history/)
│   ├── releases/             one page per release: video link + shot list
│   └── portfolio/            the 25 portfolio attachments and their descriptions; ASSETS.md = every card's files + media
│
├── cad/
│   ├── openscad/             AR-Mini_v1.scad (whole robot + every printed part) + interfaces.scad (generated)
│   ├── fusion/               hull script for Fusion 360
│   ├── 3d/                   renders (PNG) + interactive model (HTML) + src/ (Python that makes them)
│   └── stl/                  released STLs only, by version (v1/ = what was printed, with README)
│
├── pcb/
│   ├── xiao-breakout-rev0/   first board: KiCad file, README, DRC rounds
│   ├── carrier-revA/         SPEC.md of the first carrier idea (superseded)
│   └── carrier-revB/         the ordered board: SPEC.md, gen.py, .kicad_pcb, 1:1 + fit-check PDFs, drc/, measure/, src/ (checks without KiCad), history/
│
├── interfaces/interfaces.json   the only source for numbers shared by CAD and PCB
│
├── firmware/
│   ├── xiao/                 PlatformIO (platformio.ini, src/, lib/, include/secrets.example.h)
│   ├── armini/               mission state machine + safety, host tests (night tasks T1, T2)
│   └── mega/                 Arduino bench sketches: bench/, thrust-rig/, teleop/
│
├── hardware/
│   ├── breadboard/           breadboard wiring sheets (+ src/ that draws them)
│   ├── wiring/               PINOUT.md, wire colours, connectors
│   └── datasheets/           links and notes
│
├── parts/                    needs.yaml (what is missing, by release) — input of the parts agent
├── tools/                    parts/ (hourly sourcing agent) · video/ (release video agent) · board/ (the kanban page, its history and smoke test)
├── tasks/
│   ├── night/                specs for Cursor background agents (T1 … T5)
│   └── inbox/                files handed over from the workshop chat
├── scripts/                  check.sh (runs before every commit and in CI), sync_interfaces.py
│
├── data/
│   ├── board/board.json      export of the AR-Mini Board: cards (with files + media), releases, goals, analyses (+ history/)
│   ├── logs/                 one folder per test session: YYYY-MM-DD_topic/*.csv
│   ├── thrust-test/          thrust and current table + photo of the rig
│   ├── buoyancy/             draft, ballast, centre of gravity / buoyancy
│   ├── missions/             the simulation missions
│   └── scripts/              Python that makes the plots from the CSVs
│
├── sim/                      the simulation from the paper (imported)
├── software/pi/              v2: ROS 2 packages, launch files
│
└── media/
    ├── LINKS.md              card ID → iCloud folder (photos and videos are NOT in git); the card's files field → docs/portfolio/ASSETS.md
    └── photos/               a few early photos from before the iCloud rule
```

## Rules
- **One commit = one change with a verb and the card ID:** `cad: thruster pivot (70 → 75 mm) · C005`.
- **Folders with a date** `YYYY-MM-DD_topic` in data/ — they sort themselves.
- **No Git LFS:** every file is under 5 MB. Photos and videos live in iCloud (`AR-Mini-Media/01_Loops/C###_date_name/`), never in git.
- **No passwords** in code: `include/secrets.h` is in .gitignore; `secrets.example.h` shows the format. API keys only in GitHub Secrets.
- **Branches:** `main` always works and only Teddy merges into it; `dev` for AI commits; `night/*` for background agents, each ending in a pull request.
- **Tags** for releases and the portfolio: `r2a`, `r2c`, … and `portfolio-2026-11-01`.
- **history/ folders** keep superseded versions with a date prefix (`2026-10-07_…`) and a README line each: the portfolio tells how things changed. Nothing is deleted or backdated.
- **Every card links its evidence:** `media` = its iCloud folder, `files` = repo paths; both live on the board and in `data/board/board.json`.
