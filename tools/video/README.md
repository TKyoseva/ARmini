# tools/video · release video agent

Picks the 2–3 moments of a release that best show *what was tested and what happened*, cuts them into
one 30–45 s clip (title card, lower-third captions from the cards, end card) and attaches it to a **draft**
GitHub Release. Teddy reads the shot list, swaps a clip if she disagrees, and presses **Publish** on GitHub.
The video never enters git (`build/` and `*.mp4` are ignored); only `docs/releases/<rel>.md` is committed.

Runs on Teddy's Mac only — the photos and videos live in iCloud Drive
(`~/Library/Mobile Documents/com~apple~CloudDocs/AR-Mini-Media/01_Loops/C###_date_name/`, see `media/LINKS.md`).

## 5-minute setup

```bash
brew install ffmpeg gh          # cutting + GitHub Releases
gh auth login                   # once; pick GitHub.com → HTTPS → browser
python3 -m pip install -r tools/video/requirements.txt   # pillow (+ google-genai, optional)
export GEMINI_API_KEY=...       # optional, see "Privacy" below; without it the rules path is used
```

`sips` (HEIC → JPG) is part of macOS. Python 3.9+ is enough.

## The four commands

```bash
# 0. fresh board export: AR-Mini Board → Releases tab → Export JSON → save as data/board/board.json, commit

# 1. cut (rules or Gemini, depending on GEMINI_API_KEY); opens build/video in Finder
python tools/video/make.py r2a

# 2. read build/video/r2a_shotlist.md; disagree? swap one pick (FILE = a file in that card's iCloud folder)
python tools/video/make.py r2a --swap C006=C006_03.MOV

# 3. publish: draft GitHub Release on tag r2a + docs/releases/r2a.md (commit that file)
python tools/video/make.py r2a --publish

# 4. first time, or no network: rules only, nothing leaves the Mac
python tools/video/make.py r2a --no-llm
```

Other flags: `--cards C004,C006` (any cards instead of a whole release), `--vertical` (1080×1920),
`--dry-run` (with `--publish`: print the `gh` commands, change nothing), `--media PATH` (or `MEDIA_ROOT` env),
`--board PATH`, `--build PATH`, `--no-open`.

Exit codes: `0` ok · `1` error · `2` the release has no cards or no media at all · `3` `gh` missing or not
logged in (the exact `gh release create …` command is printed so you can run it by hand).

## What it does

1. **Collect** (`collect.py`): loads `data/board/board.json` (warns if the export is older than 24 h), takes
   the cards with `card.rel == release.name`, finds each card's folder (`C006_*`) in iCloud, converts
   HEIC → JPG (`sips`, then Pillow fixes the orientation) and MOV → H.264 MP4 (ffmpeg) into
   `build/video/cache/`. A file that is in iCloud but not downloaded is skipped with a warning that names it;
   nothing is force-downloaded.
2. **Judge** (`judge.py`): scores every item and keeps max 1 per card, 3 per release (2 if the release has
   2 cards; a single card may give up to 3). Two paths, same output:
   - **rules** (`--no-llm`, or no `GEMINI_API_KEY`, or any Gemini error): videos before photos, the latest
     video of each card, clip = the middle 8 s (whole file if shorter), photos 3 s.
   - **Gemini** (`gemini-3.8-flash`, config constant with its source URL): gets the cards, the rubric below
     and the media (photos inline, videos through the File API; if an upload fails, 6 frames of that video are
     sent as photos instead). Its JSON is validated against the real file names and durations; anything
     malformed falls back to rules. The shot list always says which path ran.
3. **Cut** (`cut.py`): title card 2.5 s (`AR-Mini · <release>` / goal / cut-or-target date), each pick scaled
   and padded to 1920×1080 (no crop) with a lower-third `<label> · <title> · <Outcome>` and the card's
   `result` trimmed to 60 chars, end card 2.5 s (`next: <goal of the next uncut release>` or
   `01.11 · MIT Maker Portfolio`). libx264 crf 20, 30 fps, silent AAC track. Total length asserted ≤ 45 s.
4. **Publish** (`publish.py`): `gh release create <rel> build/video/<rel>.mp4 --draft --target main
   --title "<Name> · <goal>" --notes-file build/video/<rel>_shotlist.md`; if the tag exists:
   `gh release upload --clobber` + `gh release edit --notes-file`. Writes `docs/releases/<rel>.md`.

Captions use **only** card fields (label, title, outcome, result). No music, no stock footage, no generated
images. A Fail card is as eligible as a Pass card.

### Scoring rubric (given to the model verbatim; priority order for the rules path)

1. Shows the measured result: a ruler, a scale, a meter reading, water level, the robot in water.
2. Shows the robot doing the thing the card tested.
3. Shows a fail honestly (leak, tilt, stall) — these are portfolio gold, never filter them out.
4. Process: hands, tools, printer, bench.
5. Pretty but says nothing → lowest.

## Swapping a clip

The shot list lists every picked and every rejected file with one line of why. To replace a pick:

```bash
python tools/video/make.py r2a --swap C006=C006_03.MOV
```

`C006` must be a card of the cut and `C006_03.MOV` a file in its iCloud folder. Exactly one pick changes
(the pick of that card; if the card had no pick, the lowest-scoring one). The new pick gets the middle 8 s
and the shot list says `Swapped: …`. `--swap` can be repeated. Then run `--publish` again (the existing
draft is updated with `--clobber`).

## Privacy — read before setting GEMINI_API_KEY

The selection step is the only place a vision model sees the photos and videos. Google's Gemini API terms
(https://ai.google.dev/gemini-api/terms, "Unpaid Services") say that for the **free tier** Google may use
the submitted content and the responses to improve its products and models, and that human reviewers may
read them. The same page says that for users in the EEA the paid-service data terms apply even on the free
quota — do not rely on that. Rules for this repo:

- Keep **family faces and anything personal out of the `01_Loops/` folders** (that is also the rule for the
  portfolio). Media is taken only from `01_Loops/<card folder>/`; never from `00_Inbox` or anything else.
- When in doubt, use `--no-llm`. The rules path never sends anything anywhere; without `--publish`
  nothing leaves the Mac at all.
- Uploaded files are deleted by Google after 48 h (Files API docs). The tool does not store anything
  outside `build/video/`.

## Tests

```bash
python -m pytest -q tools/video      # no network, no API key; the 6 s test clip is made with ffmpeg testsrc
```

Fixtures: `tests/fixtures/board.json` (the export shape) and two PNGs under `tests/fixtures/media/`.
The Gemini path is covered by its parser tests and a fake `google.genai` that fails (→ rules fallback).

## Files

```
make.py      CLI and the flow above; writes build/video/<rel>.mp4 and <rel>_shotlist.md
collect.py   board.json loader, media discovery, HEIC/MOV conversion, ffprobe
judge.py     captions, rules path, --swap, Gemini path + strict parser (Pick schema)
cut.py       pure plan + ffmpeg filtergraph, runs ffmpeg once
publish.py   gh release draft / upload, --dry-run, docs/releases/<rel>.md
config.py    every constant with SOURCE:/VERIFY: (sizes, fonts, model name, limits)
```
