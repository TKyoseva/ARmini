# AR-Mini · Human in the loop

Version 4 · 9 October 2026 · one person: **Teddy** · two desks, two consultants, two automated agents · goal: submit on 1 November 2026 (MIT Early Action), then keep building.

## The loop

```
Hypothesis (Teddy) → Proposal (AI) → Review (Teddy) → Build (Teddy)
      ▲                                                    │
      └── Decision (Teddy) ◄── Analysis (AI) ◄── Measure (Teddy) ◄┘
```

Every arrow goes through Teddy. Every test is a card on the **AR-Mini Board** (C001, C002 …) with a hypothesis that has a number and a tolerance. Only Teddy closes a card, never an AI.

## Who does what

| Role | Tool | What it does | Output to Teddy |
|---|---|---|---|
| **Desk 1** | Claude: workshop chat + AR-Mini Board | architecture, CAD (OpenSCAD) and EDA (KiCad) files, decision records, test plans, logistics, specs for the agents, documentation and portfolio drafts; files photos into the card folders with captions | files written into the repo folder, a proposal with a hypothesis |
| **Desk 2** | Cursor: chat in the repo + background agents | all code; every commit (`dev`); night tasks on `night/*` branches that end in a pull request | commits, pull requests with "how to verify" |
| Consultant | Gemini | reads test videos ("at which second does the tilt start?") and long datasheets | an answer with a timestamp or page |
| Consultant | ChatGPT | second opinion before first power-up, LiPo work and long prints: "what can go wrong?" | a list of risks |
| Automated | Parts agent (`tools/parts`, GitHub Actions, hourly) | checks price, stock and lead time for every open need in `parts/needs.yaml`; computes the last day to order for each release | a Telegram message only when something changed or a deadline is near |
| Automated | Release video agent (`tools/video`, on the Mac) | picks the 2–3 most telling photos or clips of a release, cuts a 30–45 s video with captions from the cards | a draft GitHub Release and a shot list |

Only one file travels between the tools by hand: [docs/STATE.md](docs/STATE.md). Everything else lives in the repo, on the board, or in iCloud (`AR-Mini-Media/01_Loops/C###_…`).

## Rules for every AI

```
You are part of the AR-Mini AI team: a ~1:9 amphibious rescue robot demonstrator.
The human in the loop is Teddy. She makes every decision and is the only one who touches the robot.

1. Every proposal ends with a HYPOTHESIS (number and tolerance), a TEST (what Teddy does, < 30 min)
   and a PASS criterion.
2. Never invent dimensions, pins or specs. If they are missing, write a measuring task instead.
   Every physical number in code carries a // SOURCE: or // VERIFY: comment.
3. Never say something works before Teddy has tested it.
4. Safety: check for shorts before power; first power from the bench supply with a current limit;
   LiPo only in the bag.
5. Small steps: three quick cards beat one big one.
6. Chat with Teddy in Bulgarian or English; everything written into the repository is English.
7. Never push to main. Never rewrite history or change commit dates. No secrets in the repo.
```

### Per role
- **Desk 1 (Claude):** Every CAD change: parameter, old → new, why, what to print (material, time), what to measure after the print. Every wiring step: a pin-to-pin table, wire colour, the measurement before power and the expected number.
- **Desk 2 (Cursor):** PlatformIO, Arduino framework. CSV over serial at 10 Hz. Secrets only in `include/secrets.h`. Run `scripts/check.sh` before every commit; commit message `<area>: <what> (<old> → <new>) · C###`.
- **Night tasks:** one task file in `tasks/night/` = one branch = one pull request. Stop after the definition of done or after 3 failed attempts at one step.
- **Parts agent:** never buys. Teddy orders; the agent only watches and warns.
- **Release video agent:** captions come only from card fields; a Fail is as eligible as a Pass; no music, no generated images.

## Teddy's work

1. **3D printer:** dry and load PETG/PLA, clean bed, first layer, nozzle and belts, print log.
2. **Assembly:** heat-set inserts, hull sections with neutral silicone, beams, arm, cradle, box.
3. **Breadboard prototype:** DevKit-Lipo + BTS7960 + servo from the sheets; `bench_v1` with PWM_MAX 150.
4. **Soldering:** pins, terminals, XT60, heat-shrink, fume extraction; pull test and continuity.
5. **Electrical measurements:** continuity and shorts BEFORE power, rail voltages, current, battery.
6. **Size and mass:** caliper on every part, scale (target 4.7 kg), difference from CAD.
7. **Water tests:** leak (dry paper inside), bathtub (floating, draft, tilt), pool (swimming, lifting the dummy "Pesho").
8. **Firmware on the board:** upload over USB-C, CSV log, servo IDs.
9. **Photos (iPhone):** every part next to a ruler, every fail before and after, the instrument display with every number.
10. **Video (iPhone):** 4K 30 fps landscape, 5 s before and after, tripod from above, slow-mo for water.
11. **Lab and safety:** deliveries checked against the BOM, LiPo in the bag under supervision, on smoke switch off first.
12. **Decide and record:** review every AI proposal, close the card, merge `dev → main` after the physical test.

## Honesty in the portfolio

"Designed, built and tested by Teddy. AI tools (Claude, Cursor, with second opinions from ChatGPT and Gemini) proposed CAD changes, wiring, code and test plans and wrote most of the code; every proposal was reviewed and every result measured by Teddy."

Only name tools that were really used. Only show what has a photo, a video or a measurement.
