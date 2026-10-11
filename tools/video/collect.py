"""board.json loader, media discovery per card, HEIC/MOV conversion into the cache, ffprobe.

No network. Everything that talks to the file system or ffmpeg lives here so judge.py and
cut.py (planning) stay pure.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import config

# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------


@dataclass
class Release:
    id: str
    name: str
    goal: str
    date: str          # ISO date, target
    cut: Optional[str]  # ISO date when cut, else None


@dataclass
class Card:
    label: str
    title: str = ""
    hyp: str = ""
    note: str = ""
    outcome: Optional[str] = None  # pass | partial | fail | None
    result: str = ""
    rel: str = ""
    photo: str = ""
    col: str = ""
    seq: int = 0


@dataclass
class Board:
    exported: str
    releases: List[Release]
    cards: List[Card]
    warnings: List[str] = field(default_factory=list)
    path: Optional[Path] = None


def _iso_date(value) -> Optional[str]:
    """Board dates: ISO strings or epoch milliseconds (like `created`)."""
    if value in (None, "", 0):
        return None
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value / 1000, dt.timezone.utc).date().isoformat()
    return str(value)[:10]


def load_board(path: Path, now: Optional[dt.datetime] = None) -> Board:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    releases = [
        Release(
            id=str(r.get("id", "")),
            name=str(r.get("name", "")),
            goal=str(r.get("goal", "") or ""),
            date=_iso_date(r.get("date")) or "",
            cut=_iso_date(r.get("cut")),
        )
        for r in data.get("releases", [])
    ]
    cards = [
        Card(
            label=str(c.get("label", "")),
            title=str(c.get("title", "") or ""),
            hyp=str(c.get("hyp", "") or ""),
            note=str(c.get("note", "") or ""),
            outcome=(c.get("outcome") or None),
            result=str(c.get("result", "") or ""),
            rel=str(c.get("rel", "") or ""),
            photo=str(c.get("photo", "") or ""),
            col=str(c.get("col", "") or ""),
            seq=int(c.get("seq", 0) or 0),
        )
        for c in data.get("cards", [])
    ]
    board = Board(exported=str(data.get("exported", "")), releases=releases, cards=cards, path=Path(path))
    age_h = export_age_hours(board.exported, now)
    if age_h is None:
        board.warnings.append(f"board.json has no readable 'exported' timestamp ({board.exported!r})")
    elif age_h > config.STALE_HOURS:
        board.warnings.append(
            f"board.json is {age_h:.0f} h old (exported {board.exported}); re-export from the AR-Mini Board"
        )
    return board


def export_age_hours(exported: str, now: Optional[dt.datetime] = None) -> Optional[float]:
    try:
        ts = dt.datetime.fromisoformat(exported.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt.timezone.utc)
    now = now or dt.datetime.now(dt.timezone.utc)
    return (now - ts).total_seconds() / 3600


def find_release(board: Board, key: str) -> Optional[Release]:
    """`r2a` or `R2a` → the release (id or name, case-insensitive)."""
    k = key.strip().lower()
    for r in board.releases:
        if r.id.lower() == k or r.name.lower() == k:
            return r
    return None


def cards_for_release(board: Board, release: Release) -> List[Card]:
    """A release's cards are the ones with card.rel == release.name (SOURCE: task T5); id accepted too."""
    names = {release.name.lower(), release.id.lower()} - {""}
    cards = [c for c in board.cards if c.rel.strip().lower() in names]
    return sorted(cards, key=lambda c: c.seq)


def cards_by_labels(board: Board, labels: List[str]) -> List[Card]:
    by_label = {c.label.upper(): c for c in board.cards}
    missing = [l for l in labels if l.upper() not in by_label]
    if missing:
        raise ValueError(f"unknown card label(s): {', '.join(missing)}")
    return [by_label[l.upper()] for l in labels]


def next_uncut_release(board: Board, current: Optional[Release], today: Optional[str] = None) -> Optional[Release]:
    """The next release that is not cut yet, after `current` (by date). None → end card default."""
    uncut = sorted((r for r in board.releases if r.cut is None and r.date), key=lambda r: r.date)
    if current is not None:
        uncut = [r for r in uncut if r.id != current.id and r.date >= current.date]
    elif today:
        uncut = [r for r in uncut if r.date >= today]
    return uncut[0] if uncut else None


# ---------------------------------------------------------------------------
# Media discovery
# ---------------------------------------------------------------------------


@dataclass
class MediaItem:
    card_label: str
    file: str                  # original file name, e.g. C006_02.MOV — the id used in picks and --swap
    path: Path                 # original path in the media root
    kind: str                  # "video" | "photo"
    mtime: float
    size: int
    duration_s: Optional[float] = None  # videos, after prepare()
    cached: Optional[Path] = None       # converted copy in the cache, after prepare()
    starred: bool = False               # ★ in captions.md = Teddy's portfolio pick
    what: str = ""                      # captions.md "What it shows"
    reading: str = ""                   # captions.md "Reading"


@dataclass
class CaptionRow:
    name: str          # file stem or name as written, without the ★
    what: str
    reading: str
    starred: bool


CAPTIONS_FILE = "captions.md"  # SOURCE: media/LINKS.md — one per card folder
STAR = "★"


def parse_captions(text: str) -> Dict[str, CaptionRow]:
    """Markdown table rows `| ★ C001_07 | what | reading |` → stem (lower) → row.
    The first cell is the file (stem or full name); a leading ★ marks Teddy's portfolio pick.
    Header and separator rows are skipped; anything that is not a table row is ignored."""
    rows: Dict[str, CaptionRow] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells or not cells[0]:
            continue
        first = cells[0]
        if set(first) <= set("-: ") or first.lower() == "file":
            continue
        starred = first.startswith(STAR)
        name = first[len(STAR):].strip() if starred else first
        name = name.strip("`* ")
        if not name:
            continue
        rows[caption_key(name)] = CaptionRow(name=name, what=cells[1] if len(cells) > 1 else "",
                                             reading=cells[2] if len(cells) > 2 else "", starred=starred)
    return rows


def caption_key(name: str) -> str:
    """`C001_07`, `C001_07.HEIC` and `c001_07.heic` all mean the same file."""
    return Path(name).stem.lower()


def read_captions(folder: Path) -> Dict[str, CaptionRow]:
    path = Path(folder) / CAPTIONS_FILE
    if not path.is_file():
        return {}
    try:
        return parse_captions(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


def apply_captions(items: List[MediaItem], rows: Dict[str, CaptionRow]) -> None:
    for item in items:
        row = rows.get(caption_key(item.file))
        if row is None:
            continue
        item.starred = row.starred
        item.what = row.what
        item.reading = row.reading


def kind_of(path: Path) -> Optional[str]:
    ext = path.suffix.lower()
    if ext in config.VIDEO_EXT:
        return "video"
    if ext in config.PHOTO_EXT:
        return "photo"
    return None


def find_card_folder(root: Path, label: str) -> Optional[Path]:
    """Folder whose name starts with `<label>_` (or equals the label)."""
    root = Path(root)
    if not root.is_dir():
        return None
    prefix = f"{label}_".lower()
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and (entry.name.lower().startswith(prefix) or entry.name.lower() == label.lower()):
            return entry
    return None


def is_cloud_only(path: Path) -> bool:
    """iCloud Drive keeps a `.<name>.icloud` placeholder for files that are not downloaded.
    Evicted files can also show their size with zero blocks on disk."""
    if (path.parent / f".{path.name}.icloud").exists():
        return True
    try:
        st = path.stat()
    except OSError:
        return True
    blocks = getattr(st, "st_blocks", None)
    return bool(st.st_size > 0 and blocks == 0)


def list_media(folder: Path, label: str, warnings: List[str]) -> List[MediaItem]:
    items: List[MediaItem] = []
    for entry in sorted(Path(folder).iterdir()):
        if entry.name.startswith("."):
            if entry.suffix == ".icloud":
                warnings.append(f"{label}: {entry.name[1:-7]} is in iCloud only (not downloaded) — skipped")
            continue
        kind = kind_of(entry)
        if kind is None or not entry.is_file():
            continue
        if is_cloud_only(entry):
            warnings.append(f"{label}: {entry.name} is in iCloud only (not downloaded) — skipped")
            continue
        st = entry.stat()
        items.append(MediaItem(card_label=label, file=entry.name, path=entry, kind=kind,
                               mtime=st.st_mtime, size=st.st_size))
    apply_captions(items, read_captions(folder))
    return items


def collect(cards: List[Card], root: Path, warnings: List[str]) -> Dict[str, List[MediaItem]]:
    """label → media items. A card without a folder → warning, empty list."""
    out: Dict[str, List[MediaItem]] = {}
    for card in cards:
        folder = find_card_folder(root, card.label)
        if folder is None:
            warnings.append(f"{card.label}: no folder {card.label}_* under {root}")
            out[card.label] = []
            continue
        items = list_media(folder, card.label, warnings)
        if not items:
            warnings.append(f"{card.label}: folder {folder.name} has no photos or videos")
        out[card.label] = items
    return out


# ---------------------------------------------------------------------------
# Conversion into the cache
# ---------------------------------------------------------------------------


def _run(cmd: List[str], what: str) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{what} failed ({proc.returncode}): {proc.stderr.strip()[-800:]}")
    return proc


def cache_name(item: MediaItem, ext: str) -> str:
    return f"{item.card_label}_{item.path.stem}_{item.size}_{int(item.mtime)}{ext}"


def convert_photo(src: Path, dst: Path) -> None:
    """HEIC → JPG with macOS sips, then Pillow applies the EXIF orientation and downsizes.
    Other formats go through Pillow directly. Without Pillow the file is copied as is."""
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    work = src
    if src.suffix.lower() == ".heic":
        if sys.platform != "darwin" or shutil.which("sips") is None:
            raise RuntimeError(f"{src.name}: HEIC conversion needs macOS sips")
        tmp = dst.with_suffix(".sips.jpg")
        _run(["sips", "-s", "format", "jpeg", str(src), "--out", str(tmp)], "sips")
        work = tmp
    try:
        from PIL import Image, ImageOps  # type: ignore
    except ImportError:
        shutil.copyfile(work, dst)
        if work != src:
            work.unlink(missing_ok=True)
        return
    with Image.open(work) as im:
        im = ImageOps.exif_transpose(im)
        im = im.convert("RGB")
        im.thumbnail((config.CACHE_MAX_SIDE, config.CACHE_MAX_SIDE))  # no upscaling
        im.save(dst, "JPEG", quality=92)
    if work != src:
        work.unlink(missing_ok=True)


def convert_video(src: Path, dst: Path) -> None:
    """MOV/MP4 → H.264 MP4 (no audio), long side ≤ CACHE_MAX_SIDE. ffmpeg applies the rotation tag."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    side = config.CACHE_MAX_SIDE
    vf = f"scale='min({side},iw)':'min({side},ih)':force_original_aspect_ratio=decrease:force_divisible_by=2"
    _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-vf", vf,
          *config.CACHE_X264_ARGS, "-an", "-movflags", "+faststart", str(dst)], "ffmpeg")


def probe_duration(path: Path) -> float:
    proc = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(path)], "ffprobe")
    return float(proc.stdout.strip())


def probe_video(path: Path) -> dict:
    """{'width', 'height', 'fps', 'duration'} of the first video stream (tests use this)."""
    proc = _run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                 "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)], "ffprobe")
    data = json.loads(proc.stdout)
    stream = data["streams"][0]
    num, den = stream["r_frame_rate"].split("/")
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "fps": float(num) / float(den),
        "duration": float(data["format"]["duration"]),
    }


def prepare(item: MediaItem, cache_dir: Path, warnings: List[str]) -> Optional[MediaItem]:
    """Convert into the cache and read the duration. Returns None (with a warning) if conversion fails."""
    cache_dir = Path(cache_dir)
    try:
        if item.kind == "photo":
            dst = cache_dir / cache_name(item, ".jpg")
            if not dst.exists():
                convert_photo(item.path, dst)
        else:
            dst = cache_dir / cache_name(item, ".mp4")
            if not dst.exists():
                convert_video(item.path, dst)
            item.duration_s = probe_duration(dst)
    except Exception as exc:  # noqa: BLE001 — one bad file must not stop the release
        warnings.append(f"{item.card_label}: {item.file} skipped — {exc}")
        return None
    item.cached = dst
    return item


def prepare_all(media: Dict[str, List[MediaItem]], cache_dir: Path, warnings: List[str]) -> Dict[str, List[MediaItem]]:
    out: Dict[str, List[MediaItem]] = {}
    for label, items in media.items():
        ready = [p for p in (prepare(i, cache_dir, warnings) for i in items) if p is not None]
        out[label] = ready
    return out


def tools_available() -> List[str]:
    """Names of the required command-line tools that are missing."""
    return [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
