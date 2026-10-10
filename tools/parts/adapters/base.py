"""Adapter base class and a polite HTTP client.

Politeness (task T4): <= 1 request/s per host, 10 s timeout, a real User-Agent naming the repo,
obey robots.txt for html adapters, whole run <= 60 requests.
"""
from __future__ import annotations

import datetime as dt
import time
import urllib.robotparser as robotparser
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

import requests

from model import Offer

USER_AGENT = "AR-Mini-parts-agent/0.1 (+https://github.com/TKyoseva/ARmini; hobby robot, 1 req/s)"
TIMEOUT_S = 10
MIN_INTERVAL_S = 1.0
REQUEST_BUDGET = 60


class BudgetExceeded(RuntimeError):
    pass


class RobotsDisallowed(RuntimeError):
    pass


class Http:
    """requests.Session wrapper with per-host rate limit, robots.txt check and a run budget."""

    def __init__(self, budget: int = REQUEST_BUDGET, min_interval: float = MIN_INTERVAL_S,
                 sleep=time.sleep, session: Optional[requests.Session] = None):
        self.budget = budget
        self.used = 0
        self.cap: Optional[int] = None   # absolute used ceiling; None = the run budget only
        self.min_interval = min_interval
        self._sleep = sleep
        self._last: Dict[str, float] = {}
        self._robots: Dict[str, Optional[robotparser.RobotFileParser]] = {}
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    # -- helpers
    def _throttle(self, url: str) -> None:
        host = urlsplit(url).netloc
        last = self._last.get(host)
        now = time.monotonic()
        if last is not None and now - last < self.min_interval:
            self._sleep(self.min_interval - (now - last))
        self._last[host] = time.monotonic()

    def _spend(self) -> None:
        limit = self.budget if self.cap is None else min(self.budget, self.cap)
        if self.used >= limit:
            raise BudgetExceeded(f"request budget of {limit} per run exhausted")
        self.used += 1

    def allowed(self, url: str) -> bool:
        """robots.txt check (cached per host). A missing/unreadable robots.txt allows everything."""
        parts = urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._robots:
            rp = robotparser.RobotFileParser()
            try:
                self._spend()
                self._throttle(base)
                r = self.session.get(base + "/robots.txt", timeout=TIMEOUT_S)
                if r.status_code == 200:
                    rp.parse(r.text.splitlines())
                    self._robots[base] = rp
                else:
                    self._robots[base] = None
            except (requests.RequestException, BudgetExceeded):
                self._robots[base] = None
        rp = self._robots[base]
        return True if rp is None else rp.can_fetch(USER_AGENT, url)

    # -- requests
    def request(self, method: str, url: str, check_robots: bool = False, **kw) -> requests.Response:
        if check_robots and not self.allowed(url):
            raise RobotsDisallowed(f"robots.txt disallows {url}")
        self._spend()
        self._throttle(url)
        kw.setdefault("timeout", TIMEOUT_S)
        r = self.session.request(method, url, **kw)
        r.raise_for_status()
        return r

    def get(self, url: str, **kw) -> requests.Response:
        return self.request("GET", url, **kw)

    def post(self, url: str, **kw) -> requests.Response:
        return self.request("POST", url, **kw)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=False).isoformat()


class Adapter:
    """One supplier. Subclasses set `name`, `kind` and implement search()/fetch()."""

    name = "base"
    kind = "none"            # api | html | link
    quotes_net = False       # True -> prices from the page are without VAT; code adds 20 %

    def __init__(self, default_lead_days: int, http: Optional[Http] = None, **_: Any):
        self.default_lead_days = int(default_lead_days)
        self.http = http

    def enabled(self) -> bool:
        return True

    def disabled_reason(self) -> str:
        return ""

    def search(self, query: str, need_id: str = "", qty: int = 1) -> List[Offer]:
        raise NotImplementedError

    def fetch(self, url: str, need_id: str = "") -> Optional[Offer]:
        """Refresh a single stored link. Default: not supported for this supplier."""
        return None

    # -- helper for subclasses
    def offer(self, need_id: str, title: str, url: str, price_eur: Optional[float], **kw) -> Offer:
        kw.setdefault("lead_days", self.default_lead_days)
        kw.setdefault("lead_source", "default")
        kw.setdefault("fetched_at", now_iso())
        kw.setdefault("confidence", "medium")
        return Offer(need_id=need_id, supplier=self.name, title=title.strip(), url=url,
                     price_eur=price_eur, **kw)
