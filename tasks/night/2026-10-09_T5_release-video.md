# T5 · Release video agent (picks the 2–3 best moments of a release, cuts a 30–45 s clip, publishes it as a GitHub Release)

**Branch:** `night/release-video` → PR to `dev`
**Budget:** ~3 h agent time, or 3 failed attempts at one step.
**Runs on:** Teddy's Mac (the media lives in iCloud Drive there), never in GitHub Actions.

## Goal
`python tools/video/make.py r2a` reads the cards of release `r2a` (text + outcome) and their photos and videos from iCloud, scores every item, keeps the 2–3 that best show *what was tested and what happened*, cuts them into one short clip with title, captions and an end card, writes a shot list that says why each item was chosen, and attaches the clip to a **draft GitHub Release** on tag `r2a`. Teddy reads the shot list, swaps a clip with one flag if she disagrees, and presses Publish on GitHub. The video never enters git history.

The selection step is the only place a vision model is used, and it is optional (`--no-llm` picks by rules). Cutting, captions and publishing are deterministic ffmpeg + `gh`.

## Context
Read: `.cursor/rules/ar-mini.mdc`, `tasks/night/README.md`, `media/LINKS.md`, `tasks/night/2026-10-09_T4_parts-agent.md` (same style: pure functions, tests without network).

Facts with source:
- Cards come from `data/board/board.json`, exported from the AR-Mini Board (Releases tab → **Export JSON**). Shape: `{exported, prefix:"C", releases:[{id,name,goal,date,cut}], cards:[{label:"C006", seq, title, hyp, note, col, outcome:"pass|partial|fail", result, photo, rel, start, end, ...}]}`. A release's cards are the ones with `card.rel == release.name`. If the file is older than 24 h, warn and continue.
- Media per card lives in iCloud Drive: `~/Library/Mobile Documents/com~apple~CloudDocs/AR-Mini-Media/01_Loops/<label>_<date>_<name>/` (folder starts with the card label, e.g. `C006_`). Files are `.HEIC/.JPG/.PNG/.MOV/.MP4`. Path is config (`MEDIA_ROOT` env or `--media`), default as above. A cloud-only file (not downloaded) is skipped with a warning naming it; do not force downloads.
- HEIC → JPG with macOS `sips -s format jpeg` (always present on a Mac); MOV → H.264 MP4 with ffmpeg. Converted copies go to `build/video/cache/` (gitignored).
- Captions use **only** card fields: label, title, outcome, and `result` trimmed to 60 chars. No invented words. Outcome is shown as on the card; a Fail card is as eligible as a Pass card.
- Output size for the portfolio: 1920×1080, 30 fps, H.264, AAC silent track, ≤ 45 s. Optional `--vertical` 1080×1920. No music (copyright).
- Publishing: `gh release create <rel> build/video/<rel>.mp4 --draft --title "<rel> · <goal>" --notes-file build/video/<rel>_shotlist.md`. Requires `gh auth status` OK; if not, print the exact command and stop with exit 3. Tag = release name, created on the current `main` HEAD; if the tag exists, `gh release upload --clobber` instead.
- Vision model: Gemini API (`GEMINI_API_KEY` env; free key from Google AI Studio). It takes photos inline and videos through the File API. Known: free-tier inputs may be used by Google to improve its models → the README must say so and tell Teddy to keep family faces out of the loop folders or use `--no-llm`. No other provider in this task.
- `build/` and all photo/video extensions are already in `.gitignore` → nothing here can land in git by accident; add a test that proves it (`git check-ignore build/video/x.mp4`).

Known unknowns (do not guess): Gemini's current model name and File API limits → read the official docs during the task, put the model name in one config constant with `// SOURCE: <url>`; if video upload fails, fall back to sampling 6 frames per video with ffmpeg and sending them as photos.

## Files to create / change
```
tools/video/make.py                      CLI: <release> | --cards C004,C006 | --no-llm | --vertical | --swap C006=IMG_1234.MOV | --publish | --media PATH
tools/video/collect.py                   board.json loader; media discovery per card; HEIC/MOV conversion into cache; ffprobe duration
tools/video/judge.py                     score items; LLM path (Gemini) and rules path; returns the same Pick schema either way
tools/video/cut.py                       pure planning: shot list → ffmpeg filtergraph (title card, clips with lower-third captions, stills 3 s, end card); runs ffmpeg
tools/video/publish.py                   gh release draft/upload; prints the command on --dry-run
tools/video/tests/                       pytest, no network, no LLM; fixtures: a tiny board.json, two PNGs, one 6 s clip made with ffmpeg testsrc at test time
tools/video/requirements.txt             google-genai (optional import), pillow; nothing heavier
tools/video/README.md                    5-minute setup (brew install ffmpeg gh; gh auth login; GEMINI_API_KEY), the four commands, the privacy note, how to swap a clip
data/board/README.md                     "Export JSON from the board, save here as board.json, commit"
docs/releases/<rel>.md                   written by make.py --publish: link to the GitHub Release + the shot list (this file IS committed; the video is not)
```

### Pick schema (same from LLM and rules)
`Pick {card_label, file, kind: video|photo, start_s, end_s (video only, 5–10 s), score 0–10, why (≤ 120 chars), caption (built by code from card fields, not by the model)}`

### Scoring rubric (given to the model verbatim; used by the rules path as priority order)
1. Shows the measured result: a ruler, a scale, a meter reading, water level, the robot in water.
2. Shows the robot doing the thing the card tested.
3. Shows a fail honestly (leak, tilt, stall) — these are portfolio gold, never filter them out.
4. Process: hands, tools, printer, bench.
5. Pretty but says nothing → lowest.
Rules path: videos before photos; within a card the latest video; clip = the middle 8 s (or whole if shorter); photos get 3 s. Pick max 1 item per card, 3 items per release, 2 if the release has 2 cards; a release with 1 card gets up to 3 items from it.

### Cut (deterministic)
- Title card 2.5 s: line 1 `AR-Mini · <release name>`, line 2 `<goal>`, line 3 `<cut date or target date>`.
- Each pick: video clip trimmed to `[start_s, end_s]`, scaled and padded to 1920×1080 (no crop), lower-third `<label> · <title> · <Outcome>`; photos 3 s static, same lower-third.
- End card 2.5 s: `next: <goal of the next uncut release>` or `01.11 · MIT Maker Portfolio` if none.
- Font: a system sans (`/System/Library/Fonts/Helvetica.ttc` on macOS, config constant); text drawn with ffmpeg `drawtext`, 48 px title, 36 px captions, dark band behind captions for readability.
- Encoding: `libx264 -crf 20 -preset medium -pix_fmt yuv420p`, silent AAC track so every player opens it. Total length asserted ≤ 45 s.

### `make.py` flow
1. Load board.json → release + its cards; exit 2 with a clear message if the release has no cards or no media at all.
2. Collect media per card, convert into cache, read durations.
3. Judge: `--no-llm` or no `GEMINI_API_KEY` → rules; else model, with the rules result as fallback on any error (say which path ran in the shot list).
4. Apply `--swap`. Write `build/video/<rel>_shotlist.md`: chosen items with score and why, then every rejected item with one line; the table also says which path judged.
5. Cut → `build/video/<rel>.mp4`. Print the path and open the folder (`open build/video` on macOS).
6. `--publish` → draft release + `docs/releases/<rel>.md`; print the GitHub URL. Without `--publish` nothing leaves the Mac.

## Do not touch
`firmware/`, `cad/`, `pcb/`, `tools/parts/`, `scripts/check.sh`, `.github/`, the board artifact. No music, no stock footage, no generated images, no text the cards do not contain. Never upload the manuscript or anything outside `01_Loops/`.

## Tests — minimum
1. Loader: release name → its cards; a card without a folder → warning, not an exception; a stale export → warning.
2. Rules judge: video beats photo; latest video wins; middle-8 s math on a 6 s file gives the whole file; max 1 per card, 3 per release, 2 when 2 cards.
3. LLM response parser: rejects out-of-range `start_s/end_s`, clamps to file duration, rejects unknown file names, falls back to rules on malformed JSON.
4. Caption builder: uses only card fields; ≤ 60 chars; outcome rendered `Pass|Partial|Fail`; a card with no result → label + title only.
5. Cut: from the fixtures (2 PNGs + one 6 s testsrc clip) `make.py --no-llm --cards …` produces an mp4 whose ffprobe duration is title + clips + end ± 0.5 s, 1920×1080, 30 fps.
6. `--swap` replaces exactly one pick and the shot list says so.
7. `git check-ignore` returns ignored for `build/video/x.mp4` and for `*.HEIC` under any path.
8. Publish on `--dry-run` prints the full `gh` command and writes nothing.

## Definition of done
- [ ] `python -m pytest -q tools/video` → all pass, no network, no API key
- [ ] `python tools/video/make.py --cards C001 --no-llm --media tools/video/tests/fixtures/media --board tools/video/tests/fixtures/board.json` produces an mp4 in `build/video/`
- [ ] `bash scripts/check.sh` → `check: OK`
- [ ] README written with the privacy note and the swap flag
- [ ] PR to `dev`, title `tools: release video agent, picks + cuts + draft GitHub Release (T5)`

## PR description must include
- the Gemini model name and docs URL you used, and whether video upload or frame sampling is the path
- the exact first run for Teddy: export board.json → `make.py r1a` → read the shot list → `--publish`
- open questions (font, vertical format, whether Fail clips should get a red lower-third)
