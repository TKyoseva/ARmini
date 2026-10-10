"""Mouser — Search API adapter.

SOURCE: https://api.mouser.com/api/docs/ui/index  (POST /api/v1/search/keyword?apiKey=…
body {"SearchByKeywordRequest": {"keyword", "records", "startingRecord"}}). Parts come back in
SearchResults.Parts[] with ManufacturerPartNumber, Description, ProductDetailUrl, Availability
("1,234 In Stock"), AvailabilityInStock, LeadTime ("14 Days"), PriceBreaks[{Quantity, Price, Currency}].
Price strings look like "0,45 €" or "€0.45"; both are parsed. Non-EUR -> price null, confidence low.
VERIFY: Teddy — business/EU account prices are net -> code adds 20 % VAT (vat_added_by_code).
Disabled (not an error) when MOUSER_API_KEY is missing. Budget: 1 request per query.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from adapters.base import Adapter
from model import Offer
from plan import add_vat

API = "https://api.mouser.com/api/v1/search/keyword"
RECORDS = 10
_NUM = re.compile(r"[\d.,]+")
_DAYS = re.compile(r"(\d+)\s*day", re.I)
_WEEKS = re.compile(r"(\d+)\s*week", re.I)


def parse_money(text: Optional[str]) -> Optional[float]:
    """'0,45 €' / '€0.45' / '1.234,56 €' / '1,234.56' -> float."""
    if not text:
        return None
    m = _NUM.search(text)
    if not m:
        return None
    s = m.group()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if len(s.split(",")[-1]) != 3 else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_int(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = _NUM.search(text)
    if not m:
        return None
    try:
        return int(m.group().replace(",", "").replace(".", ""))
    except ValueError:
        return None


def lead_days_from(text: Optional[str]) -> Optional[int]:
    """'14 Days' -> 14, '2 Weeks' -> 14, else None (factory lead; shipping is added by caller)."""
    if not text:
        return None
    m = _DAYS.search(text)
    if m:
        return int(m.group(1))
    m = _WEEKS.search(text)
    if m:
        return int(m.group(1)) * 7
    return None


def pick_break(breaks: List[Dict[str, Any]], qty: int) -> Optional[Dict[str, Any]]:
    rows = sorted((b for b in breaks if b.get("Quantity") is not None), key=lambda b: int(b["Quantity"]))
    if not rows:
        return None
    eligible = [b for b in rows if int(b["Quantity"]) <= qty]
    return eligible[-1] if eligible else rows[0]


class MouserAdapter(Adapter):
    name = "mouser"
    kind = "api"
    quotes_net = True

    def __init__(self, default_lead_days: int, api_key: Optional[str] = None, **kw):
        super().__init__(default_lead_days, **kw)
        self.api_key = api_key if api_key is not None else os.environ.get("MOUSER_API_KEY", "")

    def enabled(self) -> bool:
        return bool(self.api_key)

    def disabled_reason(self) -> str:
        return "MOUSER_API_KEY not set"

    def parse(self, data: Dict[str, Any], need_id: str, qty: int) -> List[Offer]:
        errors = data.get("Errors") or []
        if errors:
            raise RuntimeError("Mouser: " + "; ".join(str(e.get("Message", e)) for e in errors))
        offers: List[Offer] = []
        for part in (data.get("SearchResults") or {}).get("Parts") or []:
            brk = pick_break(part.get("PriceBreaks") or [], qty)
            price = None
            vat = False
            if brk and (brk.get("Currency") or "EUR").upper() == "EUR":
                raw = parse_money(brk.get("Price"))
                if raw is not None:
                    price, vat = add_vat(raw), True
            stock = parse_int(part.get("AvailabilityInStock") or part.get("Availability"))
            factory = lead_days_from(part.get("LeadTime"))
            lead = self.default_lead_days
            src = "default"
            if stock == 0 and factory:
                lead, src = factory + self.default_lead_days, "page"
            title = f"{part.get('ManufacturerPartNumber', '')} {part.get('Description', '')} ({part.get('Manufacturer', '')})"
            offers.append(self.offer(
                need_id, title, part.get("ProductDetailUrl") or "https://www.mouser.com/", price,
                vat_added_by_code=vat, stock=stock, in_stock=(stock > 0) if stock is not None else None,
                lead_days=lead, lead_source=src,
                confidence="high" if price is not None else "low",
            ))
        return offers

    def search(self, query: str, need_id: str = "", qty: int = 1) -> List[Offer]:
        assert self.http is not None
        body = {"SearchByKeywordRequest": {"keyword": query, "records": RECORDS, "startingRecord": 0}}
        r = self.http.post(API, params={"apiKey": self.api_key}, json=body)
        return self.parse(r.json(), need_id, qty)
