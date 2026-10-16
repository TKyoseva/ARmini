# tools/board — the AR-Mini Board

`ar-mini-board.html` is the source of the kanban that runs the build: Backlog → Today (WIP 3, clock) → Done → Release, with goals above (G1 EA 30.10 · G2 RD 30.12 · G3 2027), a per-card **Analysis** (challenge → solutions → decision → lesson → next activity + impact + path) and the **Roadmap** tab the seeds build. Every card carries `media` (its iCloud folder, `AR-Mini-Media/01_Loops/C###_date_name`) and `files` (paths in this repo: drawings, PDFs, CAD, PCB, data), so the portfolio can quote data, not only photos.

The live copy is a Claude artifact (the page runs on `window.claude` capabilities `db`, `user`, `downloads`); its database holds the collections `cards`, `releases`, `goals`, `analyses`. This file is the page as published; it does nothing useful opened from disk.

- `data/board/board.json` — the export (Releases → Export JSON, or written from the chat) committed at every release; `tools/video/` reads it.
- `history/2026-10-09_ar-mini-loop_v1.html` — the first version (loops, no goals, no analyses).
- `tests/test_page.py` — Playwright smoke test with a stub database (`pip install playwright && playwright install chromium`).
- Rules of the board: `docs/process/GOALS_AND_ROADMAP.md`.
