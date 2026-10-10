"""RobotShop EU (eu.robotshop.com) — link-only.

Probed 2026-10-10 with the parts-agent User-Agent: GET /robots.txt returned HTTP 403 and a
captcha page ("Just a moment..."). The product `.js` URL and `/search/suggest.json` were not
fetched. Stored prices stay in watch.yaml; confidence is low.
"""
from __future__ import annotations

from typing import List

from adapters.base import Adapter

LINK_REASON = ("eu.robotshop.com HTTP 403 captcha (Just a moment) on /robots.txt, 2026-10-10; "
               "product JSON not fetched")


def parse_payload(text: str) -> list:
    """No page is parsed. Empty input returns [], and so does anything else."""
    return []


class RobotshopEuAdapter(Adapter):
    name = "robotshop_eu"
    kind = "link"
    link_reason = LINK_REASON

    def search(self, query: str, need_id: str = "", qty: int = 1) -> List:
        return []

    def refresh(self, url: str) -> list:
        return []

    def discover(self, query: str) -> list:
        return []
