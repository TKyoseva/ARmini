"""Test 7: nothing from build/ or the phone's media formats can land in git by accident."""
from __future__ import annotations

import shutil
import subprocess

import pytest

import config

needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def _ignored(path: str) -> bool:
    proc = subprocess.run(["git", "check-ignore", "-q", path], cwd=config.REPO_ROOT)
    return proc.returncode == 0


@needs_git
@pytest.mark.parametrize("path", [
    "build/video/x.mp4",
    "build/video/cache/C006_C006_02_1_1.jpg",
    "tools/video/tests/fixtures/media/C006_2026-10-12_esc/C006_01.HEIC",
    "some/deep/path/IMG_1234.HEIC",
    "docs/anything.MOV",
    "tools/video/clip.mp4",
])
def test_media_and_build_are_ignored(path):
    assert _ignored(path), f"{path} is not ignored by .gitignore"


@needs_git
def test_fixture_pngs_and_sources_are_not_ignored():
    assert not _ignored("tools/video/tests/fixtures/media/C001_2026-10-08_thruster-measure/C001_01.PNG")
    assert not _ignored("tools/video/make.py")
    assert not _ignored("docs/releases/r2a.md")
