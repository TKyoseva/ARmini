"""Adapters against saved fixtures — no network (task T4 tests 4, 7, 8)."""
import pytest

from adapters import build_adapters, collect
from adapters.base import BudgetExceeded, Http, RobotsDisallowed, USER_AGENT
from adapters.comet import CometAdapter, parse_response
from adapters.comet import pick_break as comet_break
from adapters.linkonly import LinkOnlyAdapter, supplier_for_url
from adapters.mouser import MouserAdapter, lead_days_from, parse_money
from adapters.tme import TmeAdapter, sign
from adapters.tme import pick_break as tme_break
from adapters.vikiwat import VikiwatAdapter, parse_search
from conftest import fixture
from model import Config, Need, Release
import datetime as dt


# ---------------------------------------------------------------- comet

def test_comet_fixture_parses_offers():
    ad = CometAdapter(default_lead_days=1)
    offers = parse_response(fixture("comet_search_xt60.json"), "N001", qty=8, adapter=ad)
    assert len(offers) == 13
    xt60m = next(o for o in offers if o.title.startswith("XT60-M"))
    assert xt60m.url == "https://store.comet.bg/Catalogue/Product/5144422/"
    assert xt60m.stock == 817 and xt60m.in_stock is True
    # net 0.38 € at the qty-5 break (qty 8) -> gross 0.46 €, VAT added by code
    assert xt60m.price_eur == 0.46 and xt60m.vat_added_by_code is True
    assert xt60m.lead_days == 1 and xt60m.lead_source == "default"
    assert xt60m.confidence == "high" and xt60m.supplier == "comet"
    zero = next(o for o in offers if o.title.startswith("FXT603"))
    assert zero.stock == 0 and zero.in_stock is False and zero.price_eur == 0.31   # 0.26 net


def test_comet_price_break_selection():
    breaks = [(1, 0.46), (5, 0.38), (25, 0.35)]
    assert comet_break(breaks, 1) == 0.46
    assert comet_break(breaks, 8) == 0.38
    assert comet_break(breaks, 100) == 0.35
    assert comet_break([(10, 1.0)], 2) == 1.0        # below every break: first break
    assert comet_break([], 2) is None


def test_comet_empty_result_is_empty_list():
    ad = CometAdapter(default_lead_days=1)
    assert parse_response(fixture("comet_search_empty.json"), "N001", qty=1, adapter=ad) == []
    assert parse_response('{"listing": {}}', "N001", 1, ad) == []


# ---------------------------------------------------------------- vikiwat

def test_vikiwat_fixture_parses_offers():
    ad = VikiwatAdapter(default_lead_days=2)
    offers = parse_search(fixture("vikiwat_search_xt60.html"), "N001", ad)
    assert len(offers) == 5
    f = next(o for o in offers if "XT60-F" in o.title)
    assert f.url == "https://vikiwat.com/konektor-dc-xt60-f-prav-shtepsel-zhenski"
    assert f.price_eur == 1.05 and f.vat_added_by_code is False     # shown with tax
    assert f.stock == 3308 and f.in_stock is True
    assert f.lead_days == 2 and f.confidence == "high"
    oos = next(o for o in offers if "XT60PT-M" in o.title)
    assert oos.in_stock is False and oos.stock == 0 and oos.price_eur == 2.06


def test_vikiwat_empty_result_is_empty_list():
    ad = VikiwatAdapter(default_lead_days=2)
    assert parse_search(fixture("vikiwat_search_empty.html"), "N001", ad) == []
    assert parse_search("<html></html>", "N001", ad) == []


# ---------------------------------------------------------------- link-only

def test_linkonly_returns_null_price_low_confidence_default_lead():
    ad = LinkOnlyAdapter(default_lead_days=5, name="amazon_de")
    assert ad.search("anything") == []
    o = ad.fetch("https://www.amazon.de/dp/B000000", need_id="N002")
    assert o is not None
    assert o.price_eur is None and o.confidence == "low" and o.lead_days == 5
    assert o.supplier == "amazon_de" and o.url == "https://www.amazon.de/dp/B000000"
    assert "check price by hand" in o.title


def test_supplier_for_url():
    assert supplier_for_url("https://www.amazon.de/dp/x") == "amazon_de"
    assert supplier_for_url("https://www.bauhaus.bg/x") == "bauhaus"
    assert supplier_for_url("https://3dcolour.bg/x") == "3dcolour"
    assert supplier_for_url("https://example.com/x") is None


# ---------------------------------------------------------------- tme

def test_tme_signature_is_deterministic_hmac_sha1_base64():
    url = "https://api.tme.eu/Products/Search.json"
    params = {"Token": "tok", "Country": "BG", "Language": "EN", "SearchPlain": "M4x16 DIN 912"}
    sig = sign(url, params, "secret")
    assert sig == sign(url, dict(reversed(list(params.items()))), "secret")   # order-independent
    assert sig != sign(url, params, "other")
    assert len(sig) == 28 and sig.endswith("=")                                # base64 of 20 bytes
    # fixed vector, computed independently with hmac/sha1 over the documented base string
    # "POST&https%3A%2F%2Fapi.tme.eu%2FProducts%2FSearch.json&Country%3DBG%26Language%3DEN%26SearchPlain%3DM4x16%2BDIN%2B912%26Token%3Dtok"
    assert sig == "KKTkWsL/x/HYDu/mUu5xAC6ELtk="


def test_tme_price_break_and_disabled_without_keys(monkeypatch):
    assert tme_break([{"Amount": 1, "PriceValue": "0.5"}, {"Amount": 10, "PriceValue": "0.4"}], 8) == 0.5
    assert tme_break([{"Amount": 1, "PriceValue": "0.5"}, {"Amount": 10, "PriceValue": "0.4"}], 10) == 0.4
    assert tme_break([], 1) is None
    monkeypatch.delenv("TME_TOKEN", raising=False)
    monkeypatch.delenv("TME_SECRET", raising=False)
    assert TmeAdapter(3).enabled() is False
    assert TmeAdapter(3, token="a", secret="b").enabled() is True


# ---------------------------------------------------------------- mouser

def test_mouser_money_and_lead_parsing():
    assert parse_money("0,45 €") == 0.45
    assert parse_money("€0.45") == 0.45
    assert parse_money("1.234,56 €") == 1234.56
    assert parse_money("1,234.56") == 1234.56
    assert parse_money("") is None
    assert lead_days_from("14 Days") == 14 and lead_days_from("2 Weeks") == 14 and lead_days_from("") is None


def test_mouser_parse_adds_vat_and_stock(monkeypatch):
    monkeypatch.delenv("MOUSER_API_KEY", raising=False)
    assert MouserAdapter(4).enabled() is False
    ad = MouserAdapter(4, api_key="k")
    data = {"Errors": [], "SearchResults": {"NumberOfResult": 1, "Parts": [{
        "ManufacturerPartNumber": "XT60PW-M", "Manufacturer": "Amass", "Description": "conn",
        "ProductDetailUrl": "https://eu.mouser.com/x", "Availability": "1,234 In Stock",
        "AvailabilityInStock": "1234", "LeadTime": "14 Days",
        "PriceBreaks": [{"Quantity": 1, "Price": "10,00 €", "Currency": "EUR"}]}]}}
    [o] = ad.parse(data, "N001", qty=1)
    assert o.price_eur == 12.00 and o.vat_added_by_code is True          # net 10.00 -> 12.00
    assert o.stock == 1234 and o.in_stock is True and o.lead_days == 4 and o.lead_source == "default"
    # out of stock: factory lead time + shipping, lead_source page
    data["SearchResults"]["Parts"][0]["AvailabilityInStock"] = "0"
    [o] = ad.parse(data, "N001", qty=1)
    assert o.in_stock is False and o.lead_days == 18 and o.lead_source == "page"
    # non-EUR -> price unknown
    data["SearchResults"]["Parts"][0]["PriceBreaks"][0]["Currency"] = "USD"
    [o] = ad.parse(data, "N001", qty=1)
    assert o.price_eur is None and o.confidence == "low"
    with pytest.raises(RuntimeError, match="Mouser"):
        ad.parse({"Errors": [{"Message": "Invalid API key"}]}, "N001", 1)


# ---------------------------------------------------------------- Http politeness

class FakeResponse:
    def __init__(self, status=200, text=""):
        self.status_code, self.text = status, text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, robots="User-agent: *\nDisallow: /private\n"):
        self.headers = {}
        self.calls = []
        self.robots = robots

    def get(self, url, **kw):
        self.calls.append(("GET", url))
        return FakeResponse(200 if self.robots is not None else 404, self.robots or "")

    def request(self, method, url, **kw):
        self.calls.append((method, url))
        return FakeResponse(200, "ok")


def test_http_sets_user_agent_and_obeys_robots():
    s = FakeSession()
    sleeps = []
    h = Http(session=s, sleep=sleeps.append)
    assert "ARmini" in s.headers["User-Agent"] and USER_AGENT == s.headers["User-Agent"]
    h.get("https://shop.example/search?q=1", check_robots=True)
    with pytest.raises(RobotsDisallowed):
        h.get("https://shop.example/private/x", check_robots=True)
    assert s.calls[0] == ("GET", "https://shop.example/robots.txt")   # fetched once, cached
    assert sum(1 for c in s.calls if c[1].endswith("robots.txt")) == 1


def test_http_rate_limit_and_budget():
    s = FakeSession(robots=None)
    sleeps = []
    h = Http(session=s, sleep=sleeps.append, budget=3)
    h.get("https://a.example/1")
    h.get("https://a.example/2")          # same host within 1 s -> sleeps
    assert len(sleeps) == 1 and 0 < sleeps[0] <= 1.0
    h.get("https://b.example/1")          # other host: no sleep
    assert len(sleeps) == 1
    with pytest.raises(BudgetExceeded):
        h.get("https://b.example/2")
    assert h.used == 3


# ---------------------------------------------------------------- collect

def cfg_two_needs():
    rels = {"r2a": Release("r2a", dt.date(2026, 10, 16))}
    needs = [
        Need(id="N001", what="screws", qty=8, release="r2a", queries={"comet": "винт", "vikiwat": "M4"},
             links=["https://www.amazon.de/dp/B1"]),
        Need(id="N002", what="lipo bag", qty=1, release="r2a", status="ordered", queries={"comet": "x"},
             offers=[{"supplier": "bauhaus", "title": "bag", "url": "https://bauhaus.bg/b", "price_eur": 7.5, "in_stock": True}]),
    ]
    return Config(2, rels, ["comet", "vikiwat", "tme", "mouser", "amazon_de", "bauhaus", "3dcolour"],
                  {"comet": 1, "vikiwat": 2, "tme": 3, "mouser": 4, "amazon_de": 5, "bauhaus": 0, "3dcolour": 1}, needs)


def test_collect_runs_only_needed_adapters_and_records_errors():
    cfg = cfg_two_needs()
    adapters = build_adapters(cfg, http=None)
    seen = []
    adapters["comet"].search = lambda q, need_id="", qty=1: seen.append(("comet", q, need_id, qty)) or []  # type: ignore

    def vik_fail(q, need_id="", qty=1):
        raise ConnectionError("timeout")
    adapters["vikiwat"].search = vik_fail  # type: ignore

    offers, status = collect(cfg, adapters, {"vikiwat": {"fails": 2}}, offline=False)
    assert seen == [("comet", "винт", "N001", 8)]                # N002 is `ordered`: no search
    assert status["vikiwat"]["ok"] is False and status["vikiwat"]["fails"] == 3
    assert "timeout" in status["vikiwat"]["error"]
    assert status["comet"]["fails"] == 0 and status["tme"]["state"] == "disabled"
    # stored amazon link -> link-only offer; manual bauhaus offer is kept for the ordered need
    [amazon] = offers["N001"]
    assert amazon.supplier == "amazon_de" and amazon.price_eur is None and amazon.lead_days == 5
    [bag] = offers["N002"]
    assert bag.supplier == "bauhaus" and bag.price_eur == 7.5 and bag.lead_days == 0 and bag.fetched_at == "manual"


def test_collect_offline_touches_nothing():
    cfg = cfg_two_needs()
    adapters = build_adapters(cfg, http=None)
    offers, status = collect(cfg, adapters, {}, offline=True)
    assert status["comet"]["state"] == "skipped (offline)"
    assert status["amazon_de"]["state"] == "ok"
    assert [o.supplier for o in offers["N001"]] == ["amazon_de"]
