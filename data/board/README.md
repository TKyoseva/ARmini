# data/board

`board.json` — export of the AR-Mini Board (Releases tab → **Export JSON**). Cards, releases, outcomes, iCloud links. Save it here as `board.json` and commit it before cutting a release video (`python tools/video/make.py <rel>`; the tool warns when the export is older than 24 h) or when the workshop chat asks for it.

The board itself is the live truth; this file is a snapshot with an `exported` timestamp. A release's cards are the ones whose `rel` equals the release `name` (e.g. `R2a`).
