"""Blue Robotics (bluerobotics.com) — link-only.

Probed 2026-10-10: robots.txt for `User-agent: *` contains `Disallow: /wp-json/`.
The Store API `/wp-json/wc/store/v1/products` was not fetched. Stored prices stay in
watch.yaml; confidence is low.
"""
from __future__ import annotations

from typing import List

from adapters.base import Adapter

LINK_REASON = ("robots.txt Disallow: /wp-json/ (fetched 2026-10-10); Store API not fetched")


def parse_payload(text: str) -> list:
    """No page is parsed. Empty input returns [], and so does anything else."""
    return []


class BlueRoboticsAdapter(Adapter):
    name = "bluerobotics"
    kind = "link"
    link_reason = LINK_REASON

    def search(self, query: str, need_id: str = "", qty: int = 1) -> List:
        return []

    def refresh(self, url: str) -> list:
        return []

    def discover(self, query: str) -> list:
        return []
