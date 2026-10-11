"""RC-Terminal (rc-terminal.de) — link-only.

Probed 2026-10-10: robots.txt allows everything (`Disallow:` empty), but the product page
returned a WAF challenge ("Sicherheitsprüfung", JavaScript required) instead of HTML with
JSON-LD. The challenge token is not stored. Stored prices stay in watch.yaml; confidence is low.
"""
from __future__ import annotations

from typing import List

from adapters.base import Adapter

LINK_REASON = ("WAF challenge page instead of the product (fetched 2026-10-10); no JSON-LD")


def parse_payload(text: str) -> list:
    """No page is parsed. Empty input returns [], and so does anything else."""
    return []


class RcTerminalAdapter(Adapter):
    name = "rc_terminal"
    kind = "link"
    link_reason = LINK_REASON

    def search(self, query: str, need_id: str = "", qty: int = 1) -> List:
        return []

    def refresh(self, url: str) -> list:
        return []

    def discover(self, query: str) -> list:
        return []
