"""Score media items of a release and pick the 2–3 that best show what was tested and what happened.

Two paths, one output schema (Pick):
- rules_pick(): deterministic, no network. Videos before photos; latest video per card; middle 8 s.
- gemini_pick(): Gemini (google-genai) with the rubric; any error → rules_pick() and the shot list says so.

Captions are built here from card fields only (label, title, outcome, result ≤ 60 chars).
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import config
from collect import Card, MediaItem, Release

# SOURCE: task T5 — given to the model verbatim; the rules path uses it as priority order.
RUBRIC = """1. Shows the measured result: a ruler, a scale, a meter reading, water level, the robot in water.
2. Shows the robot doing the thing the card tested.
3. Shows a fail honestly (leak, tilt, stall) — these are portfolio gold, never filter them out.
4. Process: hands, tools, printer, bench.
5. Pretty but says nothing → lowest."""

RULES_SCORE_VIDEO = 7  # rules path cannot see content; videos rank above photos (SOURCE: task T5)
RULES_SCORE_PHOTO = 5
SWAP_SCORE = 10


@dataclass
class Pick:
    card_label: str
    file: str
    kind: str                      # video | photo
    start_s: float = 0.0
    end_s: float = 0.0             # video only
    score: float = 0.0             # 0–10
    why: str = ""                  # ≤ 120 chars
    caption: str = ""              # built by code from card fields; lines joined with "\n"

    def to_dict(self) -> dict:
        return {
            "card_label": self.card_label, "file": self.file, "kind": self.kind,
            "start_s": self.start_s, "end_s": self.end_s, "score": self.score,
            "why": self.why, "caption": self.caption,
        }


@dataclass
class Rejected:
    card_label: str
    file: str
    why: str


@dataclass
class Judgement:
    picks: List[Pick]
    rejected: List[Rejected]
    path: str                      # "rules", "gemini:<model>" or "gemini:<model> failed: … → rules"
    notes: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Captions (card fields only)
# ---------------------------------------------------------------------------

OUTCOME_LABEL = {"pass": "Pass", "partial": "Partial", "fail": "Fail"}


def outcome_label(outcome: Optional[str]) -> str:
    return OUTCOME_LABEL.get((outcome or "").strip().lower(), "")


def trim(text: str, n: int = config.RESULT_MAX_CHARS) -> str:
    text = " ".join((text or "").split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def caption_lines(card: Card) -> List[str]:
    """Line 1: `<label> · <title> · <Outcome>` (outcome only if the card has one).
    Line 2: `result` trimmed to 60 chars, only if the card has a result."""
    parts = [card.label]
    if card.title.strip():
        parts.append(" ".join(card.title.split()))
    outcome = outcome_label(card.outcome)
    if outcome:
        parts.append(outcome)
    lines = [" · ".join(parts)]
    if card.result.strip():
        lines.append(trim(card.result))
    return lines


def build_caption(card: Card) -> str:
    return "\n".join(caption_lines(card))


# ---------------------------------------------------------------------------
# Rules path
# ---------------------------------------------------------------------------


def middle_clip(duration_s: float, clip_s: float = config.CLIP_S) -> Tuple[float, float]:
    """The middle `clip_s` seconds, or the whole file if shorter."""
    duration_s = max(0.0, float(duration_s))
    if duration_s <= clip_s:
        return 0.0, round(duration_s, 3)
    start = (duration_s - clip_s) / 2
    return round(start, 3), round(start + clip_s, 3)


def pick_limit(n_cards_with_media: int) -> int:
    """3 per release, 2 if the release has 2 cards; 1 card → up to 3 items from it (SOURCE: task T5)."""
    return 2 if n_cards_with_media == 2 else config.MAX_PICKS


def _ordered(items: List[MediaItem]) -> List[MediaItem]:
    """Videos first; within a kind the latest first (mtime, then the number in the file name)."""
    return sorted(items, key=lambda i: (i.kind != "video", -i.mtime, _name_key(i.file)))


def _name_key(name: str) -> tuple:
    """Natural sort, reversed (later numbers first): C006_10 before C006_02."""
    return tuple(-int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name))


def _pick_from(item: MediaItem, card: Card, score: float, why: str) -> Pick:
    start, end = (middle_clip(item.duration_s or 0.0) if item.kind == "video" else (0.0, 0.0))
    return Pick(card_label=card.label, file=item.file, kind=item.kind, start_s=start, end_s=end,
                score=score, why=why[: config.WHY_MAX_CHARS], caption=build_caption(card))


def rules_pick(cards: List[Card], media: Dict[str, List[MediaItem]]) -> Judgement:
    cards_with_media = [c for c in cards if media.get(c.label)]
    limit = pick_limit(len(cards_with_media))
    picks: List[Pick] = []
    rejected: List[Rejected] = []

    if len(cards_with_media) == 1:
        card = cards_with_media[0]
        ordered = _ordered(media[card.label])
        for item in ordered:
            if len(picks) < limit:
                why = ("only card in this cut; " + ("video" if item.kind == "video" else "photo")
                       + f" #{len(picks) + 1} by date")
                picks.append(_pick_from(item, card, RULES_SCORE_VIDEO if item.kind == "video" else RULES_SCORE_PHOTO, why))
            else:
                rejected.append(Rejected(card.label, item.file, f"release limit {limit} reached"))
        return Judgement(picks, rejected, "rules")

    for card in cards:
        items = _ordered(media.get(card.label, []))
        if not items:
            continue
        if len(picks) >= limit:
            for item in items:
                rejected.append(Rejected(card.label, item.file, f"release limit {limit} reached"))
            continue
        best = items[0]
        why = "latest video of the card (videos beat photos)" if best.kind == "video" else "latest photo; card has no video"
        picks.append(_pick_from(best, card, RULES_SCORE_VIDEO if best.kind == "video" else RULES_SCORE_PHOTO, why))
        for item in items[1:]:
            if item.kind == "photo" and best.kind == "video":
                rejected.append(Rejected(card.label, item.file, f"photo; card has a video ({best.file})"))
            elif item.kind == "video":
                rejected.append(Rejected(card.label, item.file, f"older video than {best.file}"))
            else:
                rejected.append(Rejected(card.label, item.file, f"older photo than {best.file}"))
    return Judgement(picks, rejected, "rules")


# ---------------------------------------------------------------------------
# --swap
# ---------------------------------------------------------------------------


def apply_swap(judgement: Judgement, swap: str, cards: List[Card], media: Dict[str, List[MediaItem]]) -> Judgement:
    """`C006=IMG_1234.MOV`: the pick of card C006 becomes that file. If C006 has no pick, the
    lowest-scoring pick is replaced. Exactly one pick changes; the shot list says which."""
    if "=" not in swap:
        raise ValueError(f"--swap wants CARD=FILE, got {swap!r}")
    label, file = (s.strip() for s in swap.split("=", 1))
    label = label.upper()
    card = next((c for c in cards if c.label.upper() == label), None)
    if card is None:
        raise ValueError(f"--swap: card {label} is not in this cut ({', '.join(c.label for c in cards)})")
    item = next((i for i in media.get(card.label, []) if i.file.lower() == file.lower()), None)
    if item is None:
        names = ", ".join(i.file for i in media.get(card.label, [])) or "no media"
        raise ValueError(f"--swap: {file} is not a file of {label} ({names})")

    new_pick = _pick_from(item, card, SWAP_SCORE, "swapped in by Teddy (--swap)")
    picks = list(judgement.picks)
    idx = next((k for k, p in enumerate(picks) if p.card_label.upper() == label), None)
    if idx is None:
        if not picks:
            picks.append(new_pick)
            note = f"Swapped: {label} {item.file} added (--swap; there was no pick to replace)"
            return Judgement(picks, judgement.rejected, judgement.path, judgement.notes + [note])
        idx = min(range(len(picks)), key=lambda k: picks[k].score)
    old = picks[idx]
    picks[idx] = new_pick
    rejected = [r for r in judgement.rejected if not (r.card_label == card.label and r.file == item.file)]
    rejected.append(Rejected(old.card_label, old.file, f"replaced by --swap {label}={item.file}"))
    note = f"Swapped: {label} {item.file} replaces {old.card_label} {old.file} (--swap)"
    return Judgement(picks, rejected, judgement.path, judgement.notes + [note])


# ---------------------------------------------------------------------------
# LLM response parsing (pure; tested without network)
# ---------------------------------------------------------------------------

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "picks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "card_label": {"type": "string"},
                    "file": {"type": "string"},
                    "start_s": {"type": "number"},
                    "end_s": {"type": "number"},
                    "score": {"type": "number"},
                    "why": {"type": "string"},
                },
                "required": ["card_label", "file", "score", "why"],
            },
        },
        "rejected": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"file": {"type": "string"}, "why": {"type": "string"}},
                "required": ["file", "why"],
            },
        },
    },
    "required": ["picks"],
}


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON from the model: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("picks"), list):
        raise ValueError("model JSON has no 'picks' list")
    return data


def parse_llm_response(text: str, cards: List[Card], media: Dict[str, List[MediaItem]],
                       limit: Optional[int] = None) -> Tuple[List[Pick], List[Rejected], List[str]]:
    """Validate the model's JSON against the real files. Returns (picks, rejected, notes).
    Raises ValueError when nothing usable is left (caller falls back to rules)."""
    data = _extract_json(text)
    by_label = {c.label.upper(): c for c in cards}
    files: Dict[Tuple[str, str], MediaItem] = {
        (label.upper(), i.file.lower()): i for label, items in media.items() for i in items
    }
    cards_with_media = [c for c in cards if media.get(c.label)]
    limit = limit or pick_limit(len(cards_with_media))
    one_card = len(cards_with_media) == 1

    picks: List[Pick] = []
    notes: List[str] = []
    seen_cards: set = set()
    for raw in data["picks"]:
        if not isinstance(raw, dict):
            notes.append("model pick is not an object — dropped")
            continue
        label = str(raw.get("card_label", "")).upper()
        file = str(raw.get("file", ""))
        card = by_label.get(label)
        item = files.get((label, file.lower()))
        if card is None or item is None:
            notes.append(f"model named an unknown file {label}/{file} — dropped")
            continue
        if not one_card and label in seen_cards:
            notes.append(f"model picked {label} twice — second pick dropped")
            continue
        try:
            score = max(0.0, min(10.0, float(raw.get("score", 0))))
        except (TypeError, ValueError):
            score = 0.0
        why = " ".join(str(raw.get("why", "")).split())[: config.WHY_MAX_CHARS]
        start, end = 0.0, 0.0
        if item.kind == "video":
            dur = float(item.duration_s or 0.0)
            try:
                start = float(raw.get("start_s", 0.0))
                end = float(raw.get("end_s", start + config.CLIP_S))
            except (TypeError, ValueError):
                notes.append(f"{label}/{file}: start_s/end_s not numbers — dropped")
                continue
            if start < 0 or start >= dur or end <= start:
                notes.append(f"{label}/{file}: start_s/end_s {start}–{end} out of range (duration {dur:.1f}) — dropped")
                continue
            if end > dur:
                notes.append(f"{label}/{file}: end_s {end} clamped to duration {dur:.1f}")
                end = dur
            if end - start > config.CLIP_MAX_S:
                end = start + config.CLIP_MAX_S
                notes.append(f"{label}/{file}: clip shortened to {config.CLIP_MAX_S:.0f} s")
            if end - start < config.CLIP_MIN_S:
                if dur <= config.CLIP_MIN_S:
                    start, end = 0.0, dur  # whole file
                else:
                    end = min(dur, start + config.CLIP_MIN_S)
                    start = max(0.0, end - config.CLIP_MIN_S)
                    notes.append(f"{label}/{file}: clip extended to {config.CLIP_MIN_S:.0f} s")
            start, end = round(start, 3), round(end, 3)
        picks.append(Pick(card_label=card.label, file=item.file, kind=item.kind, start_s=start, end_s=end,
                          score=score, why=why, caption=build_caption(card)))
        seen_cards.add(label)
    if not picks:
        raise ValueError("model returned no usable pick")
    picks.sort(key=lambda p: -p.score)
    if len(picks) > limit:
        notes.append(f"model returned {len(picks)} picks; kept the top {limit}")
        picks = picks[:limit]

    picked = {(p.card_label.upper(), p.file.lower()) for p in picks}
    model_rejects = {str(r.get("file", "")).lower(): str(r.get("why", "")) for r in data.get("rejected", [])
                     if isinstance(r, dict)}
    rejected = [
        Rejected(item.card_label, item.file, model_rejects.get(item.file.lower()) or "not chosen by the model")
        for (label, _), item in files.items() if (label, item.file.lower()) not in picked
    ]
    return picks, rejected, notes


# ---------------------------------------------------------------------------
# Gemini path (network; never used in tests)
# ---------------------------------------------------------------------------


def _prompt(release: Optional[Release], cards: List[Card], media: Dict[str, List[MediaItem]], limit: int) -> str:
    lines = ["You pick the moments for a 30–45 s release video of AR-Mini, a 1:9 amphibious rescue-robot demonstrator "
             "built and tested by one student. Judge only what is visible in the media.", ""]
    if release is not None:
        lines += [f"Release {release.name}: {release.goal}", ""]
    lines.append("Cards (what was tested and what happened):")
    for c in cards:
        lines.append(f"- {c.label} · {c.title} · outcome: {outcome_label(c.outcome) or 'none'}")
        if c.hyp:
            lines.append(f"  hypothesis: {c.hyp}")
        if c.result:
            lines.append(f"  result: {c.result}")
    lines += ["", "Media (file names are the only valid ids):"]
    for label, items in media.items():
        for i in items:
            dur = f", {i.duration_s:.1f} s" if i.kind == "video" and i.duration_s else ""
            lines.append(f"- {label} / {i.file} ({i.kind}{dur})")
    lines += ["", "Scoring rubric (highest first):", RUBRIC, "",
              f"Pick at most {limit} items, at most one per card"
              + (" (one card only: up to 3 from it)" if len([c for c in cards if media.get(c.label)]) == 1 else "")
              + ". For a video give start_s and end_s, a 5–10 s window inside the file that shows the moment. "
              "Score 0–10 by the rubric. 'why' ≤ 120 characters, plain words. Also list every file you did not pick "
              "with one short reason. Answer as JSON: {\"picks\":[{card_label,file,start_s,end_s,score,why}],"
              "\"rejected\":[{file,why}]}."]
    return "\n".join(lines)


def _sample_frames(video: Path, n: int = config.FRAME_SAMPLES) -> List[Tuple[float, bytes]]:
    """Fallback when the File API refuses the video: n JPEG frames spread over the file."""
    import collect
    dur = collect.probe_duration(video)
    out: List[Tuple[float, bytes]] = []
    with tempfile.TemporaryDirectory() as tmp:
        for k in range(n):
            t = dur * (k + 0.5) / n
            frame = Path(tmp) / f"f{k}.jpg"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video),
                            "-frames:v", "1", "-vf", f"scale='min({config.FRAME_MAX_SIDE},iw)':-2", "-q:v", "4",
                            str(frame)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out.append((t, frame.read_bytes()))
    return out


def _upload_video(client, path: Path) -> object:
    """File API upload + poll until ACTIVE. SOURCE: https://ai.google.dev/gemini-api/docs/video-understanding"""
    if path.stat().st_size > config.GEMINI_FILE_MAX_BYTES:
        raise RuntimeError(f"{path.name} is larger than the File API limit")
    f = client.files.upload(file=str(path))
    deadline = time.time() + config.GEMINI_UPLOAD_TIMEOUT_S
    while True:
        state = getattr(getattr(f, "state", None), "name", None) or str(getattr(f, "state", ""))
        if state == "ACTIVE":
            return f
        if state == "FAILED":
            raise RuntimeError(f"File API processing failed for {path.name}")
        if time.time() > deadline:
            raise RuntimeError(f"File API processing timed out for {path.name}")
        time.sleep(config.GEMINI_POLL_S)
        f = client.files.get(name=f.name)


def gemini_pick(release: Optional[Release], cards: List[Card], media: Dict[str, List[MediaItem]],
                api_key: Optional[str] = None, model: str = config.GEMINI_MODEL) -> Judgement:
    """Vision-model path. Any failure → rules_pick(), and `path` says what happened."""
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    fallback = rules_pick(cards, media)
    if not api_key:
        fallback.path = "rules (no GEMINI_API_KEY)"
        return fallback
    try:
        from google import genai  # type: ignore  # optional dependency: tools/video/requirements.txt
    except ImportError:
        fallback.path = "rules (google-genai not installed: pip install -r tools/video/requirements.txt)"
        return fallback

    cards_with_media = [c for c in cards if media.get(c.label)]
    limit = pick_limit(len(cards_with_media))
    notes: List[str] = []
    try:
        client = genai.Client(api_key=api_key)
        parts: List[dict] = [{"type": "text", "text": _prompt(release, cards, media, limit)}]
        for label, items in media.items():
            for item in items:
                if item.cached is None:
                    continue
                if item.kind == "photo":
                    parts.append({"type": "text", "text": f"{label} / {item.file}:"})
                    parts.append({"type": "image", "mime_type": "image/jpeg",
                                  "data": base64.b64encode(item.cached.read_bytes()).decode("ascii")})
                else:
                    try:
                        f = _upload_video(client, item.cached)
                        parts.append({"type": "text", "text": f"{label} / {item.file} (video):"})
                        parts.append({"type": "video", "uri": f.uri, "mime_type": f.mime_type or "video/mp4"})
                    except Exception as exc:  # noqa: BLE001 — fall back to frames for this file
                        notes.append(f"{label}/{item.file}: video upload failed ({exc}); sent {config.FRAME_SAMPLES} frames instead")
                        for t, jpg in _sample_frames(item.cached):
                            parts.append({"type": "text", "text": f"{label} / {item.file} frame at {t:.1f} s:"})
                            parts.append({"type": "image", "mime_type": "image/jpeg",
                                          "data": base64.b64encode(jpg).decode("ascii")})
        # SOURCE: https://ai.google.dev/gemini-api/docs/structured-output (Interactions API, JSON schema)
        interaction = client.interactions.create(
            model=model,
            input=parts,
            response_format={"type": "text", "mime_type": "application/json", "schema": RESPONSE_SCHEMA},
        )
        text = getattr(interaction, "output_text", None) or str(interaction)
        picks, rejected, parse_notes = parse_llm_response(text, cards, media, limit)
        return Judgement(picks, rejected, f"gemini:{model}", notes + parse_notes)
    except Exception as exc:  # noqa: BLE001 — the rules result is always a valid answer
        fallback.path = f"gemini:{model} failed: {str(exc)[:160]} → rules"
        fallback.notes = notes
        return fallback
