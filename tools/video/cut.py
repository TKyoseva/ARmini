"""Shot list → ffmpeg filtergraph → mp4.

plan() and ffmpeg_command() are pure (no subprocess); run() calls ffmpeg once.
Layout (SOURCE: task T5): title card 2.5 s · clips with a lower-third · stills 3 s · end card 2.5 s.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import config
from judge import Pick

Size = Tuple[int, int]


@dataclass
class Segment:
    kind: str                       # title | clip | still | end
    duration: float
    lines: List[str] = field(default_factory=list)   # title/end: centred lines; clip/still: lower-third lines
    path: Optional[Path] = None     # clip/still: converted media in the cache
    start_s: float = 0.0            # clip: trim start inside the file

    def __post_init__(self) -> None:
        self.duration = round(float(self.duration), 3)


def total_duration(segments: List[Segment]) -> float:
    return round(sum(s.duration for s in segments), 3)


def plan(title_lines: List[str], picks: List[Pick], files: Dict[Tuple[str, str], Path],
         end_line: str) -> List[Segment]:
    """files: (card_label, file) → cached path. Picks without a cached file are skipped by the caller."""
    segments = [Segment("title", config.TITLE_S, lines=[l for l in title_lines if l])]
    for p in picks:
        path = files[(p.card_label, p.file)]
        lines = p.caption.split("\n") if p.caption else []
        if p.kind == "video":
            segments.append(Segment("clip", p.end_s - p.start_s, lines=lines, path=path, start_s=p.start_s))
        else:
            segments.append(Segment("still", config.STILL_S, lines=lines, path=path))
    segments.append(Segment("end", config.END_S, lines=[end_line]))
    return segments


def check_length(segments: List[Segment]) -> None:
    total = total_duration(segments)
    if total > config.MAX_TOTAL_S:
        raise ValueError(f"cut is {total:.1f} s, longer than {config.MAX_TOTAL_S:.0f} s — drop a pick or shorten a clip")


# ---------------------------------------------------------------------------
# ffmpeg filtergraph
# ---------------------------------------------------------------------------


def _q(value: str) -> str:
    """Quote a filter option value (paths): ffmpeg filter-level quoting with single quotes."""
    return "'" + str(value).replace("\\", "\\\\").replace("'", r"'\''") + "'"


def _drawtext(textfile: Path, font: str, size_px: int, x: str, y: str, color: str = "white") -> str:
    # textfile + expansion=none: no escaping of the caption text itself (it may contain : , ' % …)
    return (f"drawtext=fontfile={_q(font)}:textfile={_q(textfile)}:expansion=none"
            f":fontsize={size_px}:fontcolor={color}:x={x}:y={y}")


def _fit(size: Size) -> str:
    w, h = size
    return (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={config.FPS},format=yuv420p")


def _lower_third(lines: List[str], textfiles: List[Path], font: str, size: Size) -> str:
    """Dark band at the bottom with 1–2 lines of text."""
    if not lines:
        return ""
    w, h = size
    band = 150 if len(lines) > 1 else 100
    y0 = h - band
    chain = [f"drawbox=x=0:y={y0}:w={w}:h={band}:color=black@{config.BAND_ALPHA}:t=fill",
             _drawtext(textfiles[0], font, config.CAPTION_PX, "60", str(y0 + 28))]
    if len(lines) > 1:
        chain.append(_drawtext(textfiles[1], font, config.CAPTION2_PX, "60", str(y0 + 86), color="0xdddddd"))
    return "," + ",".join(chain)


def _card(lines: List[str], textfiles: List[Path], font: str, size: Size) -> str:
    """Centred lines on a dark background: line 1 at TITLE_PX, the rest at CAPTION_PX."""
    _, h = size
    n = len(lines)
    chain = ["format=yuv420p"]
    gap = 80
    first_y = h / 2 - gap * (n - 1) / 2 - config.TITLE_PX / 2
    for k, tf in enumerate(textfiles[:n]):
        px = config.TITLE_PX if k == 0 else config.CAPTION_PX
        color = "white" if k < 2 else "0xbbbbbb"
        chain.append(_drawtext(tf, font, px, "(w-text_w)/2", str(int(first_y + k * gap)), color=color))
    return ",".join(chain)


def write_textfiles(segments: List[Segment], textdir: Path) -> Dict[int, List[Path]]:
    """One UTF-8 file per text line (drawtext reads textfile=). Returns segment index → files."""
    textdir = Path(textdir)
    textdir.mkdir(parents=True, exist_ok=True)
    out: Dict[int, List[Path]] = {}
    for i, seg in enumerate(segments):
        files = []
        for k, line in enumerate(seg.lines):
            tf = textdir / f"seg{i:02d}_line{k}.txt"
            tf.write_text(line, encoding="utf-8")
            files.append(tf)
        out[i] = files
    return out


def ffmpeg_command(segments: List[Segment], out: Path, textfiles: Dict[int, List[Path]],
                   size: Size = (config.WIDTH, config.HEIGHT), font: Optional[str] = None,
                   caption_font: Optional[str] = None) -> List[str]:
    """Pure: the full ffmpeg argv. One input per segment + a silent audio source; concat; x264 + aac.
    `font` draws the title/end cards, `caption_font` the lower-thirds (defaults: config)."""
    font = font or config.font_path()
    caption_font = caption_font or config.caption_font_path()
    w, h = size
    args: List[str] = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    chains: List[str] = []
    for i, seg in enumerate(segments):
        tfs = textfiles.get(i, [])
        if seg.kind in ("title", "end"):
            args += ["-f", "lavfi", "-t", f"{seg.duration}", "-i", f"color=c={config.BACKGROUND}:s={w}x{h}:r={config.FPS}"]
            chains.append(f"[{i}:v]{_card(seg.lines, tfs, font, size)}[v{i}]")
        elif seg.kind == "clip":
            args += ["-ss", f"{seg.start_s}", "-t", f"{seg.duration}", "-i", str(seg.path)]
            chains.append(f"[{i}:v]{_fit(size)},setpts=PTS-STARTPTS,trim=duration={seg.duration}"
                          f"{_lower_third(seg.lines, tfs, caption_font, size)}[v{i}]")
        elif seg.kind == "still":
            args += ["-loop", "1", "-framerate", f"{config.FPS}", "-t", f"{seg.duration}", "-i", str(seg.path)]
            chains.append(f"[{i}:v]{_fit(size)},trim=duration={seg.duration}"
                          f"{_lower_third(seg.lines, tfs, caption_font, size)}[v{i}]")
        else:
            raise ValueError(f"unknown segment kind {seg.kind}")
    n = len(segments)
    args += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
    concat = "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vout]"
    args += ["-filter_complex", ";".join(chains + [concat]),
             "-map", "[vout]", "-map", f"{n}:a",
             *config.X264_ARGS, "-r", f"{config.FPS}", *config.AAC_ARGS,
             "-t", f"{total_duration(segments)}", "-shortest", "-movflags", "+faststart", str(out)]
    return args


def run(segments: List[Segment], out: Path, textdir: Path, size: Size = (config.WIDTH, config.HEIGHT),
        font: Optional[str] = None) -> Path:
    """Assert the length, write the text files, run ffmpeg. Returns the output path."""
    import subprocess

    check_length(segments)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    textfiles = write_textfiles(segments, textdir)
    cmd = ffmpeg_command(segments, out, textfiles, size=size, font=font)
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({proc.returncode}):\n{proc.stderr.strip()[-2000:]}")
    return out
