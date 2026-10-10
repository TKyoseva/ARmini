"""Watch lists (task T6). No network: parsers read fixtures, the agent runs --offline."""
import datetime as dt
import json
import os

import agent
import watch
from adapters.base import BudgetExceeded, Http
from adapters.bluerobotics import parse_payload as blue_parse
from adapters.hydromea import parse_hydromea
from adapters.linkonly import supplier_for_url
from adapters.rc_terminal import parse_payload as rc_parse
from adapters.robotshop_eu import RobotshopEuAdapter, parse_payload as robot_parse
from conftest import PARTS, STARTER_NEEDS, fixture
from plan import Alert
from report import render_telegram
from watch import (
    IMPORT_VAT_NOTE,
    WatchItem,
    WatchOffer,
    diff_watch,
    filter_discovery,
    format_price,
    load_watch,
    next_ids,
    rank_items,
    thrust_per_gram,
    watch_ceiling,
    wow_score,
)

TODAY = dt.date(2026, 10, 10)
WATCH = os.path.join(PARTS, "..", "..", "parts", "watch.yaml")


def _offer(**kw) -> WatchOffer:
    base = dict(shop="s", url="https://shop.example/p", price=100.0, currency="USD")
    base.update(kw)
    return WatchOffer(**base)


# ---------------------------------------------------------------- loader, wow, rank

def test_seeded_watch_yaml_loads_and_ranks_w003_w001_w002_w004():
    cfg = load_watch(WATCH)
    lst = cfg.lists[0]
    by_id = {it.id: it for it in lst.items}
    assert [it.id for it in lst.items] == ["W001", "W002", "W003", "W004"]
    assert wow_score(by_id["W003"], lst.wow_points) == 5
    assert wow_score(by_id["W001"], lst.wow_points) == 3
    assert wow_score(by_id["W002"], lst.wow_points) == 3
    assert wow_score(by_id["W004"], lst.wow_points) == 0
    assert round(thrust_per_gram(by_id["W001"]), 1) == 12.0
    assert round(thrust_per_gram(by_id["W002"]), 1) == 10.8
    assert thrust_per_gram(by_id["W003"]) is None
    assert [it.id for it in rank_items(lst.items, lst.wow_points, cfg.fx_to_eur)] == [
        "W003", "W001", "W002", "W004"]


def test_duplicate_item_id_and_unknown_feature_name_the_offender(tmp_path):
    dup = tmp_path / "dup.yaml"
    dup.write_text(
        "fx_to_eur: {USD: null}\n"
        "lists:\n"
        "  - id: t\n"
        "    title: T\n"
        "    wow_points: {rim_driven: 3}\n"
        "    items:\n"
        "      - {id: W001, name: a, features: [rim_driven]}\n"
        "      - {id: W001, name: b, features: []}\n",
        encoding="utf-8")
    try:
        load_watch(str(dup))
        raise AssertionError("duplicate id should fail")
    except watch.WatchError as e:
        assert "W001" in str(e) and "duplicate" in str(e)

    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "fx_to_eur: {USD: null}\n"
        "lists:\n"
        "  - id: t\n"
        "    title: T\n"
        "    wow_points: {rim_driven: 3}\n"
        "    items:\n"
        "      - {id: W009, name: a, features: [nope]}\n",
        encoding="utf-8")
    try:
        load_watch(str(bad))
        raise AssertionError("unknown feature should fail")
    except watch.WatchError as e:
        assert "W009" in str(e) and "nope" in str(e)


def test_guessed_features_do_not_change_wow_until_confirmed():
    points = {"rim_driven": 3, "waterjet": 3}
    item = WatchItem(id="W005", name="Rim thing", features=[], features_guessed=["rim_driven"])
    assert wow_score(item, points) == 0
    item.features = ["rim_driven"]
    assert wow_score(item, points) == 3


# ---------------------------------------------------------------- discovery

def test_discovery_filter_keeps_thrusters_and_drops_parts_and_known_urls():
    exclude = ["propeller", "prop set", "thrust kit", "duct", "penetrator", "cable",
               "magnet ring", "seal", "impeller", "speed controller", "esc"]
    known = ["https://eu.robotshop.com/products/t200"]
    kept = filter_discovery([
        {"title": "T200 Thruster", "url": "https://example.com/t200"},
        {"title": "T200 Propeller Set", "url": "https://example.com/prop"},
        {"title": "DISKDRIVE 50 Duct", "url": "https://example.com/duct"},
        {"title": "T200 Thruster", "url": known[0] + "?variant=9"},
        {"title": "Rim Driven Thruster RDT-60", "url": "https://example.com/rdt"},
    ], exclude, known)
    assert [c["title"] for c in kept] == ["T200 Thruster", "Rim Driven Thruster RDT-60"]
    assert kept[0]["features_guessed"] == []
    assert kept[1]["features_guessed"] == ["rim_driven"]


def test_category_fixture_discovery_keeps_diskdrive_and_drops_the_parts():
    products = parse_hydromea(fixture("hydromea_category.html"))
    exclude = load_watch(WATCH).lists[0].exclude_words
    known = [o.url for it in load_watch(WATCH).lists[0].items for o in it.offers]
    kept = filter_discovery(
        [{"title": p.title, "url": p.url} for p in products], exclude, known)
    assert [c["title"] for c in kept] == ["DISKDRIVE™ 50"]
    assert kept[0]["features_guessed"] == []
    assert next_ids(["W001", "W004"], 1) == ["W005"]


# ---------------------------------------------------------------- currency

def test_currency_null_rate_is_question_mark_and_rate_multiplies_and_import_vat_is_a_note():
    plain = _offer(price=100, currency="USD")
    assert format_price(plain, {"USD": None}) == "100.00 USD → ?"
    assert format_price(plain, {"USD": 0.9}) == "100.00 USD → 90.00 EUR"
    noted = _offer(price=100, currency="USD", vat_included=False, imports=True)
    text = format_price(noted, {"USD": None})
    assert "100.00 USD → ?" in text and "+ import VAT 20 %" in text
    assert IMPORT_VAT_NOTE in text


# ---------------------------------------------------------------- adapters

def test_hydromea_product_and_category_fixtures_and_empty():
    [kit] = parse_hydromea(fixture("hydromea_product.html"))
    assert "Thrust Kit" in kit.title
    assert kit.price == 80 and kit.currency == "USD" and kit.in_stock is True
    assert kit.url.endswith("/product-page/diskdrive-50-thrust-kit")

    found = parse_hydromea(fixture("hydromea_category.html"))
    assert len(found) == 5
    disk = next(p for p in found if p.title == "DISKDRIVE™ 50")
    assert disk.price == 649 and disk.currency == "USD" and disk.in_stock is None

    assert parse_hydromea(fixture("hydromea_empty.html")) == []
    assert parse_hydromea("") == []
    assert parse_hydromea("not html") == []


def test_link_only_adapters_parse_empty_fixtures_without_raising():
    assert robot_parse(fixture("robotshop_empty.json")) == []
    assert blue_parse(fixture("bluerobotics_empty.json")) == []
    assert rc_parse(fixture("rc_terminal_empty.html")) == []
    ad = RobotshopEuAdapter(0)
    assert ad.kind == "link"
    assert ad.discover("underwater thruster") == []
    assert ad.refresh("https://eu.robotshop.com/products/x") == []
    assert supplier_for_url("https://www.ebay.de/itm/227045572886") == "ebay_de"
    assert supplier_for_url("https://vxb.com/products/u2") == "vxb"


# ---------------------------------------------------------------- alerts

def _lists(top, items, discovered=()):
    return {"thruster_v2": {"top": top, "items": items, "discovered_ids": list(discovered)}}


def test_watch_new_price_stock_top_positive_negative_and_once_per_day():
    today = TODAY
    # WATCH_NEW
    old = {"alerted": {}, "lists": _lists("W003", {}, [])}
    new = _lists("W003", {}, ["W005"])
    kinds = [a.kind for a in diff_watch(old, new, today)]
    assert kinds == ["WATCH_NEW"]
    assert diff_watch(old, _lists("W003", {}, []), today) == []
    old["alerted"] = {"WATCH_NEW:W005": today.isoformat()}
    assert diff_watch(old, new, today) == []

    # WATCH_PRICE — more than 10%; exactly 10% does not fire
    old = {"alerted": {}, "lists": _lists("W003", {"W002": {"price": 100, "currency": "EUR", "eur": 100, "in_stock": True}})}
    moved = _lists("W003", {"W002": {"price": 120, "currency": "EUR", "eur": 120, "in_stock": True}})
    assert [a.kind for a in diff_watch(old, moved, today)] == ["WATCH_PRICE"]
    same = _lists("W003", {"W002": {"price": 110, "currency": "EUR", "eur": 110, "in_stock": True}})
    assert diff_watch(old, same, today) == []
    # stored USD with no EUR rate still compares in USD
    old_usd = {"alerted": {}, "lists": _lists("W003", {"W001": {"price": 649, "currency": "USD", "eur": None, "in_stock": None}})}
    usd = _lists("W003", {"W001": {"price": 800, "currency": "USD", "eur": None, "in_stock": None}})
    assert [a.kind for a in diff_watch(old_usd, usd, today)] == ["WATCH_PRICE"]
    old["alerted"] = {"WATCH_PRICE:W002": today.isoformat()}
    assert diff_watch(old, moved, today) == []

    # WATCH_STOCK — bool flip only
    old = {"alerted": {}, "lists": _lists("W003", {"W003": {"price": 439.9, "currency": "EUR", "eur": 439.9, "in_stock": True}})}
    flipped = _lists("W003", {"W003": {"price": 439.9, "currency": "EUR", "eur": 439.9, "in_stock": False}})
    assert [a.kind for a in diff_watch(old, flipped, today)] == ["WATCH_STOCK"]
    assert diff_watch(old, _lists("W003", {"W003": {"price": 439.9, "currency": "EUR", "eur": 439.9, "in_stock": True}}), today) == []
    # null → yes is not a flip
    old_null = {"alerted": {}, "lists": _lists("W003", {"W001": {"price": 1, "currency": "EUR", "eur": 1, "in_stock": None}})}
    assert diff_watch(old_null, _lists("W003", {"W001": {"price": 1, "currency": "EUR", "eur": 1, "in_stock": True}}), today) == []
    old["alerted"] = {"WATCH_STOCK:W003": today.isoformat()}
    assert diff_watch(old, flipped, today) == []

    # WATCH_TOP — a first top is not a change
    old = {"alerted": {}, "lists": _lists("W001", {})}
    assert [a.kind for a in diff_watch(old, _lists("W003", {}), today)] == ["WATCH_TOP"]
    assert diff_watch(old, _lists("W001", {}), today) == []
    assert diff_watch({"alerted": {}, "lists": _lists(None, {})}, _lists("W003", {}), today) == []
    old["alerted"] = {"WATCH_TOP:thruster_v2": today.isoformat()}
    assert diff_watch(old, _lists("W003", {}), today) == []


def test_watch_alerts_are_digest_only():
    alerts = [Alert("WATCH_NEW", "W005", "W005 new")]
    assert render_telegram([], {}, alerts, TODAY, digest=False) == ""
    text = render_telegram([], {}, alerts, TODAY, digest=True)
    assert "WATCH_NEW" in text
    quiet = render_telegram([], {}, [], TODAY, digest=True, watch_error="watch.yaml invalid: broken")
    assert "watch.yaml invalid: broken" in quiet


# ---------------------------------------------------------------- budget and agent

def test_watch_request_ceiling_is_20_inside_the_run_budget():
    assert watch_ceiling(0, 60) == 20
    assert watch_ceiling(50, 60) == 60
    http = Http(budget=60, sleep=lambda _s: None)
    http.cap = watch_ceiling(0, http.budget)
    for _ in range(20):
        http._spend()
    try:
        http._spend()
        raise AssertionError("watch cap should stop the 21st request")
    except BudgetExceeded:
        pass
    assert http.used == 20


def test_watch_runs_only_on_the_first_run_unless_flag(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    calls = []
    real = watch.run_watch

    def wrapped(*a, **k):
        calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(watch, "run_watch", wrapped)
    state = tmp_path / "state.json"
    report = tmp_path / "REPORT.md"
    args = ["--offline", "--needs", STARTER_NEEDS, "--state", str(state), "--report", str(report),
            "--today", "2026-10-10", "--watch-file", WATCH]
    assert agent.run(args) == 0
    assert calls == [1]
    text = report.read_text(encoding="utf-8")
    assert "## Watch · Thrusters for AR-Mini v2" in text
    assert text.find("| 1 | W003 |") < text.find("| 2 | W001 |") < text.find("| 3 | W002 |") < text.find("| 4 | W004 |")
    assert "99.99 USD → ?" in text and "+ import VAT 20 %" in text
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["watch"]["lists"]["thruster_v2"]["top"] == "W003"
    assert saved["watch"]["requests"] == 0

    assert agent.run(args) == 0
    assert calls == [1]          # same day, no --watch: the section is replayed, not refreshed
    assert "## Watch · Thrusters for AR-Mini v2" in report.read_text(encoding="utf-8")

    assert agent.run(args + ["--watch"]) == 0
    assert calls == [1, 1]


def test_broken_watch_yaml_keeps_the_needs_report_and_exit_0(tmp_path, capsys):
    bad = tmp_path / "watch.yaml"
    bad.write_text("lists: [\n", encoding="utf-8")
    rc = agent.run(["--dry-run", "--offline", "--watch", "--needs", STARTER_NEEDS,
                    "--watch-file", str(bad), "--state", str(tmp_path / "missing-state.json"),
                    "--today", "2026-10-10"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "| N001 |" in out
    assert out.count("watch.yaml invalid:") >= 2   # report and the daily digest
    assert "Telegram text that would be sent" in out


def test_offline_dry_run_prints_the_seeded_watch_table(capsys):
    rc = agent.run(["--dry-run", "--offline", "--watch", "--needs", STARTER_NEEDS,
                    "--watch-file", WATCH, "--state", "/nonexistent/state.json", "--today", "2026-10-10"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "## Watch · Thrusters for AR-Mini v2" in out
    assert out.find("| 1 | W003 |") < out.find("| 2 | W001 |") < out.find("| 4 | W004 |")
    assert "link-only" in out and "hydromea html" in out
    assert "requests used: 0" in out
