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


# Same shape as the real files in iCloud 01_Loops/C###_…/captions.md (media/LINKS.md): a header line,
# free text, one table `| File | What it shows | Reading |`, ★ in the first cell = Teddy's portfolio pick.
CAPTIONS = """# C001 · Cuifati thruster: dimensions, bolt pattern, mass
2026-10-08 · outcome: Partial · ★ = portfolio pick

Card result: duct Ø72.27 × 112 (box says 77).

| File | What it shows | Reading |
|---|---|---|
| ★ C001_01 | Box drawing: what the seller claims | 112 × 77 mm (claim) |
| C001_02 | Box label | — |
| ★ C001_07.HEIC | Duct outer diameter, caliper across the duct | **72.27 mm** (box said 77) |

Story in two photos: C001_01 next to C001_07.
"""


def test_parse_captions_reads_star_what_and_reading():
    rows = collect.parse_captions(CAPTIONS)
    assert set(rows) == {"c001_01", "c001_02", "c001_07"}        # header, separator and prose are skipped
    assert rows["c001_01"].starred and rows["c001_07"].starred and not rows["c001_02"].starred
    assert rows["c001_01"].what == "Box drawing: what the seller claims"
    assert rows["c001_01"].reading == "112 × 77 mm (claim)"
    assert rows["c001_07"].name == "C001_07.HEIC"                 # with or without extension, same key
    assert collect.caption_key("C001_07") == collect.caption_key("c001_07.heic") == "c001_07"


def test_list_media_marks_starred_items_from_captions(tmp_path):
    folder = tmp_path / "C001_2026-10-08_thruster-measure"
    folder.mkdir()
    for name in ("C001_01.PNG", "C001_02.PNG", "C001_07.PNG", "C001_09.PNG"):
        (folder / name).write_bytes(b"png")
    (folder / "captions.md").write_text(CAPTIONS, encoding="utf-8")
    warnings: list = []
    items = {i.file: i for i in collect.list_media(folder, "C001", warnings)}
    assert warnings == []
    assert "captions.md" not in items                              # the table is metadata, not media
    assert [f for f, i in items.items() if i.starred] == ["C001_01.PNG", "C001_07.PNG"]
    assert items["C001_07.PNG"].reading == "**72.27 mm** (box said 77)"
    assert items["C001_09.PNG"].starred is False and items["C001_09.PNG"].what == ""   # not in the table


def test_folder_without_captions_has_no_stars(media_root, cards_r1a):
    warnings: list = []
    media = collect.collect(cards_r1a, media_root, warnings)
    assert not any(i.starred for items in media.values() for i in items)


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
