# 3D model

- `AR-Mini_3D.html` — interactive model: open it in a browser. Rotate with the mouse, "Run the rescue lift", the name of every part on hover, view v1.8 (the collision) / v1.9.
- `AR-Mini_3D_renders.png` — 5 views (A3, 300 dpi); `AR-Mini_3D_hero.png` — one large view.
- `src/` — Python that builds the geometry from the same parameters as `cad/openscad/AR-Mini_v1.scad` (`armesh.py`), renders the views (`render.py`, `views.py`, `sheet.py`) and makes the HTML (`export.py` + `viewer_template.html`). Only numpy and Pillow are needed.

The hulls, beams, arch, brackets, arms, cradle and power box follow the SCAD. The ROB0154, thrusters, servos and boxes are simplified, at their measured size. The thruster in this model is still the old stand-in; the real one was measured in C001 (duct Ø72.27 × 112 mm) and is in CAD v2.0. The model will be regenerated from v2.0.
