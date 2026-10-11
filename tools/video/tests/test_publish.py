"""Test 8: publish on --dry-run prints the full gh command and writes nothing."""
from __future__ import annotations

from pathlib import Path

import config
import make
import publish
from conftest import BOARD, needs_ffmpeg


def test_dry_run_prints_command_and_writes_nothing(tmp_path):
    mp4, notes = tmp_path / "r2a.mp4", tmp_path / "r2a_shotlist.md"
    code, text, url = publish.publish("r2a", mp4, notes, "R2a · thruster spins in a bucket", dry_run=True)
    assert code == 0 and url is None
    assert "gh release create r2a" in text
    assert str(mp4) in text and "--draft" in text and "--target main" in text
    assert "--notes-file" in text and "'R2a · thruster spins in a bucket'" in text
    assert list(tmp_path.iterdir()) == []                      # nothing written


def test_commands_for_existing_tag_upload_with_clobber(tmp_path):
    cmds = publish.commands("r2a", tmp_path / "v.mp4", tmp_path / "n.md", "t", exists=True)
    assert cmds[0][:4] == ["gh", "release", "upload", "r2a"] and "--clobber" in cmds[0]
    assert cmds[1][:4] == ["gh", "release", "edit", "r2a"]


def test_publish_without_gh_exits_3(monkeypatch, tmp_path):
    monkeypatch.setattr(publish.shutil, "which", lambda name: None)
    code, text, _ = publish.publish("r2a", tmp_path / "v.mp4", tmp_path / "n.md", "t")
    assert code == publish.EXIT_NO_GH == 3
    assert "gh release create r2a" in text and "brew install gh" in text


def test_release_doc_contains_link_and_shotlist():
    doc = publish.release_doc("R2a", "goal", "r2a", "https://github.com/x/y/releases/tag/r2a", "# Shot list\n\n| a |", "r2a.mp4")
    assert doc.startswith("# R2a · goal")
    assert "https://github.com/x/y/releases/tag/r2a" in doc and "| a |" in doc and "r2a.mp4" in doc


@needs_ffmpeg
def test_make_publish_dry_run_writes_no_release_doc(media_root, tmp_path, capsys):
    doc = config.RELEASES_DOC_DIR / "r1a.md"
    existed = doc.exists()
    rc = make.main(["r1a", "--no-llm", "--publish", "--dry-run", "--media", str(media_root), "--board", str(BOARD),
                    "--build", str(tmp_path / "build"), "--no-open"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "dry-run" in out and "gh release create r1a" in out
    assert doc.exists() == existed                                # --dry-run writes nothing into docs/
