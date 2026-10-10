"""Tests 2 (rules judge), 3 (LLM response parser), 4 (caption builder), 6 (swap logic)."""
from __future__ import annotations

import json
import sys
import types

import pytest

import collect
import judge
from collect import Card, MediaItem


def _item(label, file, kind, mtime, duration=None):
    from pathlib import Path
    return MediaItem(card_label=label, file=file, path=Path(f"/x/{file}"), kind=kind, mtime=mtime, size=1,
                     duration_s=duration, cached=Path(f"/cache/{file}"))


# --- 2. rules judge --------------------------------------------------------

def test_video_beats_photo_and_latest_video_wins(cards_r1a, media_r1a):
    j = judge.rules_pick(cards_r1a, media_r1a)
    by_card = {p.card_label: p for p in j.picks}
    assert by_card["C002"].file == "C002_02.mp4"            # newest file is C002_03.PNG, but videos win
    assert by_card["C002"].kind == "video"
    assert by_card["C002"].start_s == 0.0 and by_card["C002"].end_s == pytest.approx(6.0, abs=0.1)
    assert j.path == "rules"
    reasons = {r.file: r.why for r in j.rejected}
    assert "older video" in reasons["C002_01.mp4"]
    assert "photo; card has a video" in reasons["C002_03.PNG"]


def test_middle_8s_math():
    assert judge.middle_clip(6.0) == (0.0, 6.0)             # shorter than 8 s → whole file
    assert judge.middle_clip(8.0) == (0.0, 8.0)
    assert judge.middle_clip(20.0) == (6.0, 14.0)
    assert judge.middle_clip(0.0) == (0.0, 0.0)


def test_two_cards_give_two_picks_one_per_card(cards_r1a, media_r1a):
    j = judge.rules_pick(cards_r1a, media_r1a)              # C001 + C002 have media, C003 has none
    assert len(j.picks) == 2
    assert sorted(p.card_label for p in j.picks) == ["C001", "C002"]


def test_three_cards_give_three_picks_max_one_per_card():
    cards = [Card(label=f"C00{k}", title="t", rel="R") for k in range(1, 5)]
    media = {
        "C001": [_item("C001", "C001_01.PNG", "photo", 1), _item("C001", "C001_02.PNG", "photo", 2)],
        "C002": [_item("C002", "C002_01.mp4", "video", 1, 20.0)],
        "C003": [_item("C003", "C003_01.PNG", "photo", 1)],
        "C004": [_item("C004", "C004_01.mp4", "video", 1, 9.0)],
    }
    j = judge.rules_pick(cards, media)
    assert [p.card_label for p in j.picks] == ["C001", "C002", "C003"]
    assert len({p.card_label for p in j.picks}) == 3
    assert any("release limit 3" in r.why and r.card_label == "C004" for r in j.rejected)
    c002 = next(p for p in j.picks if p.card_label == "C002")
    assert (c002.start_s, c002.end_s) == (6.0, 14.0)
    c001 = next(p for p in j.picks if p.card_label == "C001")
    assert c001.file == "C001_02.PNG"                       # latest photo


def test_single_card_gets_up_to_three_items():
    card = Card(label="C006", title="ESC in a bucket", rel="R", outcome="fail", result="stalled at 9 V")
    media = {"C006": [_item("C006", "C006_01.HEIC", "photo", 1), _item("C006", "C006_02.MOV", "video", 2, 30.0),
                      _item("C006", "C006_03.MOV", "video", 3, 4.0), _item("C006", "C006_04.HEIC", "photo", 4)]}
    j = judge.rules_pick([card], media)
    assert [p.file for p in j.picks] == ["C006_03.MOV", "C006_02.MOV", "C006_04.HEIC"]   # videos first, latest first
    assert len(j.rejected) == 1 and j.rejected[0].file == "C006_01.HEIC"
    assert all("Fail" in p.caption for p in j.picks)        # a Fail card is as eligible as a Pass card


def test_natural_file_order_breaks_mtime_ties():
    card = Card(label="C006", title="t", rel="R")
    media = {"C006": [_item("C006", "C006_02.MOV", "video", 5, 10.0), _item("C006", "C006_10.MOV", "video", 5, 10.0)]}
    assert judge.rules_pick([card], media).picks[0].file == "C006_10.MOV"


# --- 4. captions -----------------------------------------------------------

def test_caption_uses_card_fields_only_and_trims_result():
    card = Card(label="C003", title="ROB0154 plate: slots vs beams, size, mass", outcome="fail",
                result="plate 151.82 × 134.8; slots 3.2 wide, 11.3 and 26.4 mm from the edges (≈114 ±0.8 apart)")
    lines = judge.caption_lines(card)
    assert lines[0] == "C003 · ROB0154 plate: slots vs beams, size, mass · Fail"
    assert len(lines[1]) <= 60 and lines[1].endswith("…")
    assert lines[1].startswith("plate 151.82 × 134.8;")
    assert judge.build_caption(card) == "\n".join(lines)


@pytest.mark.parametrize("outcome,label", [("pass", "Pass"), ("partial", "Partial"), ("fail", "Fail"), (None, ""), ("", "")])
def test_outcome_rendering(outcome, label):
    assert judge.outcome_label(outcome) == label


def test_caption_without_result_is_label_and_title_only():
    card = Card(label="C007", title="hull_fore in the bathtub", outcome=None, result="")
    assert judge.caption_lines(card) == ["C007 · hull_fore in the bathtub"]


def test_short_result_is_not_trimmed():
    assert judge.trim("4 wires, not 3. No shorts.") == "4 wires, not 3. No shorts."
    assert len(judge.trim("x" * 100)) == 60


# --- 3. LLM response parser ------------------------------------------------

def _two_cards():
    cards = [Card(label="C001", title="a", rel="R", outcome="pass", result="r"),
             Card(label="C002", title="b", rel="R", outcome="fail", result="r")]
    media = {"C001": [_item("C001", "C001_01.PNG", "photo", 1)],
             "C002": [_item("C002", "C002_02.mp4", "video", 2, 6.0), _item("C002", "C002_01.mp4", "video", 1, 20.0)]}
    return cards, media


def test_parser_rejects_out_of_range_and_clamps_to_duration():
    cards, media = _two_cards()
    text = json.dumps({"picks": [
        {"card_label": "C002", "file": "C002_01.mp4", "start_s": 25.0, "end_s": 30.0, "score": 9, "why": "beyond the end"},
        {"card_label": "C002", "file": "C002_02.mp4", "start_s": 1.0, "end_s": 12.0, "score": 8, "why": "runs past the end"},
        {"card_label": "C001", "file": "C001_01.PNG", "score": 6, "why": "ruler in frame"},
    ]})
    picks, rejected, notes = judge.parse_llm_response(text, cards, media)
    files = {p.file: p for p in picks}
    assert "C002_01.mp4" not in files                        # start 25 s in a 20 s file → rejected
    assert files["C002_02.mp4"].end_s == 6.0                 # clamped to the file duration
    assert files["C002_02.mp4"].start_s == 1.0
    assert any("out of range" in n for n in notes) and any("clamped" in n for n in notes)
    assert {r.file for r in rejected} == {"C002_01.mp4"}


def test_parser_limits_clip_length_to_5_10_s():
    cards, media = _two_cards()
    text = json.dumps({"picks": [
        {"card_label": "C002", "file": "C002_01.mp4", "start_s": 2.0, "end_s": 18.0, "score": 9, "why": "too long"}]})
    picks, _, notes = judge.parse_llm_response(text, cards, media)
    assert (picks[0].start_s, picks[0].end_s) == (2.0, 12.0)
    text = json.dumps({"picks": [
        {"card_label": "C002", "file": "C002_01.mp4", "start_s": 2.0, "end_s": 3.0, "score": 9, "why": "too short"}]})
    picks, _, _ = judge.parse_llm_response(text, cards, media)
    assert picks[0].end_s - picks[0].start_s == pytest.approx(5.0)


def test_parser_rejects_unknown_file_names():
    cards, media = _two_cards()
    text = json.dumps({"picks": [
        {"card_label": "C002", "file": "IMG_9999.MOV", "start_s": 0, "end_s": 5, "score": 9, "why": "invented"},
        {"card_label": "C001", "file": "C001_01.PNG", "score": 6, "why": "real"}]})
    picks, _, notes = judge.parse_llm_response(text, cards, media)
    assert [p.file for p in picks] == ["C001_01.PNG"]
    assert any("unknown file" in n for n in notes)


def test_parser_raises_on_malformed_json_and_on_nothing_usable():
    cards, media = _two_cards()
    with pytest.raises(ValueError):
        judge.parse_llm_response("sorry, here is prose", cards, media)
    with pytest.raises(ValueError):
        judge.parse_llm_response(json.dumps({"picks": [{"card_label": "C009", "file": "x", "score": 1, "why": ""}]}), cards, media)


def test_parser_accepts_fenced_json_and_one_pick_per_card():
    cards, media = _two_cards()
    text = "```json\n" + json.dumps({"picks": [
        {"card_label": "C002", "file": "C002_02.mp4", "start_s": 0, "end_s": 6, "score": 9, "why": "a"},
        {"card_label": "C002", "file": "C002_01.mp4", "start_s": 0, "end_s": 8, "score": 8, "why": "b"}],
        "rejected": [{"file": "C001_01.PNG", "why": "blurry"}]}) + "\n```"
    picks, rejected, notes = judge.parse_llm_response(text, cards, media)
    assert [p.file for p in picks] == ["C002_02.mp4"]
    assert any("twice" in n for n in notes)
    assert {r.file: r.why for r in rejected}["C001_01.PNG"] == "blurry"


def test_gemini_path_falls_back_to_rules_on_any_error(monkeypatch, cards_r1a, media_r1a):
    """Inject a fake google.genai whose client explodes: the answer is the rules result and says so."""
    fake_genai = types.ModuleType("google.genai")

    class BrokenClient:
        def __init__(self, api_key):
            raise RuntimeError("no network in tests")

    fake_genai.Client = BrokenClient
    fake_google = types.ModuleType("google")
    fake_google.genai = fake_genai
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    j = judge.gemini_pick(None, cards_r1a, media_r1a, api_key="test-key", model="gemini-test")
    assert j.path.startswith("gemini:gemini-test failed") and j.path.endswith("→ rules")
    assert [p.file for p in j.picks] == [p.file for p in judge.rules_pick(cards_r1a, media_r1a).picks]


def test_gemini_path_without_key_is_rules(cards_r1a, media_r1a, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    j = judge.gemini_pick(None, cards_r1a, media_r1a)
    assert "no GEMINI_API_KEY" in j.path


# --- 6. swap ---------------------------------------------------------------

def test_swap_replaces_exactly_one_pick(cards_r1a, media_r1a):
    before = judge.rules_pick(cards_r1a, media_r1a)
    after = judge.apply_swap(before, "C002=C002_01.mp4", cards_r1a, media_r1a)
    changed = [(a.file, b.file) for a, b in zip(before.picks, after.picks) if a.file != b.file]
    assert changed == [("C002_02.mp4", "C002_01.mp4")]
    assert len(after.picks) == len(before.picks)
    assert any(n.startswith("Swapped: C002 C002_01.mp4 replaces C002 C002_02.mp4") for n in after.notes)
    assert any(r.file == "C002_02.mp4" and "--swap" in r.why for r in after.rejected)
    assert not any(r.file == "C002_01.mp4" for r in after.rejected)


def test_swap_rejects_unknown_card_or_file(cards_r1a, media_r1a):
    j = judge.rules_pick(cards_r1a, media_r1a)
    with pytest.raises(ValueError):
        judge.apply_swap(j, "C002=IMG_0000.MOV", cards_r1a, media_r1a)
    with pytest.raises(ValueError):
        judge.apply_swap(j, "C099=C002_01.mp4", cards_r1a, media_r1a)
    with pytest.raises(ValueError):
        judge.apply_swap(j, "C002", cards_r1a, media_r1a)
