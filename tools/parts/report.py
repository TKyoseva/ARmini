"""Render parts/REPORT.md (markdown) and the Telegram text (plain, <= 3500 chars via notify)."""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from model import Config, Offer, PlanLine
from plan import Alert

STATUS_ICON = {"need": "need", "ordered": "ordered", "received": "received", "skip": "skip"}


def _price(o: Optional[Offer]) -> str:
    if o is None:
        return "—"
    if o.price_eur is None:
        return "check price by hand"
    return f"{o.price_eur:.2f} €"


def _stock(o: Optional[Offer]) -> str:
    if o is None or o.in_stock is None:
        return "?"
    if o.stock is not None:
        return str(o.stock)
    return "yes" if o.in_stock else "no"


def _md(s: Any) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def _best_cell(line: PlanLine) -> str:
    o = line.best
    if o is None:
        return "no offer yet" if line.need.status == "need" else "—"
    title = o.title if len(o.title) <= 50 else o.title[:47] + "…"
    link = f"[{_md(title)}]({o.url})" if o.url else _md(title)
    return f"{o.supplier} · {_price(o)} · stock {_stock(o)} · {o.lead_days} d ({o.lead_source}) · {link}"


def render_markdown(cfg: Config, lines: List[PlanLine], adapters: Dict[str, Dict[str, Any]],
                    alerts: List[Alert], today: dt.date, run_at: str) -> str:
    out: List[str] = []
    out.append("# AR-Mini · parts report")
    out.append("")
    out.append(f"Generated {run_at} (today {today.isoformat()}, Sofia). Written by `tools/parts/agent.py`; "
               "edit `parts/needs.yaml`, not this file. Prices EUR incl. 20 % VAT.")
    out.append("")
    out.append("## Releases")
    out.append("")
    out.append("| Release | Date | Days left | Needs open / total | Goal |")
    out.append("|---|---|---:|---|---|")
    for rel in sorted(cfg.releases.values(), key=lambda r: r.date):
        mine = [l for l in lines if l.need.release == rel.id]
        open_ = [l for l in mine if l.need.status in ("need", "ordered")]
        out.append(f"| {rel.id} | {rel.date.isoformat()} | {(rel.date - today).days} | "
                   f"{len(open_)} / {len(mine)} | {_md(rel.goal)} |")
    out.append("")
    out.append("## Needs")
    out.append("")
    out.append("| Need | What | Qty | Release | Status | Order by | Slack (d) | Best offer | Note |")
    out.append("|---|---|---:|---|---|---|---:|---|---|")
    for l in sorted(lines, key=lambda l: (l.need.status != "need", l.order_by, l.need.id)):
        n = l.need
        status = n.status
        if status == "ordered":
            status += f" (eta {n.eta.isoformat() if n.eta else '?'})"
        out.append(f"| {n.id} | {_md(n.what)} | {n.qty} | {n.release} | {status} | "
                   f"{l.order_by.isoformat()} | {l.slack_days} | {_best_cell(l)} | {_md(n.note)} |")
    out.append("")
    out.append("## All offers")
    out.append("")
    out.append("| Need | Supplier | Price | Stock | Lead (d) | Conf. | Title |")
    out.append("|---|---|---|---|---:|---|---|")
    any_offer = False
    for l in lines:
        for o in sorted(l.offers, key=lambda o: (o.price_eur is None, o.price_eur or 0)):
            any_offer = True
            title = o.title if len(o.title) <= 70 else o.title[:67] + "…"
            link = f"[{_md(title)}]({o.url})" if o.url else _md(title)
            out.append(f"| {l.need.id} | {o.supplier} | {_price(o)} | {_stock(o)} | {o.lead_days} | "
                       f"{o.confidence} | {link} |")
    if not any_offer:
        out.append("| — | — | — | — | — | — | no offers in this run |")
    out.append("")
    out.append("## Adapters")
    out.append("")
    out.append("| Adapter | Kind | State | Consecutive fails | Last error |")
    out.append("|---|---|---|---:|---|")
    for name, a in adapters.items():
        out.append(f"| {name} | {a.get('kind', '?')} | {a.get('state', '?')} | {a.get('fails', 0)} | "
                   f"{_md(a.get('error') or '')} |")
    out.append("")
    out.append("## Alerts this run")
    out.append("")
    if alerts:
        for a in alerts:
            out.append(f"- **{a.kind}** · {_md(a.text)}")
    else:
        out.append("none")
    out.append("")
    return "\n".join(out)


def render_telegram(lines: List[PlanLine], adapters: Dict[str, Dict[str, Any]], alerts: List[Alert],
                    today: dt.date, digest: bool, report_url: str = "") -> str:
    """Plain-text message. Empty string means: nothing to send."""
    if not alerts and not digest:
        return ""
    out: List[str] = [f"AR-Mini parts · {today.isoformat()}"]
    if alerts:
        out.append("")
        for a in alerts:
            out.append(f"• {a.kind}: {a.text}")
    if digest:
        out.append("")
        out.append("Next to order:")
        upcoming = sorted((l for l in lines if l.need.status == "need"), key=lambda l: l.order_by)[:3]
        if not upcoming:
            out.append("  nothing open")
        for l in upcoming:
            best = f"{l.best.supplier} {_price(l.best)}" if l.best else "no offer yet"
            out.append(f"  {l.need.id} {l.need.what[:40]} → order by {l.order_by.isoformat()} "
                       f"({l.slack_days} d) · {best}")
        off = [f"{n} {a.get('state')}" for n, a in adapters.items()
               if a.get("state") not in ("ok", "skipped (offline)")]
        if off:
            out.append("Adapters: " + ", ".join(off))
    if report_url:
        out.append("")
        out.append(f"Report: {report_url}")
    return "\n".join(out)
