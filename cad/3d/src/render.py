"""Software z-buffer renderer (numpy) with CAD outlines and translucent water."""
import numpy as np
from PIL import Image, ImageFilter
from math import radians, tan

def look_at(eye, target, up=(0, 0, 1)):
    eye = np.array(eye, float); target = np.array(target, float); up = np.array(up, float)
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return eye, r, u, f

def render(parts, eye, target, W=1600, H=1000, fov=30, water_z=None, ortho=None, bg=((246, 248, 251), (222, 230, 238)),
           light=(-0.45, -0.55, 0.75), outline=True, ss=2, water_alpha=0.5):
    Wr, Hr = W * ss, H * ss
    eye, r, u, f = look_at(eye, target)
    L = np.array(light, float); L /= np.linalg.norm(L)
    L2 = np.array([0.6, 0.3, 0.4]); L2 /= np.linalg.norm(L2)
    depth = np.full((Hr, Wr), np.inf); col = np.zeros((Hr, Wr, 3)); nid = np.full((Hr, Wr), -1, int)
    nrm = np.zeros((Hr, Wr, 3))
    focal = (Hr / 2) / tan(radians(fov) / 2)
    tri_all = []; col_all = []; pid_all = []
    for i, p in enumerate(parts):
        tri_all.append(p['tris']); col_all.append(np.tile(np.array(p['color'], float), (len(p['tris']), 1))); pid_all.append(np.full(len(p['tris']), i))
    tris = np.concatenate(tri_all); cols = np.concatenate(col_all); pids = np.concatenate(pid_all)
    # face normals
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]); ln = np.linalg.norm(n, axis=1); keep = ln > 1e-9
    tris, cols, pids, n = tris[keep], cols[keep], pids[keep], n[keep] / ln[keep, None]
    # camera space
    rel = tris - eye
    xc = rel @ r; yc = rel @ u; zc = rel @ f
    if ortho:
        sx = Wr / 2 + xc * (Hr / ortho); sy = Hr / 2 - yc * (Hr / ortho); inv = 1.0 / (zc + 1e-6)
    else:
        zc_safe = np.maximum(zc, 1.0)
        sx = Wr / 2 + focal * xc / zc_safe; sy = Hr / 2 - focal * yc / zc_safe; inv = 1.0 / zc_safe
    # view dir per face (to flip normals toward camera)
    cen = tris.mean(axis=1); vd = cen - eye if not ortho else np.tile(f, (len(tris), 1))
    flip = np.sum(n * vd, axis=1) > 0; n[flip] *= -1
    diff = np.clip(n @ L, 0, 1); diff2 = np.clip(n @ L2, 0, 1)
    vdn = vd / np.linalg.norm(vd, axis=1)[:, None]
    hv = L - vdn; hv /= np.linalg.norm(hv, axis=1)[:, None]; spec = np.clip(np.sum(n * hv, axis=1), 0, 1) ** 40
    shade = 0.50 + 0.52 * diff + 0.14 * diff2
    fcol = np.clip(cols * shade[:, None] + 255 * 0.18 * spec[:, None], 0, 255)
    # rasterize, near-to-far does not matter with z-buffer
    order = np.argsort(-np.mean(zc, axis=1))
    for t in order:
        x0, x1, x2 = sx[t]; y0, y1, y2 = sy[t]
        if min(zc[t]) < 1 and not ortho: continue
        xmin = int(max(0, np.floor(min(x0, x1, x2)))); xmax = int(min(Wr - 1, np.ceil(max(x0, x1, x2))))
        ymin = int(max(0, np.floor(min(y0, y1, y2)))); ymax = int(min(Hr - 1, np.ceil(max(y0, y1, y2))))
        if xmin > xmax or ymin > ymax: continue
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-9: continue
        X, Y = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
        a = ((y1 - y2) * (X - x2) + (x2 - x1) * (Y - y2)) / den
        b = ((y2 - y0) * (X - x2) + (x0 - x2) * (Y - y2)) / den
        c = 1 - a - b
        m = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
        if not m.any(): continue
        iv = a * inv[t, 0] + b * inv[t, 1] + c * inv[t, 2]
        z = 1.0 / iv
        sub = depth[ymin:ymax + 1, xmin:xmax + 1]
        upd = m & (z < sub)
        if not upd.any(): continue
        sub[upd] = z[upd]
        col[ymin:ymax + 1, xmin:xmax + 1][upd] = fcol[t]
        nid[ymin:ymax + 1, xmin:xmax + 1][upd] = pids[t]
        nrm[ymin:ymax + 1, xmin:xmax + 1][upd] = n[t]
    # background gradient
    g = np.linspace(0, 1, Hr)[:, None, None]
    bgc = np.array(bg[0], float) * (1 - g) + np.array(bg[1], float) * g
    hit = np.isfinite(depth)
    img = np.where(hit[..., None], col, bgc)
    # water: ray-plane intersection per pixel
    if water_z is not None and ortho and abs(f[2]) < 1e-3:
        # horizontal orthographic view: everything below the water plane is seen through water
        ii = np.arange(Hr) + 0.5
        zrow = (target[2] if False else (eye + 0)[2]) - (ii - Hr / 2) * ortho / Hr
        below = (zrow < water_z)[:, None] & np.ones((1, Wr), bool)
        wc = np.array([150, 195, 225], float)
        img[below & hit] = img[below & hit] * 0.62 + wc * 0.38
        img[below & ~hit] = img[below & ~hit] * 0.2 + wc * 0.8
        wl = np.abs(zrow - water_z) < (ortho / Hr) * 2.2
        img[wl, :] = img[wl, :] * 0.35 + np.array([30, 80, 140]) * 0.65
        water_z = None
    if water_z is not None:
        jj, ii = np.meshgrid(np.arange(Wr) + 0.5, np.arange(Hr) + 0.5)
        if ortho:
            ox = (jj - Wr / 2) * ortho / Hr; oy = -(ii - Hr / 2) * ortho / Hr
            orig = eye + ox[..., None] * r + oy[..., None] * u; dirs = np.broadcast_to(f, orig.shape)
        else:
            dx = (jj - Wr / 2) / focal; dy = -(ii - Hr / 2) / focal
            dirs = f + dx[..., None] * r + dy[..., None] * u; orig = np.broadcast_to(eye, dirs.shape)
        with np.errstate(divide='ignore', invalid='ignore'):
            tpl = (water_z - orig[..., 2]) / dirs[..., 2]
        wp = orig + dirs * tpl[..., None]
        # distance along view axis
        wdepth = np.sum((wp - eye) * f, axis=-1) if not ortho else tpl
        inwater = (tpl > 0)
        front = inwater & (wdepth < depth)
        if front.any():
            rr = np.hypot(wp[..., 0] - 300, wp[..., 1])
            fade = np.clip((rr - 650) / 1100.0, 0, 1)
            wc = np.array([140, 188, 222], float)[None, None, :] * np.ones_like(img)
            wc = wc * (1 - fade[..., None]) + bgc * np.ones_like(img) * fade[..., None]
            under = front & hit
            a = water_alpha
            img[under] = img[under] * (1 - a) + wc[under] * a
            over = front & ~hit
            img[over] = wc[over]
            # faint 100 mm grid on the water near the robot
            gx = np.abs(((wp[..., 0] + 5000) % 100) - 50) > 49.3
            gy = np.abs(((wp[..., 1] + 5000) % 100) - 50) > 49.3
            gm = over & (gx | gy) & (rr < 900)
            img[gm] = img[gm] * 0.96 + np.array([255, 255, 255]) * 0.04
            wl = hit & inwater & (np.abs(depth - wdepth) < 2.5)
            img[wl] = img[wl] * 0.4 + np.array([30, 80, 140]) * 0.6
    # outlines
    if outline:
        e = np.zeros((Hr, Wr), bool)
        for dy, dx in ((0, 1), (1, 0)):
            a_id = nid; b_id = np.roll(np.roll(nid, -dy, 0), -dx, 1)
            a_d = depth; b_d = np.roll(np.roll(depth, -dy, 0), -dx, 1)
            a_n = nrm; b_n = np.roll(np.roll(nrm, -dy, 0), -dx, 1)
            both = np.isfinite(a_d) & np.isfinite(b_d)
            dd = np.zeros_like(a_d); dd[both] = np.abs(a_d[both] - b_d[both]) / a_d[both]
            e |= (a_id != b_id) | (dd > 0.02) | ((np.sum(a_n * b_n, axis=-1) < 0.82) & (a_id >= 0) & (b_id >= 0))
        e &= (hit | np.roll(hit, 1, 0) | np.roll(hit, 1, 1))
        em = e.copy()
        if ss >= 2:
            em = e | np.roll(e, 1, 0) | np.roll(e, 1, 1) | np.roll(np.roll(e, 1, 0), 1, 1)
        img[em] = img[em] * 0.35 + np.array([25, 25, 30]) * 0.65
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    return out.resize((W, H), Image.LANCZOS)
