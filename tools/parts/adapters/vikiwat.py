"""Vikiwat (vikiwat.com) — html adapter.

SOURCE (fetched 2026-10-09): header form  GET /search.html?phrase=…  returns server-rendered rows
<form class="product-info-row"> with  a.product-name (title + href),  .product-code,
.product-prices .price-value ("€ 1.05", <del> = old list price), .in-stock ("Наличен онлайн 3308 бр."),
.availability-item.out-of-stock / .quantity ("0 бр.", Plovdiv shop).
Prices are shown **with tax** (div.price-withtax) -> no VAT added.
robots.txt: "User-agent: * / Disallow:" (everything allowed, checked 2026-10-09).
"""
from __future__ import annotations

import re
from typing import List, Optional

from selectolax.lexbor import LexborHTMLParser

from adapters.base import Adapter
from model import Offer

BASE = "https://vikiwat.com"
SEARCH = BASE + "/search.html"
_EUR = re.compile(r"€\s*([\d]+(?:[.,]\d+)?)")
_INT = re.compile(r"\d+")


def _price(row) -> Optional[float]:
    for node in row.css(".product-prices .price-value"):
        if node.tag == "del":
            continue
        m = _EUR.search(node.text())
        if m:
            return float(m.group(1).replace(",", "."))
    return None


def _stock(row) -> Optional[int]:
    total = None
    for sel in (".in-stock", ".availability-item .quantity"):
        for node in row.css(sel):
            m = _INT.search(node.text())
            if m:
                total = (total or 0) + int(m.group())
    return total


def parse_search(html: str, need_id: str, adapter: "VikiwatAdapter") -> List[Offer]:
    doc = LexborHTMLParser(html)
    offers: List[Offer] = []
    for row in doc.css("form.product-info-row"):
        a = row.css_first("a.product-name")
        if a is None:
            continue
        href = a.attributes.get("href", "")
        url = href if href.startswith("http") else BASE + href
        title = a.text(strip=True)
        code = row.css_first(".product-code")
        if code is not None and code.text(strip=True):
            title += f" [{code.text(strip=True)}]"
        price = _price(row)
        stock = _stock(row)
        out_of_stock = row.css_first(".availability-item.out-of-stock") is not None and not row.css_first(".in-stock")
        in_stock = (stock > 0) if stock is not None else (False if out_of_stock else None)
        offers.append(adapter.offer(
            need_id, title, url, price,
            stock=stock, in_stock=in_stock,
            confidence="high" if price is not None else "low",
        ))
    return offers


class VikiwatAdapter(Adapter):
    name = "vikiwat"
    kind = "html"
    quotes_net = False

    def search(self, query: str, need_id: str = "", qty: int = 1) -> List[Offer]:
        assert self.http is not None
        r = self.http.get(SEARCH, params={"phrase": query}, check_robots=True)
        return parse_search(r.text, need_id, self)
