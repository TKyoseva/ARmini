# Goals, releases, analyses, roadmap — how the board works from 15.10.2026

The kanban stays: Backlog → Today (WIP 3, the clock starts when a card is pulled) → Done → Release. Three things are added above and below it.

## 1. Goals (global, dated)

| Goal | Due | What it is |
|---|---|---|
| **G1** | **30.10.2026** (hard 01.11) | Maker Portfolio v1 for Early Action: R3b full cycle on video, portfolio PDF/site, repo public |
| **G2** | **30.12.2026** (hard ~05.01) | Portfolio v2 for Regular Decision: real-water evidence and measured numbers (thrust, drag, thermal range, runtime), carrier rev B in the boat |
| **G3** | **2027** | AR-Mini v2 + the first activity from the roadmap (publication / competition / open-source release); university year 1 with a lab and a first grant |

Goals live in the board (`goals` collection) and show above the columns with a countdown. Every milestone and every release belongs to a goal.

## 2. Releases every few days

- A **milestone** is a dated target with a sentence a test can check (R1a … R4). It is cut when the test passes.
- A **release** is cut from Done whenever there is something to show — **every 3–4 days or when 5+ cards are done**, whichever comes first — named by date (`R-1018`). It is a changelog entry, not a promise.
- Each cut = the board entry + a git tag `r2026-10-18` on `dev` (Cursor) + one line in `docs/LOG.md` + the ★ media of its cards. The portfolio is written from the release notes.
- Today holds 3 cards. A card that has not moved for two days goes back to Backlog (its clock resets); the time-per-card chart stays honest.

## 3. An analysis on every card

Written at card close by Claude (as a draft while the card runs, if it is already clear), approved or edited by Teddy on the board. Fields:

1. **Challenge we hit** — what, in one breath, and why it mattered.
2. **Solutions that exist** — the options found, each with where it comes from (datasheet, paper, practice, ours); the one we chose marked ✓.
3. **What we chose and why.**
4. **Lesson that transfers** — the sentence that goes into FAILS_AND_FIXES.
5. **Next activity** — research · publication · patent · open source · business idea · none. "None" is a fine answer; most print cards are none.
6. **Impact 0–3 on three axes, in this order of importance:** nature & people → financial → scientific. The roadmap sorts by this order.
7. **Path** — once admitted: which course or lab would host it (per school, since the school is not known yet), which grant pays for it, which competition it fits. These are suggestions as of October 2026; names, eligibility and dates are verified when applying.
8. **Seed** yes/no and **when** (by 30.10 · by 30.12 · 2027 · university year 1 · year 2+).

Not every closed card gets a full analysis the same day: the 5 strongest challenges of the EA phase first (G1 criterion), the rest by G2.

## 4. Roadmap

The **Roadmap** tab on the board = the goals with their criteria and milestones + every seed grouped by activity type, sorted nature & people → financial → scientific, with its path. It is the living document; at G2 it is exported (`board.json` → `docs/portfolio/roadmap_v1.md`) as the personal development roadmap for the next years, and refreshed at every goal.

First three analyses (15.10): C041 thruster kick-up mount (publication, 2027), C032 carrier rev B (open-source tool, university), C021 Pesho thermal dummy (research — the highest-impact thread, draft).
