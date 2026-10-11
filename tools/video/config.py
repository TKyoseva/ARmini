"""Constants for the release video agent (tools/video).

Every number that comes from outside this code carries a SOURCE: or VERIFY: comment.
Paths can be overridden on the command line (`--board`, `--media`, `--build`) or by env.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# --- inputs -----------------------------------------------------------------
DEFAULT_BOARD = REPO_ROOT / "data" / "board" / "board.json"  # SOURCE: data/board/README.md
# SOURCE: media/LINKS.md — photos and videos live in iCloud Drive, folder per card.
DEFAULT_MEDIA_ROOT = Path(
    os.environ.get(
        "MEDIA_ROOT",
        str(Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
            / "AR-Mini-Media" / "01_Loops"),
    )
)
STALE_HOURS = 24  # SOURCE: task T5 — warn (and continue) if the export is older
PHOTO_EXT = {".heic", ".jpg", ".jpeg", ".png"}
VIDEO_EXT = {".mov", ".mp4"}

# --- outputs ----------------------------------------------------------------
BUILD_DIR = REPO_ROOT / "build" / "video"  # gitignored (build/)
RELEASES_DOC_DIR = REPO_ROOT / "docs" / "releases"  # written by --publish, committed

# --- video format (SOURCE: task T5 "Output size for the portfolio") ---------
WIDTH, HEIGHT = 1920, 1080
VERTICAL_WIDTH, VERTICAL_HEIGHT = 1080, 1920
FPS = 30
MAX_TOTAL_S = 45.0
TITLE_S = 2.5
END_S = 2.5
STILL_S = 3.0
CLIP_S = 8.0           # rules path: the middle 8 s of a video
CLIP_MIN_S = 5.0       # LLM picks: clip length allowed 5–10 s
CLIP_MAX_S = 10.0
MAX_PICKS = 3          # per release; 2 if the release has 2 cards
RESULT_MAX_CHARS = 60  # caption line 2: card.result trimmed
WHY_MAX_CHARS = 120    # Pick.why
CACHE_MAX_SIDE = 1920  # converted copies are downscaled to this long side (no upscaling)

# --- text -------------------------------------------------------------------
# SOURCE: task T5 — Helvetica for the title and end cards.
FONT = "/System/Library/Fonts/Helvetica.ttc"
# VERIFY (Teddy, open question in the PR): Helvetica.ttc has no glyphs for the arrows used in card
# results (→ ↔ render as boxes; checked with ffmpeg drawtext on 2026-10-09). The lower-thirds
# therefore use Arial Unicode when it exists and fall back to FONT otherwise.
CAPTION_FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
FONT_FALLBACKS = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",   # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",        # Debian/Ubuntu (CI)
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]
TITLE_PX = 48
CAPTION_PX = 36
CAPTION2_PX = 30
BAND_ALPHA = 0.6
BACKGROUND = "0x101418"
END_CARD_DEFAULT = "01.11 · MIT Maker Portfolio"  # SOURCE: task T5

# --- encoding (SOURCE: task T5) ---------------------------------------------
X264_ARGS = ["-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p"]
AAC_ARGS = ["-c:a", "aac", "-b:a", "64k"]
CACHE_X264_ARGS = ["-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p"]

# --- Gemini (optional; only in judge.py when GEMINI_API_KEY is set) ---------
# SOURCE: https://ai.google.dev/gemini-api/docs/models (stable Flash model, page dated 2026-10-06)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
# SOURCE: https://ai.google.dev/gemini-api/docs/files — per-file max 2 GB, 20 GB/project, kept 48 h
GEMINI_FILE_MAX_BYTES = 2 * 1024 ** 3
# SOURCE: https://ai.google.dev/gemini-api/docs/video-understanding — inline data for requests < 20 MB
GEMINI_INLINE_MAX_BYTES = 20 * 1024 ** 2
GEMINI_POLL_S = 5                 # SOURCE: docs sample polls files.get every 5 s
GEMINI_UPLOAD_TIMEOUT_S = 180     # VERIFY: our choice, long enough for a 1-min 1080p clip
FRAME_SAMPLES = 6                 # SOURCE: task T5 — fallback: 6 frames per video as photos
FRAME_MAX_SIDE = 1024             # VERIFY: our choice, keeps the request small


def font_path() -> str:
    """Title/end cards: FONT, else the first existing fallback (FONT if none exists; ffmpeg will say so)."""
    for candidate in [FONT, *FONT_FALLBACKS]:
        if Path(candidate).exists():
            return candidate
    return FONT


def caption_font_path() -> str:
    """Lower-thirds: CAPTION_FONT if it exists, else the same font as the cards."""
    return CAPTION_FONT if Path(CAPTION_FONT).exists() else font_path()
