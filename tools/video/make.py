#!/usr/bin/env python3
"""AR-Mini release video: pick the 2–3 best moments of a release, cut a ≤ 45 s clip, draft a GitHub Release.

    python tools/video/make.py r2a                       # rules or Gemini (if GEMINI_API_KEY), cut, open build/video
    python tools/video/make.py r2a --no-llm              # rules only, nothing leaves the Mac
    python tools/video/make.py r2a --swap C006=C006_03.MOV
    python tools/video/make.py r2a --publish             # draft GitHub Release + docs/releases/r2a.md
    python tools/video/make.py --cards C004,C006 --no-llm

Exit codes: 0 ok · 1 error · 2 release has no cards / no media · 3 gh missing or not logged in.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import collect  # noqa: E402
import config  # noqa: E402
import cut  # noqa: E402
import judge  # noqa: E402
import publish  # noqa: E402

EXIT_NO_CARDS = 2


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="make.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("release", nargs="?", help="release id or name from board.json, e.g. r2a")
    ap.add_argument("--cards", help="comma-separated card labels instead of a whole release, e.g. C004,C006")
    ap.add_argument("--no-llm", action="store_true", help="pick by rules only; never call Gemini")
    ap.add_argument("--vertical", action="store_true", help="1080×1920 instead of 1920×1080")
    ap.add_argument("--swap", action="append", default=[], metavar="CARD=FILE",
                    help="replace the pick of CARD with FILE from its folder (repeatable)")
    ap.add_argument("--publish", action="store_true", help="draft GitHub Release + docs/releases/<rel>.md")
    ap.add_argument("--dry-run", action="store_true", help="with --publish: print the gh commands, change nothing")
    ap.add_argument("--media", type=Path, default=config.DEFAULT_MEDIA_ROOT, help="iCloud 01_Loops folder (or MEDIA_ROOT)")
    ap.add_argument("--board", type=Path, default=config.DEFAULT_BOARD, help="board.json export")
    ap.add_argument("--build", type=Path, default=config.BUILD_DIR, help="output folder (default build/video)")
    ap.add_argument("--no-open", action="store_true", help="do not open the output folder in Finder")
    args = ap.parse_args(argv)
    if not args.release and not args.cards:
        ap.error("give a release id (e.g. r2a) or --cards C004,C006")
    return args


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def today() -> str:
    return dt.date.today().isoformat()


def resolve_cards(board: collect.Board, args: argparse.Namespace) -> Tuple[Optional[collect.Release], List[collect.Card], str]:
    """→ (release or None, cards, slug for file names)."""
    release = None
    if args.release:
        release = collect.find_release(board, args.release)
        if release is None:
            names = ", ".join(r.id for r in board.releases)
            raise SystemExit(f"error: release {args.release!r} not in {board.path} (known: {names})")
    if args.cards:
        labels = [l.strip() for l in args.cards.split(",") if l.strip()]
        cards = collect.cards_by_labels(board, labels)
        if release is None:
            rels = {c.rel for c in cards if c.rel}
            if len(rels) == 1:
                release = collect.find_release(board, rels.pop())
        slug = release.id if (release and not args.cards) else "-".join(c.label for c in cards)
    else:
        cards = collect.cards_for_release(board, release)
        slug = release.id
    return release, cards, slug


def title_lines(release: Optional[collect.Release], cards: List[collect.Card]) -> List[str]:
    """Title card (SOURCE: task T5): `AR-Mini · <release>` / `<goal>` / `<cut date or target date>`.
    Without a release: the card label(s), the single card's title, today's date (the cut date)."""
    if release is not None:
        return [f"AR-Mini · {release.name}", release.goal, release.cut or release.date]
    labels = ", ".join(c.label for c in cards)
    second = cards[0].title if len(cards) == 1 else f"{len(cards)} cards"
    return [f"AR-Mini · {labels}", second, today()]


def end_line(board: collect.Board, release: Optional[collect.Release]) -> str:
    nxt = collect.next_uncut_release(board, release, today=today())
    return f"next: {nxt.goal}" if nxt and nxt.goal else config.END_CARD_DEFAULT


def render_shotlist(release: Optional[collect.Release], cards: List[collect.Card], judgement: judge.Judgement,
                    segments: List[cut.Segment], board: collect.Board, warnings: List[str], out_name: str,
                    selector: str = "") -> str:
    """selector: how this cut was asked for (`r2a` or `--cards C004,C006`), echoed in the swap hint."""
    name = release.name if release else ", ".join(c.label for c in cards)
    goal = release.goal if release else ""
    lines = [f"# Shot list · {name}" + (f" · {goal}" if goal else ""), ""]
    lines.append(f"- Judged by: **{judgement.path}**")
    lines.append(f"- Board export: {board.exported or 'unknown'}" + (" ⚠ stale" if any("old" in w for w in board.warnings) else ""))
    lines.append(f"- Output: `{out_name}` · {cut.total_duration(segments):.1f} s "
                 f"(title {config.TITLE_S} + {len(judgement.picks)} items + end {config.END_S})")
    lines += ["", "## Picked", "", "| # | Card | File | Kind | Clip | Score | Why |", "|---|---|---|---|---|---|---|"]
    for k, p in enumerate(judgement.picks, 1):
        clip = f"{p.start_s:.1f}–{p.end_s:.1f} s" if p.kind == "video" else f"{config.STILL_S:.0f} s still"
        lines.append(f"| {k} | {p.card_label} | {p.file} | {p.kind} | {clip} | {p.score:g} | {p.why} |")
    lines += ["", "Captions (card fields only):", ""]
    for p in judgement.picks:
        lines.append(f"- {p.card_label}: " + " / ".join(p.caption.split("\n")))
    if judgement.notes:
        lines += ["", "## Notes", ""] + [f"- {n}" for n in judgement.notes]
    lines += ["", "## Rejected", ""]
    lines += [f"- {r.file} · {r.card_label} · {r.why}" for r in judgement.rejected] or ["- (nothing)"]
    if warnings:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in warnings]
    selector = selector or (release.id if release else "--cards " + ",".join(c.label for c in cards))
    lines += ["", f"To change a pick: `python tools/video/make.py {selector} --swap CARD=FILE` "
              "(FILE from the card's iCloud folder), then `--publish`.", ""]
    return "\n".join(lines)


def open_folder(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    missing = collect.tools_available()
    if missing:
        print(f"error: {', '.join(missing)} not found — brew install ffmpeg", file=sys.stderr)
        return 1

    # 1. board → release + cards
    try:
        board = collect.load_board(args.board)
    except (OSError, ValueError) as exc:
        print(f"error: cannot read {args.board}: {exc}", file=sys.stderr)
        return 1
    warnings: List[str] = list(board.warnings)
    for w in warnings:
        warn(w)
    try:
        release, cards, slug = resolve_cards(board, args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not cards:
        print(f"error: release {args.release!r} has no cards (card.rel must equal the release name "
              f"{release.name if release else ''!r}); nothing to cut", file=sys.stderr)
        return EXIT_NO_CARDS

    # 2. media → cache
    build = Path(args.build)
    cache = build / "cache"
    media = collect.collect(cards, args.media, warnings)
    if not any(media.values()):
        for w in warnings[len(board.warnings):]:
            warn(w)
        print(f"error: no photos or videos for {', '.join(c.label for c in cards)} under {args.media}", file=sys.stderr)
        return EXIT_NO_CARDS
    media = collect.prepare_all(media, cache, warnings)
    for w in warnings[len(board.warnings):]:
        warn(w)
    if not any(media.values()):
        print("error: every media file failed to convert; see warnings", file=sys.stderr)
        return EXIT_NO_CARDS

    # 3. judge
    if args.no_llm:
        judgement = judge.rules_pick(cards, media)
        judgement.path = "rules (--no-llm)"
    else:
        judgement = judge.gemini_pick(release, cards, media)

    # 4. swap + shot list
    for swap in args.swap:
        try:
            judgement = judge.apply_swap(judgement, swap, cards, media)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    files: Dict[Tuple[str, str], Path] = {(i.card_label, i.file): i.cached for items in media.values() for i in items if i.cached}
    size = (config.VERTICAL_WIDTH, config.VERTICAL_HEIGHT) if args.vertical else (config.WIDTH, config.HEIGHT)
    suffix = "_vertical" if args.vertical else ""
    out_mp4 = build / f"{slug}{suffix}.mp4"
    shotlist_path = build / f"{slug}_shotlist.md"
    segments = cut.plan(title_lines(release, cards), judgement.picks, files, end_line(board, release))
    try:
        cut.check_length(segments)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    selector = f"--cards {args.cards}" if args.cards else release.id
    shotlist = render_shotlist(release, cards, judgement, segments, board, warnings, out_mp4.name, selector)
    build.mkdir(parents=True, exist_ok=True)
    shotlist_path.write_text(shotlist, encoding="utf-8")

    # 5. cut
    try:
        cut.run(segments, out_mp4, cache / "text", size=size)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"shot list: {shotlist_path}")
    print(f"video:     {out_mp4}  ({cut.total_duration(segments):.1f} s, {size[0]}×{size[1]}, judged by {judgement.path})")
    if not args.no_open:
        open_folder(build)

    # 6. publish
    if args.publish:
        if release is None:
            print("error: --publish needs a release id (the GitHub tag); --cards alone cannot be published", file=sys.stderr)
            return 1
        title = f"{release.name} · {release.goal}".rstrip(" ·")
        code, text, url = publish.publish(release.id, out_mp4, shotlist_path, title, dry_run=args.dry_run)
        print(text)
        if code != 0:
            return code
        if not args.dry_run:
            doc = publish.release_doc(release.name, release.goal, release.id, url, shotlist, out_mp4.name)
            path = publish.write_release_doc(config.RELEASES_DOC_DIR / f"{release.id}.md", doc)
            print(f"release note: {path}  (commit this; the video stays out of git)")
            if url:
                print(url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
