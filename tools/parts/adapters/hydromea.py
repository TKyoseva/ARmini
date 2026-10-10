"""Hydromea (hydromea.com, Wix) — html adapter. JSON-LD only.

SOURCE (fetched 2026-10-10, robots.txt `User-agent: * / Allow: /`, Disallow only `*?lightbox=`):
- product page JSON-LD `@type: Product` with `offers.price`, `priceCurrency`, `availability`
  (fixture: tests/fixtures/hydromea_product.html, DiskDrive 50 Thrust Kit, 80 USD, InStock)
- category page JSON-LD `@type: ItemList` of products
  (fixture: tests/fixtures/hydromea_category.html, `/category/diskdrive-50-products`)

Discovery uses that category page. The live HTML is about 2.3 MB; the fixtures keep the JSON-LD.
VAT is not in the JSON-LD, so this adapter does not set vat_included.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from selectolax.lexbor import LexborHTMLParser

from adapters.base import Adapter

# SOURCE: tasks/night/2026-10-10_T6 — the discovery page named in the task.
CATEGORY_URL = "https://www.hydromea.com/category/diskdrive-50-products"


@dataclass
class PageProduct:
    title: str
    url: str
    price: Optional[float]
    currency: Optional[str]
    in_stock: Optional[bool]


def _price(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def _stock(availability: Any) -> Optional[bool]:
    text = str(availability or "")
    if "OutOfStock" in text:
        return False
    if "InStock" in text:
        return True
    return None


def _product(node: Dict[str, Any]) -> Optional[PageProduct]:
    offers = node.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if not isinstance(offers, dict):
        offers = {}
    title = str(node.get("name") or "")
    url = str(offers.get("url") or node.get("url") or "")
    if not title and not url:
        return None
    return PageProduct(title=title, url=url, price=_price(offers.get("price")),
                       currency=(str(offers["priceCurrency"]) if offers.get("priceCurrency") else None),
                       in_stock=_stock(offers.get("availability")))


def _walk(node: Any, out: List[PageProduct]) -> None:
    if isinstance(node, list):
        for item in node:
            _walk(item, out)
        return
    if not isinstance(node, dict):
        return
    if "@graph" in node:
        _walk(node["@graph"], out)
    types = node.get("@type")
    types = types if isinstance(types, list) else [types]
    if "Product" in types:
        product = _product(node)
        if product is not None:
            out.append(product)
    if "ItemList" in types:
        for el in node.get("itemListElement") or []:
            if isinstance(el, dict):
                _walk(el.get("item") or {}, out)


def parse_hydromea(html: str) -> List[PageProduct]:
    """Products from JSON-LD. Empty or non-HTML input returns [], never raises."""
    if not html or not str(html).strip():
        return []
    try:
        doc = LexborHTMLParser(html)
        blocks = []
        for node in doc.css('script[type="application/ld+json"]'):
            raw = node.text() or ""
            if not raw.strip():
                continue
            try:
                blocks.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    except Exception:  # noqa: BLE001 — a bad page is an empty result, not a failed run
        return []
    out: List[PageProduct] = []
    _walk(blocks, out)
    return out


class HydromeaAdapter(Adapter):
    name = "hydromea"
    kind = "html"
    quotes_net = False

    def __init__(self, default_lead_days: int = 0, http=None, **kw):
        super().__init__(default_lead_days, http=http, **kw)
        self._pages: Dict[str, List[PageProduct]] = {}

    def _page(self, url: str) -> List[PageProduct]:
        if url not in self._pages:
            assert self.http is not None
            response = self.http.get(url, check_robots=True)
            self._pages[url] = parse_hydromea(response.text)
        return self._pages[url]

    def refresh(self, url: str) -> List[PageProduct]:
        return self._page(url)

    def discover(self, query: str) -> List[PageProduct]:
        # The query (yaml: "diskdrive") selects this shop; the page is the category from T6.
        return self._page(CATEGORY_URL)

    def search(self, query: str, need_id: str = "", qty: int = 1):
        return []
