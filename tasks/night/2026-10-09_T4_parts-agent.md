# T4 · Parts agent (hourly sourcing + order-by-date alerts)

**Branch:** `night/parts-agent` → PR to `dev`
**Budget:** ~3 h agent time, or 3 failed attempts at one step.
**Depends on:** nothing in firmware. Python 3.12 only.

## Goal
A small, boring, reliable agent that keeps AR-Mini's next releases supplied. Teddy writes what she needs in one file (`parts/needs.yaml`, by release). Every hour GitHub Actions runs `tools/parts/agent.py`: it asks the suppliers for price, stock and lead time, computes the **last day to order** for every need (`release date − lead days − safety days`), and sends a Telegram message **only when something changed or a deadline is near**. It never buys anything. It keeps working after 1 November with no change except new lines in `needs.yaml`.

No LLM in the hourly loop. The hourly run is deterministic code with tests. Search queries are written when the need is added (by Teddy, or by the Cursor agent in chat when she says "add need: …").

## Context
Read: `.cursor/rules/ar-mini.mdc`, `tasks/night/README.md`, `.github/workflows/check.yml` (style of our CI), `parts/needs.yaml` (starter file, already in the repo), `docs/STATE.md` (release ids and dates; the board uses the same ids).

Facts with source:
- Releases and their dates come **only** from `parts/needs.yaml` → `releases:`. Teddy copies them from the AR-Mini Board. The agent never invents a date.
- Bulgaria uses the euro since 1 Jan 2026. All prices are normalised to **EUR including 20 % VAT**. If a supplier quotes net (TME, Mouser business prices), multiply by 1.20 and set `vat_added_by_code: true` on the offer.
- Delivery to Sofia. Default lead days per supplier are config in `needs.yaml` → `suppliers.default_lead_days`; an adapter may override with a real value from the page (`lead_source: page|default`).
- Suppliers Teddy actually uses: TME (api), Mouser (api), Comet (comet.bg, html), Vikiwat (vikiwat.com, html), Amazon.de (link only), Bauhaus and 3D Colour (link only / manual).
- Amazon.de blocks scrapers. **Do not fight it.** The `amazon_de` adapter returns the stored link, default lead days, `price: null`, `confidence: low`, and the report says "check price by hand".
- Secrets live only in GitHub → Settings → Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TME_TOKEN`, `TME_SECRET`, `MOUSER_API_KEY`. The agent must run with **none** of them set (adapters without a key are reported as `disabled`, Telegram falls back to stdout).

Known unknowns (do not guess): exact HTML of comet.bg / vikiwat.com search pages — fetch one page each, save it as a fixture, write the parser against the fixture; if a site refuses (403, captcha) or `robots.txt` disallows the search path, implement the adapter as link-only and say so in the PR.

## Files to create / change
```
parts/needs.yaml                         exists; do not change its schema without saying so in the PR
parts/README.md                          how to add a need, statuses, how to read the report, how to run locally
tools/parts/agent.py                     CLI: --dry-run (no Telegram, no commit, prints report) · --once (default) · --needs PATH
tools/parts/model.py                     dataclasses: Release, Need, Offer, Plan line; needs.yaml loader + validator
tools/parts/plan.py                      pure functions: order_by, slack_days, best_offer, diff(old_state, new_state) -> list[Alert]
tools/parts/adapters/__init__.py         registry; every adapter: search(query) -> list[Offer], fetch(url) -> Offer|None
tools/parts/adapters/tme.py              TME API (token+secret; HMAC signing per their docs)
tools/parts/adapters/mouser.py           Mouser Search API
tools/parts/adapters/comet.py            html search, fixture-tested
tools/parts/adapters/vikiwat.py          html search, fixture-tested
tools/parts/adapters/linkonly.py         amazon_de, bauhaus, 3dcolour: stored link, default lead, price null
tools/parts/notify.py                    telegram(text) with stdout fallback; one message per run, max 3500 chars
tools/parts/report.py                    renders parts/REPORT.md (markdown table) and the Telegram text
tools/parts/tests/                       pytest; fixtures/ holds one saved html page per shop; no network in tests
tools/parts/requirements.txt             requests, pyyaml, selectolax (or bs4); nothing heavier
.github/workflows/parts.yml              cron '7 4-20 * * *' (07–23 Sofia) + workflow_dispatch; see below
```

### Data model (keep it this small)
- `Release {id, date}`
- `Need {id, what, qty, for (release id), spec{}, queries{supplier: str}, links[], offers[] (manual), status need|ordered|received|skip, ordered (date|null), eta (date|null), note}`
- `Offer {need_id, supplier, title, url, price_eur (float|null), vat_added_by_code, stock (int|null), in_stock (bool|null), lead_days, lead_source, fetched_at, confidence high|medium|low}`
- `State` = `parts/state.json`: `{needs: {id: {best: Offer, offers: [Offer], order_by, slack_days, alerted: {kind: iso}}}, adapters: {name: {ok, error, at}}, run_at}`

### Rules in `plan.py` (all pure, all tested)
- `order_by(release.date, lead_days, safety_days=2)`; weekends are not shipping days: if the result lands on Sat/Sun move it to the Friday before.
- `slack_days = order_by − today`.
- `best_offer`: filter `in_stock != False`, then `arrives_by = today + lead_days ≤ release.date`, then lowest `price_eur` (null prices sort last), tie → preferred supplier order from `needs.yaml`.
- `diff` produces alerts, each with a `kind` and a one-line text:
  - `NEW_BEST` first offer found, or best supplier changed
  - `PRICE` best price moved more than 10 %
  - `OUT_OF_STOCK` best offer went out of stock
  - `ORDER_SOON` slack ≤ 3 days (once per day, not every hour)
  - `OVERDUE` slack < 0 and status still `need` (once per day)
  - `ETA_LATE` status `ordered` and (`eta` null or `eta` > release date − 1)
  - `RELEASE_AT_RISK` release within 2 days and any need for it not `received`
  - `ADAPTER_DOWN` adapter failed 3 runs in a row (once per day)
- Nothing to alert → no Telegram message, except the **07:00 digest** (first run of the day): one message with next three `order_by` dates and any adapter that is disabled or down.

### Behaviour of `agent.py`
1. Load and validate `needs.yaml` (unknown release id, duplicate need id, missing `for` → exit 2 with a clear message; the workflow turns that into a Telegram message "needs.yaml invalid: …").
2. Load `state.json` if present.
3. For every need with status `need`: run each adapter it has a query or link for; collect offers; manual `offers:` in the yaml count too.
4. For every need: compute `order_by`, `slack_days`, `best`.
5. `diff` → alerts. Write `state.json` and `parts/REPORT.md` (always, even if no alerts).
6. Send Telegram if alerts or digest time. Exit 0.
7. Politeness: ≤ 1 request/s per host, 10 s timeout, a real `User-Agent` naming the repo, obey `robots.txt` for html adapters. Whole run ≤ 60 requests.

### Workflow `parts.yml`
- Checks out `dev`, installs `tools/parts/requirements.txt`, runs `python tools/parts/agent.py` with the secrets as env.
- Commits `parts/state.json` and `parts/REPORT.md` to a **bot branch `parts-bot`** (create if missing, `git push --force-with-lease`), never to `dev` or `main`. Commit author `parts-bot <actions@github.com>`. The Telegram message links to `parts/REPORT.md` on that branch.
- `workflow_dispatch` input `dry_run: true` runs without commit or Telegram and prints the report in the job log.
- Budget note in the PR: ~17 runs/day × ~1 min ≈ 510 min/month of the free 2 000.

## Do not touch
`firmware/`, `cad/`, `pcb/`, `hardware/`, `scripts/check.sh`, `.github/workflows/check.yml`, `docs/`. Do not add Python deps outside `tools/parts/requirements.txt`. No LLM calls, no API keys in code, no checkout or cart automation of any kind.

## Tests — minimum
1. `order_by`: 16 Oct release, lead 3, safety 2 → 11 Oct (Sat) → moved to Fri 9 Oct.
2. `slack_days` negative when order_by is in the past.
3. `best_offer`: out-of-stock excluded; arrives-too-late excluded; cheapest wins; null price loses to a priced offer; tie broken by supplier preference.
4. VAT: net 10.00 → 12.00 with `vat_added_by_code: true`.
5. `diff`: each alert kind has one positive and one negative case; `ORDER_SOON` and `OVERDUE` fire once per day, not twice in two runs.
6. Loader: unknown release id → validation error naming the need id; `status: skip` needs are ignored by adapters but still listed in the report.
7. Each html adapter parses its fixture into ≥ 1 offer with title, url, price, in_stock; a fixture with no results → `[]`, not an exception.
8. `linkonly` returns price `null`, `confidence: low`, default lead days.
9. `report`: the dry-run report for the starter `needs.yaml` contains the example need, its `order_by` and the adapter status table.
10. Telegram text ≤ 3500 chars for 30 needs with alerts (truncates with "… +N more").

## Definition of done
- [ ] `python -m pytest -q tools/parts` → all pass, no network
- [ ] `python tools/parts/agent.py --dry-run` prints a report from the starter `needs.yaml` with no secrets set
- [ ] `.github/workflows/parts.yml` passes `actionlint` (or at minimum a `workflow_dispatch` dry run on the branch succeeds)
- [ ] `grep -r "TOKEN\|SECRET\|API_KEY" tools/parts parts | grep -v "os.environ\|README\|\.md"` → nothing
- [ ] `bash scripts/check.sh` → `check: OK`
- [ ] `parts/README.md` written: the five statuses, how to add a need in 30 seconds, how to run `--dry-run` in Cursor, what the five secrets are and how to get them
- [ ] PR to `dev`, title `tools: parts agent, hourly sourcing + order-by alerts (T4)`

## PR description must include
- which adapters are real (api / html) and which ended up link-only, and why
- the safety-days and default lead-days you shipped, marked `VERIFY: Teddy`
- the exact 5-minute setup for Teddy: BotFather, chat id, the five secrets, enabling the workflow
- open questions
