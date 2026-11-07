# AR-Mini · parts report

Generated 2026-11-07T18:48:46+02:00 (today 2026-11-07, Sofia). Written by `tools/parts/agent.py`; edit `parts/needs.yaml`, not this file. Prices EUR incl. 20 % VAT.

## Releases

| Release | Date | Days left | Needs open / total | Goal |
|---|---|---:|---|---|
| r2a | 2026-10-16 | -22 | 1 / 1 | thruster spins in bucket; coupon fits |
| r2b | 2026-10-19 | -19 | 0 / 0 | 4 sections + chassis float |
| r2c | 2026-10-22 | -16 | 0 / 0 | swims on remote |
| r3a | 2026-10-26 | -12 | 0 / 0 | thermal camera finds Pesho |
| r3b | 2026-10-29 | -9 | 0 / 0 | full cycle |
| r4 | 2026-10-31 | -7 | 0 / 0 | video + portfolio |

## Needs

| Need | What | Qty | Release | Status | Order by | Slack (d) | Best offer | Note |
|---|---|---:|---|---|---|---:|---|---|
| N001 | M4 x 16 socket head screws, stainless A2 (thruster frame to pad) | 8 | r2a | need | 2026-10-09 | -29 | no offer yet | length VERIFY: pad 5 + frame 9.68 → 16 or 20 (decision 0004) |

## All offers

| Need | Supplier | Price | Stock | Lead (d) | Conf. | Title |
|---|---|---|---|---:|---|---|
| — | — | — | — | — | — | no offers in this run |

## Adapters

| Adapter | Kind | State | Consecutive fails | Last error |
|---|---|---|---:|---|
| comet | html | ok | 0 |  |
| vikiwat | html | ok | 0 |  |
| tme | api | disabled | 0 | TME_TOKEN / TME_SECRET not set |
| mouser | api | disabled | 0 | MOUSER_API_KEY not set |
| amazon_de | link | ok | 0 |  |
| bauhaus | link | ok | 0 |  |
| 3dcolour | link | ok | 0 |  |

## Alerts this run

none

## Watch · Thrusters for AR-Mini v2 (after 1 November)

robotshop_eu link-only (eu.robotshop.com HTTP 403 captcha (Just a moment) on /robots.txt, 2026-10-10; product JSON not fetched); bluerobotics link-only (robots.txt Disallow: /wp-json/ (fetched 2026-10-10); Store API not fetched); hydromea html; rc_terminal link-only (WAF challenge page instead of the product (fetched 2026-10-10); no JSON-LD); ebay_de link-only (stored price; eBay is not scraped); vxb link-only (stored price; link-only); notes: hydromea https://www.hydromea.com/category/diskdrive-50-products: page had no offer with this URL; stored price kept

Watch requests this run: 4 (cap 20).

Ranked by wow, then thrust per gram at 12 V (null last), then lowest price in EUR (unknown last).

| Rank | ID | Name | Wow (features) | Thrust @12 V | Current @12 V | Mass | Size | Best price (orig → EUR) | Stock | Checked | Fit |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | W003 | [TFL B54270 jet drive, all-aluminium, 4-blade impeller d39](https://www.rc-terminal.de/TFL-Jetantrieb-B54270-Voll-Aluminium-fuer-RC-Rennboote-mit-4-Blatt-Alu-Impeller) | 5 (waterjet, steerable) | — | — | — | length 220 (130 inside the hull, ~90 outside) | 439.90 EUR → 439.90 EUR | no | stored | Needs a 110 x 55 intake in the hull bottom: breaks our rule 'no holes below the waterline', so a v2 hull would be designed around it. Racing-boat power, far more than we need. Story: the RNLI Shannon class uses twin Hamilton HJ364 waterjets instead of propellers, for manoeuvring alongside a casualty. |
| 2 | W001 | [Hydromea DiskDrive 50](https://www.hydromea.com/category/diskdrive-50-products) | 3 (rim_driven) | 2.1 kgf | — | 175 g | 82 x 95 x 15 | 649.00 USD → ? | ? | stored | 15 mm thick: could lie flat against the transom or sit in a slot in the hull. Needs its own ESC. Swiss shop: customs + 20 % import VAT on arrival. |
| 3 | W002 | [Blue Robotics T200](https://eu.robotshop.com/products/bluerobotics-t200-thruster-w-o-speed-controller) | 3 (published_data, rov_pedigree) | 3.71 kgf | 17 A | 344 g | d100 x 113 | 253.00 EUR → 253.00 EUR | yes | stored | d100 = the whole v1 hull width (100 mm). Two at 12 V draw 34 A, over our 30 A main fuse. Full curves published: our thrust rig can be checked against them. |
| 4 | W004 | [ApisQueen U2 mini (with 45 A ESC)](https://vxb.com/products/u2-mini-underwater-thruster-12-to-16v-130w-brushle) | 0 | — | — | 286 g | — | 99.99 USD → ? + import VAT 20 % on arrival | ? | stored | Same size class as the Cuifati we have. Here as the baseline the others are compared against. |

### Unrated (found by the agent)

| ID | Name | Guessed features | Price | URL |
|---|---|---|---|---|
| W005 | [DISKDRIVE™ 50](https://www.hydromea.com/product-page/diskdrive-50) | — | 649.00 USD → ? | https://www.hydromea.com/product-page/diskdrive-50 |

### Rejected

- MHZ Jet 58 steerable jet drive ([https://www.mhz-powerboats.com/Jet-58-Lenkbar-Jetantrieb/1723-58](https://www.mhz-powerboats.com/Jet-58-Lenkbar-Jetantrieb/1723-58)) — EUR 549, 760 g, needs 4.5-6 kW and a boat of at least 1.30 m
- Azimuth pod (off the shelf) ([https://www.printables.com/model/1631558-rc-tugboat-with-functional-azimuth-thrusters](https://www.printables.com/model/1631558-rc-tugboat-with-functional-azimuth-thrusters)) — no small ready-made unit found on 10.10; a 3D-printed design exists -> a v2 BUILD idea, not a purchase
