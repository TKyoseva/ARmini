"""Data model for the AR-Mini parts agent + needs.yaml loader/validator.

Kept deliberately small (see tasks/night/2026-10-09_T4_parts-agent.md):
Release, Need, Offer, PlanLine, and the Config that holds them.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import yaml

STATUSES = ("need", "ordered", "received", "skip")
CONFIDENCES = ("high", "medium", "low")
LEAD_SOURCES = ("page", "default", "manual")


class NeedsError(Exception):
    """needs.yaml is invalid. The message names the offending need/release."""


@dataclass
class Release:
    id: str
    date: dt.date
    goal: str = ""


@dataclass
class Need:
    id: str
    what: str
    qty: int
    release: str                       # yaml key `for`
    spec: Dict[str, Any] = field(default_factory=dict)
    queries: Dict[str, str] = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    offers: List[Dict[str, Any]] = field(default_factory=list)   # manual offers, raw
    status: str = "need"
    ordered: Optional[dt.date] = None
    eta: Optional[dt.date] = None
    note: str = ""


@dataclass
class Offer:
    need_id: str
    supplier: str
    title: str
    url: str
    price_eur: Optional[float]         # EUR incl. 20 % VAT, None = unknown
    lead_days: int
    vat_added_by_code: bool = False
    stock: Optional[int] = None
    in_stock: Optional[bool] = None
    lead_source: str = "default"       # page | default | manual
    fetched_at: str = ""               # ISO timestamp
    confidence: str = "medium"         # high | medium | low

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Offer":
        known = {k: d.get(k) for k in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        if known.get("lead_days") is None:
            known["lead_days"] = 0
        return cls(**known)


@dataclass
class PlanLine:
    need: Need
    release: Release
    order_by: dt.date
    slack_days: int
    best: Optional[Offer]
    offers: List[Offer]


@dataclass
class Config:
    safety_days: int
    releases: Dict[str, Release]
    prefer: List[str]
    default_lead_days: Dict[str, int]
    needs: List[Need]

    def release_of(self, need: Need) -> Release:
        return self.releases[need.release]

    def lead_for(self, supplier: str) -> int:
        """Default lead days for a supplier; the slowest known supplier if unknown."""
        if supplier in self.default_lead_days:
            return int(self.default_lead_days[supplier])
        return max(self.default_lead_days.values()) if self.default_lead_days else 0


# ---------------------------------------------------------------- loader

def _date(value: Any, where: str) -> Optional[dt.date]:
    if value is None or value == "":
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError:
        raise NeedsError(f"{where}: bad date {value!r}, expected YYYY-MM-DD")


def _int(value: Any, where: str, minimum: int = 0) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise NeedsError(f"{where}: expected an integer, got {value!r}")
    if n < minimum:
        raise NeedsError(f"{where}: must be >= {minimum}, got {n}")
    return n


def parse_config(raw: Dict[str, Any]) -> Config:
    if not isinstance(raw, dict):
        raise NeedsError("top level must be a mapping")

    safety_days = _int(raw.get("safety_days", 2), "safety_days")

    releases: Dict[str, Release] = {}
    for i, r in enumerate(raw.get("releases") or []):
        if not isinstance(r, dict) or "id" not in r or "date" not in r:
            raise NeedsError(f"releases[{i}]: needs `id` and `date`")
        rid = str(r["id"])
        if rid in releases:
            raise NeedsError(f"release {rid}: duplicate id")
        date = _date(r["date"], f"release {rid}")
        if date is None:
            raise NeedsError(f"release {rid}: missing date")
        releases[rid] = Release(id=rid, date=date, goal=str(r.get("goal", "")))
    if not releases:
        raise NeedsError("releases: none defined (copy id + date from the AR-Mini Board)")

    sup = raw.get("suppliers") or {}
    prefer = [str(s) for s in (sup.get("prefer") or [])]
    default_lead = {str(k): _int(v, f"suppliers.default_lead_days.{k}") for k, v in (sup.get("default_lead_days") or {}).items()}
    for s in prefer:
        if s not in default_lead:
            raise NeedsError(f"suppliers.prefer: {s} has no default_lead_days")

    needs: List[Need] = []
    seen = set()
    for i, n in enumerate(raw.get("needs") or []):
        if not isinstance(n, dict) or "id" not in n:
            raise NeedsError(f"needs[{i}]: missing `id`")
        nid = str(n["id"])
        if nid in seen:
            raise NeedsError(f"need {nid}: duplicate id")
        seen.add(nid)
        if not n.get("for"):
            raise NeedsError(f"need {nid}: missing `for` (release id)")
        rel = str(n["for"])
        if rel not in releases:
            raise NeedsError(f"need {nid}: unknown release id {rel!r} (known: {', '.join(releases)})")
        status = str(n.get("status", "need"))
        if status not in STATUSES:
            raise NeedsError(f"need {nid}: status {status!r} not in {STATUSES}")
        queries = {str(k): str(v) for k, v in (n.get("queries") or {}).items() if v}
        for s in queries:
            if s not in default_lead:
                raise NeedsError(f"need {nid}: query for unknown supplier {s!r}")
        manual = n.get("offers") or []
        for j, o in enumerate(manual):
            if not isinstance(o, dict) or "supplier" not in o:
                raise NeedsError(f"need {nid}: offers[{j}] needs at least `supplier`")
        needs.append(Need(
            id=nid,
            what=str(n.get("what", "")),
            qty=_int(n.get("qty", 1), f"need {nid}: qty", minimum=1),
            release=rel,
            spec=dict(n.get("spec") or {}),
            queries=queries,
            links=[str(u) for u in (n.get("links") or [])],
            offers=list(manual),
            status=status,
            ordered=_date(n.get("ordered"), f"need {nid}: ordered"),
            eta=_date(n.get("eta"), f"need {nid}: eta"),
            note=str(n.get("note") or ""),
        ))

    return Config(safety_days=safety_days, releases=releases, prefer=prefer,
                  default_lead_days=default_lead, needs=needs)


def load_needs(path: str) -> Config:
    with open(path, encoding="utf-8") as fh:
        try:
            raw = yaml.safe_load(fh)
        except yaml.YAMLError as e:
            raise NeedsError(f"YAML syntax: {e}")
    return parse_config(raw or {})
