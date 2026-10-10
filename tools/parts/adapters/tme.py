"""TME (tme.eu) — API adapter.

SOURCE: TME developer docs https://developers.tme.eu (actions Products/Search, Products/GetPrices,
Products/GetStocks). Every call is a POST of form fields + `Token` + `ApiSignature`, where
  signature_base = "POST&" + quote(url) + "&" + quote(urlencode(sorted(params)))
  ApiSignature   = base64(HMAC-SHA1(app_secret, signature_base))
VERIFY: Teddy — signing is written from the docs and self-tested only; the first live run with
TME_TOKEN/TME_SECRET set confirms it (an E_AUTHORIZATION error means the signature is wrong).
Prices: GetPrices returns PriceType NET for business accounts -> code adds 20 % VAT.
Disabled (not an error) when TME_TOKEN or TME_SECRET is missing. Budget: 3 requests per query.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode

from adapters.base import Adapter
from model import Offer
from plan import add_vat

API = "https://api.tme.eu"
MAX_SYMBOLS = 10


def sign(url: str, params: Dict[str, Any], secret: str) -> str:
    """ApiSignature for one call. Pure, so it is unit-tested against a fixed vector."""
    encoded = urlencode(sorted(params.items()), safe="")
    base = "POST&" + quote(url, safe="") + "&" + quote(encoded, safe="")
    digest = hmac.new(secret.encode("utf-8"), base.encode("utf-8"), hashlib.sha1).digest()
    return base64.b64encode(digest).decode("ascii")


def pick_break(price_list: List[Dict[str, Any]], qty: int) -> Optional[float]:
    """PriceList = [{Amount, PriceValue}, …]: largest Amount <= qty, else the smallest break."""
    breaks = sorted((int(p["Amount"]), float(p["PriceValue"])) for p in price_list
                    if p.get("Amount") is not None and p.get("PriceValue") is not None)
    if not breaks:
        return None
    eligible = [v for a, v in breaks if a <= qty]
    return eligible[-1] if eligible else breaks[0][1]


class TmeAdapter(Adapter):
    name = "tme"
    kind = "api"
    quotes_net = True

    def __init__(self, default_lead_days: int, token: Optional[str] = None,
                 secret: Optional[str] = None, **kw):
        super().__init__(default_lead_days, **kw)
        self.token = token if token is not None else os.environ.get("TME_TOKEN", "")
        self.secret = secret if secret is not None else os.environ.get("TME_SECRET", "")

    def enabled(self) -> bool:
        return bool(self.token and self.secret)

    def disabled_reason(self) -> str:
        return "TME_TOKEN / TME_SECRET not set"

    def _call(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        assert self.http is not None
        url = f"{API}/{action}.json"
        p = {"Token": self.token, "Country": "BG", "Language": "EN", **params}
        p["ApiSignature"] = sign(url, p, self.secret)
        r = self.http.post(url, data=p)
        data = r.json()
        if data.get("Status") != "OK":
            raise RuntimeError(f"TME {action}: {data.get('Status')} {data.get('Error', '')}")
        return data.get("Data") or {}

    def search(self, query: str, need_id: str = "", qty: int = 1) -> List[Offer]:
        found = self._call("Products/Search", {"SearchPlain": query}).get("ProductList") or []
        found = found[:MAX_SYMBOLS]
        if not found:
            return []
        symbols = [p["Symbol"] for p in found]
        sym_params = {f"SymbolList[{i}]": s for i, s in enumerate(symbols)}
        prices = self._call("Products/GetPrices", {"Currency": "EUR", **sym_params})
        stocks = self._call("Products/GetStocks", sym_params)
        net = prices.get("PriceType", "NET").upper() == "NET"
        currency = prices.get("Currency", "EUR")
        price_by = {p["Symbol"]: p.get("PriceList") or [] for p in prices.get("ProductList") or []}
        stock_by = {s["Symbol"]: s.get("Amount") for s in stocks.get("ProductList") or []}

        offers: List[Offer] = []
        for p in found:
            sym = p["Symbol"]
            raw = pick_break(price_by.get(sym, []), qty)
            price = None
            if raw is not None and currency == "EUR":
                price = add_vat(raw) if net else round(raw, 2)
            page = p.get("ProductInformationPage") or ""
            url = ("https:" + page) if page.startswith("//") else (page or f"https://www.tme.eu/en/details/{sym}/")
            stock = stock_by.get(sym)
            stock = int(stock) if stock is not None else None
            offers.append(self.offer(
                need_id, f"{sym} {p.get('Description', '')} ({p.get('Producer', '')})", url, price,
                vat_added_by_code=bool(price is not None and net),
                stock=stock, in_stock=(stock > 0) if stock is not None else None,
                confidence="high" if price is not None else "low",
            ))
        return offers
