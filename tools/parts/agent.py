#!/usr/bin/env python3
"""AR-Mini parts agent — hourly sourcing + order-by-date alerts.

    python tools/parts/agent.py --dry-run        # no Telegram, no files written, report to stdout
    python tools/parts/agent.py                  # writes parts/state.json + parts/REPORT.md, Telegram if due
    python tools/parts/agent.py --needs PATH     # another needs.yaml
    python tools/parts/agent.py --offline        # skip the network (tests, airplane)

Exit codes: 0 ok · 2 needs.yaml invalid (message on stderr starts with "needs.yaml invalid:").
It never buys anything. Spec: tasks/night/2026-10-09_T4_parts-agent.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapters import Http, build_adapters, collect  # noqa: E402
from model import Config, NeedsError, PlanLine, load_needs  # noqa: E402
from notify import telegram  # noqa: E402
from plan import carry_alerted, diff, plan_need, record_alerts  # noqa: E402
from report import render_markdown, render_telegram  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_NEEDS = os.path.join(REPO, "parts", "needs.yaml")
DEFAULT_STATE = os.path.join(REPO, "parts", "state.json")
DEFAULT_REPORT = os.path.join(REPO, "parts", "REPORT.md")


def sofia_now() -> dt.datetime:
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("Europe/Sofia"))
    except Exception:  # noqa: BLE001 — no tzdata: Sofia is UTC+2/+3, use +2 as the safe side
        return dt.datetime.now(dt.timezone(dt.timedelta(hours=2)))


def load_state(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh) or {}
    except (OSError, ValueError) as e:
        print(f"warning: ignoring unreadable state {path}: {e}", file=sys.stderr)
        return {}


def is_first_run_today(old_state: Dict[str, Any], now: dt.datetime) -> bool:
    run_at = old_state.get("run_at")
    if not run_at:
        return True
    try:
        prev = dt.datetime.fromisoformat(run_at)
    except ValueError:
        return True
    if prev.tzinfo is None:
        prev = prev.replace(tzinfo=dt.timezone.utc)
    return prev.astimezone(now.tzinfo).date() < now.date()


def build_state(cfg: Config, lines: List[PlanLine], adapters: Dict[str, Dict[str, Any]],
                now: dt.datetime) -> Dict[str, Any]:
    needs: Dict[str, Any] = {}
    for l in lines:
        needs[l.need.id] = {
            "status": l.need.status,
            "release": l.release.id,
            "release_date": l.release.date.isoformat(),
            "eta": l.need.eta.isoformat() if l.need.eta else None,
            "order_by": l.order_by.isoformat(),
            "slack_days": l.slack_days,
            "best": l.best.to_dict() if l.best else None,
            "offers": [o.to_dict() for o in l.offers],
            "alerted": {},
        }
    return {"run_at": now.replace(microsecond=0).isoformat(), "needs": needs,
            "adapters": adapters, "alerted": {}}


def run(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="no Telegram, no files written; print the report")
    ap.add_argument("--once", action="store_true", default=True, help="run once (default, the only mode)")
    ap.add_argument("--needs", default=DEFAULT_NEEDS, help="path to needs.yaml")
    ap.add_argument("--state", default=DEFAULT_STATE, help="path to state.json (read + written)")
    ap.add_argument("--report", default=DEFAULT_REPORT, help="path to REPORT.md (written)")
    ap.add_argument("--today", default=None, help="override today's date (YYYY-MM-DD), for tests")
    ap.add_argument("--offline", action="store_true", help="do not call any supplier")
    ap.add_argument("--digest", action="store_true", help="force the daily digest into this run's message")
    args = ap.parse_args(argv)

    now = sofia_now()
    if args.today:
        now = dt.datetime.combine(dt.date.fromisoformat(args.today), now.timetz())
    today = now.date()

    # 1. load + validate
    try:
        cfg = load_needs(args.needs)
    except (NeedsError, OSError) as e:
        print(f"needs.yaml invalid: {e}", file=sys.stderr)
        return 2

    # 2. previous state
    old_state = load_state(args.state)

    # 3. collect offers
    http = None if args.offline else Http()
    adapters = build_adapters(cfg, http)
    offers_by_need, adapter_status = collect(cfg, adapters, old_state.get("adapters") or {},
                                             offline=args.offline)

    # 4. plan
    lines = [plan_need(cfg, n, offers_by_need.get(n.id, []), today) for n in cfg.needs]

    # 5. diff -> alerts, state, report
    new_state = build_state(cfg, lines, adapter_status, now)
    alerts = diff(old_state, new_state, cfg, today)
    carry_alerted(old_state, new_state)
    record_alerts(new_state, alerts, today)
    digest = args.digest or is_first_run_today(old_state, now)
    report_md = render_markdown(cfg, lines, adapter_status, alerts, today, new_state["run_at"])
    text = render_telegram(lines, adapter_status, alerts, today, digest,
                           report_url=os.environ.get("PARTS_REPORT_URL", ""))

    if args.dry_run:
        print(report_md)
        print("\n---\nTelegram text that would be sent:\n")
        print(text or "(nothing — no alerts and not the first run of the day)")
        print(f"\nrequests used: {http.used if http else 0}")
        return 0

    os.makedirs(os.path.dirname(os.path.abspath(args.state)), exist_ok=True)
    with open(args.state, "w", encoding="utf-8") as fh:
        json.dump(new_state, fh, indent=1, ensure_ascii=False, sort_keys=True)
    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write(report_md)

    # 6. notify
    if text:
        telegram(text)
    else:
        print("no alerts, no digest — nothing sent")
    return 0


if __name__ == "__main__":
    sys.exit(run())
