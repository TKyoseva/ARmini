"""Pure planning rules: order-by dates, slack, best offer, alert diff.

No I/O, no clock: every function takes `today` explicitly so tests are deterministic.
Rules per tasks/night/2026-10-09_T4_parts-agent.md.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from model import Config, Need, Offer, PlanLine

VAT_RATE = 1.20          # SOURCE: Bulgarian standard VAT 20 %, prices normalised to EUR incl. VAT
PRICE_MOVE = 0.10        # PRICE alert when the best price moves more than 10 %
ORDER_SOON_DAYS = 3      # ORDER_SOON when slack <= 3 days
RELEASE_RISK_DAYS = 2    # RELEASE_AT_RISK when the release is within 2 days
ADAPTER_DOWN_RUNS = 3    # ADAPTER_DOWN after 3 consecutive failed runs

# Alerts that describe a *state* (not an event) fire at most once per calendar day.
DAILY_KINDS = ("ORDER_SOON", "OVERDUE", "ETA_LATE", "RELEASE_AT_RISK", "ADAPTER_DOWN")


@dataclass
class Alert:
    kind: str
    key: str          # need id, release id or adapter name
    text: str         # one line, no markdown


# ------------------------------------------------------------ dates

def add_vat(net: float) -> float:
    """Net EUR -> gross EUR (20 % VAT), rounded to cents."""
    return round(net * VAT_RATE, 2)


def order_by(release_date: dt.date, lead_days: int, safety_days: int = 2) -> dt.date:
    """Last day to order. Weekends are not shipping days: Sat/Sun -> the Friday before."""
    d = release_date - dt.timedelta(days=int(lead_days) + int(safety_days))
    if d.weekday() == 5:      # Saturday
        d -= dt.timedelta(days=1)
    elif d.weekday() == 6:    # Sunday
        d -= dt.timedelta(days=2)
    return d


def slack_days(order_by_date: dt.date, today: dt.date) -> int:
    return (order_by_date - today).days


def arrives_by(today: dt.date, lead_days: int) -> dt.date:
    return today + dt.timedelta(days=int(lead_days))


# ------------------------------------------------------------ offers

def best_offer(offers: Iterable[Offer], release_date: dt.date, today: dt.date,
               prefer: List[str]) -> Optional[Offer]:
    """Cheapest offer that is not out of stock and arrives before the release.

    null prices sort last; ties are broken by supplier preference order, unknown suppliers last.
    """
    rank = {s: i for i, s in enumerate(prefer)}
    candidates = [o for o in offers
                  if o.in_stock is not False and arrives_by(today, o.lead_days) <= release_date]
    if not candidates:
        return None

    def key(o: Offer):
        return (o.price_eur is None, o.price_eur if o.price_eur is not None else 0.0,
                rank.get(o.supplier, len(rank)), o.url)

    return min(candidates, key=key)


def lead_for_need(cfg: Config, need: Need, best: Optional[Offer]) -> int:
    """Lead days used for order_by: the best offer's, else the slowest supplier this need could use."""
    if best is not None:
        return best.lead_days
    suppliers = set(need.queries) | {o.get("supplier") for o in need.offers if o.get("supplier")}
    leads = [cfg.lead_for(s) for s in suppliers if s]
    if leads:
        return max(leads)
    return max(cfg.default_lead_days.values()) if cfg.default_lead_days else 0


def plan_need(cfg: Config, need: Need, offers: List[Offer], today: dt.date) -> PlanLine:
    rel = cfg.release_of(need)
    best = best_offer(offers, rel.date, today, cfg.prefer)
    ob = order_by(rel.date, lead_for_need(cfg, need, best), cfg.safety_days)
    return PlanLine(need=need, release=rel, order_by=ob, slack_days=slack_days(ob, today),
                    best=best, offers=list(offers))


# ------------------------------------------------------------ state helpers

def _alerted_today(entry: Dict[str, Any], kind: str, today: dt.date) -> bool:
    return (entry.get("alerted") or {}).get(kind) == today.isoformat()


def _best(entry: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return (entry or {}).get("best") or None


def _fmt_price(o: Optional[Dict[str, Any]]) -> str:
    if not o or o.get("price_eur") is None:
        return "price ?"
    return f"{o['price_eur']:.2f} €"


# ------------------------------------------------------------ diff

def diff(old_state: Dict[str, Any], new_state: Dict[str, Any], cfg: Config,
         today: dt.date) -> List[Alert]:
    """Compare two state snapshots and return the alerts to send.

    `*_state` have the shape written by agent.py:
      {needs: {id: {best, offers, order_by, slack_days, status, eta, release, alerted}},
       adapters: {name: {ok, error, at, fails}}, alerted: {key: iso}, run_at}
    The daily kinds consult `alerted` in **old_state** so they fire once per day.
    """
    alerts: List[Alert] = []
    old_needs = old_state.get("needs") or {}
    new_needs = new_state.get("needs") or {}
    needs_by_id = {n.id: n for n in cfg.needs}

    for nid, new in new_needs.items():
        need = needs_by_id.get(nid)
        if need is None or need.status == "skip":
            continue
        old = old_needs.get(nid) or {}
        ob, nb = _best(old), _best(new)
        status = need.status

        if status == "need":
            # NEW_BEST: first offer found, or best supplier changed
            if nb and (ob is None or ob.get("supplier") != nb.get("supplier")):
                alerts.append(Alert("NEW_BEST", nid,
                                    f"{nid} best: {nb['supplier']} {_fmt_price(nb)} · {nb.get('title', '')[:60]}"))
            # PRICE: same supplier, price moved > 10 %
            elif nb and ob and ob.get("price_eur") and nb.get("price_eur") is not None:
                oldp, newp = float(ob["price_eur"]), float(nb["price_eur"])
                if abs(newp - oldp) / oldp > PRICE_MOVE:
                    alerts.append(Alert("PRICE", nid,
                                        f"{nid} price {nb['supplier']}: {oldp:.2f} → {newp:.2f} €"))
            # OUT_OF_STOCK: yesterday's best is now out of stock
            if ob:
                for o in new.get("offers") or []:
                    if o.get("url") == ob.get("url") and o.get("supplier") == ob.get("supplier") \
                            and o.get("in_stock") is False:
                        alerts.append(Alert("OUT_OF_STOCK", nid,
                                            f"{nid} out of stock at {ob['supplier']}: {ob.get('title', '')[:60]}"))
                        break
            slack = new.get("slack_days")
            if slack is not None:
                if slack < 0 and not _alerted_today(old, "OVERDUE", today):
                    alerts.append(Alert("OVERDUE", nid,
                                        f"{nid} OVERDUE by {-slack} d (order-by was {new.get('order_by')}) for {need.release}"))
                elif 0 <= slack <= ORDER_SOON_DAYS and not _alerted_today(old, "ORDER_SOON", today):
                    alerts.append(Alert("ORDER_SOON", nid,
                                        f"{nid} order by {new.get('order_by')} ({slack} d left) · "
                                        f"{nb['supplier'] + ' ' + _fmt_price(nb) if nb else 'no offer yet'}"))

        elif status == "ordered":
            rel = cfg.release_of(need)
            late = need.eta is None or need.eta > rel.date - dt.timedelta(days=1)
            if late and not _alerted_today(old, "ETA_LATE", today):
                eta = need.eta.isoformat() if need.eta else "unknown"
                alerts.append(Alert("ETA_LATE", nid,
                                    f"{nid} ordered, eta {eta} vs release {rel.id} {rel.date.isoformat()}"))

    # RELEASE_AT_RISK: release within 2 days and any need for it not received
    old_global = old_state.get("alerted") or {}
    for rel in cfg.releases.values():
        days = (rel.date - today).days
        if 0 <= days <= RELEASE_RISK_DAYS:
            open_needs = [n.id for n in cfg.needs
                          if n.release == rel.id and n.status not in ("received", "skip")]
            key = f"RELEASE_AT_RISK:{rel.id}"
            if open_needs and old_global.get(key) != today.isoformat():
                alerts.append(Alert("RELEASE_AT_RISK", rel.id,
                                    f"release {rel.id} in {days} d, not received: {', '.join(open_needs)}"))

    # ADAPTER_DOWN: 3 consecutive failed runs, once per day
    for name, a in (new_state.get("adapters") or {}).items():
        if (a.get("fails") or 0) >= ADAPTER_DOWN_RUNS:
            key = f"ADAPTER_DOWN:{name}"
            if old_global.get(key) != today.isoformat():
                alerts.append(Alert("ADAPTER_DOWN", name,
                                    f"adapter {name} failed {a.get('fails')} runs: {str(a.get('error') or '')[:80]}"))

    return alerts


def record_alerts(new_state: Dict[str, Any], alerts: List[Alert], today: dt.date) -> None:
    """Carry `alerted` dates into new_state so the daily kinds fire once per day."""
    iso = today.isoformat()
    for a in alerts:
        if a.kind in ("RELEASE_AT_RISK", "ADAPTER_DOWN"):
            new_state.setdefault("alerted", {})[f"{a.kind}:{a.key}"] = iso
        else:
            entry = new_state.setdefault("needs", {}).setdefault(a.key, {})
            entry.setdefault("alerted", {})[a.kind] = iso


def carry_alerted(old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
    """Copy previous `alerted` maps into the new state before recording today's alerts."""
    for nid, old in (old_state.get("needs") or {}).items():
        if old.get("alerted") and nid in (new_state.get("needs") or {}):
            new_state["needs"][nid]["alerted"] = dict(old["alerted"])
    if old_state.get("alerted"):
        new_state["alerted"] = dict(old_state["alerted"])
