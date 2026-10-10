"""needs.yaml loader + validator (task T4 test 6)."""
import datetime as dt

import pytest
import yaml

from conftest import STARTER_NEEDS
from model import NeedsError, load_needs, parse_config

BASE = """
safety_days: 2
releases:
  - { id: r2a, date: 2026-10-16, goal: "thruster" }
  - { id: r2b, date: 2026-10-19 }
suppliers:
  prefer: [comet, vikiwat, tme]
  default_lead_days: { comet: 1, vikiwat: 2, tme: 3, amazon_de: 5 }
needs:
  - id: N001
    what: screws
    qty: 8
    for: r2a
    queries: { comet: "винт", tme: "M4x16" }
    status: need
"""


def load(text: str):
    return parse_config(yaml.safe_load(text))


def test_starter_file_loads():
    cfg = load_needs(STARTER_NEEDS)
    assert "r2a" in cfg.releases and cfg.releases["r2a"].date == dt.date(2026, 10, 16)
    assert cfg.needs[0].id == "N001" and cfg.needs[0].release == "r2a"
    assert cfg.safety_days == 2
    assert cfg.lead_for("comet") == 1 and cfg.lead_for("unknown") == max(cfg.default_lead_days.values())


def test_valid_config():
    cfg = load(BASE)
    assert cfg.needs[0].qty == 8
    assert cfg.needs[0].queries == {"comet": "винт", "tme": "M4x16"}
    assert cfg.needs[0].ordered is None and cfg.needs[0].eta is None


def test_unknown_release_names_the_need():
    with pytest.raises(NeedsError) as e:
        load(BASE.replace("for: r2a", "for: r9z"))
    assert "N001" in str(e.value) and "r9z" in str(e.value)


def test_duplicate_need_id():
    text = BASE + "  - { id: N001, what: dup, qty: 1, for: r2b }\n"
    with pytest.raises(NeedsError, match="N001.*duplicate"):
        load(text)


def test_missing_for():
    with pytest.raises(NeedsError, match="N001.*missing `for`"):
        load(BASE.replace("    for: r2a\n", ""))


def test_bad_status_and_qty():
    with pytest.raises(NeedsError, match="status"):
        load(BASE.replace("status: need", "status: maybe"))
    with pytest.raises(NeedsError, match="qty"):
        load(BASE.replace("qty: 8", "qty: 0"))


def test_bad_date():
    with pytest.raises(NeedsError, match="bad date"):
        load(BASE.replace("2026-10-16", "16.10.2026"))


def test_query_for_unknown_supplier():
    with pytest.raises(NeedsError, match="unknown supplier"):
        load(BASE.replace('tme: "M4x16"', 'ebay: "M4x16"'))


def test_prefer_without_lead_days():
    with pytest.raises(NeedsError, match="prefer"):
        load(BASE.replace("prefer: [comet, vikiwat, tme]", "prefer: [comet, mouser]"))


def test_no_releases():
    with pytest.raises(NeedsError, match="releases"):
        load("safety_days: 2\nreleases: []\nneeds: []\n")


def test_skip_needs_are_loaded_but_not_searched():
    """status: skip -> no adapter call, still present for the report."""
    from adapters import build_adapters, collect

    cfg = load(BASE.replace("status: need", "status: skip"))
    adapters = build_adapters(cfg, http=None)
    calls = []
    adapters["comet"].search = lambda q, need_id="", qty=1: calls.append(q) or []   # type: ignore
    offers, status = collect(cfg, adapters, {}, offline=False)
    assert calls == []
    assert list(offers) == ["N001"] and offers["N001"] == []
    assert status["comet"]["state"] == "ok"
