# T6 · Watch lists in the parts agent (first list: thrusters for v2)

**Branch:** `night/thruster-watch` → PR to `dev`
**Budget:** ~2 h agent time, or 3 failed attempts at one step.
**Depends on:** T4 (parts agent, merged as PR #6). Python 3.12 only.

## Goal
Teddy wants the parts agent to keep looking for the most impressive thrusters for AR-Mini v2 (after 1 November). There is no deadline and no budget, so this is not a `need`. In the morning the agent also reads `parts/watch.yaml` (already in the repo, 4 seeded candidates). Once a day it does the following:
1. Refreshes price and stock of every stored offer.
2. Searches a few shops for new products and adds them as **unrated**.
3. Ranks each list by `rank_by`.
4. Writes a "Watch" section into `parts/REPORT.md`.

Telegram gets the changes only in the daily digest: a new candidate, a price move over 10 %, a stock change, or a new #1.

No LLM in the loop. "Looks impressive" is a human judgment. It is stored as `features` per item, and the score is the sum of `wow_points` from the yaml, so the ranking is deterministic and testable.

## Context
Read: `.cursor/rules/ar-mini.mdc`, `tasks/night/README.md`, `tasks/night/2026-10-09_T4_parts-agent.md`, `parts/README.md`, `parts/watch.yaml`, all of `tools/parts/`.

Facts with source:
- `parts/watch.yaml` schema is in the file itself (lists → items → offers). Prices there are the 2026-10-10 manual check, with URLs. Keep the file's schema; propose changes in the PR, do not silently rename keys.
- Ranking: `wow` = sum of `wow_points[f]` for `f` in `features` (confirmed features only). Ties are broken by `thrust_kgf_12v / mass_g`, where null sorts last. Then by the lowest price in EUR, where unknown sorts last.
- Seed ranking that the tests must reproduce:
  - W003 (wow 5);
  - W001 (3, 2.1 kgf / 175 g = 12.0 g/g);
  - W002 (3, 3.71 / 344 = 10.8);
  - W004 (0).
- Currency: `fx_to_eur` holds fixed rates set by hand; null means the report shows the original currency only and the EUR cell says `?`. `vat_included: false` with `import: true` means the report adds "+ import VAT 20 % on arrival". Do not fetch exchange rates from the internet.
- The watch run happens **only on the first run of the day** (reuse `is_first_run_today`) or with `--watch` on the CLI. It has its own budget of **≤ 20 requests**, inside the existing 60 per run.
- A broken `watch.yaml` must **not** stop the needs part. Report `watch.yaml invalid: …` in the digest and the report, then continue. Exit code stays 0 for that case. `needs.yaml` invalid is still exit 2.

Shops (adapters). For each one, fetch ONE real page first, save it as a fixture, and write the parser against the fixture. If `robots.txt` disallows the path, or the site answers 403 or a captcha, make it link-only and say so in the PR.
- `robotshop_eu` (eu.robotshop.com, looks like Shopify):
  - Try the product JSON (`<product url>.js`) for price and `available`.
  - Try predictive search (`/search/suggest.json?q=…&resources[type]=product`) for discovery.
  - The page shows prices "tax included". Confirm against the fixture.
- `bluerobotics` (bluerobotics.com, WooCommerce): try the public Store API `/wp-json/wc/store/v1/products?search=…`. Prices are in USD without VAT.
- `hydromea` (hydromea.com, Wix product pages): try the JSON-LD `offers` on the product page. For discovery, use the category page `/category/diskdrive-50-products`.
- `rc_terminal` (rc-terminal.de): JSON-LD on the product page if present. Discovery is the shop search for `Jetantrieb`, or link-only if not parseable.
- `ebay_de`, `vxb`: **link-only** (stored price, `confidence: low`). Do not scrape eBay.

Discovery filters:
- The title must contain one of: thruster, jet, jetantrieb, diskdrive, rim (case-insensitive).
- Drop any title containing a word from `exclude_words`.
- Drop URLs already in the list, compared without the query string.
- A new product gets the next free `W###`, `status: unrated`, and `features_guessed` from the title: `rim|hubless` → rim_driven; `jet` → waterjet; `azimuth|steer|lenkbar|vector` → steerable.
- Guessed features are shown but **never counted** in `wow` until a human moves them to `features`.
- Discovered items live in `state.json` (branch `parts-bot`), not in `watch.yaml`. The agent never edits the yaml. Cursor does that when Teddy says "add watch:" or "rate".

## Files to create / change
```
tools/parts/watch.py                 loader + validator for watch.yaml, wow score, ranking, discovery filter, diff → WatchAlert
tools/parts/adapters/robotshop_eu.py  fixture-tested (or link-only, see above)
tools/parts/adapters/bluerobotics.py  fixture-tested (or link-only)
tools/parts/adapters/hydromea.py      fixture-tested (or link-only)
tools/parts/adapters/rc_terminal.py   fixture-tested (or link-only)
tools/parts/adapters/linkonly.py      add hosts: ebay.de, vxb.com
tools/parts/adapters/__init__.py      register the new adapters
tools/parts/agent.py                  --watch flag; run watch on the first run of the day; state["watch"]; keep exit codes
tools/parts/report.py                 "## Watch · <list title>" section + "Unrated (found by the agent)" table + digest lines
tools/parts/tests/test_watch.py       + fixtures/ for each html/json adapter
parts/README.md                       a "Watch lists" section: what it is, the 4 Cursor phrases, how ranking works
```

Report table per list:
`Rank | ID | Name | Wow (features) | Thrust @12 V | Current @12 V | Mass | Size | Best price (orig → EUR) | Stock | Checked | Fit`

Below it: "Unrated (found by the agent)" with the guessed features, then "Rejected" (name + why).

Alerts, digest only, never hourly. Each alert fires once per day at most:
- `WATCH_NEW`: a new unrated product found.
- `WATCH_PRICE`: the best price of an item moved more than 10 %.
- `WATCH_STOCK`: in stock ↔ out of stock.
- `WATCH_TOP`: rank 1 of a list changed.

## Do not touch
- `parts/needs.yaml` and its loader rules.
- `plan.py` order-by logic.
- `.github/workflows/parts.yml`. It already runs hourly and `pull_request` already covers `parts/**`. Change it only if a test proves you must, and explain in the PR.
- Also: `firmware/`, `cad/`, `pcb/`, `hardware/`, `docs/`, `scripts/check.sh`.
- No LLM calls. No new secrets. No checkout or cart automation of any kind.

## Tests — minimum
1. Loader: the seeded `parts/watch.yaml` loads. Duplicate item id → error naming it. Unknown feature (not in `wow_points`) → error naming item and feature.
2. Wow + ranking reproduce the seed order W003, W001, W002, W004.
3. Guessed features do not change `wow`. Moving one into `features` does.
4. Discovery filter:
   - "T200 Thruster" kept;
   - "T200 Propeller Set" dropped;
   - "DISKDRIVE 50 Duct" dropped;
   - an already-listed URL with `?variant=…` dropped;
   - "Rim Driven Thruster RDT-60" kept with `rim_driven` guessed.
5. Currency: USD offer with `fx_to_eur.USD: null` → EUR `?`. With 0.9 → 0.9 × price. `vat_included: false` + `import: true` → note "+ import VAT 20 %".
6. Each new adapter parses its fixture. An empty-result fixture → `[]`, not an exception.
7. Watch runs only on the first run of the day. With `--watch` it runs anyway. Watch requests ≤ 20.
8. Broken watch.yaml → needs report still produced, exit 0, digest contains `watch.yaml invalid`.
9. Each WATCH_* alert: one positive and one negative case, at most once per day.
10. `--dry-run --offline` prints the Watch section from the seeded yaml with stored prices.

## Definition of done
- [ ] `python -m pytest -q tools/parts` → all pass, no network (the 57 existing tests still pass)
- [ ] `python tools/parts/agent.py --dry-run --offline --watch` prints "## Watch · Thrusters for AR-Mini v2" with W003 first
- [ ] `python tools/parts/agent.py --dry-run --watch` (network) shows which adapters were real and which link-only
- [ ] `bash scripts/check.sh` → `check: OK`
- [ ] `parts/README.md` has the Watch section
- [ ] PR to `dev`, title `tools: parts agent watch lists, thrusters for v2 (T6)`

## PR description must include
- which shop adapters are real (json/html) and which ended up link-only, and why
- the dry-run Watch table (paste it)
- anything in `watch.yaml` the agent could not parse or had to guess
- open questions for Teddy
