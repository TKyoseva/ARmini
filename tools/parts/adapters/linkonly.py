"""Link-only suppliers: amazon_de, bauhaus, 3dcolour.

Amazon.de blocks scrapers (task T4: "do not fight it"); Bauhaus and 3D Colour are pick-up /
manual shops. These adapters never touch the network: fetch(url) returns the stored link with
the default lead days, price null and confidence low, and the report says "check price by hand".
"""
from __future__ import annotations

from typing import List, Optional
from urllib.parse import urlsplit

from adapters.base import Adapter
from model import Offer

# host fragment -> supplier name (used to route need.links[] to an adapter)
HOSTS = {
    "amazon.": "amazon_de",
    "bauhaus.": "bauhaus",
    "3dcolour": "3dcolour",
    "3dcolor": "3dcolour",
}


def supplier_for_url(url: str) -> Optional[str]:
    host = urlsplit(url).netloc.lower()
    for frag, name in HOSTS.items():
        if frag in host:
            return name
    return None


class LinkOnlyAdapter(Adapter):
    kind = "link"

    def __init__(self, default_lead_days: int, name: str = "link", **kw):
        super().__init__(default_lead_days, **kw)
        self.name = name

    def search(self, query: str, need_id: str = "", qty: int = 1) -> List[Offer]:
        return []            # no search without a browser; store a link in needs.yaml instead

    def fetch(self, url: str, need_id: str = "") -> Optional[Offer]:
        host = urlsplit(url).netloc or url
        return self.offer(need_id, f"{host} (check price by hand)", url, None,
                          in_stock=None, stock=None, confidence="low")
