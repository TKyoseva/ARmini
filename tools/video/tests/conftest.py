"""Shared fixtures. No network, no API key. The 6 s clip is made with ffmpeg testsrc at test time
(mp4 is gitignored); the two PNGs are committed under fixtures/media."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TOOL_DIR = HERE.parent
sys.path.insert(0, str(TOOL_DIR))

import collect  # noqa: E402

FIXTURES = HERE / "fixtures"
BOARD = FIXTURES / "board.json"
PNG_DIR = FIXTURES / "media" / "C001_2026-10-08_thruster-measure"

HAVE_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
needs_ffmpeg = pytest.mark.skipif(not HAVE_FFMPEG, reason="ffmpeg/ffprobe not installed")


def make_clip(path: Path, seconds: float, size: str = "640x360") -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                    "-i", f"testsrc=size={size}:rate=30", "-t", str(seconds),
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(path)], check=True)


@pytest.fixture(scope="session")
def media_root(tmp_path_factory) -> Path:
    """C001: 2 PNGs · C002: 2 clips (6 s latest, 3 s older) + 1 newer PNG · C004: 1 PNG · C003: no folder.
    No captions.md anywhere: the ★ tests build their own folder (test_collect) or set `starred` (test_judge)."""
    root = tmp_path_factory.mktemp("media")
    shutil.copytree(PNG_DIR, root / PNG_DIR.name)
    c002 = root / "C002_2026-10-08_thruster-wires"
    c002.mkdir()
    now = time.time()
    if HAVE_FFMPEG:
        make_clip(c002 / "C002_01.mp4", 3.0)
        make_clip(c002 / "C002_02.mp4", 6.0)
    else:  # placeholders so the discovery tests still run
        (c002 / "C002_01.mp4").write_bytes(b"x")
        (c002 / "C002_02.mp4").write_bytes(b"x")
    shutil.copy(PNG_DIR / "C001_01.PNG", c002 / "C002_03.PNG")
    os.utime(c002 / "C002_01.mp4", (now - 300, now - 300))
    os.utime(c002 / "C002_02.mp4", (now - 200, now - 200))
    os.utime(c002 / "C002_03.PNG", (now - 100, now - 100))   # newest file, but a photo
    c004 = root / "C004_2026-10-09_rob0154-plate"
    c004.mkdir()
    shutil.copy(PNG_DIR / "C001_02.PNG", c004 / "C004_01.PNG")
    return root


@pytest.fixture
def board() -> collect.Board:
    return collect.load_board(BOARD)


@pytest.fixture
def cards_r1a(board):
    return collect.cards_for_release(board, collect.find_release(board, "r1a"))


@pytest.fixture
def media_r1a(board, cards_r1a, media_root, tmp_path):
    """Discovered + converted media for R1a (C001, C002; C003 has no folder)."""
    warnings: list = []
    media = collect.collect(cards_r1a, media_root, warnings)
    if HAVE_FFMPEG:
        media = collect.prepare_all(media, tmp_path / "cache", warnings)
    else:
        for items in media.values():
            for i in items:
                i.cached = i.path
                if i.kind == "video":
                    i.duration_s = 6.0 if i.file.endswith("02.mp4") else 3.0
    return media
