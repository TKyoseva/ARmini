# hardware/breadboard/src — the Python that drew the breadboard sheets

Drawn in the Claude workshop chat, 07–11.10.2026. `bb.py` holds the PIL primitives (A3 landscape, 300 dpi); the sheets import it. Fonts and part photos were those of that workspace (`/usr/share/fonts/opentype/inter/`, a local `bom_img3/` folder) — adjust the two paths at the top of `bb.py` / the sheet scripts to re-render.

| Script | Sheet |
|---|---|
| `sheet1.py` | 1 — motor & servo bench on the Mega 2560 (07.10) |
| `sheet2.py` | 2 — XIAO controller (07.10) |
| `sheet3.py` | 2b — DevKit-Lipo controller (10.10) |
| `ladder_step.py` | 2b ladder step — battery divider, leak probe, KILL rocker (C027, 11.10; matplotlib, no bb.py) |
| `v1_all.py` | 3 — v1, everything on one board (11.10; matplotlib) |

`docs/process/src/aiflow.py` (the build-process poster) also imports `bb.py` from here.
`AR-Mini_breadboards.pdf` one level up = sheets 1, 2, 2b as one print file.
