#!/usr/bin/env python3
"""Pesho v3, the AR-Mini rescue dummy (1:9), built from signed-distance fields.

This file is the single source for Pesho (it replaces dummy_head / dummy_lid in AR-Mini_v1.scad).
Why Python and not OpenSCAD: OpenSCAD cannot run in the cloud workspace, and the floating check
below needs the same geometry anyway.

Three printed parts
  body  red PLA    the life vest is the float: torso + shoulder ring, printed sealed (3 walls, 10 % infill);
                   the legs are flooded shells with an M12 pocket in each boot (up to 3 nuts each);
                   arms out and down at 45° (a starfish float), 155 mm span, so they rest on both cradle rods (112 apart).
  head  white PETG the hand-warmer capsule (warmer rolled against the wall, chimney vents, engraved face).
                   PETG because the warmer reaches ~50 °C and PLA starts to soften at 55–60.
  lid   white PETG the helmet top with 6 vent slots, push fit.

Ballast: M12 nuts in the boot pockets, held by a 1.75 mm filament piece pushed through the cross hole under them.
  thermal test  3 + 3: almost upright (~12° back), the whole head out of the water
  cradle test   1 + 1: on his back (~85°), face ~2 cm out
  (python3 cad/pesho/pesho.py --float gives the numbers; warmer and nut weighed 12.10)

Run
  python3 cad/pesho/pesho.py            STLs into build/ (pesho_body.stl, pesho_head.stl, pesho_lid.stl)
  python3 cad/pesho/pesho.py --float    floating table for the ballast cases
  python3 cad/pesho/pesho.py --render   PNG views into build/
Needs numpy, scipy (render only) and scikit-image.
"""
import argparse
import os
import struct
import sys

import numpy as np

# ---------------------------------------------------------------- measured / to measure
WARMER_L, WARMER_W, WARMER_T = 82.6, 52.3, 6.0   # Decathlon hand warmer, measured 12.10 through the wrapper; thickness: MEASURE
WARMER_G = 45.0                                   # weighed 12.10: 45 g in its wrapper
NUT_G = 16.0                                      # M12 hex nut, weighed 12.10 (16 g -> ISO 4032 size, AF 18)
NUT_H = 10.8                                      # ISO 4032 height (DIN 934 is 10.0) -> pocket fits both
POCKET_AF = 19.4                                  # across flats: DIN 934 M12 = 19, ISO 4032 = 18 (the pin holds either)
PIN_D = 2.2                                       # cross hole for a 1.75 mm filament piece
PLA, PETG = 1.24, 1.27                            # g/cm3
WALL = 1.2                                        # slicer walls (3 x 0.4) for the mass estimate
INFILL = 0.10

# ---------------------------------------------------------------- head (v2 of 12.10, wall 1.2 instead of 1.6)
HD = 46.0; HWALL = 1.2; HFLOOR = 1.6; PLENUM = 5.0; LEDGE = 2.5; PLUG = 4.0
BORE = HD - 2 * HWALL                                                  # 43.6
HH = HFLOOR + PLENUM + LEDGE + np.ceil(WARMER_W) + 2 + PLUG            # 68.1
BAND_Z, BAND = 50.0, 1.4                                              # helmet band: top 18 mm stand 1.4 proud

# ---------------------------------------------------------------- body
LEG_X = 15.0                       # leg centres
LEG_H = (12.5, 14.0)               # leg half sizes x, y
LEG_TOP = 50.0
BOOT_C = (3.5, 7.0)                # boot centre y, z
BOOT_H = (13.5, 17.5, 7.0)
SHELL = 1.6                        # leg shell
SOLE = 2.0
POCKET_TOP = 3.6 + 3 * NUT_H + 0.4     # up to three nuts above the pin
PIN_Z = 2.5
CHEST_C, CHEST_H = (0, 2.5, 92), (28, 22, 28)     # the vest: a bit deeper at the front, like a real life vest
WAIST_C, WAIST_H = (0, 2, 57), (25, 17, 11)
SHOULDER = (25.0, 4.0, 108.0)
ARM_A, ARM_L, ARM_R, HAND_R = 135.0, 62.0, 7.0, 8.5   # arms out and down at 45° (starfish float): under water they float, on the cradle they span both rods
RING_RO, RING_Z0, RING_TOP, RING_Y = 42.0, 104.0, 128.0, 2.0   # shoulder float ring (life-vest yoke): lifts the head out
CUP = 1.6
COLLAR_TOP = RING_TOP
HEAD_Z0 = RING_TOP - CUP           # head floor sits here in the assembly (126.4)


# ================================================================ SDF helpers (work on open grids or flat arrays)
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def rbox(x, y, z, c, h, r):
    qx = np.abs(x - c[0]) - (h[0] - r)
    qy = np.abs(y - c[1]) - (h[1] - r)
    qz = np.abs(z - c[2]) - (h[2] - r)
    out = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
    ins = np.minimum(np.maximum(np.maximum(qx, qy), qz), 0)
    return out + ins - r


def cyl(a, b, w, ca, cb, r, w0, w1):
    """capped cylinder, axis along w; (a, b) are the two other coordinates"""
    d = np.sqrt((a - ca) ** 2 + (b - cb) ** 2) - r
    e = np.maximum(w0 - w, w - w1)
    return np.minimum(np.maximum(d, e), 0) + np.sqrt(np.maximum(d, 0) ** 2 + np.maximum(e, 0) ** 2)


def capsule(x, y, z, a, b, r):
    bax, bay, baz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    pax, pay, paz = x - a[0], y - a[1], z - a[2]
    t = np.clip((pax * bax + pay * bay + paz * baz) / (bax * bax + bay * bay + baz * baz), 0, 1)
    return np.sqrt((pax - bax * t) ** 2 + (pay - bay * t) ** 2 + (paz - baz * t) ** 2) - r


def sphere(x, y, z, c, r):
    return np.sqrt((x - c[0]) ** 2 + (y - c[1]) ** 2 + (z - c[2]) ** 2) - r


def hex2(u, v, r):
    """2D hexagon, inradius r, flats facing +-v"""
    kx, ky, kz = -0.866025404, 0.5, 0.577350269
    u = np.abs(u); v = np.abs(v)
    d = np.minimum(kx * u + ky * v, 0)
    u = u - 2 * d * kx; v = v - 2 * d * ky
    u = u - np.clip(u, -kz * r, kz * r); v = v - r
    return np.sqrt(u * u + v * v) * np.sign(v)


def hexprism(flat_coord, other, axis, cf, co, af, w0, w1):
    d = hex2(other - co, flat_coord - cf, af / 2)
    e = np.maximum(w0 - axis, axis - w1)
    return np.minimum(np.maximum(d, e), 0) + np.sqrt(np.maximum(d, 0) ** 2 + np.maximum(e, 0) ** 2)


# ================================================================ parts
def head_sdf(x, y, z):
    r = np.sqrt(x * x + y * y)
    rout = HD / 2 + np.clip(z - (BAND_Z - BAND), 0, BAND)                  # helmet band with a 45° underside
    outer = np.maximum(np.maximum(r - rout, -z), z - HH)
    rb = BORE / 2
    cav = np.maximum(r - rb, np.maximum(HFLOOR - z, z - (HFLOOR + PLENUM)))                     # air space under the warmer
    z1 = HFLOOR + PLENUM
    cav = np.minimum(cav, np.maximum(r - (rb - (z - z1)), np.maximum(z1 - z, z - (z1 + LEDGE))))  # 45° ledge
    cav = np.minimum(cav, np.maximum(r - rb, (z1 + LEDGE) - z))                                   # warmer bay + mouth
    cav = np.minimum(cav, np.maximum(r - (rb - LEDGE), HFLOOR - z))                               # open core
    for k in range(6):                                                                            # inlets under the warmer
        a = np.radians(60 * k)
        t = x * np.cos(a) + y * np.sin(a)
        p = np.sqrt((-x * np.sin(a) + y * np.cos(a)) ** 2 + (z - (HFLOOR + PLENUM / 2)) ** 2)
        cav = np.minimum(cav, np.maximum(p - 1.5, 15 - t))
    # face, engraved 0.8 deep: arc length u around the front (+y), height v
    u = (HD / 2) * np.arctan2(x, y)
    deep = 22.2 - r
    for s in (-1, 1):
        cav = np.minimum(cav, np.maximum(np.sqrt((u - s * 9.0) ** 2 + (z - 39) ** 2) - 3.8, deep))
    smile = np.abs(np.sqrt(u * u + (z - 34) ** 2) - 9.0) - 1.0
    cav = np.minimum(cav, np.maximum(np.maximum(smile, z - 31.0), deep))
    return np.maximum(outer, -cav)


def lid_sdf(x, y, z):
    """printed top-down: z = 0 is the top of the helmet"""
    r = np.sqrt(x * x + y * y)
    R = HD / 2 + BAND
    flange = np.maximum(np.maximum(r - (R - np.maximum(0.8 - z, 0)), -z), z - 2.0)
    po = (BORE - 0.4) / 2
    plug = np.maximum(np.maximum(r - po, (po - 1.6) - r), np.maximum(1.9 - z, z - (2.0 + PLUG)))
    lid = np.minimum(flange, plug)
    cut = r - 3.0
    for k in range(6):
        a = np.radians(30 + 60 * k)
        t = x * np.cos(a) + y * np.sin(a)
        p = np.abs(-x * np.sin(a) + y * np.cos(a))
        cut = np.minimum(cut, np.maximum(p - 1.6, np.maximum(7 - t, t - 17)))
    return np.maximum(lid, -cut)


def body_sdf(x, y, z):
    # torso = the vest float
    t = smin(rbox(x, y, z, CHEST_C, CHEST_H, 10), rbox(x, y, z, WAIST_C, WAIST_H, 8), 6)
    for s in (-1, 1):
        t = np.minimum(t, rbox(x, y, z, (s * 12.5, CHEST_C[1] + CHEST_H[1], 94), (10.5, 2.5, 22), 2.5))   # vest panels
    front = CHEST_C[1] + CHEST_H[1] + 2.5                                                              # front face of the panels
    t = np.maximum(t, -np.minimum(rbox(x, y, z, (0, front, 80), (30, 0.6, 1.2), 0.3),
                                  rbox(x, y, z, (0, front, 100), (30, 0.6, 1.2), 0.3)))                # reflective stripes, 0.6 deep
    t = np.minimum(t, rbox(x, y, z, (-12.5, front, 90), (4.2, 1.0, 1.4), 0.4))                         # rescue cross on the left panel
    t = np.minimum(t, rbox(x, y, z, (-12.5, front, 90), (1.4, 1.0, 4.2), 0.4))
    t = np.minimum(t, rbox(x, y, z, (0, 3, 64), (26.6, 19.0, 3.2), 3))                                 # belt
    t = np.minimum(t, rbox(x, y, z, (0, 21.5, 64), (5, 1.6, 4.4), 1))                                  # buckle
    # shoulder float ring: round top, 45° underside from r 28 so it prints without supports
    r = np.sqrt(x * x + (y - RING_Y) ** 2)
    zc, hz, er = (RING_Z0 + RING_TOP) / 2, (RING_TOP - RING_Z0) / 2, 5.0
    qr, qz = r - (RING_RO - er), np.abs(z - zc) - (hz - er)
    ring = np.sqrt(np.maximum(qr, 0) ** 2 + np.maximum(qz, 0) ** 2) + np.minimum(np.maximum(qr, qz), 0) - er
    ring = np.maximum(ring, (RING_Z0 + np.maximum(r - 28, 0) - z) * 0.7071)
    t = smin(t, ring, 3)
    # arms in a Y, mitten hands
    a = np.radians(ARM_A)
    for s in (-1, 1):
        sh = (s * SHOULDER[0], SHOULDER[1], SHOULDER[2])
        hd = (sh[0] + s * ARM_L * np.sin(a), sh[1], sh[2] + ARM_L * np.cos(a))
        arm = np.minimum(capsule(x, y, z, sh, hd, ARM_R), sphere(x, y, z, hd, HAND_R))
        t = smin(t, arm, 5)
    # legs and boots
    legs = None
    for s in (-1, 1):
        lg = smin(rbox(x, y, z, (s * LEG_X, 0, LEG_TOP / 2), (LEG_H[0], LEG_H[1], LEG_TOP / 2), 4),
                  rbox(x, y, z, (s * LEG_X, BOOT_C[0], BOOT_C[1]), BOOT_H, 4), 3)
        legs = lg if legs is None else np.minimum(legs, lg)
    body = smin(t, legs, 3)
    # ---- cuts
    cut = cyl(x, y, z, 0, 0, HD / 2 + 0.3, COLLAR_TOP - CUP, COLLAR_TOP + 5)                           # cup for the head
    for s in (-1, 1):
        xc = s * LEG_X
        lg = smin(rbox(x, y, z, (xc, 0, LEG_TOP / 2), (LEG_H[0], LEG_H[1], LEG_TOP / 2), 4),
                  rbox(x, y, z, (xc, BOOT_C[0], BOOT_C[1]), BOOT_H, 4), 3)
        rxy = np.sqrt((x - xc) ** 2 + y ** 2)
        cav = np.maximum(np.maximum(lg + SHELL, SOLE - z), (z - (LEG_TOP - 3 - rxy)) * 0.7071)         # flooded leg, 45° roof
        tube = hexprism(x, y, z, xc, 0, POCKET_AF + 2 * SHELL, -1, POCKET_TOP + SHELL)
        cav = np.maximum(cav, -tube)
        cut = np.minimum(cut, cav)
        cut = np.minimum(cut, hexprism(x, y, z, xc, 0, POCKET_AF, -1, POCKET_TOP))                    # nut pocket (2 x M12)
        # flood holes, placed beside the pocket tube: water in, air out, upright or lying
        cut = np.minimum(cut, cyl(y, z, x, -9, 18, 2.0, *sorted((xc + s * 6, xc + s * 30))))            # outer side
        cut = np.minimum(cut, cyl(x, z, y, xc + s * 8, 30, 2.0, 6, 30))                                # front
        cut = np.minimum(cut, cyl(x, z, y, xc + s * 8, 30, 2.0, -30, -6))                              # back
        cut = np.minimum(cut, cyl(x, z, y, xc, LEG_TOP - 5.5, 1.25, -30, 0))                           # vent at the top of the roof
    cut = np.minimum(cut, cyl(y, z, x, 0, PIN_Z, PIN_D / 2, -40, 40))                                # pin, boots
    return np.maximum(np.maximum(body, -cut), -z)        # flat on the bed (the smooth blends bulge 0.75 below)


PARTS = {
    #        sdf       bounds (x0,x1, y0,y1, z0,z1)                    voxel  material
    "body": (body_sdf, (-80, 80, -42, 47, -1, 131), 0.45, PLA),
    "head": (head_sdf, (-26, 26, -26, 26, -1, 70), 0.30, PETG),
    "lid":  (lid_sdf,  (-26, 26, -26, 26, -1, 8), 0.25, PETG),
}


# ================================================================ meshing and STL
def grid(bounds, h):
    o = 0.0291 * h                     # keep grid points off the exact faces (no degenerate triangles)
    x = np.arange(bounds[0] + o, bounds[1] + h, h, dtype=np.float32)
    y = np.arange(bounds[2] + o, bounds[3] + h, h, dtype=np.float32)
    z = np.arange(bounds[4] + o, bounds[5] + h, h, dtype=np.float32)
    return x, y, z


def field(name, h=None):
    f, b, hh, _ = PARTS[name]
    h = h or hh
    x, y, z = grid(b, h)
    d = f(x[:, None, None], y[None, :, None], z[None, None, :]).astype(np.float32)
    return d, (x, y, z), h


def mesh(name):
    from skimage.measure import marching_cubes
    d, (x, y, z), h = field(name)
    v, f, _, _ = marching_cubes(d, 0.0, spacing=(h, h, h))
    v += np.array([x[0], y[0], z[0]], dtype=np.float32)
    v, inv = np.unique(v.astype(np.float32), axis=0, return_inverse=True)   # weld vertices as the STL stores them
    f = inv.reshape(-1)[f]
    f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]   # collapse the odd sliver
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0
    if vol < 0:
        f = f[:, ::-1]
        vol = -vol
    return v, f, vol


def write_stl(path, v, f):
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(f), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
    rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
    with open(path, "wb") as fh:
        fh.write(b"AR-Mini Pesho v3 (cad/pesho/pesho.py)".ljust(80, b" "))
        fh.write(struct.pack("<I", len(f)))
        fh.write(rec.tobytes())


# ================================================================ floating check
def assembly(h=0.7):
    """voxel model of the assembled Pesho, standing, feet at z = 0: occupancy and mass per voxel"""
    b = (-80, 80, -45, 48, -1, 205)
    x, y, z = grid(b, h)
    X, Y, Z = x[:, None, None], y[None, :, None], z[None, None, :]
    occ = np.zeros((len(x), len(y), len(z)), bool)
    lab = np.zeros(occ.shape, np.uint8)
    mass = np.zeros(occ.shape, np.float32)
    v = h ** 3 / 1000.0   # cm3 per voxel
    for nm, d, rho in (("body", body_sdf(X, Y, Z), PLA),
                       ("head", head_sdf(X, Y, Z - HEAD_Z0), PETG),
                       ("lid", lid_sdf(X, Y, (HEAD_Z0 + HH + 2.0) - Z), PETG)):
        ins = d < 0
        print(f"  {nm}: solid {ins.sum() * v:6.1f} cm3, mass {np.where(ins, np.where(d > -WALL, rho, rho * INFILL), 0).sum() * v:5.1f} g", file=sys.stderr)
        occ |= ins
        lab[ins] = {"body": 1, "head": 2, "lid": 2}[nm]
        dens = np.where(d > -WALL, rho, rho * INFILL)        # walls solid, inside 10 % infill (thin parts are all wall)
        mass += np.where(ins, dens * v, 0).astype(np.float32)
    assembly.labels = lab
    return (x, y, z), occ, mass, v


def floating(cases, h=1.0):
    (x, y, z), occ, mass, v = assembly(h)
    I, J, K = np.nonzero(occ)
    px, py, pz = x[I], y[J], z[K]
    pm = mass[I, J, K]
    pv = np.full(len(I), v)
    m_print = float(pm.sum())
    warm = (0.0, 0.0, HEAD_Z0 + HFLOOR + PLENUM + LEDGE + WARMER_W / 2)      # warmer centre
    warm_v = WARMER_L * WARMER_W * WARMER_T / 1000 * 0.9
    boot_nuts = [(s * LEG_X, 0.0, 3.6 + NUT_H * (k + 0.5)) for k in range(3) for s in (-1, 1)]
    out = []
    for label, nb in cases:
        pts = [warm] + boot_nuts[:nb]
        ms = [WARMER_G] + [NUT_G] * nb
        vs = [warm_v] + [NUT_G / 7.85] * nb
        X = np.concatenate([px, [p[0] for p in pts]]); Y = np.concatenate([py, [p[1] for p in pts]])
        Z = np.concatenate([pz, [p[2] for p in pts]])
        M = np.concatenate([pm, ms]); V = np.concatenate([pv, vs])
        Mt = M.sum()
        cg = np.array([(X * M).sum(), (Y * M).sum(), (Z * M).sum()]) / Mt
        res = []
        for th in np.radians(np.arange(-180, 181, 2)):
            up = np.array([0, np.sin(th), np.cos(th)])
            hgt = Y * up[1] + Z * up[2]
            o = np.argsort(hgt)
            cv = np.cumsum(V[o])
            i = np.searchsorted(cv, Mt)              # fresh water: 1 g displaces 1 cm3
            if i >= len(o):
                res.append((th, np.nan, np.nan)); continue
            sub = o[: i + 1]
            cb = np.array([(X[sub] * V[sub]).sum(), (Y[sub] * V[sub]).sum(), (Z[sub] * V[sub]).sum()]) / V[sub].sum()
            e = np.array([0, np.cos(th), -np.sin(th)])
            wl = hgt[o[i]]
            res.append((th, float((cb - cg) @ e), wl))
        res = np.array(res)
        eq = []
        for k in range(len(res) - 1):
            a, b = res[k, 1], res[k + 1, 1]
            if np.isfinite(a) and np.isfinite(b) and a > 0 >= b:
                th = res[k, 0] + (res[k + 1, 0] - res[k, 0]) * a / (a - b)
                eq.append((np.degrees(th), res[k, 2], -(b - a) / (res[k + 1, 0] - res[k, 0])))
        # how much of the head clears the water at the stable attitude
        details = []
        for thd, wl, k_stab in eq:
            th = np.radians(thd)
            up = np.array([0, np.sin(th), np.cos(th)])
            # lowest point of the head cylinder (radius 24.4) measured along 'up'
            low = min(HEAD_Z0 * up[2], (HEAD_Z0 + HH) * up[2]) - (HD / 2 + BAND) * abs(up[1])
            ang, hz = np.meshgrid(np.linspace(0, 2 * np.pi, 72, endpoint=False), np.linspace(0, HH, 30))
            sy, sz = 23.5 * np.cos(ang), HEAD_Z0 + hz                                        # head surface points (y, z)
            above = (sy * up[1] + sz * up[2]) > wl
            face = 23 * up[1] + (HEAD_Z0 + 38) * up[2] - wl                                  # between the eyes
            details.append(dict(angle=thd, wl=wl, head_low_above_water=low - wl, collar_above_water=COLLAR_TOP * up[2] - wl,
                                head_out=100 * above.mean(), face=face, stiffness=k_stab))
        out.append(dict(case=label, mass=Mt, print_mass=m_print, cg=cg, eq=details, nuts=pts[1:], warm=warm))
    return out


# ================================================================ render (ortho views by ray marching the SDF)
def render(path, h=0.35):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def scene(px, py, pz):
        d = body_sdf(px, py, pz)
        d = np.minimum(d, head_sdf(px, py, pz - HEAD_Z0))
        d = np.minimum(d, lid_sdf(px, py, (HEAD_Z0 + HH + 2.0) - pz))
        return d

    def view(az, el, W=520, H=760, span=(170, 250), cz=100):
        a, e = np.radians(az), np.radians(el)
        fwd = -np.array([np.cos(e) * np.sin(a), np.cos(e) * np.cos(a), np.sin(e)])  # camera looks along fwd
        right = np.array([np.cos(a), -np.sin(a), 0.0])
        upv = np.cross(fwd, right)
        us = np.linspace(-span[0] / 2, span[0] / 2, W)
        vs = np.linspace(span[1] / 2, -span[1] / 2, H)
        U, V = np.meshgrid(us, vs)
        org = np.array([0, 0, cz]) - fwd * 200
        P = org[None, None, :] + U[..., None] * right + V[..., None] * upv
        P = P.reshape(-1, 3)
        t = np.zeros(len(P)); hit = np.zeros(len(P), bool); act = np.ones(len(P), bool)
        for _ in range(160):
            idx = np.nonzero(act)[0]
            if len(idx) == 0:
                break
            q = P[idx] + fwd * t[idx, None]
            d = scene(q[:, 0], q[:, 1], q[:, 2])
            t[idx] += np.maximum(d, 0.05)
            hit[idx[d < 0.05]] = True
            act[idx[(d < 0.05) | (t[idx] > 420)]] = False
        q = P + fwd * t[:, None]
        eps = 0.25
        nx = scene(q[:, 0] + eps, q[:, 1], q[:, 2]) - scene(q[:, 0] - eps, q[:, 1], q[:, 2])
        ny = scene(q[:, 0], q[:, 1] + eps, q[:, 2]) - scene(q[:, 0], q[:, 1] - eps, q[:, 2])
        nz = scene(q[:, 0], q[:, 1], q[:, 2] + eps) - scene(q[:, 0], q[:, 1], q[:, 2] - eps)
        n = np.stack([nx, ny, nz], 1); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        light = -fwd * 0.6 + upv * 0.6 + right * 0.3; light /= np.linalg.norm(light)
        sh = np.clip(n @ light, 0, 1) * 0.75 + 0.25
        is_head = (q[:, 2] > HEAD_Z0 + 0.2) & (np.abs(q[:, 0]) < HD / 2 + BAND + 0.5) & (np.abs(q[:, 1]) < HD / 2 + BAND + 0.5)
        col = np.where(is_head[:, None], np.array([0.95, 0.95, 0.93]), np.array([0.80, 0.12, 0.10]))
        img = np.where(hit[:, None], col * sh[:, None], np.array([1, 1, 1]))
        return img.reshape(H, W, 3)

    views = [("front", 0, 8), ("3/4", 35, 18), ("side", 90, 5), ("back", 180, 10)]
    fig, axs = plt.subplots(1, 4, figsize=(16, 6.6), dpi=130)
    for ax, (nm, az, el) in zip(axs, views):
        ax.imshow(view(az, el)); ax.set_title(nm, fontsize=11); ax.axis("off")
    fig.suptitle("Pesho v3 (12.10): red PLA life-vest body, white PETG hand-warmer head + helmet lid", fontsize=13, x=0.01, ha="left")
    fig.savefig(path, bbox_inches="tight", facecolor="white")


def render_float(path, h=0.7):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import RegularPolygon, Rectangle
    cases = [("Thermal test: 3 + 3 nuts in the boots", 6), ("Cradle test: 1 + 1 nut in the boots", 2)]
    res = floating(cases, h)
    (x, y, z), occ, mass, v = assembly(h)
    lab = assembly.labels.max(axis=0).astype(float)            # side view: look along x
    lab[lab == 0] = np.nan
    Y, Z = np.meshgrid(y, z, indexing="ij")
    fig, axs = plt.subplots(1, 2, figsize=(13, 6.4), dpi=140)
    for ax, r in zip(axs, res):
        e = max(r["eq"], key=lambda q: q["angle"])               # the face-up one
        th = np.radians(e["angle"])
        S = Y * np.cos(th) - Z * np.sin(th)
        H = Y * np.sin(th) + Z * np.cos(th) - e["wl"]
        ax.axhspan(-150, 0, color="#cfe8f7", zorder=0)
        ax.axhline(0, color="#3b8fc4", lw=1.2, zorder=3)
        ax.pcolormesh(S, H, lab, cmap=matplotlib.colors.ListedColormap(["#c0392b", "#e8e8e3"]), vmin=1, vmax=2, shading="nearest", zorder=2)
        for p in r["nuts"]:
            ax.add_patch(RegularPolygon((p[1] * np.cos(th) - p[2] * np.sin(th), p[1] * np.sin(th) + p[2] * np.cos(th) - e["wl"]),
                                        6, radius=5, color="#333", zorder=4))
        w = r["warm"]
        ax.add_patch(Rectangle((w[1] * np.cos(th) - w[2] * np.sin(th) - 5, w[1] * np.sin(th) + w[2] * np.cos(th) - e["wl"] - 5), 10, 10,
                               angle=0, color="#f39c12", zorder=4))
        ax.set_aspect("equal"); ax.set_xlim(-150, 150); ax.set_ylim(-130, 130); ax.axis("off")
        ax.set_title(f"{r['case']}\n{r['mass']:.0f} g · leans back {e['angle']:.0f}° · head {e['head_out']:.0f} % out of the water · face {e['face']:+.0f} mm",
                     fontsize=10.5, loc="left")
        ax.text(-145, -120, "water", color="#3b8fc4", fontsize=9)
    fig.text(0.01, 0.01, f"Computed from the same geometry as the STLs (pesho.py --float). Assumed: warmer {WARMER_G:.0f} g, M12 nut {NUT_G} g, vest printed sealed "
             f"({WALL} mm walls, {INFILL:.0%} infill). Black hexagons = nuts, orange = warmer.", fontsize=8.5, color="#555")
    fig.savefig(path, bbox_inches="tight", facecolor="white")


# ================================================================ main
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "build"))
    ap.add_argument("--float", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--parts", default="body,head,lid")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.float:
        for r in floating([("no nuts", 0), ("cradle 1+1", 2), ("2+2", 4), ("thermal 3+3", 6)]):
            print(f"{r['case']:<18} total {r['mass']:6.1f} g (prints {r['print_mass']:5.1f} g)  CG z {r['cg'][2]:5.1f} y {r['cg'][1]:5.1f}")
            for e in r["eq"]:
                print(f"    stable at {e['angle']:6.1f} deg (0 upright, 90 on the back)  head surface out {e['head_out']:3.0f} %"
                      f"  face {e['face']:+5.1f} mm  head lowest {e['head_low_above_water']:+6.1f} mm  stiffness {e['stiffness']:.0f}")
        sys.exit(0)
    if a.render:
        render(os.path.join(a.out, "pesho_views.png"))
        render_float(os.path.join(a.out, "pesho_float.png"))
        sys.exit(0)
    for name in a.parts.split(","):
        v, f, vol = mesh(name)
        p = os.path.join(a.out, f"pesho_{name}.stl")
        write_stl(p, v, f)
        print(f"{name}: {len(f)} triangles, {vol / 1000:.1f} cm3 solid, {os.path.getsize(p) / 1e6:.1f} MB -> {p}")
