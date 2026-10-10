"""Pure planning rules (task T4 tests 1–5)."""
import datetime as dt

from model import Config, Need, Offer, Release
from plan import add_vat, best_offer, diff, order_by, plan_need, record_alerts, slack_days

D = dt.date
PREFER = ["comet", "vikiwat", "tme", "mouser", "amazon_de"]


def offer(supplier="comet", price=1.0, in_stock=True, lead=1, url=None, **kw) -> Offer:
    return Offer(need_id="N001", supplier=supplier, title=f"{supplier} part", url=url or f"https://{supplier}/x",
                 price_eur=price, lead_days=lead, in_stock=in_stock, **kw)


def config(needs=None, releases=None, safety=2) -> Config:
    rels = releases or {"r2a": Release("r2a", D(2026, 10, 16)), "r2b": Release("r2b", D(2026, 10, 19))}
    return Config(safety_days=safety, releases=rels, prefer=PREFER,
                  default_lead_days={"comet": 1, "vikiwat": 2, "tme": 3, "mouser": 4, "amazon_de": 5},
                  needs=needs or [])


# 1. order_by -------------------------------------------------------------

def test_order_by_spec_case_16_oct_lead_3_safety_2():
    # Task T4 test 1: 16 Oct 2026 release, lead 3, safety 2 -> 11 Oct -> Fri 9 Oct.
    # (The task calls 11 Oct 2026 a Saturday; it is a Sunday. Either way the weekend rule gives Fri 9 Oct.)
    assert D(2026, 10, 11).weekday() == 6
    assert order_by(D(2026, 10, 16), 3, 2) == D(2026, 10, 9)


def test_order_by_moves_saturday_to_friday():
    # release Thu 15 Oct, lead 3, safety 2 -> Sat 10 Oct -> Fri 9 Oct
    assert D(2026, 10, 10).weekday() == 5
    assert order_by(D(2026, 10, 15), 3, 2) == D(2026, 10, 9)


def test_order_by_moves_sunday_to_friday():
    # release Tue 20 Oct, lead 2, safety 0 -> Sun 18 Oct -> Fri 16 Oct
    assert D(2026, 10, 18).weekday() == 6
    assert order_by(D(2026, 10, 20), 2, 0) == D(2026, 10, 16)


def test_order_by_weekday_unchanged():
    assert order_by(D(2026, 10, 16), 1, 2) == D(2026, 10, 13)   # Tuesday


# 2. slack ----------------------------------------------------------------

def test_slack_negative_in_the_past():
    assert slack_days(D(2026, 10, 9), D(2026, 10, 12)) == -3
    assert slack_days(D(2026, 10, 12), D(2026, 10, 9)) == 3
    assert slack_days(D(2026, 10, 9), D(2026, 10, 9)) == 0


# 3. best_offer -----------------------------------------------------------

TODAY = D(2026, 10, 9)
REL = D(2026, 10, 16)


def test_best_excludes_out_of_stock():
    cheap_oos = offer("comet", 0.5, in_stock=False)
    ok = offer("vikiwat", 1.0)
    assert best_offer([cheap_oos, ok], REL, TODAY, PREFER) is ok


def test_best_excludes_arrives_too_late():
    late = offer("mouser", 0.5, lead=8)     # 9 + 8 = 17 Oct > 16 Oct
    ok = offer("comet", 1.0, lead=1)
    assert best_offer([late, ok], REL, TODAY, PREFER) is ok
    exact = offer("tme", 0.4, lead=7)       # arrives exactly on release day: allowed
    assert best_offer([late, ok, exact], REL, TODAY, PREFER) is exact


def test_best_cheapest_wins():
    a, b = offer("comet", 2.0), offer("vikiwat", 1.5)
    assert best_offer([a, b], REL, TODAY, PREFER) is b


def test_best_null_price_loses_to_priced():
    unknown = offer("amazon_de", None, in_stock=None, lead=5)
    priced = offer("tme", 9.0, lead=3)
    assert best_offer([unknown, priced], REL, TODAY, PREFER) is priced
    assert best_offer([unknown], REL, TODAY, PREFER) is unknown


def test_best_tie_broken_by_supplier_preference():
    v = offer("vikiwat", 1.0, lead=2)
    c = offer("comet", 1.0, lead=1)
    assert best_offer([v, c], REL, TODAY, PREFER) is c
    assert best_offer([c, v], REL, TODAY, PREFER) is c


def test_best_none_when_nothing_qualifies():
    assert best_offer([], REL, TODAY, PREFER) is None
    assert best_offer([offer(in_stock=False)], REL, TODAY, PREFER) is None


# 4. VAT -------------------------------------------------------------------

def test_vat_net_to_gross():
    assert add_vat(10.00) == 12.00
    assert add_vat(0.38) == 0.46


# plan_need: lead for a need without offers = slowest supplier it could use ---

def test_plan_need_without_offers_uses_slowest_candidate_supplier():
    need = Need(id="N001", what="x", qty=8, release="r2a", queries={"comet": "a", "vikiwat": "b", "tme": "c"})
    line = plan_need(config([need]), need, [], TODAY)
    assert line.best is None
    assert line.order_by == D(2026, 10, 9)     # lead 3 (tme) + safety 2 -> Sat 11 -> Fri 9
    assert line.slack_days == 0


# 5. diff ------------------------------------------------------------------

def need_state(best=None, offers=None, slack=10, status="need", order_by_="2026-10-19", alerted=None, eta=None):
    return {"status": status, "release": "r2a", "release_date": "2026-10-16", "eta": eta,
            "order_by": order_by_, "slack_days": slack,
            "best": best.to_dict() if best else None,
            "offers": [o.to_dict() for o in (offers if offers is not None else ([best] if best else []))],
            "alerted": alerted or {}}


def state(need_entry, adapters=None, alerted=None):
    return {"needs": {"N001": need_entry}, "adapters": adapters or {}, "alerted": alerted or {}}


def kinds(alerts):
    return sorted(a.kind for a in alerts)


def cfg_with(status="need", eta=None, release="r2a"):
    return config([Need(id="N001", what="screws", qty=8, release=release, status=status, eta=eta,
                        queries={"comet": "q"})])


def test_new_best_first_offer_and_supplier_change():
    c = cfg_with()
    assert kinds(diff(state(need_state()), state(need_state(best=offer("comet"))), c, TODAY)) == ["NEW_BEST"]
    assert kinds(diff(state(need_state(best=offer("comet"))), state(need_state(best=offer("vikiwat"))), c, TODAY)) == ["NEW_BEST"]
    # same supplier, same price -> nothing
    assert kinds(diff(state(need_state(best=offer("comet"))), state(need_state(best=offer("comet"))), c, TODAY)) == []


def test_price_alert_over_10_percent_only():
    c = cfg_with()
    old = state(need_state(best=offer("comet", 1.00)))
    assert kinds(diff(old, state(need_state(best=offer("comet", 1.15))), c, TODAY)) == ["PRICE"]
    assert kinds(diff(old, state(need_state(best=offer("comet", 0.85))), c, TODAY)) == ["PRICE"]
    assert kinds(diff(old, state(need_state(best=offer("comet", 1.09))), c, TODAY)) == []


def test_out_of_stock_alert():
    c = cfg_with()
    was = offer("comet", 1.0, url="https://comet/a")
    old = state(need_state(best=was))
    gone = offer("comet", 1.0, in_stock=False, url="https://comet/a")
    other = offer("vikiwat", 2.0)
    new = state(need_state(best=other, offers=[gone, other]))
    assert kinds(diff(old, new, c, TODAY)) == ["NEW_BEST", "OUT_OF_STOCK"]
    # still in stock -> no alert
    assert kinds(diff(old, state(need_state(best=was, offers=[was])), c, TODAY)) == []


def test_order_soon_once_per_day():
    c = cfg_with()
    soon = need_state(slack=3, order_by_="2026-10-12")
    first = diff(state(need_state(slack=10)), state(soon), c, TODAY)
    assert kinds(first) == ["ORDER_SOON"]
    # second run the same day: old state carries today's alerted date -> silent
    new_state = state(dict(soon))
    record_alerts(new_state, first, TODAY)
    assert kinds(diff(new_state, state(soon), c, TODAY)) == []
    # next day it fires again
    assert kinds(diff(new_state, state(soon), c, TODAY + dt.timedelta(days=1))) == ["ORDER_SOON"]
    # slack 4 -> not soon
    assert kinds(diff(state(need_state(slack=10)), state(need_state(slack=4)), c, TODAY)) == []


def test_overdue_once_per_day_and_only_for_status_need():
    c = cfg_with()
    late = need_state(slack=-1, order_by_="2026-10-08")
    first = diff(state(need_state(slack=0)), state(late), c, TODAY)
    assert kinds(first) == ["OVERDUE"]
    new_state = state(dict(late))
    record_alerts(new_state, first, TODAY)
    assert kinds(diff(new_state, state(late), c, TODAY)) == []
    # ordered needs are never OVERDUE (they get ETA_LATE instead)
    c2 = cfg_with(status="ordered", eta=D(2026, 10, 12))
    assert kinds(diff(state(need_state(slack=0)), state(need_state(slack=-1, status="ordered")), c2, TODAY)) == []


def test_eta_late():
    rel = D(2026, 10, 16)
    ok = cfg_with(status="ordered", eta=rel - dt.timedelta(days=1))
    assert kinds(diff(state(need_state(status="ordered")), state(need_state(status="ordered")), ok, TODAY)) == []
    late = cfg_with(status="ordered", eta=rel)
    assert kinds(diff(state(need_state(status="ordered")), state(need_state(status="ordered")), late, TODAY)) == ["ETA_LATE"]
    unknown = cfg_with(status="ordered", eta=None)
    assert kinds(diff(state(need_state(status="ordered")), state(need_state(status="ordered")), unknown, TODAY)) == ["ETA_LATE"]


def test_release_at_risk():
    c = cfg_with()
    far = D(2026, 10, 9)
    assert "RELEASE_AT_RISK" not in kinds(diff(state(need_state()), state(need_state()), c, far))
    close = D(2026, 10, 14)        # 2 days before r2a
    alerts = diff(state(need_state()), state(need_state()), c, close)
    assert "RELEASE_AT_RISK" in kinds(alerts)
    # once per day
    new_state = state(need_state())
    record_alerts(new_state, alerts, close)
    assert "RELEASE_AT_RISK" not in kinds(diff(new_state, state(need_state()), c, close))
    # all received -> no risk
    c_done = cfg_with(status="received")
    assert kinds(diff(state(need_state(status="received")), state(need_state(status="received")), c_done, close)) == []


def test_adapter_down_after_three_fails_once_per_day():
    c = cfg_with()
    two = state(need_state(), adapters={"comet": {"fails": 2, "error": "boom"}})
    three = state(need_state(), adapters={"comet": {"fails": 3, "error": "boom"}})
    assert kinds(diff(state(need_state()), two, c, TODAY)) == []
    alerts = diff(state(need_state()), three, c, TODAY)
    assert kinds(alerts) == ["ADAPTER_DOWN"]
    record_alerts(three, alerts, TODAY)
    assert kinds(diff(three, state(need_state(), adapters={"comet": {"fails": 4}}), c, TODAY)) == []


def test_skip_needs_never_alert():
    c = cfg_with(status="skip")
    assert diff(state(need_state(slack=-5, status="skip")), state(need_state(slack=-5, status="skip", best=offer())), c, TODAY) == []
