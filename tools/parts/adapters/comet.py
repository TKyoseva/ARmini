"""Comet Electronics (store.comet.bg) — html adapter.

SOURCE (fetched 2026-10-09): the search page /Search/?keywords=… renders its result table with
JavaScript from  POST /ajax/get_result_listing.php  (same form fields). The response is JSON
{"listing": {"content": "<table class=search_result_list>…", "total": N, "pages": P}}.
Prices are quoted **net** ("Единична цена без ДДС"), so 20 % VAT is added here.
Cookie settings_currency=EUR makes the price cell read "0.46000 EUR | 0.90000 BGN".
Stock cells: td.p-stock (София склад), td.p-stock.last (Пловдив магазин).
robots.txt on store.comet.bg only blocks SemrushBot/AhrefsBot (checked 2026-10-09).
"""
from __future__ import annotations

import json
import re
from typing import List, Optional
from urllib.parse import urlencode

from selectolax.lexbor import LexborHTMLParser

from adapters.base import Adapter
from model import Offer
from plan import add_vat

BASE = "https://store.comet.bg"
SEARCH_PAGE = BASE + "/Search/"
AJAX = BASE + "/ajax/get_result_listing.php"
_PRICE_EUR = re.compile(r"([\d]+(?:\.\d+)?)\s*EUR")
_INT = re.compile(r"\d+")


def _price_breaks(cell) -> List[tuple]:
    """[(min_qty, net_eur), …] from the nested price table."""
    out = []
    for tr in cell.css("tr"):
        tds = tr.css("td")
        if len(tds) < 2:
            continue
        qty_m = _INT.search(tds[0].text())
        price_m = _PRICE_EUR.search(tds[-1].text())
        if qty_m and price_m:
            out.append((int(qty_m.group()), float(price_m.group(1))))
    return out


def pick_break(breaks: List[tuple], qty: int) -> Optional[float]:
    """Price for the largest break whose min qty <= qty; the first break if qty is below all."""
    if not breaks:
        return None
    eligible = [p for q, p in breaks if q <= qty]
    return eligible[-1] if eligible else breaks[0][1]


def parse_listing(content_html: str, need_id: str, qty: int, adapter: "CometAdapter") -> List[Offer]:
    doc = LexborHTMLParser(content_html)
    offers: List[Offer] = []
    for row in doc.css("table.search_result_list > tbody > tr"):
        a = row.css_first("td.p-name a")
        if a is None:
            continue
        href = a.attributes.get("href", "")
        url = href if href.startswith("http") else BASE + href
        desc = row.css_first("td.p-desc")
        manu = row.css_first("td.p-manu")
        title = a.text(strip=True)
        if desc is not None and desc.text(strip=True):
            title += " — " + desc.text(strip=True)
        if manu is not None and manu.text(strip=True):
            title += f" ({manu.text(strip=True)})"
        stock = 0
        for s in row.css("td.p-stock"):
            m = _INT.search(s.text())
            if m:
                stock += int(m.group())
        price_cell = row.css_first("td.price")
        net = pick_break(_price_breaks(price_cell), qty) if price_cell is not None else None
        offers.append(adapter.offer(
            need_id, title, url,
            add_vat(net) if net is not None else None,
            vat_added_by_code=net is not None,
            stock=stock, in_stock=stock > 0,
            confidence="high" if net is not None else "low",
        ))
    return offers


def parse_response(text: str, need_id: str, qty: int, adapter: "CometAdapter") -> List[Offer]:
    data = json.loads(text.lstrip("\ufeff"))
    listing = data.get("listing") or {}
    if not listing.get("total"):
        return []
    return parse_listing(listing.get("content") or "", need_id, qty, adapter)


class CometAdapter(Adapter):
    name = "comet"
    kind = "html"
    quotes_net = True

    def search(self, query: str, need_id: str = "", qty: int = 1) -> List[Offer]:
        assert self.http is not None
        form = {"language": "bg", "keywords": query, "manufacturer_id": "", "package": "",
                "page": "", "sort": "", "items_per_page": "20", "show_prices": "3", "log_stats": "0"}
        r = self.http.post(
            AJAX, data=form, check_robots=True,
            headers={"X-Requested-With": "XMLHttpRequest",
                     "Referer": f"{SEARCH_PAGE}?{urlencode({'keywords': query})}"},
            cookies={"settings_currency": "EUR", "settings_show_prices": "3"},
        )
        return parse_response(r.text, need_id, qty, self)
