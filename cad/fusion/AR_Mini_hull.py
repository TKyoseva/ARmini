"""
AmphiReach AR-Mini v1.6 - Fusion 360 script (synced with AR-Mini_v1.scad v1.6, 2.10.2026)
Builds the catamaran hull natively in Fusion (parametric timeline), same numbers as AR-Mini_v1.scad.

HOW TO RUN
  1. Fusion 360 > new Design (empty, mm units).
  2. Utilities > Add-Ins > Scripts and Add-Ins > Scripts > "+" (Create) > give it a name,
     Python, then replace the generated .py with this file.  Or: "+" next to "My Scripts",
     pick the folder that contains this file.
  3. Run.  ~20 s.  You get: User Parameters, hull port fore/aft (two bodies), the mirrored
     starboard hull, and reference bodies (beams, ROB0154 box).

WHAT IS PARAMETRIC
  Heights, thicknesses, hole depths and the split plane reference the User Parameters, so you
  can change hull_H, wall, rim_h, boss_h, cut_x etc. in Modify > Change Parameters and the model
  updates.  The hull OUTLINE (length, beam, bow curve) is drawn from the numbers at run time:
  to change those, edit the PARAMS table below and re-run in a fresh document.

WHAT IS NOT HERE
  Brackets, arms, coupler: export them from AR-Mini_v1.scad as STL and Insert > Insert Mesh,
  or model them in Fusion (each is a 10-minute part).

Units: the Fusion API works in cm internally; helper mm() converts.
"""
import adsk.core, adsk.fusion, traceback, math

# name: (value in mm, comment)   -- keep in sync with AR-Mini_v1.scad
PARAMS = {
    'hull_L':   (610, 'hull overall length'),
    'hull_W':   (100, 'beam of one hull'),
    'hull_H':   (120, 'hull depth'),
    'bow_len':  (150, 'parabolic bow taper length'),
    'wall':     (1.8, 'wall / floor thickness, 4 perimeters'),
    'cut_x':    (305, 'split plane, two 305 mm sections'),
    'bulk_t':   (3,   'bulkhead thickness at the joint'),
    'rib_t':    (3,   'internal rib thickness'),
    'rim_h':    (10,  'ribs stop this far below the rim'),
    'draft':    (42,  'predicted waterline at ~4.7 kg'),
    'joint_bolt_y': (32, 'joint bolts +/- from hull centreline'),
    'bolt_d':   (3.4, 'M3 clearance'),
    'insert_d': (4.0, 'M3 heat-set insert hole'),
    'gap':      (250, 'clear width between hulls (ROB0154 measured over tracks 230 + 10 + margin)'),
    'beam':     (15,  'square aluminium tube'),
    'boss_w':   (24,  'rim boss depth inward'),
    'boss_l':   (30,  'rim boss length'),
    'boss_h':   (20,  'rim boss height'),
    'boss_pitch': (16, 'insert spacing on a boss'),
    'tp_w':     (44,  'thruster pad width'),
    'tp_h':     (44,  'thruster pad height'),
    'tp_t':     (6,   'thruster pad thickness'),
    'tp_z':     (25,  'thruster pad centre above bottom'),
    'tp_pitch': (20,  'thruster bolt pattern  MEASURE'),
    'arch_x':   (165, 'bow arch position (straight hull section)'),
    'arch_z':   (235, 'arch tube underside, clears cradle sweep'),
    'pivot_x':  (200, 'cradle servo shaft x'),
    'shaft_z':  (105, 'cradle servo shaft height'),
    'arm_len':  (110, 'lift arm length'),
    'arm_gap':  (22,  'parallelogram pivot spacing'),
    'motor_axis': (62, 'ROB0154 track bottom -> sprocket axis (measured); must exceed draft'),
}
RIB_X   = [100, 200, 420, 520]
BOSS_X  = [165, 200, 385, 500]     # arch, pivot, beam, beam (beams sit under the ROB0154 top plate 364..516)
BEAM_X  = [385, 500]
JOINT_Z = [75, 105]
CH_X, CH_L, CH_W, CH_H = 290, 300, 230, 124.6
PLATE_X, PLATE_L, PLATE_W, PLATE_T = 364, 152.2, 134.8, 2


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('Open a Design document first.')
            return
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        feats = root.features
        planes = root.constructionPlanes

        # ---------- user parameters ----------
        up = design.userParameters
        for name, (val, com) in PARAMS.items():
            if up.itemByName(name) is None:
                up.add(name, adsk.core.ValueInput.createByString('%g mm' % val), 'mm', com)

        P = {k: v[0] for k, v in PARAMS.items()}
        L, W, H, BL, wall = P['hull_L'], P['hull_W'], P['hull_H'], P['bow_len'], P['wall']
        yc = P['gap'] / 2 + W / 2                      # port hull centreline (global y)

        def mm(x):
            return x / 10.0

        def V(expr):
            return adsk.core.ValueInput.createByString(expr)

        def pt(x, y, z=0):
            return adsk.core.Point3D.create(mm(x), mm(y), mm(z))

        def hw(x):                                      # local half-width of the hull at station x
            return W / 2 if x >= BL else (W / 2) * math.sqrt(x / BL)

        def offset_plane(base, dist_expr):
            pin = planes.createInput()
            pin.setByOffset(base, V(dist_expr))
            return planes.add(pin)

        def all_profiles(sk):
            coll = adsk.core.ObjectCollection.create()
            for i in range(sk.profiles.count):
                coll.add(sk.profiles.item(i))
            return coll

        NEW  = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
        CUT  = adsk.fusion.FeatureOperations.CutFeatureOperation

        # ---------- 1. hull outline: one fitted spline through the parabolic bow + 3 lines ----------
        sk = root.sketches.add(root.xYConstructionPlane)
        sk.name = 'Hull outline'
        pts = adsk.core.ObjectCollection.create()
        n = 24
        for i in range(n, 0, -1):
            t = i / n
            pts.add(pt(BL * t, yc - (W / 2) * math.sqrt(t)))
        pts.add(pt(0, yc))
        for i in range(1, n + 1):
            t = i / n
            pts.add(pt(BL * t, yc + (W / 2) * math.sqrt(t)))
        spl = sk.sketchCurves.sketchFittedSplines.add(pts)
        lines = sk.sketchCurves.sketchLines
        l1 = lines.addByTwoPoints(spl.endSketchPoint, pt(L, yc + W / 2))
        l2 = lines.addByTwoPoints(l1.endSketchPoint, pt(L, yc - W / 2))
        lines.addByTwoPoints(l2.endSketchPoint, spl.startSketchPoint)

        ext = feats.extrudeFeatures.addSimple(sk.profiles.item(0), V('hull_H'), NEW)
        hull = ext.bodies.item(0)
        hull.name = 'Hull port'

        # ---------- 2. shell: remove the top face ----------
        top = None
        for f in hull.faces:
            if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
                if top is None or f.centroid.z > top.centroid.z:
                    top = f
        fc = adsk.core.ObjectCollection.create()
        fc.add(top)
        shin = feats.shellFeatures.createInput(fc, False)
        shin.insideThickness = V('wall')
        feats.shellFeatures.add(shin)

        # ---------- 3. ribs (full height minus cable notch) ----------
        sk = root.sketches.add(root.xYConstructionPlane)
        sk.name = 'Ribs'
        for x in RIB_X:
            h = hw(x) - wall + 0.6
            sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(x - P['rib_t'] / 2, yc - h), pt(x + P['rib_t'] / 2, yc + h))
        feats.extrudeFeatures.addSimple(all_profiles(sk), V('hull_H - rim_h'), JOIN)

        # ---------- 4. bulkhead pair at the joint ----------
        sk = root.sketches.add(root.xYConstructionPlane)
        sk.name = 'Bulkheads'
        h = W / 2 - wall + 0.6
        cx = P['cut_x']; bt = P['bulk_t']
        sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(cx - bt, yc - h), pt(cx, yc + h))
        sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(cx, yc - h), pt(cx + bt, yc + h))
        feats.extrudeFeatures.addSimple(all_profiles(sk), V('hull_H'), JOIN)

        # ---------- 5. rim bosses on the inner side, with insert holes ----------
        pl = offset_plane(root.xYConstructionPlane, 'hull_H - boss_h')
        pl.name = 'Boss base'
        sk = root.sketches.add(pl)
        sk.name = 'Bosses'
        y0 = yc - W / 2                                   # inner wall, outer face
        for x in BOSS_X:
            sk.sketchCurves.sketchLines.addTwoPointRectangle(
                sk.modelToSketchSpace(pt(x - P['boss_l'] / 2, y0, H - P['boss_h'])),
                sk.modelToSketchSpace(pt(x + P['boss_l'] / 2, y0 + wall + P['boss_w'], H - P['boss_h'])))
        feats.extrudeFeatures.addSimple(all_profiles(sk), V('boss_h'), JOIN)

        pl = offset_plane(root.xYConstructionPlane, 'hull_H')
        pl.name = 'Rim'
        sk = root.sketches.add(pl)
        sk.name = 'Boss insert holes'
        yb = y0 + wall + P['boss_w'] / 2
        for x in BOSS_X:
            for dx in (-P['boss_pitch'] / 2, P['boss_pitch'] / 2):
                sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(pt(x + dx, yb, H)), mm(P['insert_d'] / 2))
        feats.extrudeFeatures.addSimple(all_profiles(sk), V('3 mm - boss_h'), CUT)   # downward, 17 mm deep

        # ---------- 6. thruster pad on the transom + blind insert holes ----------
        # (symmetric extents about a mid-plane, so the result does not depend on the plane normal)
        pl = offset_plane(root.yZConstructionPlane, 'hull_L + tp_t / 2')
        pl.name = 'Transom pad mid'
        sk = root.sketches.add(pl)
        sk.name = 'Thruster pad'
        xm = L + P['tp_t'] / 2
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            sk.modelToSketchSpace(pt(xm, yc - P['tp_w'] / 2, P['tp_z'] - P['tp_h'] / 2)),
            sk.modelToSketchSpace(pt(xm, yc + P['tp_w'] / 2, P['tp_z'] + P['tp_h'] / 2)))
        ein = feats.extrudeFeatures.createInput(sk.profiles.item(0), JOIN)
        ein.setSymmetricExtent(V('tp_t'), True)
        feats.extrudeFeatures.add(ein)

        pl = offset_plane(root.yZConstructionPlane, 'hull_L + tp_t / 2 + 1 mm')
        pl.name = 'Pad holes mid'
        sk = root.sketches.add(pl)
        sk.name = 'Thruster insert holes'
        xh = L + P['tp_t'] / 2 + 1
        for dy in (-P['tp_pitch'] / 2, P['tp_pitch'] / 2):
            for dz in (-P['tp_pitch'] / 2, P['tp_pitch'] / 2):
                sk.sketchCurves.sketchCircles.addByCenterRadius(
                    sk.modelToSketchSpace(pt(xh, yc + dy, P['tp_z'] + dz)), mm(P['insert_d'] / 2))
        ein = feats.extrudeFeatures.createInput(all_profiles(sk), CUT)
        ein.setSymmetricExtent(V('tp_t'), True)          # blind: 5 mm into the pad, 1 mm of pad + wall left
        feats.extrudeFeatures.add(ein)

        # ---------- 7. joint bolt holes through both bulkheads (above the waterline) ----------
        pl = offset_plane(root.yZConstructionPlane, 'cut_x')
        pl.name = 'Split plane'
        sk = root.sketches.add(pl)
        sk.name = 'Joint bolt holes'
        for z in JOINT_Z:
            for s in (-1, 1):
                sk.sketchCurves.sketchCircles.addByCenterRadius(
                    sk.modelToSketchSpace(pt(cx, yc + s * P['joint_bolt_y'], z)), mm(P['bolt_d'] / 2))
        ein = feats.extrudeFeatures.createInput(all_profiles(sk), CUT)
        ein.setSymmetricExtent(V('2 * bulk_t + 4 mm'), True)
        feats.extrudeFeatures.add(ein)

        # ---------- 8. split into two printable sections ----------
        sin = feats.splitBodyFeatures.createInput(hull, pl, True)
        sf = feats.splitBodyFeatures.add(sin)
        for i in range(sf.bodies.count):
            b = sf.bodies.item(i)
            b.name = 'Hull port FORE' if b.boundingBox.minPoint.x < mm(cx) - 0.1 else 'Hull port AFT'

        # ---------- 9. mirror -> starboard hull ----------
        bc = adsk.core.ObjectCollection.create()
        for i in range(sf.bodies.count):
            bc.add(sf.bodies.item(i))
        min_ = feats.mirrorFeatures.createInput(bc, root.xZConstructionPlane)
        mf = feats.mirrorFeatures.add(min_)
        for i in range(mf.bodies.count):
            b = mf.bodies.item(i)
            b.name = 'Hull stbd FORE' if b.boundingBox.minPoint.x < mm(cx) - 0.1 else 'Hull stbd AFT'

        # ---------- 10. reference bodies ----------
        pl = offset_plane(root.xYConstructionPlane, 'hull_H + 6 mm')
        pl.name = 'Beam underside'
        sk = root.sketches.add(pl)
        sk.name = 'REF beams'
        half = yc - W / 2 + wall + P['boss_w'] / 2 + 13
        for x in BEAM_X:
            sk.sketchCurves.sketchLines.addTwoPointRectangle(
                sk.modelToSketchSpace(pt(x - P['beam'] / 2, -half, H + 6)),
                sk.modelToSketchSpace(pt(x + P['beam'] / 2, half, H + 6)))
        e = feats.extrudeFeatures.addSimple(all_profiles(sk), V('beam'), NEW)
        for i in range(e.bodies.count):
            e.bodies.item(i).name = 'REF beam %d' % (i + 1)

        sk = root.sketches.add(root.xYConstructionPlane)
        sk.name = 'REF ROB0154'
        sk.sketchCurves.sketchLines.addTwoPointRectangle(pt(CH_X, -CH_W / 2), pt(CH_X + CH_L, CH_W / 2))
        e = feats.extrudeFeatures.addSimple(sk.profiles.item(0), V('%g mm' % CH_H), NEW)
        e.bodies.item(0).name = 'REF ROB0154 (300x230x124.6)'
        pl = offset_plane(root.xYConstructionPlane, '%g mm' % (CH_H - PLATE_T))
        pl.name = 'Chassis plate'
        sk = root.sketches.add(pl)
        sk.name = 'REF plate'
        sk.sketchCurves.sketchLines.addTwoPointRectangle(sk.modelToSketchSpace(pt(PLATE_X, -PLATE_W / 2, CH_H - PLATE_T)),
                                                          sk.modelToSketchSpace(pt(PLATE_X + PLATE_L, PLATE_W / 2, CH_H - PLATE_T)))
        e = feats.extrudeFeatures.addSimple(sk.profiles.item(0), V('%g mm' % PLATE_T), NEW)
        e.bodies.item(0).name = 'REF ROB0154 top plate (bolts under the beams)'

        ui.messageBox('AR-Mini hull built.\n\nBeam tube length: %.0f mm\nCheck the timeline, then Modify > Change Parameters.' % (2 * half))

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
