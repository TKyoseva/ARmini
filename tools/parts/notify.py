"""Telegram notification with stdout fallback. One message per run, <= 3500 chars.

Secrets come only from the environment: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (GitHub → Settings →
Secrets). Without them the text is printed to stdout and the function returns False.
Usage from the workflow:  python tools/parts/notify.py "needs.yaml invalid: …"
"""
from __future__ import annotations

import os
import sys
from typing import Optional

import requests

MAX_CHARS = 3500
TIMEOUT_S = 10


def truncate(text: str, limit: int = MAX_CHARS) -> str:
    """Cut at a line boundary and append '… +N more' (N = dropped lines)."""
    if len(text) <= limit:
        return text
    lines = text.splitlines()
    kept = []
    size = 0
    for i, line in enumerate(lines):
        extra = len(line) + 1
        marker = f"… +{len(lines) - i} more"
        if size + extra + len(marker) + 1 > limit:
            kept.append(marker)
            return "\n".join(kept)
        kept.append(line)
        size += extra
    return "\n".join(kept)


def telegram(text: str, token: Optional[str] = None, chat_id: Optional[str] = None,
             out=None) -> bool:
    """Send `text` (truncated to 3500 chars). Returns True if Telegram accepted it."""
    token = token if token is not None else os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id if chat_id is not None else os.environ.get("TELEGRAM_CHAT_ID", "")
    text = truncate(text)
    out = out or sys.stdout
    if not token or not chat_id:
        print("[telegram disabled — TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set]\n" + text, file=out)
        return False
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=TIMEOUT_S,
    )
    if r.status_code != 200:
        print(f"[telegram HTTP {r.status_code}] {r.text[:200]}\n{text}", file=out)
        return False
    return True


if __name__ == "__main__":
    telegram(" ".join(sys.argv[1:]) or sys.stdin.read())
