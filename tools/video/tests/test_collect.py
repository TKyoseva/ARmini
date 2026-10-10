"""Test 1 (loader) + media discovery."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import collect
from conftest import BOARD


def test_release_lookup_by_id_or_name(board):
    assert collect.find_release(board, "r1a").name == "R1a"
    assert collect.find_release(board, "R1A").id == "r1a"
    assert collect.find_release(board, "nope") is None


def test_release_cards_by_rel_name(board):
    rel = collect.find_release(board, "r1a")
    labels = [c.label for c in collect.cards_for_release(board, rel)]
    assert labels == ["C001", "C002", "C003"]          # card.rel == release.name, ordered by seq
    assert [c.label for c in collect.cards_for_release(board, collect.find_release(board, "r1b"))] == ["C004"]


def test_cards_by_labels_unknown_label(board):
    try:
        collect.cards_by_labels(board, ["C001", "C999"])
    except ValueError as exc:
        assert "C999" in str(exc)
    else:
        raise AssertionError("unknown label must raise")


def test_stale_export_warns_but_loads():
    exported = dt.datetime.fromisoformat("2026-10-09T07:57:24+00:00")
    fresh = collect.load_board(BOARD, now=exported + dt.timedelta(hours=1))
    assert fresh.warnings == []
    stale = collect.load_board(BOARD, now=exported + dt.timedelta(hours=25))
    assert any("old" in w for w in stale.warnings)
    assert len(stale.cards) == 4


def test_card_without_folder_is_a_warning_not_an_exception(board, cards_r1a, media_root):
    warnings: list = []
    media = collect.collect(cards_r1a, media_root, warnings)
    assert media["C003"] == []
    assert any(w.startswith("C003:") and "no folder" in w for w in warnings)
    assert [i.file for i in media["C001"]] == ["C001_01.PNG", "C001_02.PNG"]
    assert {i.kind for i in media["C002"]} == {"video", "photo"}


def test_cloud_only_file_is_skipped_with_a_warning(tmp_path):
    folder = tmp_path / "C009_2026-10-10_x"
    folder.mkdir()
    (folder / "C009_01.PNG").write_bytes(b"png")
    (folder / ".C009_02.HEIC.icloud").write_bytes(b"placeholder")   # iCloud: not downloaded
    warnings: list = []
    items = collect.list_media(folder, "C009", warnings)
    assert [i.file for i in items] == ["C009_01.PNG"]
    assert any("C009_02.HEIC" in w and "iCloud" in w for w in warnings)


def test_kind_of_extensions():
    assert collect.kind_of(Path("a.HEIC")) == "photo"
    assert collect.kind_of(Path("a.MOV")) == "video"
    assert collect.kind_of(Path("a.mp4")) == "video"
    assert collect.kind_of(Path("captions.md")) is None


def test_next_uncut_release(board):
    r1a = collect.find_release(board, "r1a")
    assert collect.next_uncut_release(board, r1a).id == "r1b"
    r1b = collect.find_release(board, "r1b")
    assert collect.next_uncut_release(board, r1b) is None            # R0 is cut, nothing after R1b
    assert collect.next_uncut_release(board, None, today="2026-10-12").id == "r1b"


def test_iso_date_accepts_epoch_ms_and_strings():
    assert collect._iso_date(1791511500000) == "2026-10-09"
    assert collect._iso_date("2026-10-11") == "2026-10-11"
    assert collect._iso_date(None) is None
