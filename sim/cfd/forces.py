#!/usr/bin/env python3
"""AR-Mini C085 · drag of the hull patch from a finished OpenFOAM case (ascii fields), without function objects.

  python3 forces.py <case dir>      → prints one JSON line

Same definition as OpenFOAM's `forces`: pressure part = Σ rho·p_cell·Sf (zeroGradient wall), viscous part = Σ rho·(nu + nut_wall)·(U_cell − U_wall)/d·|Sf|
on the wall faces of patch `hull` (Sf points out of the water into the hull, d = wall distance of the cell centre).
"""
import json
import os
import re
import sys

import numpy as np

RHO, NU = 998.2, 1.0e-6


def body(path):
    s = open(path).read()
    return s[s.index("}", s.index("FoamFile")) + 1:]


def read_list(text, width):
    m = re.search(r"\n(\d+)\s*\n?\(", text)
    n = int(m.group(1))
    a = text.index("(", m.start()) + 1
    b = text.rindex(")")
    vals = np.array(text[a:b].replace("(", " ").replace(")", " ").split(), dtype=float)
    return vals.reshape(n, width) if width > 1 else vals[:n]


def read_faces(text):
    m = re.search(r"\n(\d+)\s*\n?\(", text)
    a = text.index("(", m.start()) + 1
    return [list(map(int, f.split("(")[1].split())) for f in text[a:text.rindex(")")].split(")") if "(" in f]


def patch_block(text, name):
    m = re.search(r"\n\s*%s\s*\{" % name, text)
    i = text.index("{", m.start()); d = 0
    for j in range(i, len(text)):
        d += text[j] == "{"; d -= text[j] == "}"
        if d == 0:
            return text[i + 1:j]


def patch_values(field_text, name, width, n):
    blk = patch_block(field_text[field_text.index("boundaryField"):], name)
    m = re.search(r"value\s+nonuniform\s+List<\w+>\s*", blk)
    if not m:
        u = re.search(r"value\s+uniform\s+([^;]+);", blk)
        v = np.array(u.group(1).replace("(", " ").replace(")", " ").split(), dtype=float) if u else np.zeros(width)
        return np.tile(v, (n, 1)) if width > 1 else np.full(n, v[0])
    return read_list("\n" + blk[m.end():], width)


def main(case):
    t = max((d for d in os.listdir(case) if re.fullmatch(r"\d+", d) and d != "0"), key=int)
    pm = os.path.join(case, "constant", "polyMesh")
    pts = read_list(body(os.path.join(pm, "points")), 3)
    faces = read_faces(body(os.path.join(pm, "faces")))
    owner = read_list(body(os.path.join(pm, "owner")), 1).astype(int)
    neigh = read_list(body(os.path.join(pm, "neighbour")), 1).astype(int)
    hb = patch_block(body(os.path.join(pm, "boundary")), "hull")
    n = int(re.search(r"nFaces\s+(\d+)", hb).group(1)); s0 = int(re.search(r"startFace\s+(\d+)", hb).group(1))

    def face_geom(f):
        p = pts[f]; c0 = p.mean(axis=0); S = np.zeros(3); C = np.zeros(3); A = 0.0
        for i in range(len(f)):
            a, b = p[i], p[(i + 1) % len(f)]
            s = 0.5 * np.cross(a - c0, b - c0); m = np.linalg.norm(s)
            S += s; C += m * (a + b + c0) / 3; A += m
        return S, C / A

    wall_cells = owner[s0:s0 + n]
    need = set(wall_cells.tolist())
    cell_faces = {c: [] for c in need}
    for i, c in enumerate(owner):
        if c in need:
            cell_faces[c].append(i)
    for i, c in enumerate(neigh):
        if c in need:
            cell_faces[c].append(i)
    geom = {}
    def g(i):
        if i not in geom:
            geom[i] = face_geom(faces[i])
        return geom[i]
    cc = {}
    for c, fl in cell_faces.items():
        est = np.mean([g(i)[1] for i in fl], axis=0); V = 0.0; C = np.zeros(3)
        for i in fl:
            S, Cf = g(i)
            v = abs(np.dot(S, Cf - est)) / 3
            V += v; C += v * (0.75 * Cf + 0.25 * est)
        cc[c] = C / V

    ft = lambda name: body(os.path.join(case, t, name))
    U = read_list(ft("U")[:ft("U").index("boundaryField")], 3)
    p = read_list(ft("p")[:ft("p").index("boundaryField")], 1)   # hull patch is zeroGradient: wall p = cell p
    nut_w = patch_values(ft("nut"), "hull", 1, n)
    Fp = np.zeros(3); Fv = np.zeros(3); area = 0.0; yplus = []
    for k in range(n):
        S, Cf = g(s0 + k); A = np.linalg.norm(S); nrm = S / A
        c = wall_cells[k]; d = abs(np.dot(nrm, Cf - cc[c]))
        Ut = U[c] - np.dot(U[c], nrm) * nrm
        tau = RHO * (NU + nut_w[k]) * Ut / d
        Fp += RHO * p[c] * S; Fv += tau * A; area += A
        yplus.append(d * np.sqrt(np.linalg.norm(tau) / RHO) / NU)
    out = dict(case=os.path.basename(os.path.normpath(case)), iterations=int(t), wall_faces=n, wall_area_m2=round(area, 5),
               drag_pressure_N=round(float(Fp[0]), 5), drag_viscous_N=round(float(Fv[0]), 5),
               drag_N=round(float(Fp[0] + Fv[0]), 5), side_N=round(float(Fp[1] + Fv[1]), 5),
               yplus_mean=round(float(np.mean(yplus)), 1), yplus_max=round(float(np.max(yplus)), 1))
    print(json.dumps(out))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
