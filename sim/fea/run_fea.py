#!/usr/bin/env python3
"""AR-Mini C083 · static FEA of beam_leg and thruster_bracket: Gmsh mesh → CalculiX → numbers + plots.

  python3 sim/fea/run_fea.py            # needs gmsh, ccx (CalculiX 2.21), numpy, matplotlib

Linear elastic, so everything scales with the thrust: the solve uses F_REF and the report gives MPa per newton,
the safety factor at F_NOM and the thrust at which the safety factor would be SF_TARGET.
Units mm, N, MPa.
"""
import math
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")          # meshes and solver files, gitignored
RES = os.path.join(HERE, "results")      # the table and the two plots, committed

# --- Inputs (each with its source) -----------------------------------------------------------------------------
E, NU = 2100.0, 0.38     # PETG printed. SOURCE: project convention, FAILS_AND_FIXES 35 (E 2.1 GPa); nu = typical PETG
YIELD = 25.0             # MPa, "PETG printed" = half of the filament value. SOURCE: FAILS_AND_FIXES 35
SF_TARGET = 3.0          # SOURCE: FAILS_AND_FIXES 35
F_REF = 10.0             # N, the load in the solve
F_NOM = 20.0             # N, ASSUMED thrust of one Cuifati 560 KV at 12 V. NOT MEASURED → replace with C061.
# Geometry of the load path. SOURCE: cad/openscad/AR-Mini_v1.scad (th_*), beam_leg.scad
PIN = (19.0, 75.0)                   # hinge pin (x, z), bracket coordinates
TH_AFT, PLATE_DZ = 47.0, -29.5       # arm plate centre from the pin
AXIS_DZ = -4.1 - 75.0                # prop axis below the pin (th_axis_z − th_pivot_z) = −79.1
LOCK_R = 10.0
BL_X1, BL_ROW_MID = 513.7, 49.0      # beam_leg pad face x, centre of the deep rows 29/69
SKIP = 3.0                           # mm: ignore stress closer than this to a fixed or rigid-coupled face (constraint artefact)


def arm_statics(F):
    """Forces of the arm ON the bracket for a forward thrust F (thruster pushes the boat towards the bow = −x).
    The arm is held by the hinge pin (force only) and the M3 lock pin at radius LOCK_R (force ⟂ radius)."""
    a = math.atan2(PLATE_DZ, TH_AFT)
    lam = F * (-AXIS_DZ) / LOCK_R                      # lock-pin force magnitude
    L_on_arm = (lam * -math.sin(a), lam * math.cos(a))
    T = (-F, 0.0)
    P_on_arm = (-(T[0] + L_on_arm[0]), -(T[1] + L_on_arm[1]))
    lock_xy = (PIN[0] + LOCK_R * math.cos(a), PIN[1] + LOCK_R * math.sin(a))
    return {"pin": (-P_on_arm[0], -P_on_arm[1]), "lock": (-L_on_arm[0], -L_on_arm[1]), "lock_xy": lock_xy, "lam": lam}


def mesh(geo, h, tag):
    inp = os.path.join(OUT, f"{tag}_mesh.inp")
    subprocess.run(["gmsh", os.path.join(HERE, geo), "-3", "-setnumber", "h", str(h), "-format", "inp", "-o", inp],
                   check=True, capture_output=True)
    s = open(inp).read()
    nodes = {}
    nb = s.split("*NODE\n", 1)[1].split("*", 1)[0]
    for ln in nb.strip().splitlines():
        p = ln.split(",")
        nodes[int(p[0])] = tuple(map(float, p[1:4]))
    els = {}
    for m in re.finditer(r"\*ELEMENT, type=C3D10, ELSET=\w+\n([^*]*)", s):
        flat = [int(v) for v in re.findall(r"-?\d+", m.group(1))]
        for i in range(0, len(flat), 11):
            els[flat[i]] = flat[i + 1:i + 11]
    nsets = {}
    for m in re.finditer(r"\*NSET,NSET=(\w+)\n([^*]*)", s):
        nsets[m.group(1)] = [int(v) for v in re.findall(r"\d+", m.group(2))]
    used = {n for e in els.values() for n in e}
    nodes = {k: v for k, v in nodes.items() if k in used}
    return nodes, els, nsets


def write_deck(tag, nodes, els, nsets, fixed, loads):
    """loads: list of (nset name, ref xyz, force xyz). Each loaded set is a rigid body on a reference node."""
    nmax = max(nodes)
    L = ["*HEADING", f"AR-Mini C083 {tag}", "*NODE, NSET=NALL"]
    L += [f"{k}, {x:.6f}, {y:.6f}, {z:.6f}" for k, (x, y, z) in sorted(nodes.items())]
    refs = []
    for i, (name, xyz, f) in enumerate(loads):
        r, q = nmax + 1 + 2 * i, nmax + 2 + 2 * i
        L += [f"{r}, {xyz[0]:.6f}, {xyz[1]:.6f}, {xyz[2]:.6f}", f"{q}, {xyz[0]:.6f}, {xyz[1]:.6f}, {xyz[2]:.6f}"]
        refs.append((name, r, q, f))
    L.append("*ELEMENT, TYPE=C3D10, ELSET=BODY")
    L += [f"{k}, " + ", ".join(map(str, v)) for k, v in sorted(els.items())]
    for name in [fixed] + [l[0] for l in loads]:
        L.append(f"*NSET, NSET={name}")
        ns = nsets[name]
        L += [", ".join(map(str, ns[i:i + 12])) for i in range(0, len(ns), 12)]
    L += ["*MATERIAL, NAME=PETG", "*ELASTIC", f"{E}, {NU}", "*SOLID SECTION, ELSET=BODY, MATERIAL=PETG"]
    for name, r, q, _ in refs:
        L.append(f"*RIGID BODY, NSET={name}, REF NODE={r}, ROT NODE={q}")
    L += ["*BOUNDARY", f"{fixed}, 1, 3", "*STEP", "*STATIC", "*CLOAD"]
    for _, r, _, f in refs:
        L += [f"{r}, {d}, {v:.6f}" for d, v in zip((1, 2, 3), f) if abs(v) > 1e-12]
    L += ["*NODE FILE", "U", "*EL FILE", "S", "*NODE PRINT, NSET=NALL, TOTALS=ONLY", "RF", "*END STEP", ""]
    open(os.path.join(OUT, tag + ".inp"), "w").write("\n".join(L))
    return [r for _, r, _, _ in refs]


def read_frd(tag):
    disp, stress, block = {}, {}, None
    for ln in open(os.path.join(OUT, tag + ".frd")):
        if ln.startswith(" -4"):
            block = ln.split()[1]
        elif ln.startswith(" -3"):
            block = None
        elif ln.startswith(" -1") and block in ("DISP", "STRESS"):
            n = int(ln[3:13])
            v = [float(ln[13 + 12 * i:25 + 12 * i]) for i in range(6 if block == "STRESS" else 3)]
            (stress if block == "STRESS" else disp)[n] = v
    return disp, stress


def von_mises(s):
    xx, yy, zz, xy, yz, zx = s
    return math.sqrt(0.5 * ((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2) + 3 * (xy ** 2 + yz ** 2 + zx ** 2))


def solve(part, geo, h, fixed, loads):
    tag = f"{part}_h{h:g}"
    nodes, els, nsets = mesh(geo, h, tag)
    write_deck(tag, nodes, els, nsets, fixed, loads)
    r = subprocess.run(["ccx", tag], cwd=OUT, capture_output=True, text=True)
    if "Job finished" not in r.stdout:
        sys.exit(f"ccx failed for {tag}:\n{r.stdout[-2000:]}")
    disp, stress = read_frd(tag)
    ids = np.array(sorted(n for n in nodes if n in stress))
    xyz = np.array([nodes[n] for n in ids])
    vm = np.array([von_mises(stress[n]) for n in ids])
    u = np.array([np.linalg.norm(disp[n]) for n in ids])
    # distance to the nearest constrained node (fixed or rigid-coupled): stresses right at those nodes are artefacts
    con = np.array([nodes[n] for name in [fixed] + [l[0] for l in loads] for n in nsets[name] if n in nodes])
    from scipy.spatial import cKDTree
    d, _ = cKDTree(con).query(xyz)
    free = d > SKIP
    tot = re.findall(r"total force.*\n\s*\n?\s*([-\dEe.+]+)\s+([-\dEe.+]+)\s+([-\dEe.+]+)", open(os.path.join(OUT, tag + ".dat")).read())
    return dict(tag=tag, h=h, nodes=len(nodes), els=len(els), xyz=xyz, vm=vm, u=u, free=free, ids=ids, elmap=els,
                node_xyz=nodes, peak_all=vm.max(), peak=vm[free].max(), at=xyz[free][vm[free].argmax()],
                umax=u.max(), rf=tuple(map(float, tot[-1])) if tot else None, nsets=nsets, disp=disp)


def plot(res, title, path, view=(18, -60)):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    faces = {}
    for e in res["elmap"].values():
        a, b, c, d = e[:4]
        for f in ((a, b, c), (a, b, d), (a, c, d), (b, c, d)):
            k = tuple(sorted(f))
            faces[k] = None if k in faces else f
    vmn = dict(zip(res["ids"].tolist(), res["vm"].tolist()))
    tris, vals = [], []
    for f in faces.values():
        if f:
            tris.append([res["node_xyz"][n] for n in f])
            vals.append(sum(vmn.get(n, 0) for n in f) / 3)
    vals = np.array(vals) / F_REF * F_NOM
    fig = plt.figure(figsize=(11, 7.5), dpi=150)
    ax = fig.add_subplot(111, projection="3d")
    vmax = res["peak"] / F_REF * F_NOM
    pc = Poly3DCollection(tris, linewidths=0.05, edgecolors=(0, 0, 0, 0.15))
    pc.set_array(np.clip(vals, 0, vmax)); pc.set_cmap("viridis"); pc.set_clim(0, vmax)
    ax.add_collection3d(pc)
    P = res["xyz"]
    for i, s in enumerate("xyz"):
        getattr(ax, f"set_{s}lim")(P[:, i].min(), P[:, i].max())
    ax.set_box_aspect(np.ptp(P, axis=0)); ax.view_init(*view)
    ax.set_xlabel("x, mm"); ax.set_ylabel("y, mm"); ax.set_zlabel("z, mm")
    p = res["at"]
    ax.scatter([p[0]], [p[1]], [p[2]], color="red", s=40, depthshade=False)
    cb = fig.colorbar(pc, ax=ax, shrink=0.6, pad=0.02); cb.set_label(f"von Mises stress at {F_NOM:g} N thrust, MPa")
    ax.set_title(title, fontsize=11)
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RES, exist_ok=True)
    st = arm_statics(F_REF)
    axis = (BL_X1 + PIN[0] + TH_AFT, 0.0, BL_ROW_MID - 79.0 + PIN[1] + AXIS_DZ)   # prop axis on the beam_leg: z −34.1
    cases = {
        "beam_leg": ("beam_leg.geo", (4.0, 2.8, 2.0), "FIX", [("LOAD", axis, (-F_REF, 0, 0))]),
        "thruster_bracket": ("thruster_bracket.geo", (2.0, 1.4, 1.0), "FIX",
                             [("PIN", (PIN[0], 0, PIN[1]), (st["pin"][0], 0, st["pin"][1])),
                              ("LOCK", (st["lock_xy"][0], 0, st["lock_xy"][1]), (st["lock"][0], 0, st["lock"][1]))]),
    }
    rep = ["# C083 · FEA results (generated by run_fea.py)", "",
           f"PETG printed: E {E:g} MPa, nu {NU}, yield {YIELD:g} MPa. Solve at {F_REF:g} N, reported at the ASSUMED thrust {F_NOM:g} N.",
           f"Lock pin force = thrust × {-AXIS_DZ:g} / {LOCK_R:g} = {st['lam'] / F_REF:.2f} × thrust; hinge pin force = "
           f"{math.hypot(*st['pin']) / F_REF:.2f} × thrust.", ""]
    for part, (geo, hs, fixed, loads) in cases.items():
        runs = [solve(part, geo, h, fixed, loads) for h in hs]
        rep += [f"## {part}", "", "| mesh size, mm | nodes | elements | peak von Mises, MPa/N | at (x, y, z), mm | max deflection, mm/N | reaction sum, N |",
                "|---|---|---|---|---|---|---|"]
        for r in runs:
            rep.append(f"| {r['h']:g} | {r['nodes']} | {r['els']} | {r['peak'] / F_REF:.4f} | "
                       f"{r['at'][0]:.1f}, {r['at'][1]:.1f}, {r['at'][2]:.1f} | {r['umax'] / F_REF:.5f} | "
                       f"{', '.join(f'{v:.2f}' for v in r['rf']) if r['rf'] else 'n/a'} |")
            print(rep[-1])
        a, b = runs[-2]["peak"], runs[-1]["peak"]
        conv = abs(b - a) / b * 100
        k = b / F_REF
        rep += ["", f"Convergence, two finest meshes: {conv:.1f} % ({'OK' if conv <= 10 else 'NOT within 10 %'}).",
                f"At {F_NOM:g} N: peak {k * F_NOM:.2f} MPa, safety factor {YIELD / (k * F_NOM):.1f}, deflection {runs[-1]['umax'] / F_REF * F_NOM:.3f} mm.",
                f"Thrust at which the safety factor is {SF_TARGET:g}: {YIELD / SF_TARGET / k:.0f} N.", ""]
        print("\n".join(rep[-4:]))
        plot(runs[-1], f"AR-Mini {part} · von Mises at {F_NOM:g} N thrust (assumed) · peak {k * F_NOM:.2f} MPa, "
             f"SF {YIELD / (k * F_NOM):.1f} · mesh {runs[-1]['h']:g} mm", os.path.join(RES, f"C083_{part}_von_mises.png"),
             view=(18, -60) if part == "beam_leg" else (20, -50))
    # Hand check the FEA cannot give (the pins are rigid in the model): bearing pressure of the pins in the lug holes.
    lug_t, pin_d, lock_d = 6.0, 5.3, 3.3          # SOURCE: AR-Mini_v1.scad (lugs |y| 19..25, th_pin_d, th_lock_d)
    b_lock = st["lam"] / F_REF / (2 * lock_d * lug_t)
    b_pin = math.hypot(*st["pin"]) / F_REF / (2 * pin_d * lug_t)
    rep += ["## Hand check: pin bearing in the bracket lugs (force / (2 lugs × pin Ø × 6 mm))", "",
            f"Lock pin Ø{lock_d:g}: {b_lock:.3f} MPa/N → {b_lock * F_NOM:.2f} MPa at {F_NOM:g} N, safety factor {YIELD / (b_lock * F_NOM):.1f}; "
            f"safety factor {SF_TARGET:g} at {YIELD / SF_TARGET / b_lock:.0f} N.",
            f"Hinge pin Ø{pin_d:g}: {b_pin:.3f} MPa/N → {b_pin * F_NOM:.2f} MPa at {F_NOM:g} N, safety factor {YIELD / (b_pin * F_NOM):.1f}.", ""]
    print("\n".join(rep[-3:]))
    open(os.path.join(RES, "results.md"), "w").write("\n".join(rep) + "\n")


if __name__ == "__main__":
    main()
