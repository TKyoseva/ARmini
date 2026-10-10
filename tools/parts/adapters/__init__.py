"""Adapter registry + the per-run collection loop.

Every adapter: search(query, need_id, qty) -> list[Offer], fetch(url, need_id) -> Offer | None.
Adapters without their key report `disabled`; a failing adapter is recorded (ok=False, error)
and the run continues with the other suppliers.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from adapters.base import Adapter, BudgetExceeded, Http, now_iso
from adapters.comet import CometAdapter
from adapters.linkonly import LinkOnlyAdapter, supplier_for_url
from adapters.mouser import MouserAdapter
from adapters.tme import TmeAdapter
from model import Config, Need, Offer

LINK_ONLY = ("amazon_de", "bauhaus", "3dcolour")


def build_adapters(cfg: Config, http: Optional[Http]) -> Dict[str, Adapter]:
    """One adapter per supplier named in needs.yaml → suppliers.default_lead_days."""
    out: Dict[str, Adapter] = {}
    for name in cfg.default_lead_days:
        lead = cfg.lead_for(name)
        if name == "comet":
            out[name] = CometAdapter(lead, http=http)
        elif name == "vikiwat":
            from adapters.vikiwat import VikiwatAdapter
            out[name] = VikiwatAdapter(lead, http=http)
        elif name == "tme":
            out[name] = TmeAdapter(lead, http=http)
        elif name == "mouser":
            out[name] = MouserAdapter(lead, http=http)
        else:
            out[name] = LinkOnlyAdapter(lead, name=name, http=http)
    return out


def manual_offers(cfg: Config, need: Need) -> List[Offer]:
    """Offers Teddy typed into needs.yaml → offers[]. They count like fetched ones."""
    out: List[Offer] = []
    for o in need.offers:
        sup = str(o.get("supplier"))
        lead = o.get("lead_days")
        out.append(Offer(
            need_id=need.id, supplier=sup, title=str(o.get("title") or "manual offer"),
            url=str(o.get("url") or ""),
            price_eur=float(o["price_eur"]) if o.get("price_eur") is not None else None,
            lead_days=int(lead) if lead is not None else cfg.lead_for(sup),
            lead_source="manual" if lead is not None else "default",
            stock=o.get("stock"), in_stock=o.get("in_stock"),
            fetched_at="manual", confidence=str(o.get("confidence") or "high"),
        ))
    return out


def collect(cfg: Config, adapters: Dict[str, Adapter], prev_adapters: Dict[str, Any],
            offline: bool = False) -> Tuple[Dict[str, List[Offer]], Dict[str, Dict[str, Any]]]:
    """Run every adapter a need has a query or link for. Returns offers per need and adapter status.

    Adapter status: {name: {kind, ok, error, at, fails}}; `fails` counts consecutive failed runs
    (carried from the previous state) so plan.diff can raise ADAPTER_DOWN after 3.
    """
    offers: Dict[str, List[Offer]] = {}
    status: Dict[str, Dict[str, Any]] = {}
    errors: Dict[str, str] = {}
    used: set = set()

    for name, ad in adapters.items():
        prev_fails = int((prev_adapters.get(name) or {}).get("fails") or 0)
        if not ad.enabled():
            status[name] = {"kind": ad.kind, "ok": None, "state": "disabled",
                            "error": ad.disabled_reason(), "at": now_iso(), "fails": 0}
        else:
            status[name] = {"kind": ad.kind, "ok": True, "state": "ok", "error": "",
                            "at": now_iso(), "fails": prev_fails}

    for need in cfg.needs:
        offers[need.id] = manual_offers(cfg, need)
        if need.status != "need":
            continue                      # ordered / received / skip: no network for this need
        for sup, query in need.queries.items():
            ad = adapters.get(sup)
            if ad is None or not ad.enabled() or ad.kind == "link":
                continue
            if offline:
                continue
            used.add(sup)
            try:
                offers[need.id].extend(ad.search(query, need_id=need.id, qty=need.qty))
            except BudgetExceeded as e:
                errors[sup] = str(e)
                break
            except Exception as e:  # noqa: BLE001 — one supplier failing must not stop the run
                errors[sup] = f"{type(e).__name__}: {e}"[:200]
        for url in need.links:
            sup = supplier_for_url(url)
            ad = adapters.get(sup) if sup else None
            if ad is None:
                ad = LinkOnlyAdapter(cfg.lead_for("amazon_de"), name="link")
            try:
                o = ad.fetch(url, need_id=need.id)
                if o is not None:
                    offers[need.id].append(o)
            except Exception as e:  # noqa: BLE001
                errors[ad.name] = f"{type(e).__name__}: {e}"[:200]

    for name, err in errors.items():
        st = status.setdefault(name, {"kind": "?", "fails": 0})
        st.update(ok=False, state="error", error=err, at=now_iso(), fails=int(st.get("fails") or 0) + 1)
    for name, st in status.items():
        if name not in errors:
            st["fails"] = 0          # a clean (or unused) run breaks the failure streak
    if offline:
        for name, st in status.items():
            if st.get("state") == "ok" and st.get("kind") != "link":
                st["state"] = "skipped (offline)"
    return offers, status


__all__ = ["Adapter", "Http", "build_adapters", "collect", "manual_offers", "LINK_ONLY"]
