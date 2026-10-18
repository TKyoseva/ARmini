# DRC rounds — carrier rev B (kicad-cli, KiCad 10.0.6 on the Mac)

| File | Date | Result |
|---|---|---|
| `2026-10-12_round1.rpt` | 12.10 | first generated board: 162 KB of violations (clearances, unconnected, courtyards) |
| `2026-10-12_round2.rpt` | 12.10 | second pass of gen.py |
| `2026-10-13_round3.rpt` | 13.10 | third pass; the remaining items were fixed in gen.py the same night |
| `2026-10-15_clean.rpt` | 15.10 | 0 violations / 0 unconnected / 0 footprint errors on the corrected U2 footprint (commit ddcb48b) — the file that went to the fit check and the order |
