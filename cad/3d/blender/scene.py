"""AR-Mini · Blender scene of the planned rescue cycle (card C086).

    blender -b -P cad/3d/blender/scene.py -- --stills            3 stills, 1920 x 1080
    blender -b -P cad/3d/blender/scene.py -- --anim              25 s, 600 frames, MP4 (or PNG frames)
    blender -b -P cad/3d/blender/scene.py -- --frame 300         one frame
    options: --res 1280 720   --samples 48   --step 2   --out DIR   --save scene.blend   --cpu

Every solid is parts/*.stl, exported from the repo CAD by export_parts.sh (mm, x from the bow, z from the hull bottom).
This is an ANIMATION OF THE PLAN. Nothing in it is a measurement; the motion is keyframed by hand, there is no physics.
Written to run on Blender 4.2 … 5.x (also as `python3 scene.py` with the bpy module).
"""
import argparse
import math
import os
import shutil
import subprocess
import sys

import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "parts")
MM = 0.001

# ---- kinematics, from parts/kinematics.txt (echo of parts.scad) -------------------------------------------
KIN = {}
with open(os.path.join(PARTS, "kinematics.txt")) as fh:
    for tok in fh.read().split()[1:]:
        k, v = tok.split("=")
        KIN[k] = float(v)
PIVOT_X, SHAFT_Z, ARM_L, ARM_GAP = KIN["pivot_x"], KIN["shaft_z"], KIN["arm_len"], KIN["arm_gap"]
DRAFT = KIN["draft"]
CX0 = 305.0                      # robot yaw centre, mm from the bow (half the hull length)

# ---- timeline (24 fps) ------------------------------------------------------------------------------------
FPS = 24
F_APPROACH = (1, 168)            # 7 s   drive to the dummy, cradle down
F_LIFT = (216, 360)              # 6 s   cradle 215° -> 120°
F_TURN = (384, 504)              # 5 s   half circle
F_END = 600                      # 25 s
A_DOWN, A_UP = KIN["deploy_a"], 120.0
START_DIST = 2.6                 # m
TURN_R = 0.55                    # m, radius of the return turn
CAPTIONS = [
    (1, 96, "1  Search: the thermal camera on the arch looks for a warm head"),
    (97, 215, "2  Approach: cradle down, 34 mm under the waterline"),
    (216, 383, "3  Lift: two servos raise the cradle and the dummy out of the water"),
    (384, 600, "4  Return: the rudder turns the boat, the thruster brings it back"),
]
NOTE = "AR-Mini: animation of the plan, built from the CAD in the repo. Not a test."

MATS = {
    "white":  dict(color=(0.86, 0.86, 0.84), rough=0.45),
    "black":  dict(color=(0.02, 0.02, 0.022), rough=0.5),
    "petg":   dict(color=(0.09, 0.09, 0.10), rough=0.35),
    "alu":    dict(color=(0.78, 0.79, 0.80), rough=0.3, metal=1.0),
    "orange": dict(color=(0.90, 0.30, 0.03), rough=0.45),
    "red":    dict(color=(0.70, 0.03, 0.03), rough=0.45),
    "box":    dict(color=(0.55, 0.57, 0.58), rough=0.6),
}
# name: (material, parent)   parent: robot | arm_d | arm_i | cradle | rudder | pesho
OBJECTS = {
    "hull_l": ("white", "robot"), "hull_r": ("white", "robot"), "brackets": ("black", "robot"),
    "beams": ("alu", "robot"), "leg": ("petg", "robot"), "th_mount": ("petg", "robot"),
    "thruster": ("black", "robot"), "rudder_mount": ("petg", "robot"),
    "box_power": ("box", "robot"), "box_logic": ("box", "robot"),
    "arm_drive_l": ("orange", "arm_d"), "arm_drive_r": ("orange", "arm_d"),
    "arm_idler_l": ("orange", "arm_i"), "arm_idler_r": ("orange", "arm_i"),
    "couplers": ("orange", "cradle"), "cradle": ("alu", "cradle"),
    "rudder_blade": ("orange", "rudder"),
    "pesho_body": ("red", "pesho"), "pesho_head": ("white", "pesho"),
}


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def span(f, a, b):
    return ease((f - a) / float(b - a))


# ---- motion as plain functions of the frame ---------------------------------------------------------------
def alpha_at(f):
    return A_DOWN + (A_UP - A_DOWN) * span(f, *F_LIFT)


def cradle_local(f):
    """coupler upper pivot in robot coordinates, mm"""
    a = math.radians(alpha_at(f))
    return Vector((PIVOT_X + ARM_L * math.cos(a), 0.0, SHAFT_Z + ARM_L * math.sin(a)))


def robot_pose(f):
    """(x, y, yaw) of the yaw centre in world metres. The bow points to -x at yaw 0. The dummy floats at the world origin."""
    x_catch = (CX0 - (PIVOT_X + ARM_L * math.cos(math.radians(A_DOWN)) - 110.0)) * MM   # cradle centre over the origin
    if f <= F_TURN[0]:
        return x_catch + START_DIST * (1 - span(f, *F_APPROACH)), 0.0, 0.0
    th = math.pi * span(f, *F_TURN)                         # half circle to port, centre at (x_catch, -TURN_R)
    x = x_catch - TURN_R * math.sin(th)
    y = -TURN_R * (1 - math.cos(th))
    if f > F_TURN[1]:
        x += 1.6 * ((f - F_TURN[1]) / float(F_END - F_TURN[1])) ** 1.3
    return x, y, th


def robot_matrix(f):
    x, y, yaw = robot_pose(f)
    bob = 0.003 * math.sin(f * 0.21) + 0.002 * math.sin(f * 0.13 + 1.0)
    pitch = math.radians(0.6) * math.sin(f * 0.17)
    return (Matrix.Translation((x, y, -DRAFT * MM + bob)) @ Euler((0, pitch, yaw)).to_matrix().to_4x4()
            @ Matrix.Translation((-CX0 * MM, 0, 0)))


def rudder_angle(f):
    if F_TURN[0] - 12 <= f <= F_TURN[1] + 12:
        return math.radians(25) * math.sin(math.pi * (f - F_TURN[0] + 12) / float(F_TURN[1] - F_TURN[0] + 24))
    return 0.0


def pesho_matrix(f):
    """on his back across the two cradle rods; floats until the lift starts, then rides the cradle"""
    c = cradle_local(max(f, F_LIFT[0]))
    rod_top = c.z - ARM_GAP - 12 + 2.5
    local = Matrix.Translation(((c.x - 110.0) * MM, 0.098, (rod_top + 40.0) * MM)) @ Euler((math.radians(90), 0, 0)).to_matrix().to_4x4()
    if f >= F_LIFT[0]:
        return robot_matrix(f) @ local
    m = robot_matrix(F_LIFT[0]) @ local                     # where the cradle will meet him
    m.translation.z += 0.002 * math.sin(f * 0.19)
    return m


# ---- scene building ---------------------------------------------------------------------------------------
def material(name, color, rough=0.5, metal=0.0, emit=0.0, trans=0.0, ior=1.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["IOR"].default_value = ior
    for key in ("Transmission Weight", "Transmission"):
        if key in b.inputs:
            b.inputs[key].default_value = trans
            break
    if emit:
        for key in ("Emission Color", "Emission"):
            if key in b.inputs:
                b.inputs[key].default_value = (*color, 1)
                break
        b.inputs["Emission Strength"].default_value = emit
    return m


def import_stl(path):
    before = set(bpy.data.objects)
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=path)
    else:
        bpy.ops.import_mesh.stl(filepath=path)
    ob = (set(bpy.data.objects) - before).pop()
    ob.data.transform(Matrix.Scale(MM, 4))
    return ob


def smooth(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    for op in ("shade_auto_smooth", "shade_smooth_by_angle"):
        if hasattr(bpy.ops.object, op):
            try:
                getattr(bpy.ops.object, op)(angle=math.radians(35))
                return
            except Exception:
                pass


def empty(name, parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.parent = parent
    return e


def key_matrix(ob, m, f):
    loc, rot, _ = m.decompose()
    ob.rotation_mode = "QUATERNION"
    ob.location, ob.rotation_quaternion = loc, rot
    ob.keyframe_insert("location", frame=f)
    ob.keyframe_insert("rotation_quaternion", frame=f)


def text(name, body, size, loc, parent, mat):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.size = body, size
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent, ob.location = parent, loc
    ob.data.materials.append(mat)
    for attr in ("visible_shadow", "visible_glossy", "visible_diffuse", "visible_transmission"):
        if hasattr(ob, attr):
            setattr(ob, attr, False)
    return ob


def build(args):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end, sc.render.fps = 1, F_END, FPS
    sc.unit_settings.system = "METRIC"
    mats = {k: material(k, **v) for k, v in MATS.items()}

    par = {"robot": empty("robot")}
    for k in ("arm_d", "arm_i", "cradle", "rudder"):
        par[k] = empty(k, par["robot"])
    par["pesho"] = empty("pesho")
    par["arm_d"].location = (PIVOT_X * MM, 0, SHAFT_Z * MM)
    par["arm_i"].location = (PIVOT_X * MM, 0, (SHAFT_Z - ARM_GAP) * MM)
    par["rudder"].location = (KIN["rudder_x"] * MM, 0, KIN["rudder_z"] * MM)
    for name, (mat, p) in OBJECTS.items():
        ob = import_stl(os.path.join(PARTS, name + ".stl"))
        ob.name = name
        ob.data.materials.append(mats[mat])
        ob.parent = par[p]
        smooth(ob)

    # water, lake bottom, light
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, 0))
    water = bpy.context.object
    water.name = "water"
    wm = material("water", (0.55, 0.80, 0.85), rough=0.03, trans=1.0, ior=1.333)
    nt = wm.node_tree
    noise, bump = nt.nodes.new("ShaderNodeTexNoise"), nt.nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = 9.0
    noise.inputs["Detail"].default_value = 3.0
    bump.inputs["Strength"].default_value = 0.12
    nt.links.new(noise.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
    water.data.materials.append(wm)
    if hasattr(water, "visible_shadow"):
        water.visible_shadow = False                         # the sun reaches the hulls under the surface
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, -0.9))
    bpy.context.object.name = "lake_bottom"
    bpy.context.object.data.materials.append(material("bottom", (0.0, 0.0, 0.0), rough=1.0))
    bm = bpy.data.materials["bottom"].node_tree.nodes["Principled BSDF"]          # flat colour: no boat shadow on the bottom
    for key in ("Emission Color", "Emission"):
        if key in bm.inputs:
            bm.inputs[key].default_value = (0.03, 0.10, 0.11, 1)
            break
    bm.inputs["Emission Strength"].default_value = 1.0
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy, sun.data.angle = 4.0, math.radians(3)
    sun.rotation_euler = (math.radians(52), 0, math.radians(-30))   # behind the camera, no glare on the water
    sc.collection.objects.link(sun)
    sc.world = bpy.data.worlds.new("sky")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.50, 0.68, 0.92, 1)
    bg.inputs[1].default_value = 1.0

    # camera on a target
    cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    cam.data.lens, cam.data.clip_start = 35, 0.02
    sc.collection.objects.link(cam)
    sc.camera = cam
    tgt = empty("target")
    con = cam.constraints.new("TRACK_TO")
    con.target, con.track_axis, con.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
    shots = [   # frame, camera (x, y, z) in world metres; the target follows the boat (see the motion loop)
        (1,   (-1.6, -2.2, 1.25)),
        (120, (-1.0, -1.5, 0.75)),
        (216, (-0.75, -0.85, 0.42)),
        (360, (-0.70, -0.75, 0.48)),
        (504, (-1.2, -2.7, 1.05)),
        (600, (-1.4, -3.0, 1.25)),
    ]
    for f, c in shots:
        cam.location = c
        cam.keyframe_insert("location", frame=f)

    # captions ride on the camera, 0.1 m in front of it (nearer than anything in the scene)
    tm = material("text", (1, 1, 1), emit=1.6)
    strip = material("strip", (0.01, 0.02, 0.03), rough=1.0)
    text("note", NOTE, 0.0017, (-0.049, -0.0262, -0.1), cam, tm)
    bpy.ops.mesh.primitive_plane_add(size=1)
    bar = bpy.context.object
    bar.name, bar.parent, bar.location, bar.scale = "strip", cam, (0, -0.0243, -0.1002), (0.12, 0.0075, 1)
    bar.data.materials.append(strip)
    for attr in ("visible_shadow", "visible_glossy", "visible_diffuse", "visible_transmission"):
        if hasattr(bar, attr):
            setattr(bar, attr, False)
    for i, (a, b, body) in enumerate(CAPTIONS):
        t = text("cap%d" % (i + 1), body, 0.0024, (-0.049, -0.0232, -0.1), cam, tm)
        for f, hide in ((1, a > 1), (a, False), (b + 1, True)):
            t.hide_render = t.hide_viewport = hide
            t.keyframe_insert("hide_render", frame=f)
            t.keyframe_insert("hide_viewport", frame=f)

    # motion, one key per frame (plain functions above, no drivers)
    for f in range(1, F_END + 1):
        key_matrix(par["robot"], robot_matrix(f), f)
        key_matrix(par["pesho"], pesho_matrix(f), f)
        a = -math.radians(alpha_at(f))
        for k in ("arm_d", "arm_i"):
            par[k].rotation_euler = (0, a, 0)
            par[k].keyframe_insert("rotation_euler", frame=f)
        par["cradle"].location = cradle_local(f) * MM
        par["cradle"].keyframe_insert("location", frame=f)
        par["rudder"].rotation_euler = (0, 0, rudder_angle(f))
        par["rudder"].keyframe_insert("rotation_euler", frame=f)
        x, y, _ = robot_pose(f)
        w = 0.5 + 0.5 * span(f, *F_TURN)                     # between the boat and the dummy, later the boat alone
        tgt.location = (x * w, y * w, 0.03 + 0.05 * span(f, *F_LIFT) - 0.05 * span(f, *F_TURN))
        tgt.keyframe_insert("location", frame=f)

    # render settings
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = args.res[0], args.res[1], 100
    r.engine = "CYCLES"
    sc.cycles.samples = args.samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 6
    if not args.cpu:
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            for kind in ("METAL", "OPTIX", "CUDA"):
                try:
                    prefs.compute_device_type = kind
                    prefs.get_devices()
                    if any(d.type == kind for d in prefs.devices):
                        for d in prefs.devices:
                            d.use = True
                        sc.cycles.device = "GPU"
                        print("C086: Cycles on", kind)
                        break
                except Exception:
                    continue
        except Exception:
            pass
    return sc


def render_png(sc, frame, path):
    sc.frame_set(frame)
    s = sc.render.image_settings
    if hasattr(s, "media_type"):
        s.media_type = "IMAGE"
    s.file_format = "PNG"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("C086: wrote", path)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else (sys.argv[1:] if not bpy.app.binary_path else [])
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--anim", action="store_true")
    ap.add_argument("--frame", type=int, action="append", default=[])
    ap.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--save")
    ap.add_argument("--cpu", action="store_true")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    sc = build(args)
    if args.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save))
    stills = {"C086_still_1_approach": 130, "C086_still_2_lift": 330, "C086_still_3_return": 470}
    if args.stills:
        for name, f in stills.items():
            render_png(sc, f, os.path.join(args.out, name + ".png"))
    for f in args.frame:
        render_png(sc, f, os.path.join(args.out, "C086_frame_%04d.png" % f))
    if args.anim:
        frames = os.path.join(args.out, "frames")
        os.makedirs(frames, exist_ok=True)
        for f in range(1, F_END + 1, args.step):
            p = os.path.join(frames, "f%04d.png" % f)
            if not os.path.exists(p):                        # a stopped run continues where it was
                render_png(sc, f, p)
        mp4 = os.path.join(args.out, "C086_rescue_cycle_plan.mp4")
        ff = shutil.which("ffmpeg")
        if ff and args.step == 1:
            subprocess.check_call([ff, "-y", "-framerate", str(FPS), "-start_number", "1", "-i", os.path.join(frames, "f%04d.png"),
                                   "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", mp4])
            print("C086: wrote", mp4)
        else:
            print("C086: frames are in", frames, "(no ffmpeg found, or --step > 1): encode them at", FPS, "fps")


if __name__ == "__main__":
    main()
