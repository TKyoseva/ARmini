"""Tests 2 (rules judge), 3 (LLM response parser), 4 (caption builder), 6 (swap logic)."""
from __future__ import annotations

import json
import sys
import types

import pytest

import collect
import judge
from collect import Card, MediaItem


def _item(label, file, kind, mtime, duration=None, starred=False):
    from pathlib import Path
    return MediaItem(card_label=label, file=file, path=Path(f"/x/{file}"), kind=kind, mtime=mtime, size=1,
                     duration_s=duration, cached=Path(f"/cache/{file}"), starred=starred)


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


# --- ★ from captions.md (Desk 1 review) --------------------------------------

def test_star_beats_latest_video_and_video_beats_photo_otherwise():
    cards = [Card(label="C002", title="wires", rel="R", outcome="pass"), Card(label="C003", title="plate", rel="R")]
    media = {
        "C002": [_item("C002", "C002_01.mp4", "video", 1, 3.0, starred=True),   # older, but Teddy's ★
                 _item("C002", "C002_02.mp4", "video", 2, 6.0),
                 _item("C002", "C002_03.PNG", "photo", 3)],
        "C003": [_item("C003", "C003_01.PNG", "photo", 1), _item("C003", "C003_02.mp4", "video", 2, 9.0)],
    }
    j = judge.rules_pick(cards, media)
    by_card = {p.card_label: p for p in j.picks}
    assert by_card["C002"].file == "C002_01.mp4"
    assert by_card["C002"].why == judge.STAR_WHY == "★ Teddy's pick (captions.md)"
    assert by_card["C002"].score == judge.RULES_SCORE_STAR > judge.RULES_SCORE_VIDEO
    assert by_card["C003"].file == "C003_02.mp4"                   # no ★ on this card → the old rules
    assert by_card["C003"].why != judge.STAR_WHY
    reasons = {r.file: r.why for r in j.rejected}
    assert "★ C002_01.mp4" in reasons["C002_02.mp4"] and "captions.md" in reasons["C002_02.mp4"]


def test_star_photo_beats_unstarred_video_within_a_card():
    card = Card(label="C001", title="t", rel="R")
    media = {"C001": [_item("C001", "C001_01.mp4", "video", 9, 20.0), _item("C001", "C001_07.HEIC", "photo", 1, starred=True),
                      _item("C001", "C001_02.HEIC", "photo", 5)]}
    j = judge.rules_pick([card], media)                            # one card → up to 3 items, ★ first
    assert [p.file for p in j.picks] == ["C001_07.HEIC", "C001_01.mp4", "C001_02.HEIC"]
    assert j.picks[0].why == judge.STAR_WHY and j.picks[1].why != judge.STAR_WHY


def test_inline_order_puts_every_star_first_then_card_order():
    cards = [Card(label="C001", title="a", rel="R"), Card(label="C002", title="b", rel="R")]
    media = {"C001": [_item("C001", "C001_01.PNG", "photo", 1), _item("C001", "C001_02.PNG", "photo", 2)],
             "C002": [_item("C002", "C002_01.mp4", "video", 1, 6.0), _item("C002", "C002_05.PNG", "photo", 5, starred=True)]}
    order = [i.file for i in judge.inline_order(cards, media)]
    assert order == ["C002_05.PNG", "C001_02.PNG", "C001_01.PNG", "C002_01.mp4"]


def test_prompt_lists_captions_and_marks_stars():
    cards = [Card(label="C001", title="thruster", rel="R", outcome="partial", result="Ø72.27")]
    item = _item("C001", "C001_07.HEIC", "photo", 1, starred=True)
    item.what, item.reading = "Duct outer diameter, caliper across the duct", "72.27 mm (box said 77)"
    text = judge._prompt(None, cards, {"C001": [item, _item("C001", "C001_02.HEIC", "photo", 2)]}, 3)
    assert "- C001 / C001_07.HEIC (photo) ★ · shows: Duct outer diameter, caliper across the duct · reading: 72.27 mm (box said 77)" in text
    assert "- C001 / C001_02.HEIC (photo)\n" in text               # no caption row → nothing invented
    assert "★ = Teddy's own portfolio pick" in text and "captions.md" in text


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


class _FakeFile:
    def __init__(self, name):
        self.name, self.uri, self.mime_type = name, f"https://files.example/{name}", "video/mp4"
        self.state = types.SimpleNamespace(name="ACTIVE")


class _FakeGemini:
    """google.genai stand-in: records uploads, deletes and the request; answers with `reply` or raises."""

    def __init__(self, reply=None, fail_create=False, fail_delete=False):
        self.uploaded, self.deleted, self.requests = [], [], []
        self.reply, self.fail_create, self.fail_delete = reply, fail_create, fail_delete
        outer = self

        class Files:
            def upload(self, file):
                f = _FakeFile(f"files/{len(outer.uploaded) + 1}")
                outer.uploaded.append((file, f.name))
                return f

            def get(self, name):
                return _FakeFile(name)

            def delete(self, name):
                if outer.fail_delete:
                    raise RuntimeError("403")
                outer.deleted.append(name)

        class Interactions:
            def create(self, model, input, response_format):
                outer.requests.append(input)
                if outer.fail_create:
                    raise RuntimeError("quota")
                return types.SimpleNamespace(output_text=outer.reply)

        class Client:
            def __init__(self, api_key):
                self.files, self.interactions = Files(), Interactions()

        self.Client = Client

    def install(self, monkeypatch):
        fake_genai = types.ModuleType("google.genai")
        fake_genai.Client = self.Client
        fake_google = types.ModuleType("google")
        fake_google.genai = fake_genai
        monkeypatch.setitem(sys.modules, "google", fake_google)
        monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
        return self


def _images_in(request):
    """(label/file heading, base64 length) for every inline image, in request order."""
    out = []
    for head, part in zip(request, request[1:]):
        if part.get("type") == "image":
            out.append((head["text"].rstrip(":"), len(part["data"])))
    return out


def test_gemini_request_keeps_stars_under_the_size_cap_and_lists_skipped(monkeypatch, cards_r1a, media_r1a):
    c001 = {i.file: i for i in media_r1a["C001"]}
    c001["C001_01.PNG"].starred = True                            # the older photo is Teddy's ★
    monkeypatch.setattr(judge, "_photo_bytes", lambda path, max_side=1024: b"j" * 3000)   # 4000 chars of base64 each
    monkeypatch.setattr(judge, "_upload_video", lambda client, path: (_ for _ in ()).throw(RuntimeError("no File API")))
    monkeypatch.setattr(judge, "_sample_frames", lambda path: [(1.0, b"f" * 3000)])
    prompt_len = len(judge._prompt(None, cards_r1a, media_r1a, 2).encode("utf-8"))
    monkeypatch.setattr(judge.config, "GEMINI_INLINE_MAX_BYTES", prompt_len + 4000 * 2 + 100)  # room for two images
    reply = json.dumps({"picks": [{"card_label": "C001", "file": "C001_01.PNG", "score": 9, "why": "ruler"},
                                  {"card_label": "C002", "file": "C002_02.mp4", "start_s": 0, "end_s": 6, "score": 8, "why": "meter"}]})
    fake = _FakeGemini(reply).install(monkeypatch)

    j = judge.gemini_pick(None, cards_r1a, media_r1a, api_key="k", model="gemini-test")

    assert j.path == "gemini:gemini-test"
    heads = [h for h, _ in _images_in(fake.requests[0])]
    assert heads[0] == "C001 / C001_01.PNG"                      # ★ first, although C001_02 is newer
    assert len(heads) == 2                                        # the cap stopped the request there
    skipped = [n for n in j.notes if "not sent to the model" in n]
    assert skipped and all("MB" in n for n in skipped)
    assert not any("C001_01.PNG" in n for n in skipped)
    assert [p.file for p in j.picks] == ["C001_01.PNG", "C002_02.mp4"]
    assert fake.deleted == []                                     # nothing was uploaded, nothing to delete


def test_gemini_photos_are_downscaled_to_frame_max_side(media_r1a):
    pytest.importorskip("PIL")
    from PIL import Image
    import io
    item = media_r1a["C001"][0]
    jpg = judge._photo_bytes(item.cached, max_side=16)
    with Image.open(io.BytesIO(jpg)) as im:
        assert im.format == "JPEG" and max(im.size) <= 16
    assert judge._b64_len(3000) == 4000 and judge._b64_len(1) == 4


def test_gemini_deletes_every_upload_after_the_interaction(monkeypatch, cards_r1a, media_r1a):
    reply = json.dumps({"picks": [{"card_label": "C002", "file": "C002_02.mp4", "start_s": 0, "end_s": 5, "score": 8, "why": "m"}]})
    fake = _FakeGemini(reply).install(monkeypatch)
    monkeypatch.setattr(judge, "_photo_bytes", lambda path, max_side=1024: b"j")
    j = judge.gemini_pick(None, cards_r1a, media_r1a, api_key="k", model="gemini-test")
    assert j.path == "gemini:gemini-test"
    assert len(fake.uploaded) == 2                                # both C002 clips went through the File API
    assert sorted(fake.deleted) == sorted(name for _, name in fake.uploaded)
    assert [part["uri"] for part in fake.requests[0] if part.get("type") == "video"] == \
        [f"https://files.example/{name}" for _, name in fake.uploaded]


def test_gemini_deletes_uploads_even_when_the_request_fails(monkeypatch, cards_r1a, media_r1a):
    fake = _FakeGemini(fail_create=True).install(monkeypatch)
    monkeypatch.setattr(judge, "_photo_bytes", lambda path, max_side=1024: b"j")
    j = judge.gemini_pick(None, cards_r1a, media_r1a, api_key="k", model="gemini-test")
    assert j.path.startswith("gemini:gemini-test failed: quota") and j.path.endswith("→ rules")
    assert len(fake.uploaded) == 2 and sorted(fake.deleted) == sorted(name for _, name in fake.uploaded)


def test_gemini_failed_delete_is_a_note_not_an_error(monkeypatch, cards_r1a, media_r1a):
    reply = json.dumps({"picks": [{"card_label": "C001", "file": "C001_01.PNG", "score": 8, "why": "m"}]})
    _FakeGemini(reply, fail_delete=True).install(monkeypatch)
    monkeypatch.setattr(judge, "_photo_bytes", lambda path, max_side=1024: b"j")
    j = judge.gemini_pick(None, cards_r1a, media_r1a, api_key="k", model="gemini-test")
    assert j.path == "gemini:gemini-test"                         # the answer stands; the shot list says so
    assert sum("could not delete upload" in n and "48 h" in n for n in j.notes) == 2


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
