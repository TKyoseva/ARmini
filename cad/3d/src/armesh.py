"""AR-Mini v1.8 geometry rebuilt from AR-Mini_v1.scad (units mm, SCAD frame: x aft, y port, z up).
Every part = dict(name, color, tris[N,3,3] in LOCAL frame, xf=transform spec, label).
xf: ('fixed',) | ('arm', pivot(x,y,z)) | ('cradle',) | ('dummy',)
"""
import numpy as np
from math import cos, sin, radians, sqrt, pi

# ---------------- parameters (from the SCAD) ----------------
hull_L, hull_W, hull_H, bow_len = 610, 100, 120, 150
wall, floor_t, cut_x, bulk_t, rib_t = 1.8, 2.0, 305, 3, 3
rib_x = [100, 200, 420, 520]; rim_h = 10; draft = 42
gap, beam = 250, 15
beam_x = [385, 500]; boss_x = [165, 200, 385, 500]
boss_w, boss_l, boss_h = 24, 30, 20
ch_L, ch_W, ch_H = 300, 230, 124.6
plate_L, plate_W, plate_t = 152.2, 134.8, 2
ch_x = 290; plate_x = ch_x + (ch_L - plate_L) / 2
motor_axis = 62
arch_x, arch_z, post_w = 165, 235, 20
tp_w, tp_h, tp_t, tp_z = 44, 44, 6, 25
pb_L, pb_W, pb_H, pb_lid_t = 152, 135, 66, 3
pivot_x, shaft_z, arm_len, arm_w, arm_t, arm_gap = 200, 105, 110, 12, 6, 22
deploy_a, stow_a, cradle_L = 215, 45, 220
servo = [40.5, 20.4, 28.0]; servo_shaft_off = 10.4; servo_ear_dx = 4.85; servo_ear_dz = 5; servo_top = 12.7
cam_tilt = 15

boss_y = gap / 2 + wall + boss_w / 2           # 138.8
vp = 6
blk_y0 = -vp - 3 - servo[2]                    # -37
arm_y = gap / 2 + blk_y0 - servo_top - 4       # 71.3
coupler_y = arm_y - arm_t - 4                  # 61.3
idler_y = coupler_y - 4                        # 57.3
beam_len = 2 * (boss_y + 13)                   # 303.6
hull_cy = gap / 2 + hull_W / 2                 # 175

def cradle_pos(alpha):
    cx = pivot_x + arm_len * cos(radians(alpha)); cz = shaft_z + arm_len * sin(radians(alpha))
    return cx, cz, cz - arm_gap - 12

# ---------------- colours (Dimi's PLA code + materials) ----------------
COL = dict(
    hull=(236, 233, 226),     # PETG hull
    hull_in=(214, 210, 200),
    seam=(70, 70, 70),
    black=(40, 40, 42),       # PLA black = structure
    orange=(242, 120, 20),    # PLA orange = moving parts
    alu=(196, 200, 206), alu_dk=(150, 155, 162),
    rubber=(30, 30, 32), wheel=(85, 88, 92), chassis=(70, 74, 80), motor=(200, 170, 70),
    blue=(40, 105, 200), blue_lt=(95, 150, 225),   # PLA blue = enclosures
    red=(205, 35, 35), red_dk=(160, 25, 25),       # Pesho
    servo=(30, 30, 34), servo_horn=(220, 220, 220),
    pcb_green=(30, 110, 60), pcb_blue=(30, 70, 170), lens=(15, 15, 15),
    ip65=(28, 28, 30), gland=(20, 20, 20), brass=(200, 160, 60), toggle=(200, 200, 205),
    prop=(60, 60, 64), cable=(25, 25, 25),
)

# ---------------- transforms ----------------
def T(x, y, z):
    m = np.eye(4); m[:3, 3] = [x, y, z]; return m
def Rx(a):
    a = radians(a); c, s = cos(a), sin(a); m = np.eye(4); m[1, 1] = c; m[1, 2] = -s; m[2, 1] = s; m[2, 2] = c; return m
def Ry(a):
    a = radians(a); c, s = cos(a), sin(a); m = np.eye(4); m[0, 0] = c; m[0, 2] = s; m[2, 0] = -s; m[2, 2] = c; return m
def Rz(a):
    a = radians(a); c, s = cos(a), sin(a); m = np.eye(4); m[0, 0] = c; m[0, 1] = -s; m[1, 0] = s; m[1, 1] = c; return m
def S(x, y, z):
    m = np.eye(4); m[0, 0], m[1, 1], m[2, 2] = x, y, z; return m
def apply(m, tris):
    t = tris.reshape(-1, 3); t = t @ m[:3, :3].T + m[:3, 3]; return t.reshape(-1, 3, 3)
def mirror_y(tris):
    t = tris.copy(); t[..., 1] *= -1; return t

# ---------------- primitives ----------------
def quad(a, b, c, d): return [[a, b, c], [a, c, d]]

def box(x0, y0, z0, x1, y1, z1):
    p = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    out = []
    for a, b, c, d in f: out += quad(p[a], p[b], p[c], p[d])
    return np.array(out, float)

def cyl(r, h, n=32, r2=None, caps=True, z0=0):
    """along +z from z0 to z0+h"""
    r2 = r if r2 is None else r2
    out = []
    ang = [2 * pi * i / n for i in range(n + 1)]
    for i in range(n):
        a, b = ang[i], ang[i + 1]
        p0 = [r * cos(a), r * sin(a), z0]; p1 = [r * cos(b), r * sin(b), z0]
        q0 = [r2 * cos(a), r2 * sin(a), z0 + h]; q1 = [r2 * cos(b), r2 * sin(b), z0 + h]
        out += quad(p0, p1, q1, q0)
        if caps:
            out.append([[0, 0, z0], p1, p0]); out.append([[0, 0, z0 + h], q0, q1])
    return np.array(out, float)

def tube(r_out, r_in, h, n=40, z0=0):
    out = []
    ang = [2 * pi * i / n for i in range(n + 1)]
    for i in range(n):
        a, b = ang[i], ang[i + 1]
        o0 = [r_out * cos(a), r_out * sin(a)]; o1 = [r_out * cos(b), r_out * sin(b)]
        i0 = [r_in * cos(a), r_in * sin(a)]; i1 = [r_in * cos(b), r_in * sin(b)]
        out += quad(o0 + [z0], o1 + [z0], o1 + [z0 + h], o0 + [z0 + h])
        out += quad(i1 + [z0], i0 + [z0], i0 + [z0 + h], i1 + [z0 + h])
        out += quad(o0 + [z0 + h], o1 + [z0 + h], i1 + [z0 + h], i0 + [z0 + h])
        out += quad(i0 + [z0], i1 + [z0], o1 + [z0], o0 + [z0])
    return np.array(out, float)

def cyl_between(p0, p1, r, n=24, caps=True):
    p0 = np.array(p0, float); p1 = np.array(p1, float); v = p1 - p0; h = np.linalg.norm(v); v /= h
    c = cyl(r, h, n, caps=caps)
    z = np.array([0, 0, 1.0]); ax = np.cross(z, v); s = np.linalg.norm(ax); co = np.dot(z, v)
    if s < 1e-9: R = np.eye(3) if co > 0 else np.diag([1, -1, -1])
    else:
        ax /= s; K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
        R = np.eye(3) + s * K + (1 - co) * K @ K
    return (c.reshape(-1, 3) @ R.T + p0).reshape(-1, 3, 3)

def sphere(r, n=24, m=16, sx=1, sy=1, sz=1):
    out = []
    for j in range(m):
        t0, t1 = pi * j / m, pi * (j + 1) / m
        for i in range(n):
            p0, p1 = 2 * pi * i / n, 2 * pi * (i + 1) / n
            def P(t, p): return [r * sx * sin(t) * cos(p), r * sy * sin(t) * sin(p), r * sz * cos(t)]
            a, b, c, d = P(t0, p0), P(t0, p1), P(t1, p1), P(t1, p0)
            if j == 0: out.append([a, c, d])
            elif j == m - 1: out.append([a, b, c])
            else: out += quad(a, b, c, d)
    return np.array(out, float)

def prism(poly, z0, z1, hole=None):
    """extrude a convex polygon (list of xy) z0..z1; with hole (same vertex count) -> ring"""
    poly = [list(p) for p in poly]; n = len(poly); out = []
    if hole is None:
        c = np.mean(poly, axis=0).tolist()
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            out += quad(a + [z0], b + [z0], b + [z1], a + [z1])
            out.append([c + [z0], b + [z0], a + [z0]]); out.append([c + [z1], a + [z1], b + [z1]])
    else:
        hole = [list(p) for p in hole]
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]; ia, ib = hole[i], hole[(i + 1) % n]
            out += quad(a + [z0], b + [z0], b + [z1], a + [z1])
            out += quad(ib + [z0], ia + [z0], ia + [z1], ib + [z1])
            out += quad(a + [z1], b + [z1], ib + [z1], ia + [z1])
            out += quad(ia + [z0], ib + [z0], b + [z0], a + [z0])
    return np.array(out, float)

def convex_hull2d(pts):
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def circles_hull(circs, n=32):
    pts = []
    for cx, cy, r in circs:
        pts += [(cx + r * cos(2 * pi * i / n), cy + r * sin(2 * pi * i / n)) for i in range(n)]
    return convex_hull2d(pts)

def offset_poly(poly, d):
    """inward offset of a CCW convex polygon by d (vertex-normal miter)"""
    P = np.array(poly, float); n = len(P); out = []
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        e1 = b - a; e2 = c - b
        n1 = np.array([-e1[1], e1[0]]) / np.linalg.norm(e1); n2 = np.array([-e2[1], e2[0]]) / np.linalg.norm(e2)
        m = n1 + n2; m /= np.linalg.norm(m); k = d / max(0.3, np.dot(m, n1))
        out.append((b + m * k).tolist())
    return out

def ccw(poly):
    P = np.array(poly); a = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    return poly if a > 0 else poly[::-1]

# ---------------- hull ----------------
def hull_outline(nb=28):
    pts = []
    for i in range(nb, 0, -1):          # port side bow, from shoulder to tip
        u = i / nb; pts.append((bow_len * u * u, hull_W / 2 * u))
    pts.append((0.0, 0.0))
    for i in range(1, nb + 1):
        u = i / nb; pts.append((bow_len * u * u, -hull_W / 2 * u))
    pts += [(hull_L, -hull_W / 2), (hull_L, hull_W / 2)]
    return ccw(pts)

def half_w(x):
    return hull_W / 2 * sqrt(min(1.0, x / bow_len))

def hull_parts():
    """left (port) hull, local -> global translate y=+175. Returns list of (name, color, tris)."""
    out = []
    o = hull_outline(); inn = offset_poly(o, wall)
    shell = prism(o, 0, hull_H, hole=inn)
    floor = prism(inn, 0, floor_t)
    out.append(('Hull (PETG, 2 × 305 mm sections)', 'hull', np.concatenate([shell])))
    out.append(('hull floor', 'hull_in', floor))
    for x in rib_x:
        w = half_w(x) - wall
        out.append(('rib', 'hull_in', box(x - rib_t / 2, -w, floor_t, x + rib_t / 2, w, hull_H - rim_h)))
    w = hull_W / 2 - wall
    out.append(('bulkheads', 'hull_in', box(cut_x - bulk_t, -w, floor_t, cut_x + bulk_t, w, hull_H)))
    # seam at the section joint (outside)
    out.append(('seam', 'seam', box(cut_x - 0.6, hull_W / 2, 0, cut_x + 0.6, hull_W / 2 + 0.5, hull_H)))
    out.append(('seam', 'seam', box(cut_x - 0.6, -hull_W / 2 - 0.5, 0, cut_x + 0.6, -hull_W / 2, hull_H)))
    out.append(('seam', 'seam', box(cut_x - 0.6, -hull_W / 2, -0.5, cut_x + 0.6, hull_W / 2, 0)))
    # rim bosses on the inner side (local -y)
    for x in boss_x:
        out.append(('boss', 'hull_in', box(x - boss_l / 2, -hull_W / 2 + wall, hull_H - boss_h, x + boss_l / 2, -hull_W / 2 + wall + boss_w, hull_H)))
    # thruster pad
    out.append(('thruster pad', 'hull', box(hull_L, -tp_w / 2, tp_z - tp_h / 2, hull_L + tp_t, tp_w / 2, tp_z + tp_h / 2)))
    return out

# ---------------- brackets & frame ----------------
def beam_bracket():
    w, d, fl = boss_l, 26, 6; h = fl + beam + 4
    return np.concatenate([box(-w / 2, -d / 2, 0, w / 2, d / 2, fl),
                           box(-w / 2, -d / 2, fl, -beam / 2 - 0.2, d / 2, h),
                           box(beam / 2 + 0.2, -d / 2, fl, w / 2, d / 2, h)])

def arch_post():
    h = arch_z - hull_H; H = h + beam + 4
    return np.concatenate([box(-post_w / 2, -13, 0, post_w / 2, 13, h),
                           box(-boss_l / 2, -13, 0, boss_l / 2, 13, 8),
                           box(-post_w / 2, -13, h, -beam / 2 - 0.2, 13, H),
                           box(beam / 2 + 0.2, -13, h, post_w / 2, 13, H)])

def pivot_bracket():
    pt = 6; zs = shaft_z - hull_H
    x0 = -servo_shaft_off - servo_ear_dx - 5; x1 = servo[0] - servo_shaft_off + servo_ear_dx + 5
    z0 = zs - arm_gap - 8
    parts = [box(-boss_l / 2, 0, 0, boss_l / 2, wall + boss_w, pt),
             box(-boss_l / 2, -vp, z0, boss_l / 2, 0, pt),
             box(x0, blk_y0, z0, x1, blk_y0 + servo[2] + 3, 0)]
    idler_boss = apply(T(0, blk_y0, zs - arm_gap) @ Rx(90), cyl(4.5, 16, 24))
    parts.append(idler_boss)
    return np.concatenate(parts)

def pivot_servo():
    """TD-8120MG / ST3215 body protruding from the bracket pocket + horn; local bracket frame"""
    zs = shaft_z - hull_H
    body = box(-servo_shaft_off, blk_y0 - servo_top, zs - servo[1] / 2, servo[0] - servo_shaft_off, blk_y0 + 2, zs + servo[1] / 2)
    ears = box(-servo_shaft_off - servo_ear_dx - 3, blk_y0 - 2.5, zs - servo[1] / 2, servo[0] - servo_shaft_off + servo_ear_dx + 3, blk_y0, zs + servo[1] / 2)
    horn = apply(T(0, blk_y0 - servo_top, zs) @ Rx(90), cyl(9, 3, 28))
    pin = apply(T(0, blk_y0, zs - arm_gap) @ Rx(90), cyl(1.6, servo[2] + 18, 12))
    return np.concatenate([body, ears]), horn, pin

def arm_local(drive):
    """arm in the pivot-local frame at alpha = 0 (pointing +x), extruded toward -y"""
    r0 = 14 if drive else arm_w / 2
    poly = ccw(circles_hull([(0, 0, r0), (arm_len, 0, arm_w / 2)], 40))
    a = prism(poly, 0, arm_t)                 # xy, z 0..6
    return apply(Rx(90), a)                   # -> x-z plane, y 0..-6

def coupler_local():
    poly = ccw(circles_hull([(0, 0, 7), (0, -arm_gap, 7)], 32))
    plate = apply(Rx(90), prism(poly, -4, 4))
    bossb = box(-8, -7, -arm_gap - 19, 8, 7, -arm_gap - 5)
    return np.concatenate([plate, bossb])

# ---------------- ROB0154 ----------------
def track_profile():
    circs = [(ch_x + 35, motor_axis, 35), (ch_x + 70, 22, 22), (ch_x + 150, 22, 22), (ch_x + 230, 22, 22), (ch_x + ch_L - 30, 30, 30)]
    return ccw(circles_hull([(x, z, r) for x, z, r in circs], 40)), circs

def chassis_parts():
    out = []
    prof, circs = track_profile()
    inner = offset_poly(prof, 8)
    tw = 40; ty = ch_W / 2 - tw                # track from y 75 to 115
    for s in (1, -1):
        belt = prism(prof, 0, tw, hole=inner)   # in x-z plane, extrude along "z" -> map to y
        belt = belt[..., [0, 2, 1]]             # (x, zprof, y) -> (x, y, z)
        belt[..., 1] += ty
        if s < 0: belt = mirror_y(belt)
        out.append(('ROB0154 track', 'rubber', belt))
        # grousers
        P = np.array(prof + [prof[0]]); seg = np.diff(P, axis=0); L = np.linalg.norm(seg, axis=1)
        cum = np.concatenate([[0], np.cumsum(L)]); tot = cum[-1]; gr = []
        for k in range(int(tot // 13)):
            d = k * 13; i = np.searchsorted(cum, d) - 1; i = max(0, min(i, len(L) - 1))
            t = (d - cum[i]) / L[i]; px, pz = P[i] + seg[i] * t; tx, tz = seg[i] / L[i]; nx, nz = tz, -tx
            ang = np.degrees(np.arctan2(tz, tx))
            g = box(-2, ty + 1, 0, 2, ty + tw - 1, 3)
            g = apply(T(px, 0, pz) @ Ry(-ang), g)
            gr.append(g)
        gr = np.concatenate(gr)
        if s < 0: gr = mirror_y(gr)
        out.append(('track grousers', 'rubber', gr))
        # wheels (visible from the inside / through the gap)
        wh = []
        for x, z, r in circs:
            wh.append(cyl_between((x, ty + 4, z), (x, ty + tw - 4, z), r - 9, 28))
        wh = np.concatenate(wh)
        if s < 0: wh = mirror_y(wh)
        out.append(('wheels', 'wheel', wh))
        # side plate (inside the track)
        sp_poly = ccw(circles_hull([(ch_x + 35, motor_axis, 20), (ch_x + 70, 30, 14), (ch_x + 230, 30, 14), (ch_x + ch_L - 30, 32, 16), (plate_x + 10, ch_H - 6, 6), (plate_x + plate_L - 10, ch_H - 6, 6)], 24))
        spl = prism(sp_poly, 0, 3)[..., [0, 2, 1]]; spl[..., 1] += ty - 4
        if s < 0: spl = mirror_y(spl)
        out.append(('side plate', 'chassis', spl))
        # gear motor at the front sprocket
        mot = cyl_between((ch_x + 35, ty - 4, motor_axis), (ch_x + 35, ty - 50, motor_axis), 12.5, 28)
        gb = box(ch_x + 22, ty - 16, motor_axis - 14, ch_x + 48, ty - 4, motor_axis + 14)
        m = np.concatenate([mot, gb])
        if s < 0: m = mirror_y(m)
        out.append(('DC gear motor', 'motor', m))
    # top plate + posts to the side plates
    out.append(('ROB0154 top plate (bolts under the beams)', 'chassis', box(plate_x, -plate_W / 2, ch_H - plate_t, plate_x + plate_L, plate_W / 2, ch_H)))
    posts = []
    for x in (plate_x + 12, plate_x + plate_L - 12):
        for s in (1, -1):
            posts.append(box(x - 6, s * (plate_W / 2) - 4 if s > 0 else -plate_W / 2 - 4 + 0, 60, x + 6, s * (plate_W / 2) + 4 if s > 0 else -plate_W / 2 + 4, ch_H - plate_t))
    out.append(('chassis posts', 'chassis', np.concatenate(posts)))
    # bottom crossbars
    out.append(('chassis crossbar', 'chassis', box(ch_x + 60, -(ch_W / 2 - tw - 4), 18, ch_x + 72, ch_W / 2 - tw - 4, 30)))
    out.append(('chassis crossbar', 'chassis', box(ch_x + 220, -(ch_W / 2 - tw - 4), 18, ch_x + 232, ch_W / 2 - tw - 4, 30)))
    return out

# ---------------- power box / logic box ----------------
def power_box(z_base):
    cx = plate_x + plate_L / 2; out = []
    rails = []
    for bx in beam_x:
        for sgn in (-1, 1):
            x0 = bx + sgn * (beam / 2 + 0.3) + (-3 if sgn < 0 else 0)
            rails.append(box(x0, -pb_W / 2 + 8, z_base - 3, x0 + 3, pb_W / 2 - 8, z_base))
    out.append(('locating rails (v1.9)', 'blue', np.concatenate(rails)))
    t = 2.4
    walls = np.concatenate([box(cx - pb_L / 2, -pb_W / 2, z_base, cx + pb_L / 2, pb_W / 2, z_base + 2.4),
                            box(cx - pb_L / 2, -pb_W / 2, z_base, cx - pb_L / 2 + t, pb_W / 2, z_base + pb_H),
                            box(cx + pb_L / 2 - t, -pb_W / 2, z_base, cx + pb_L / 2, pb_W / 2, z_base + pb_H),
                            box(cx - pb_L / 2, -pb_W / 2, z_base, cx + pb_L / 2, -pb_W / 2 + t, z_base + pb_H),
                            box(cx - pb_L / 2, pb_W / 2 - t, z_base, cx + pb_L / 2, pb_W / 2, z_base + pb_H)])
    out.append(('Power box (v1.9, on the beams): fuse block + 2 × BTS7960', 'blue', walls))
    out.append(('power box lid', 'blue_lt', box(cx - pb_L / 2, -pb_W / 2, z_base + pb_H, cx + pb_L / 2, pb_W / 2, z_base + pb_H + pb_lid_t)))
    gl = []
    for i in range(6):
        y = -pb_W / 2 + pb_W * (i + 1) / 7
        gl.append(cyl_between((cx + pb_L / 2, y, z_base + pb_H * 0.55), (cx + pb_L / 2 + 10, y, z_base + pb_H * 0.55), 7.5, 6))
    out.append(('PG7 glands', 'gland', np.concatenate(gl)))
    tg = np.concatenate([cyl_between((cx - pb_L / 2, 0, z_base + pb_H * 0.6), (cx - pb_L / 2 - 8, 0, z_base + pb_H * 0.6), 7, 16),
                         cyl_between((cx - pb_L / 2 - 8, 0, z_base + pb_H * 0.6), (cx - pb_L / 2 - 26, 0, z_base + pb_H * 0.6 + 10), 2.2, 10)])
    out.append(('50 A main switch', 'toggle', tg))
    return out

def logic_box():
    out = []
    x0, x1 = 440, 590; y0, y1 = hull_cy - 55, hull_cy + 55; z0 = 146
    out.append(('Logic box IP65 150 × 110 × 70: XIAO + PCA9685 + BNO055', 'ip65', box(x0, y0, z0, x1, y1, z0 + 62)))
    out.append(('logic box lid', 'ip65', box(x0 - 1, y0 - 1, z0 + 62, x1 + 1, y1 + 1, z0 + 70)))
    sad = [box(x - 8, hull_cy - 50, hull_H, x + 8, hull_cy + 50, z0) for x in (455, 575)]
    out.append(('printed saddles', 'black', np.concatenate(sad)))
    gl = [cyl_between((x1, hull_cy + dy, z0 + 25), (x1 + 12, hull_cy + dy, z0 + 25), 8, 6) for dy in (-30, 0, 30)]
    out.append(('cable glands', 'gland', np.concatenate(gl)))
    return out

# ---------------- thrusters ----------------
def thruster(yc):
    z = tp_z; x0 = hull_L + tp_t
    parts = {}
    parts['mount'] = box(x0, yc - 18, z - 18, x0 + 6, yc + 18, z + 18)
    body = np.concatenate([cyl_between((x0 + 6, yc, z), (x0 + 50, yc, z), 15, 32),
                           cyl_between((x0 + 50, yc, z), (x0 + 58, yc, z), 15, 32)])
    hub = cyl_between((x0 + 58, yc, z), (x0 + 74, yc, z), 6, 20)
    duct = apply(T(x0 + 52, yc, z) @ Ry(90), tube(26, 23.5, 30, 48))
    struts = np.concatenate([apply(T(x0 + 66, yc, z) @ Rx(a), box(-1, -1.2, 5, 1, 1.2, 23.6)) for a in (0, 120, 240)])
    blades = np.concatenate([apply(T(x0 + 62, yc, z) @ Rx(a) @ Ry(25), box(-4, -1, 6, 4, 1, 22)) for a in (0, 120, 240)])
    return [('Cuifati 560 KV thruster', 'black', np.concatenate([body, duct, struts])),
            ('thruster mount', 'black', parts['mount']),
            ('propeller', 'prop', np.concatenate([hub, blades]))]

# ---------------- camera pan on the arch ----------------
def cam_pan():
    out = []
    c = beam / 2 + 5; bx = servo[0] + 2 * (servo_ear_dx + 5); by = servo[1] + 12; bz = servo[2] + 4
    zc = arch_z + beam / 2
    mount = np.concatenate([box(arch_x - c, -by / 2, zc - c, arch_x + c, by / 2, zc + c),
                            box(arch_x - bx / 2, -by / 2, zc + c, arch_x + bx / 2, by / 2, zc + c + bz)])
    out.append(('Camera pan mount (black PLA)', 'black', mount))
    ztop = zc + c + bz
    sv = box(arch_x - servo[0] / 2, -servo[1] / 2, ztop - 2, arch_x + servo[0] / 2, servo[1] / 2, ztop + servo_top)
    out.append(('Pan servo (ST3215 ID 3)', 'servo', sv))
    sx = arch_x - servo[0] / 2 + servo_shaft_off
    zp = ztop + servo_top
    out.append(('horn', 'servo_horn', apply(T(sx, 0, zp), cyl(9, 2.5, 24))))
    poly = ccw(circles_hull([(0, 0, 14), (-26, 0, 12)], 32))
    plate = apply(T(sx, 0, zp + 2.5), prism(poly, 0, 4))
    tab = apply(T(sx - 30, 0, zp + 2.5) @ Ry(-cam_tilt), box(0, -13, 0, 3, 13, 22))
    out.append(('Camera plate (orange PLA)', 'orange', np.concatenate([plate, tab])))
    # MLX90642-D45 on the tab, lens forward (-x)
    pcb = apply(T(sx - 30, 0, zp + 2.5) @ Ry(-cam_tilt), box(-1.6, -12, 4, 0, 12, 20))
    lens = apply(T(sx - 30, 0, zp + 2.5) @ Ry(-cam_tilt), cyl_between((-1.6, 0, 12), (-9, 0, 12), 4.5, 20))
    out.append(('MLX90642-D45 thermal camera', 'pcb_green', pcb))
    out.append(('lens', 'lens', lens))
    return out

# ---------------- Pesho ----------------
def pesho_local():
    """lying along x, centred on (0,0,0): head toward -x"""
    torso = apply(T(-50, 0, 0) @ Ry(90), cyl(19, 105, 32))
    tc0 = apply(T(-50, 0, 0), sphere(19, 24, 12, sx=0.5))
    tc1 = apply(T(55, 0, 0), sphere(19, 24, 12, sx=0.5))
    head = apply(T(-75, 0, 2), sphere(23, 28, 16))
    neck = apply(T(-62, 0, 0) @ Ry(90), cyl(11, 14, 20))
    legs = np.concatenate([apply(T(55, s * 9, -2) @ Ry(90), cyl(8, 45, 20)) for s in (1, -1)])
    arms = np.concatenate([apply(T(-42, s * 22, 0) @ Ry(90), cyl(6.5, 70, 18)) for s in (1, -1)])
    return [('Pesho — rescue dummy (red PLA head, hand warmer inside)', 'red', np.concatenate([head])),
            ('Pesho body (foam)', 'red_dk', np.concatenate([torso, tc0, tc1, neck, legs, arms]))]

# ---------------- MLX90640 110° on the cradle ----------------
def cradle_cam_local(cx, rod_z):
    x = cx - cradle_L
    brk = box(x - 4, -16, rod_z, x + 2, 16, rod_z + 26)
    pcb = box(x + 2, -14, rod_z + 6, x + 3.6, 14, rod_z + 22)
    lens = cyl_between((x + 3.6, 0, rod_z + 14), (x + 9, 0, rod_z + 14), 5, 20)
    return [('cradle camera bracket', 'black', brk), ('MLX90640 110° (cradle)', 'pcb_blue', pcb), ('lens', 'lens', lens)]

# ============================================================
def build(alpha=deploy_a, box_fix=True, with_dummy=True, dummy_follows=True):
    """returns parts with LOCAL tris and xf spec; use world() to place them."""
    parts = []
    def add(name, col, tris, xf=('fixed',), side=None):
        parts.append(dict(name=name, color=COL[col], col=col, tris=np.asarray(tris, float), xf=xf))
    # hulls
    for s in (1, -1):
        for n, c, t in hull_parts():
            t = apply(T(0, hull_cy, 0), t)
            add(n, c, t if s > 0 else mirror_y(t))
    # brackets, posts, beams, arch
    bb = []; ap = []
    for s in (1, -1):
        for bx in beam_x:
            t = apply(T(bx, boss_y, hull_H), beam_bracket()); bb.append(t if s > 0 else mirror_y(t))
        t = apply(T(arch_x, boss_y, hull_H), arch_post()); ap.append(t if s > 0 else mirror_y(t))
    add('Beam brackets (black PLA)', 'black', np.concatenate(bb))
    add('Arch posts (black PLA)', 'black', np.concatenate(ap))
    for bx in beam_x:
        add('Cross-beam Al 15 × 15 × 1', 'alu', box(bx - beam / 2, -beam_len / 2, hull_H + 6, bx + beam / 2, beam_len / 2, hull_H + 6 + beam))
    add('Arch tube Al 15 × 15', 'alu', box(arch_x - beam / 2, -beam_len / 2, arch_z, arch_x + beam / 2, beam_len / 2, arch_z + beam))
    for n, c, t in cam_pan(): add(n, c, t)
    # pivot brackets + servos + arms
    for s in (1, -1):
        g = T(pivot_x, gap / 2, hull_H)
        pb = apply(g, pivot_bracket()); sv, horn, pin = [apply(g, x) for x in pivot_servo()]
        if s < 0: pb, sv, horn, pin = [mirror_y(x) for x in (pb, sv, horn, pin)]
        add('Pivot bracket (black PLA)', 'black', pb)
        add('Lift servo (ST3215 ID 1/2)', 'servo', sv)
        add('servo horn', 'servo_horn', horn)
        add('idler pin', 'alu_dk', pin)
        for drive in (True, False):
            y = arm_y if drive else idler_y
            z = shaft_z if drive else shaft_z - arm_gap
            loc = arm_local(drive)
            if s < 0:
                loc = mirror_y(loc); y = -y
            add('Lift arm (orange PLA)' if drive else 'Idler arm (orange PLA)', 'orange', loc, xf=('arm', (pivot_x, y, z)))
    # cradle (coupler, rod, cam) at the deployed reference, moved by xf
    cx0, cz0, rz0 = cradle_pos(deploy_a)
    cp = []
    for s in (1, -1):
        t = apply(T(cx0, s * coupler_y, cz0), coupler_local()); cp.append(t)
    add('Couplers (orange PLA)', 'orange', np.concatenate(cp), xf=('cradle',))
    rod = [cyl_between((cx0 - cradle_L, s * coupler_y, rz0), (cx0 + 8, s * coupler_y, rz0), 2.5, 12) for s in (1, -1)]
    rod.append(cyl_between((cx0 - cradle_L, -coupler_y, rz0), (cx0 - cradle_L, coupler_y, rz0), 2.5, 12))
    add('Cradle rod Al Ø5 (220 × 123)', 'alu', np.concatenate(rod), xf=('cradle',))
    for n, c, t in cradle_cam_local(cx0, rz0): add(n, c, t, xf=('cradle',))
    # chassis
    for n, c, t in chassis_parts(): add(n, c, t)
    # boxes
    for n, c, t in power_box(hull_H + 6 + beam if box_fix else ch_H): add(n, c, t, xf=('pbox',))
    for n, c, t in logic_box(): add(n, c, t)
    # thrusters
    for s in (1, -1):
        for n, c, t in thruster(s * hull_cy): add(n, c, t)
    # dummy, placed on the deployed cradle
    if with_dummy:
        for n, c, t in pesho_local():
            add(n, c, apply(T(cx0 - cradle_L / 2 + 5, 0, rz0 + 2.5 + 19), t), xf=('cradle',) if dummy_follows else ('fixed',))
    return parts

def world(parts, alpha):
    cx0, cz0, _ = cradle_pos(deploy_a); cx, cz, _ = cradle_pos(alpha)
    out = []
    for p in parts:
        xf = p['xf']; t = p['tris']
        if xf[0] == 'arm':
            px, py, pz = xf[1]; t = apply(T(px, py, pz) @ Ry(-alpha), t)
        elif xf[0] == 'cradle':
            t = apply(T(cx - cx0, 0, cz - cz0), t)
        out.append(dict(p, tris=t))
    return out

if __name__ == '__main__':
    P = build()
    n = sum(len(p['tris']) for p in P)
    print(len(P), 'parts', n, 'triangles')
    W = world(P, deploy_a)
    allt = np.concatenate([p['tris'] for p in W]).reshape(-1, 3)
    print('bbox', allt.min(0).round(1), allt.max(0).round(1))
    print('cradle deployed', cradle_pos(deploy_a), 'stowed', cradle_pos(stow_a))
