# parts/ · what AR-Mini still needs, and when to order it

`needs.yaml` is the input for purchases. `watch.yaml` is a second list with no deadline (see Watch lists).
Every hour a GitHub Action runs `tools/parts/agent.py`:
it asks the suppliers for price, stock and lead time, computes the **last day to order** for every
need (`release date − lead days − safety days`, weekends moved to the Friday before) and sends a
Telegram message **only when something changed or a deadline is near**. It never buys anything.

The agent does not use an LLM. The hourly run is deterministic code with tests
(`tools/parts/tests`). Spec: `tasks/night/2026-10-09_T4_parts-agent.md`.

## The five statuses

| status | meaning | who sets it | what the agent does |
|---|---|---|---|
| `need` | not ordered yet | Teddy (or `add need:` in Cursor) | searches every hour, computes order-by, alerts |
| `ordered` | order placed; `ordered:` and `eta:` filled | Teddy (`ordered N###, eta <date>`) | no search; alerts `ETA_LATE` if `eta` is missing or ≥ release date |
| `received` | in the lab | Teddy (`received N###`) | nothing, listed in the report |
| `skip` | ignore for now | Teddy | no search, no alerts, still listed |
| *(no line)* | — | — | a need that is deleted disappears from the report |

Statuses move `need → ordered → received`. Releases and their dates are copied from the AR-Mini
Board; the agent never invents a date.

## Add a need in 30 seconds

In Cursor chat: `add need: XT60 connector pair, 4, for r2c` → the agent appends a block, writes the
search queries (Bulgarian for comet/vikiwat, English for tme/mouser) and commits.

By hand, append to `needs:` in `needs.yaml`:

```yaml
  - id: N002                       # next free number
    what: "XT60 connector pair (battery to power box)"
    qty: 4
    for: r2c                       # release id from `releases:` above
    spec: { type: XT60, gender: "M+F" }
    queries:
      comet: "XT60 конектор"
      vikiwat: "XT60"
      tme: "XT60 connector"
    links: []                      # e.g. https://www.amazon.de/dp/… (link-only: price checked by hand)
    offers: []                     # manual: {supplier: bauhaus, title: …, url: …, price_eur: 7.50, in_stock: true}
    status: need
    ordered: null
    eta: null
    note: ""
```

Rules the loader enforces (exit 2 + a Telegram message if broken): unique `id`, a known `for`,
`qty ≥ 1`, `status` one of the four, dates as `YYYY-MM-DD`, queries only for suppliers listed in
`suppliers.default_lead_days`.

## Read the report

`parts/REPORT.md` is written on the bot branch **`parts-bot`** (never on `dev`):
<https://github.com/TKyoseva/ARmini/blob/parts-bot/parts/REPORT.md>

- **Releases** — days left and open needs per release.
- **Needs** — one line per need: `Order by` is the last day to place the order, `Slack` is days left
  (negative = overdue), `Best offer` is the cheapest in-stock offer that still arrives before the
  release. `check price by hand` = link-only supplier (Amazon, Bauhaus, 3D Colour), price unknown.
- **All offers** — everything found this run, with confidence (`high` = parsed price, `low` = guess).
- **Adapters** — `ok` / `disabled` (no API key) / `error` (3 errors in a row → `ADAPTER_DOWN` alert).

Prices are **EUR incl. 20 % VAT**. Comet, TME and Mouser quote net; the agent adds VAT and marks the
offer `vat_added_by_code: true`. Vikiwat shows gross prices.

Alerts: `NEW_BEST`, `PRICE` (> 10 %), `OUT_OF_STOCK`, `ORDER_SOON` (≤ 3 days), `OVERDUE`,
`ETA_LATE`, `RELEASE_AT_RISK` (release ≤ 2 days, something not received), `ADAPTER_DOWN`.
The state-type alerts (`ORDER_SOON`, `OVERDUE`, `ETA_LATE`, `RELEASE_AT_RISK`, `ADAPTER_DOWN`)
fire once per day, not every hour. The first run of each day also sends a digest: the next three
order-by dates and any disabled/down adapter.

## Run it locally (Cursor terminal)

```bash
python3 -m venv .venv && source .venv/bin/activate          # once
pip install -r tools/parts/requirements.txt                 # once

python tools/parts/agent.py --dry-run             # asks comet + vikiwat, prints the report, writes nothing
python tools/parts/agent.py --dry-run --offline   # no network at all
python tools/parts/agent.py --dry-run --offline --watch   # watch table from the stored prices
python -m pytest -q tools/parts                   # tests, no network
```

In Cursor chat: `parts report` runs the dry run and shows the table.
`--dry-run` never sends Telegram and never writes files. Without `--dry-run` the agent writes
`parts/state.json` and `parts/REPORT.md` (both gitignored on `dev`; the workflow commits them to
`parts-bot`).

## Watch lists

`parts/watch.yaml` is research, not a purchase. There is no release date and no order-by day, so it is
not a `need`. The first run of each day (about 07:07 Sofia) also reads it: refreshes price and stock,
searches a few shops for new products, ranks each list, and writes a **Watch** section into the report.
Later runs the same day reuse that section and do not fetch again. `--watch` forces a refresh.
The watch phase has its own cap of 20 requests, inside the 60 for the whole run.

Telegram hears about it only in the daily digest, and each of these at most once per day:
`WATCH_NEW` (a new unrated product), `WATCH_PRICE` (best price moved more than 10 %),
`WATCH_STOCK` (in stock ↔ out of stock), `WATCH_TOP` (rank 1 changed).

A broken `watch.yaml` is reported as `watch.yaml invalid: …` in the report and the digest. The needs
part still runs and the exit code stays 0. The agent never edits `watch.yaml`. Products it finds are
stored as `unrated` in `state.json` on the `parts-bot` branch, with guessed features that do **not**
count until a human confirms them.

Ranking is fixed, so it can be tested: `wow` is the sum of `wow_points` for confirmed `features` only.
Ties break on thrust per gram at 12 V (`thrust_kgf_12v × 1000 / mass_g`; a missing number sorts last),
then on the lowest price in EUR (unknown sorts last). Rates live in `fx_to_eur` and are typed by hand.
A null rate leaves the original currency and prints `?` in the EUR column. The agent does not fetch
exchange rates. `vat_included: false` with `import: true` adds the note "+ import VAT 20 % on arrival";
it does not change the price figure.

In Cursor chat:

- `add watch: <url> to thruster_v2`
- `rate W005: rim_driven, steerable`
- `reject W005: <reason>`
- `promote W001 for <release id>` (copies it into `needs.yaml`)

Shops that answer with a captcha, or whose robots.txt disallows the path, stay link-only: the stored
price is kept and the confidence is low. Spec: `tasks/night/2026-10-10_T6_thruster-watch.md`.

## The five secrets

GitHub → repository → Settings → Secrets and variables → Actions → *New repository secret*.
The agent runs with none of them set: TME/Mouser are reported `disabled`, Telegram falls back to
the job log.

| secret | how to get it |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram → @BotFather → `/newbot` → copy the token (`123456:ABC…`) |
| `TELEGRAM_CHAT_ID` | send any message to the new bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `message.chat.id` |
| `TME_TOKEN`, `TME_SECRET` | <https://developers.tme.eu> → log in with the TME account → *Generate new anonymous key* → token + application secret |
| `MOUSER_API_KEY` | <https://www.mouser.com/api-hub/> → *Sign up for Search API* → key arrives by e-mail |

Then: GitHub → Actions → **parts** → *Run workflow* → branch `dev` (or the night branch you want
to test), `dry_run = true` once, read the job log, then run it again without dry run. The hourly
schedule always reads `needs.yaml` from `dev`; it starts once the workflow file is on `main`
(GitHub runs cron schedules from the default branch only).

## Suppliers

| supplier | adapter | prices | lead days (default, `VERIFY: Teddy`) |
|---|---|---|---|
| comet | html (`store.comet.bg`, the search AJAX endpoint) | net → +20 % | 1 |
| vikiwat | html (`vikiwat.com/search.html?phrase=`) | gross | 2 |
| tme | API (`api.tme.eu`, HMAC-signed) | net → +20 % | 3 |
| mouser | API (`api.mouser.com` keyword search) | net → +20 % | 4 |
| amazon_de, bauhaus, 3dcolour | link only — stored link, price null, "check price by hand" | — | 5 / 0 / 1 |

Politeness: ≤ 1 request/s per host, 10 s timeout, User-Agent names this repo, robots.txt obeyed,
≤ 60 requests per run.
