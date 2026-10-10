"""Draft GitHub Release with the mp4 attached, via `gh`. --dry-run prints the commands and writes nothing.

SOURCE: task T5 — `gh release create <tag> <mp4> --draft --title "<name> · <goal>" --notes-file <shotlist>`,
tag on the current `main` HEAD; if the tag exists, `gh release upload --clobber` instead.
"""
from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

EXIT_NO_GH = 3


def gh_status() -> Tuple[bool, str]:
    """(ok, reason). ok only if `gh` exists and `gh auth status` succeeds."""
    if shutil.which("gh") is None:
        return False, "gh is not installed (brew install gh)"
    proc = subprocess.run(["gh", "auth", "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        return False, "gh is not logged in (gh auth login): " + (proc.stderr or proc.stdout).strip()[-300:]
    return True, "ok"


def tag_exists(tag: str) -> bool:
    proc = subprocess.run(["gh", "release", "view", tag], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode == 0


def commands(tag: str, mp4: Path, notes: Path, title: str, exists: bool) -> List[List[str]]:
    """Pure: the gh commands for a new draft release, or for refreshing an existing one."""
    if exists:
        return [
            ["gh", "release", "upload", tag, str(mp4), "--clobber"],
            ["gh", "release", "edit", tag, "--notes-file", str(notes)],
        ]
    return [[
        "gh", "release", "create", tag, str(mp4), "--draft", "--target", "main",
        "--title", title, "--notes-file", str(notes),
    ]]


def render(cmds: List[List[str]]) -> str:
    return "\n".join(shlex.join(c) for c in cmds)


def release_url(tag: str) -> Optional[str]:
    proc = subprocess.run(["gh", "release", "view", tag, "--json", "url", "-q", ".url"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def publish(tag: str, mp4: Path, notes: Path, title: str, dry_run: bool = False) -> Tuple[int, str, Optional[str]]:
    """Returns (exit_code, printed text, release url). dry_run: prints the create command, touches nothing."""
    if dry_run:
        cmds = commands(tag, mp4, notes, title, exists=False)
        return 0, "dry-run — would run:\n" + render(cmds), None
    ok, reason = gh_status()
    if not ok:
        cmds = commands(tag, mp4, notes, title, exists=False)
        return EXIT_NO_GH, f"{reason}\nrun this yourself when gh works:\n{render(cmds)}", None
    cmds = commands(tag, mp4, notes, title, exists=tag_exists(tag))
    for cmd in cmds:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return 1, f"{shlex.join(cmd)}\nfailed ({proc.returncode}): {(proc.stderr or proc.stdout).strip()[-800:]}", None
    url = release_url(tag)
    return 0, render(cmds) + (f"\n{url}" if url else ""), url


def release_doc(release_name: str, goal: str, tag: str, url: Optional[str], shotlist_md: str, mp4_name: str) -> str:
    """docs/releases/<rel>.md — committed; the video is not."""
    head = [f"# {release_name} · {goal}".rstrip(" ·"), ""]
    head.append(f"GitHub Release (draft until Teddy presses Publish): {url or '(url unknown — gh release view ' + tag + ')'}")
    head.append(f"Video: `{mp4_name}` attached to the release; not in git (see .gitignore).")
    head += ["", "---", "", shotlist_md.strip(), ""]
    return "\n".join(head)


def write_release_doc(path: Path, text: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path

