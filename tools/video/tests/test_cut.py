"""Test 5 (cut via make.py end to end), 6 (--swap through the CLI) and the pure filtergraph builder."""
from __future__ import annotations

from pathlib import Path

import pytest

import collect
import config
import cut
import make
from conftest import BOARD, needs_ffmpeg
from judge import Pick


def test_plan_and_duration_are_pure(tmp_path):
    picks = [Pick("C002", "C002_02.mp4", "video", 0.0, 6.0, 7, "why", "C002 · b · Pass\n4 wires"),
             Pick("C001", "C001_01.PNG", "photo", 0, 0, 5, "why", "C001 · a · Partial")]
    files = {("C002", "C002_02.mp4"): tmp_path / "v.mp4", ("C001", "C001_01.PNG"): tmp_path / "p.jpg"}
    segs = cut.plan(["AR-Mini · R1a", "goal", "2026-10-11"], picks, files, "next: lift Pesho")
    assert [s.kind for s in segs] == ["title", "clip", "still", "end"]
    assert cut.total_duration(segs) == pytest.approx(2.5 + 6.0 + 3.0 + 2.5)
    assert segs[1].start_s == 0.0 and segs[1].lines == ["C002 · b · Pass", "4 wires"]
    textfiles = cut.write_textfiles(segs, tmp_path / "text")
    cmd = cut.ffmpeg_command(segs, tmp_path / "out.mp4", textfiles, font="/f/font.ttf")
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "concat=n=4:v=1:a=0[vout]" in fc
    assert fc.count("drawtext=") == 3 + 2 + 1 + 1                  # title 3 lines, clip 2, still 1, end 1
    assert "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080" in fc
    assert "anullsrc" in " ".join(cmd) and "libx264" in cmd and "aac" in cmd
    assert (tmp_path / "text" / "seg01_line1.txt").read_text(encoding="utf-8") == "4 wires"


def test_length_guard():
    segs = [cut.Segment("title", 2.5), cut.Segment("clip", 41.0), cut.Segment("end", 2.5)]
    with pytest.raises(ValueError):
        cut.check_length(segs)


def test_vertical_size_in_filtergraph(tmp_path):
    segs = [cut.Segment("title", 2.5, lines=["a"]), cut.Segment("end", 2.5, lines=["b"])]
    cmd = cut.ffmpeg_command(segs, tmp_path / "o.mp4", cut.write_textfiles(segs, tmp_path), size=(1080, 1920), font="/f")
    assert "s=1080x1920" in " ".join(cmd)


@needs_ffmpeg
def test_make_cuts_an_mp4_of_the_expected_length(media_root, tmp_path, capsys):
    build = tmp_path / "build"
    rc = make.main(["--cards", "C001,C002", "--no-llm", "--media", str(media_root), "--board", str(BOARD),
                    "--build", str(build), "--no-open"])
    assert rc == 0
    out = build / "C001-C002.mp4"
    assert out.exists()
    info = collect.probe_video(out)
    expected = config.TITLE_S + config.STILL_S + 6.0 + config.END_S     # C001 photo 3 s + C002 6 s clip (whole file)
    assert info["duration"] == pytest.approx(expected, abs=0.5)
    assert (info["width"], info["height"]) == (1920, 1080)
    assert info["fps"] == pytest.approx(30.0)
    shotlist = (build / "C001-C002_shotlist.md").read_text(encoding="utf-8")
    assert "rules (--no-llm)" in shotlist and "C002_02.mp4" in shotlist and "## Rejected" in shotlist
    assert "C001 · Cuifati thruster: dimensions, bolt pattern, mass · Partial" in shotlist


@needs_ffmpeg
def test_make_release_r1a_uses_release_title_and_vertical(media_root, tmp_path):
    build = tmp_path / "build"
    rc = make.main(["r1a", "--no-llm", "--vertical", "--media", str(media_root), "--board", str(BOARD),
                    "--build", str(build), "--no-open"])
    assert rc == 0
    info = collect.probe_video(build / "r1a_vertical.mp4")
    assert (info["width"], info["height"]) == (1080, 1920)
    text = (build / "cache" / "text" / "seg00_line0.txt").read_text(encoding="utf-8")
    assert text == "AR-Mini · R1a"
    end = sorted((build / "cache" / "text").glob("seg*_line0.txt"))[-1].read_text(encoding="utf-8")
    assert end == "next: the arm lifts Pesho in the bathtub"


@needs_ffmpeg
def test_make_swap_replaces_one_pick_and_says_so(media_root, tmp_path):
    build = tmp_path / "build"
    rc = make.main(["--cards", "C001,C002", "--no-llm", "--swap", "C002=C002_01.mp4", "--media", str(media_root),
                    "--board", str(BOARD), "--build", str(build), "--no-open"])
    assert rc == 0
    shotlist = (build / "C001-C002_shotlist.md").read_text(encoding="utf-8")
    assert "Swapped: C002 C002_01.mp4 replaces C002 C002_02.mp4 (--swap)" in shotlist
    picked_rows = [l for l in shotlist.splitlines() if l.startswith("| ") and "| video |" in l]
    assert len(picked_rows) == 1 and "C002_01.mp4" in picked_rows[0]
    info = collect.probe_video(build / "C001-C002.mp4")
    assert info["duration"] == pytest.approx(config.TITLE_S + config.STILL_S + 3.0 + config.END_S, abs=0.5)


def test_make_exit_2_when_release_has_no_cards(tmp_path, capsys):
    rc = make.main(["r0", "--no-llm", "--media", str(tmp_path), "--board", str(BOARD), "--build", str(tmp_path), "--no-open"])
    assert rc == 2
    assert "no cards" in capsys.readouterr().err


def test_make_exit_2_when_no_media_at_all(tmp_path, capsys):
    rc = make.main(["r1a", "--no-llm", "--media", str(tmp_path / "empty"), "--board", str(BOARD),
                    "--build", str(tmp_path), "--no-open"])
    assert rc == 2
    assert "no photos or videos" in capsys.readouterr().err


def test_make_needs_release_or_cards():
    with pytest.raises(SystemExit):
        make.parse_args([])
