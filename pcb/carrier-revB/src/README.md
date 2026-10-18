# pcb/carrier-revB/src — the Python that checked rev B without KiCad

Made in the Claude workshop chat (13–15.10.2026, C032) while KiCad was only on the Mac. `gen.py` one level up writes the board; these read it back.

| Script | Does | Output |
|---|---|---|
| `sx.py` | tiny s-expression parser + `footprints()` for KiCad 9/10 files (`(net "NAME")` form) | — |
| `geom_export.py BOARD` | footprint/pad/net dump + summary: nets without tracks, segment widths, silk texts, Edge.Cuts | `fps.json` |
| `conn_check.py BOARD` | rough connectivity (union-find on endpoints), track widths per net, antenna keep-out, Edge.Cuts; **kicad-cli DRC is the authority** — nets that reach a pad through the GND pour report as split groups | `geom.json` |
| `assembled_view.py geom.json` | 2.5-D oblique render with real part heights (box clearance) | `AR-Mini_carrier_revB_assembled.png` |
| `fitcheck.py BOARD OUT.pdf` | pads-only 1:1 A4 sheet with a 100 mm bar and a 50 × 50 square — print at 100 %, push real pins through the paper (FAILS 152) | `AR-Mini_carrier_revB_fitcheck_1to1.pdf` |
| `mockup.py` | the placement mock-up drawn before the board existed (11.10) | `AR-Mini_carrier_revB_mockup.png` |
| `draw_u2_measure.py` | "what to measure on the PCA9685 module" instruction sheet (13.10) | `measure/U2_PCA9685_measure.png` |

Order used on 15.10: `gen.py` → `conn_check.py` → `fitcheck.py` → print → pins → (Mac) `kicad-cli pcb drc` → `drc/`.
Needs Python 3 + matplotlib; no KiCad.
