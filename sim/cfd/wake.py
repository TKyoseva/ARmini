#!/usr/bin/env python3
"""AR-Mini C085 · wake picture: speed on a horizontal cut at half draft, from a kept case converted by foamToVTK.

  foamToVTK -latestTime -case out/pair_U0.6 && python3 wake.py out/pair_U0.6 0.6
"""
import glob
import os
import sys

import numpy as np
import pyvista as pv

case, U = sys.argv[1], float(sys.argv[2])
HERE = os.path.dirname(os.path.abspath(__file__))
f = sorted(glob.glob(os.path.join(case, "VTK", "*", "internal.vtu")) + glob.glob(os.path.join(case, "VTK", "*.vtk")) +
           glob.glob(os.path.join(case, "VTK", "*.vtm")))[-1]
m = pv.read(f)
if isinstance(m, pv.MultiBlock):
    m = m.combine()
cut = m.slice(normal="z", origin=(0, 0, -0.0115)).cell_data_to_point_data()
p = cut.points; u = np.linalg.norm(cut["U"], axis=1) / U
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
tri = mtri.Triangulation(p[:, 0], p[:, 1])
# drop triangles that bridge the hull (long edges across the hole)
xy = np.c_[p[:, 0], p[:, 1]][tri.triangles]
edge = np.max(np.linalg.norm(xy - np.roll(xy, 1, axis=1), axis=2), axis=1)
tri.set_mask(edge > 0.06)
fig, ax = plt.subplots(figsize=(11, 4.6), dpi=150)
c = ax.tricontourf(tri, u, levels=np.linspace(0, 1.2, 25), cmap="viridis", extend="max")
# mirror: the other hull of the catamaran (symmetry plane y = 0.175 m)
tri2 = mtri.Triangulation(p[:, 0], 0.35 - p[:, 1], tri.triangles, mask=tri.mask)
ax.tricontourf(tri2, u, levels=np.linspace(0, 1.2, 25), cmap="viridis", extend="max")
ax.axhline(0.175, color="w", lw=0.6, ls="--")
ax.set_xlim(-0.3, 2.0); ax.set_ylim(-0.25, 0.60); ax.set_aspect("equal")
ax.set_xlabel("x from the bow, m (flow from the left)"); ax.set_ylabel("y, m")
fig.colorbar(c, ax=ax, shrink=0.8, label=f"water speed / {U:g} m/s")
ax.set_title(f"AR-Mini catamaran wake at {U:g} m/s, horizontal cut at half draft (C085, OpenFOAM, no waves)", fontsize=10)
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
fig.savefig(os.path.join(HERE, "results", "C085_wake.png"), bbox_inches="tight")
