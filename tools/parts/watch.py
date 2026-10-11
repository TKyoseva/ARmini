"""Watch lists: research with no order-by date (task T6).

`parts/watch.yaml` is loaded and validated here. Ranking, the discovery filter and the
alert diff are pure functions. The agent never writes the yaml; discovered products go
into state["watch"] only.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional
from urllib.parse import urlsplit

import yaml

from plan import Alert

# SOURCE: tasks/night/2026-10-10_T6 — watch has its own cap, inside the run budget of 60.
WATCH_REQUEST_BUDGET = 20
# SOURCE: tasks/night/2026-10-10_T6 — same threshold as plan.PRICE_MOVE ("more than 10 %").
PRICE_MOVE = 0.10
# SOURCE: tasks/night/2026-10-10_T6 — note only, the price figure is not multiplied.
IMPORT_VAT_NOTE = "+ import VAT 20 % on arrival"

# Title must contain one of these (case-insensitive substring). SOURCE: T6.
KEEP_WORDS = ("thruster", "jet", "jetantrieb", "diskdrive", "rim")
# Guessed from the title. Counted in wow only after a human copies them to `features`.
_GUESS = (
    (re.compile(r"rim|hubless", re.I), "rim_driven"),
    (re.compile(r"jet", re.I), "waterjet"),
    (re.compile(r"azimuth|steer|lenkbar|vector", re.I), "steerable"),
)
_ITEM_ID = re.compile(r"W(\d+)$")


class WatchError(Exception):
    """watch.yaml is invalid. The message names the offending item or feature."""


def watch_ceiling(used: int, budget: int, watch_budget: int = WATCH_REQUEST_BUDGET) -> int:
    """Absolute Http.used cap for the watch phase: at most `watch_budget` more requests,
    and never past the run budget."""
    return min(int(budget), int(used) + int(watch_budget))


# ---------------------------------------------------------------- data

@dataclass
class WatchOffer:
    shop: str
    url: str
    price: Optional[float]
    currency: str = ""
    vat_included: Optional[bool] = None
    imports: Optional[bool] = None          # yaml key `import`
    in_stock: Optional[bool] = None
    note: str = ""
    confidence: str = "high"
    checked: str = "stored"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shop": self.shop, "url": self.url, "price": self.price, "currency": self.currency,
            "vat_included": self.vat_included, "import": self.imports, "in_stock": self.in_stock,
            "note": self.note, "confidence": self.confidence, "checked": self.checked,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WatchOffer":
        price = d.get("price")
        return cls(
            shop=str(d.get("shop") or ""),
            url=str(d.get("url") or ""),
            price=float(price) if price is not None else None,
            currency=str(d.get("currency") or ""),
            vat_included=d.get("vat_included"),
            imports=d.get("import"),
            in_stock=d.get("in_stock"),
            note=str(d.get("note") or ""),
            confidence=str(d.get("confidence") or "high"),
            checked=str(d.get("checked") or "stored"),
        )


@dataclass
class WatchItem:
    id: str
    name: str
    features: List[str] = field(default_factory=list)
    features_guessed: List[str] = field(default_factory=list)
    status: str = "watch"
    spec: Dict[str, Any] = field(default_factory=dict)
    offers: List[WatchOffer] = field(default_factory=list)
    fit: str = ""
    maker: str = ""
    kind: str = ""
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "maker": self.maker, "kind": self.kind,
            "features": list(self.features), "features_guessed": list(self.features_guessed),
            "status": self.status, "spec": dict(self.spec),
            "offers": [o.to_dict() for o in self.offers], "sources": list(self.sources),
            "fit": self.fit,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WatchItem":
        return cls(
            id=str(d.get("id") or ""),
            name=str(d.get("name") or ""),
            maker=str(d.get("maker") or ""),
            kind=str(d.get("kind") or ""),
            features=[str(f) for f in (d.get("features") or [])],
            features_guessed=[str(f) for f in (d.get("features_guessed") or [])],
            status=str(d.get("status") or "watch"),
            spec=dict(d.get("spec") or {}),
            offers=[WatchOffer.from_dict(o) for o in (d.get("offers") or []) if isinstance(o, dict)],
            sources=[str(u) for u in (d.get("sources") or [])],
            fit=str(d.get("fit") or ""),
        )


@dataclass
class Rejected:
    name: str
    url: str = ""
    why: str = ""


@dataclass
class WatchList:
    id: str
    title: str
    wow_points: Dict[str, int]
    items: List[WatchItem]
    asked: str = ""
    budget_eur: Optional[float] = None
    must: Dict[str, Any] = field(default_factory=dict)
    rank_by: List[str] = field(default_factory=list)
    discover: Dict[str, List[str]] = field(default_factory=dict)
    exclude_words: List[str] = field(default_factory=list)
    rejected: List[Rejected] = field(default_factory=list)


@dataclass
class WatchFile:
    fx_to_eur: Dict[str, Optional[float]]
    lists: List[WatchList]


@dataclass
class WatchRow:
    rank: int
    item_id: str
    name: str
    wow: str
    thrust: str
    current: str
    mass: str
    size: str
    price: str
    stock: str
    checked: str
    fit: str
    url: str


@dataclass
class UnratedRow:
    item_id: str
    name: str
    guessed: str
    price: str
    url: str


@dataclass
class WatchListView:
    list_id: str
    title: str
    rows: List[WatchRow]
    unrated: List[UnratedRow]
    rejected: List[Rejected]


@dataclass
class WatchView:
    adapter_line: str
    request_line: str
    lists: List[WatchListView]


@dataclass
class WatchRun:
    error: str = ""
    view: Optional[WatchView] = None
    alerts: List[Alert] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------- loader

def _features(value: Any, where: str) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise WatchError(f"{where}: features must be a list")
    return [str(f) for f in value]


def load_watch(path: str) -> WatchFile:
    try:
        with open(path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except OSError as e:
        raise WatchError(str(e))
    except yaml.YAMLError as e:
        raise WatchError(f"YAML syntax: {e}")
    if not isinstance(raw, dict):
        raise WatchError("top level must be a mapping")
    fx: Dict[str, Optional[float]] = {}
    for k, v in (raw.get("fx_to_eur") or {}).items():
        fx[str(k)] = None if v is None else float(v)

    lists: List[WatchList] = []
    seen_ids: set = set()
    for i, lst in enumerate(raw.get("lists") or []):
        if not isinstance(lst, dict) or "id" not in lst:
            raise WatchError(f"lists[{i}]: missing `id`")
        points = {str(k): int(v) for k, v in (lst.get("wow_points") or {}).items()}
        items: List[WatchItem] = []
        for j, n in enumerate(lst.get("items") or []):
            if not isinstance(n, dict) or "id" not in n:
                raise WatchError(f"lists[{i}].items[{j}]: missing `id`")
            iid = str(n["id"])
            if iid in seen_ids:
                raise WatchError(f"{iid}: duplicate id")
            seen_ids.add(iid)
            features = _features(n.get("features"), iid)
            for f in features:
                if f not in points:
                    raise WatchError(f"{iid}: unknown feature {f!r}")
            offers = []
            for o in n.get("offers") or []:
                if isinstance(o, dict):
                    offers.append(WatchOffer.from_dict(o))
            items.append(WatchItem(
                id=iid, name=str(n.get("name") or ""), maker=str(n.get("maker") or ""),
                kind=str(n.get("kind") or ""), features=features,
                features_guessed=_features(n.get("features_guessed"), iid),
                status=str(n.get("status") or "watch"), spec=dict(n.get("spec") or {}),
                offers=offers, sources=[str(u) for u in (n.get("sources") or [])],
                fit=str(n.get("fit") or ""),
            ))
        rejected = []
        for r in lst.get("rejected") or []:
            if isinstance(r, dict):
                rejected.append(Rejected(name=str(r.get("name") or ""), url=str(r.get("url") or ""),
                                         why=str(r.get("why") or "")))
        discover = {}
        for shop, queries in (lst.get("discover") or {}).items():
            discover[str(shop)] = [str(q) for q in (queries or [])]
        budget = lst.get("budget_eur")
        lists.append(WatchList(
            id=str(lst["id"]), title=str(lst.get("title") or lst["id"]), wow_points=points,
            items=items, asked=str(lst.get("asked") or ""),
            budget_eur=None if budget is None else float(budget),
            must=dict(lst.get("must") or {}),
            rank_by=[str(k) for k in (lst.get("rank_by") or [])],
            discover=discover,
            exclude_words=[str(w) for w in (lst.get("exclude_words") or [])],
            rejected=rejected,
        ))
    return WatchFile(fx_to_eur=fx, lists=lists)


# ---------------------------------------------------------------- score, price, rank

def wow_score(item: WatchItem, points: Dict[str, int]) -> int:
    """Sum of wow_points for confirmed `features` only. `features_guessed` never counts."""
    return sum(int(points[f]) for f in item.features if f in points)


def thrust_per_gram(item: WatchItem) -> Optional[float]:
    """Gram-force per gram at 12 V.

    SOURCE: tasks/night/2026-10-10_T6 — 2.1 kgf / 175 g = 12.0, 3.71 / 344 = 10.8.
    That is thrust_kgf_12v * 1000 / mass_g. Missing thrust or mass returns None (sorts last).
    """
    thrust = item.spec.get("thrust_kgf_12v")
    mass = item.spec.get("mass_g")
    if thrust is None or mass is None:
        return None
    mass_f = float(mass)
    if mass_f == 0:
        return None
    return float(thrust) * 1000.0 / mass_f


def to_eur(price: Optional[float], currency: str, fx: Dict[str, Optional[float]]) -> Optional[float]:
    """Fixed rates from watch.yaml. EUR passes through. A null rate stays unknown (no network)."""
    if price is None:
        return None
    cur = (currency or "").upper()
    if cur == "EUR":
        return float(price)
    rate = fx.get(cur)
    if rate is None:
        return None
    return float(rate) * float(price)


def format_price(offer: Optional[WatchOffer], fx: Dict[str, Optional[float]]) -> str:
    """`orig → EUR`. Unknown EUR is `?`. Import VAT is a note, not added into the figure."""
    if offer is None or offer.price is None:
        return "—"
    eur = to_eur(offer.price, offer.currency, fx)
    eur_s = "?" if eur is None else f"{eur:.2f} EUR"
    cell = f"{offer.price:.2f} {offer.currency} → {eur_s}"
    if offer.vat_included is False and offer.imports is True:
        cell += " " + IMPORT_VAT_NOTE
    return cell


def best_offer(item: WatchItem, fx: Dict[str, Optional[float]]) -> Optional[WatchOffer]:
    """Lowest EUR price. Unknown EUR sorts last, so the first stored offer wins when no rate is set."""
    if not item.offers:
        return None

    def key(pair):
        i, o = pair
        eur = to_eur(o.price, o.currency, fx)
        return (eur is None, eur if eur is not None else 0.0, i)

    return min(enumerate(item.offers), key=key)[1]


def rank_items(items: Iterable[WatchItem], points: Dict[str, int],
               fx: Dict[str, Optional[float]]) -> List[WatchItem]:
    """Rated items only (status != unrated). wow desc, thrust/gram desc (null last), EUR asc (null last)."""
    rated = [it for it in items if it.status != "unrated"]

    def key(it: WatchItem):
        tpg = thrust_per_gram(it)
        offer = best_offer(it, fx)
        eur = to_eur(offer.price, offer.currency, fx) if offer else None
        return (-wow_score(it, points), tpg is None, -(tpg or 0.0), eur is None,
                eur if eur is not None else 0.0, it.id)

    return sorted(rated, key=key)


def _spec_cell(spec: Dict[str, Any], key: str, unit: str) -> str:
    value = spec.get(key)
    if value is None or value == "":
        return "—"
    return f"{value} {unit}".strip()


def _stock(offer: Optional[WatchOffer]) -> str:
    if offer is None or offer.in_stock is None:
        return "?"
    return "yes" if offer.in_stock else "no"


def _wow_cell(item: WatchItem, points: Dict[str, int]) -> str:
    score = wow_score(item, points)
    if item.features:
        return f"{score} ({', '.join(item.features)})"
    return str(score)


def build_list_view(lst: WatchList, items: List[WatchItem], fx: Dict[str, Optional[float]]) -> WatchListView:
    rows: List[WatchRow] = []
    for rank, it in enumerate(rank_items(items, lst.wow_points, fx), start=1):
        offer = best_offer(it, fx)
        rows.append(WatchRow(
            rank=rank, item_id=it.id, name=it.name, wow=_wow_cell(it, lst.wow_points),
            thrust=_spec_cell(it.spec, "thrust_kgf_12v", "kgf"),
            current=_spec_cell(it.spec, "current_a_12v", "A"),
            mass=_spec_cell(it.spec, "mass_g", "g"),
            size=_spec_cell(it.spec, "size_mm", ""),
            price=format_price(offer, fx), stock=_stock(offer),
            checked=offer.checked if offer else "—", fit=it.fit,
            url=offer.url if offer else "",
        ))
    unrated: List[UnratedRow] = []
    for it in items:
        if it.status != "unrated":
            continue
        offer = best_offer(it, fx)
        guessed = ", ".join(it.features_guessed) if it.features_guessed else "—"
        unrated.append(UnratedRow(item_id=it.id, name=it.name, guessed=guessed,
                                  price=format_price(offer, fx), url=offer.url if offer else ""))
    return WatchListView(list_id=lst.id, title=lst.title, rows=rows, unrated=unrated,
                         rejected=list(lst.rejected))


# ---------------------------------------------------------------- discovery

def url_key(url: str) -> str:
    """Identity of a product URL with the query string removed. Empty if it has no host."""
    parts = urlsplit((url or "").strip())
    if not parts.netloc:
        return ""
    path = parts.path.rstrip("/")
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}{path}"


def title_excluded(title: str, words: Iterable[str]) -> bool:
    """Drop a title that contains an exclude word (phrase, or a whole word)."""
    text = title.lower()
    for word in words:
        w = str(word).lower().strip()
        if not w:
            continue
        if " " in w:
            if w in text:
                return True
        elif re.search(rf"(?<!\w){re.escape(w)}(?!\w)", text):
            return True
    return False


def guess_features(title: str) -> List[str]:
    found: List[str] = []
    for cre, name in _GUESS:
        if cre.search(title) and name not in found:
            found.append(name)
    return found


def filter_discovery(candidates: Iterable[Dict[str, Any]], exclude_words: Iterable[str],
                     known_urls: Iterable[str]) -> List[Dict[str, Any]]:
    """Keep titles with a thruster word, drop exclude_words and URLs already in the list."""
    known = {url_key(u) for u in known_urls if u}
    out: List[Dict[str, Any]] = []
    seen: set = set()
    for c in candidates:
        title = str(c.get("title") or "")
        url = str(c.get("url") or "")
        if not any(w in title.lower() for w in KEEP_WORDS):
            continue
        if title_excluded(title, exclude_words):
            continue
        key = url_key(url)
        if not key or key in known or key in seen:
            continue
        seen.add(key)
        out.append({**c, "title": title, "url": url, "features_guessed": guess_features(title)})
    return out


def next_ids(existing: Iterable[str], count: int) -> List[str]:
    nums = []
    for iid in existing:
        m = _ITEM_ID.search(str(iid))
        if m:
            nums.append(int(m.group(1)))
    start = max(nums) if nums else 0
    return [f"W{start + k:03d}" for k in range(1, count + 1)]


# ---------------------------------------------------------------- alerts

def _item_snap(item: WatchItem, fx: Dict[str, Optional[float]]) -> Dict[str, Any]:
    offer = best_offer(item, fx)
    if offer is None:
        return {"price": None, "currency": "", "eur": None, "in_stock": None}
    return {
        "price": offer.price,
        "currency": offer.currency,
        "eur": to_eur(offer.price, offer.currency, fx),
        "in_stock": offer.in_stock,
    }


def _comparable(snap: Optional[Dict[str, Any]]) -> Optional[tuple]:
    if not snap:
        return None
    if snap.get("eur") is not None:
        return ("EUR", float(snap["eur"]))
    if snap.get("price") is not None and snap.get("currency"):
        return (str(snap["currency"]), float(snap["price"]))
    return None


def snapshot_lists(file: WatchFile, items_by_list: Dict[str, List[WatchItem]]) -> Dict[str, Any]:
    lists: Dict[str, Any] = {}
    for lst in file.lists:
        items = items_by_list.get(lst.id, [])
        ranked = rank_items(items, lst.wow_points, file.fx_to_eur)
        lists[lst.id] = {
            "top": ranked[0].id if ranked else None,
            "items": {it.id: _item_snap(it, file.fx_to_eur) for it in items},
            "discovered_ids": [it.id for it in items if it.status == "unrated"],
        }
    return lists


def diff_watch(old: Dict[str, Any], new_lists: Dict[str, Any], today: dt.date) -> List[Alert]:
    """WATCH_* alerts. Each fires at most once per day (`alerted` on the previous state).

    WATCH_NEW: an unrated id that was not in the previous discovered set.
    WATCH_PRICE: best price moved by more than 10 % (same currency, or both in EUR).
    WATCH_STOCK: in stock flipped to out of stock, or the other way. null is not a side of that flip.
    WATCH_TOP: rank 1 changed. A first observation (no previous top) is not a change.
    """
    alerts: List[Alert] = []
    alerted = old.get("alerted") or {}
    iso = today.isoformat()
    old_lists = old.get("lists") or {}

    def seen(kind: str, key: str) -> bool:
        return alerted.get(f"{kind}:{key}") == iso

    for list_id, new in new_lists.items():
        prev = old_lists.get(list_id) or {}
        old_ids = set(prev.get("discovered_ids") or [])
        for iid in new.get("discovered_ids") or []:
            if iid not in old_ids and not seen("WATCH_NEW", iid):
                alerts.append(Alert("WATCH_NEW", iid, f"{iid} new unrated candidate on {list_id}"))
        old_top, new_top = prev.get("top"), new.get("top")
        if old_top and new_top and old_top != new_top and not seen("WATCH_TOP", list_id):
            alerts.append(Alert("WATCH_TOP", list_id, f"{list_id} rank 1 changed {old_top} → {new_top}"))
        old_items = prev.get("items") or {}
        for iid, snap in (new.get("items") or {}).items():
            before = old_items.get(iid)
            if not before:
                continue
            a, b = _comparable(before), _comparable(snap)
            if a and b and a[0] == b[0] and a[1] and abs(b[1] - a[1]) / abs(a[1]) > PRICE_MOVE \
                    and not seen("WATCH_PRICE", iid):
                alerts.append(Alert("WATCH_PRICE", iid,
                                    f"{iid} price {a[1]:.2f} → {b[1]:.2f} {a[0]}"))
            old_stock, new_stock = before.get("in_stock"), snap.get("in_stock")
            if isinstance(old_stock, bool) and isinstance(new_stock, bool) and old_stock != new_stock \
                    and not seen("WATCH_STOCK", iid):
                alerts.append(Alert("WATCH_STOCK", iid,
                                    f"{iid} stock {'yes' if old_stock else 'no'} → {'yes' if new_stock else 'no'}"))
    return alerts


def stamp_alerts(alerted: Dict[str, str], alerts: List[Alert], today: dt.date) -> None:
    iso = today.isoformat()
    for a in alerts:
        alerted[f"{a.kind}:{a.key}"] = iso


# ---------------------------------------------------------------- run

def _as_candidates(shop: str, products: Iterable[Any]) -> List[Dict[str, Any]]:
    out = []
    for p in products:
        out.append({
            "shop": shop,
            "title": getattr(p, "title", "") or "",
            "url": getattr(p, "url", "") or "",
            "price": getattr(p, "price", None),
            "currency": getattr(p, "currency", None) or "",
            "in_stock": getattr(p, "in_stock", None),
        })
    return out


def _apply_refresh(offer: WatchOffer, products: List[Any], today: dt.date) -> None:
    want = url_key(offer.url)
    hit = next((p for p in products if url_key(getattr(p, "url", "") or "") == want), None)
    if hit is None:
        return
    if getattr(hit, "price", None) is not None:
        offer.price = float(hit.price)
    if getattr(hit, "currency", None):
        offer.currency = str(hit.currency)
    if getattr(hit, "in_stock", None) is not None:
        offer.in_stock = hit.in_stock
    offer.checked = today.isoformat()
    offer.confidence = "high"


def _link_only(adapter: Any) -> bool:
    return getattr(adapter, "kind", "") == "link"


def run_watch(path: str, old: Dict[str, Any], today: dt.date, adapters: Dict[str, Any],
              offline: bool = False, http: Any = None) -> WatchRun:
    """Load watch.yaml, refresh and discover unless offline, rank, diff alerts.

    A broken file does not raise: the result's `error` starts with `watch.yaml invalid:`.
    """
    old = old or {}
    try:
        cfg = load_watch(path)
    except WatchError as e:
        msg = f"watch.yaml invalid: {e}"
        return WatchRun(error=msg, state={
            "error": msg, "ran_on": today.isoformat(),
            "alerted": dict(old.get("alerted") or {}),
        })

    notes: List[str] = []
    stop = False
    start_used = int(http.used) if http is not None else 0

    def guarded(fn: Callable[[], Any]) -> list:
        nonlocal stop
        if stop or offline:
            return []
        try:
            return list(fn() or [])
        except Exception as e:  # noqa: BLE001 — one shop must not stop needs or the other shops
            name = type(e).__name__
            if name == "BudgetExceeded":
                stop = True
            notes.append(f"{name}: {e}"[:200])
            return []

    items_by_list: Dict[str, List[WatchItem]] = {}
    discovered_out: Dict[str, List[Dict[str, Any]]] = {}
    old_discovered = old.get("discovered") or {}

    for lst in cfg.lists:
        items = [WatchItem.from_dict(it.to_dict()) for it in lst.items]
        known_ids = {it.id for it in items}
        for raw in old_discovered.get(lst.id) or []:
            if isinstance(raw, dict) and raw.get("id") not in known_ids:
                extra = WatchItem.from_dict(raw)
                items.append(extra)
                known_ids.add(extra.id)

        for it in items:
            for offer in it.offers:
                ad = adapters.get(offer.shop)
                if ad is None or _link_only(ad):
                    if ad is not None and _link_only(ad):
                        offer.confidence = "low"
                    continue
                products = guarded(lambda offer=offer, ad=ad: ad.refresh(offer.url))
                _apply_refresh(offer, products, today)
                if products and offer.checked != today.isoformat():
                    notes.append(f"{offer.shop} {offer.url}: page had no offer with this URL; stored price kept")

        known_urls = [o.url for it in items for o in it.offers]
        known_urls += [r.url for r in lst.rejected]
        existing_ids = [it.id for it in items]
        for shop, queries in lst.discover.items():
            ad = adapters.get(shop)
            if ad is None or _link_only(ad):
                continue
            for query in queries:
                products = guarded(lambda ad=ad, query=query: ad.discover(query))
                fresh = filter_discovery(_as_candidates(shop, products), lst.exclude_words, known_urls)
                for iid, cand in zip(next_ids(existing_ids, len(fresh)), fresh):
                    offer = WatchOffer(
                        shop=shop, url=cand["url"],
                        price=float(cand["price"]) if cand.get("price") is not None else None,
                        currency=str(cand.get("currency") or ""),
                        in_stock=cand.get("in_stock"),
                        confidence="high" if cand.get("price") is not None else "low",
                        checked=today.isoformat(),
                    )
                    items.append(WatchItem(
                        id=iid, name=cand["title"], status="unrated", features=[],
                        features_guessed=list(cand.get("features_guessed") or []),
                        offers=[offer],
                    ))
                    existing_ids.append(iid)
                    known_urls.append(cand["url"])
        items_by_list[lst.id] = items
        discovered_out[lst.id] = [it.to_dict() for it in items if it.status == "unrated"]

    new_lists = snapshot_lists(cfg, items_by_list)
    alerts = diff_watch(old, new_lists, today)
    alerted = dict(old.get("alerted") or {})
    stamp_alerts(alerted, alerts, today)

    adapter_bits = []
    for name, ad in adapters.items():
        if _link_only(ad):
            why = getattr(ad, "link_reason", "") or "stored price, confidence low"
            adapter_bits.append(f"{name} link-only ({why})")
        else:
            adapter_bits.append(f"{name} {getattr(ad, 'kind', '?')}")
    if notes:
        adapter_bits.append("notes: " + "; ".join(notes))
    used = (int(http.used) if http is not None else 0) - start_used
    request_line = f"Watch requests this run: {used} (cap {WATCH_REQUEST_BUDGET})."
    view = WatchView(adapter_line="; ".join(adapter_bits), request_line=request_line,
                     lists=[build_list_view(lst, items_by_list[lst.id], cfg.fx_to_eur) for lst in cfg.lists])
    state = {
        "ran_on": today.isoformat(),
        "error": "",
        "alerted": alerted,
        "lists": new_lists,
        "discovered": discovered_out,
        "requests": used,
    }
    return WatchRun(view=view, alerts=alerts, state=state)
