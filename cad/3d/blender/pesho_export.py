"""Pesho v3 for the Blender scene: the assembled dummy from cad/pesho/pesho.py, standing, feet at z = 0,
decimated to a few thousand triangles. Writes parts/pesho_body.stl (red PLA) and parts/pesho_head.stl (white PETG, head + lid).
Needs numpy, scikit-image, pyvista."""
import os, sys
import numpy as np
import pyvista as pv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "pesho"))
import pesho as P


def poly(name):
    v, f, _ = P.mesh(name)
    return pv.PolyData(v.astype(np.float32), np.hstack([np.full((len(f), 1), 3), f]).astype(np.int64))


body = poly("body")
head = poly("head").translate((0, 0, P.HEAD_Z0), inplace=False)
lid = poly("lid")
lid.points[:, 2] = (P.HEAD_Z0 + P.HH + 2.0) - lid.points[:, 2]      # the lid sits upside down on the head
for name, m, keep in (("pesho_body", body, 0.02), ("pesho_head", head + lid, 0.02)):
    m = m.triangulate().clean().decimate(1 - keep)
    m.compute_normals(auto_orient_normals=True, inplace=True)
    out = os.path.join(HERE, "parts", name + ".stl")
    m.save(out, binary=True)
    print(name, m.n_cells, "triangles", [round(float(b), 1) for b in m.bounds])
