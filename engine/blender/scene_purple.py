#!/usr/bin/env python3
"""Blender scene: purple fly-through chapter rebuilt in REAL 3D.
Run: blender -b -E BLENDER_EEVEE_NEXT --python scene_purple.py -- -o OUTDIR
Cards are real thin boxes with textured front faces, tumbling toward a real
camera, among emissive light streaks, lit by colored point lights.
"""
import bpy, math, os, sys, random

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUTDIR = argv[1] if len(argv) > 1 else os.path.expanduser(
    "~/workspace/video-edit/ref-agent-test/frames3d")
TEXDIR = os.path.expanduser("~/workspace/video-edit/ref-agent-test/tex")
os.makedirs(OUTDIR, exist_ok=True)

FPS = 60
FRAMES = 150  # 2.5 s
random.seed(42)

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, FRAMES
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(OUTDIR, "f_")
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.45
try:
    scene.eevee.taa_render_samples = 32
    scene.eevee.use_motion_blur = True
except Exception:
    pass
try:
    scene.cycles.samples = 32
    scene.cycles.use_denoising = False
except Exception:
    pass

# ---------- world: deep purple ----------
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.012, 0.0, 0.03, 1.0)
bg.inputs[1].default_value = 1.0

# ---------- camera ----------
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 34
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (0, 0, 0)
cam.rotation_euler = (math.radians(90), 0, 0)  # look down -Y? -> fix below
# Blender camera looks along its local -Z; rotating x by 90deg makes it face -Y world... we want it to face -Z world is wrong too.
# Convention used here: cards travel along +Z toward camera at origin facing -Z is default (no rotation).
cam.rotation_euler = (0, 0, 0)
# gentle handheld sway
for f in range(1, FRAMES + 1):
    t = f / FPS
    cam.location = (math.sin(t * 0.9) * 0.14, math.cos(t * 0.7) * 0.10, 0)
    cam.rotation_euler = (math.sin(t * 0.6) * 0.012, math.sin(t * 0.8) * 0.016, 0)
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)

# ---------- lights ----------
def point(name, loc, color, energy):
    d = bpy.data.lights.new(name, "POINT")
    d.color = color; d.energy = energy
    o = bpy.data.objects.new(name, d)
    o.location = loc
    scene.collection.objects.link(o)
point("Magenta", (5, 3, -5), (1.0, 0.25, 0.9), 900)
point("Blue", (-6, -2, -7), (0.3, 0.45, 1.0), 800)
point("Front", (0, 1, 1.5), (0.7, 0.6, 1.0), 1500)
point("Mid", (0, 0.5, -2), (0.75, 0.65, 1.0), 520)

# ---------- materials ----------
def face_material(texfile):
    m = bpy.data.materials.new("Face")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(TEXDIR, texfile))
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.6
    bsdf.inputs["Roughness"].default_value = 0.42
    return m

def body_material(rgb):
    m = bpy.data.materials.new("Body")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = 0.5
    return m

# ---------- cards ----------
def make_card(texfile, body_rgb):
    # body: thin box; faces: two planes (a cube's atlas UVs would sample only
    # a strip of the texture, planes carry full 0..1 UVs)
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.dimensions = (2.6, 1.7, 0.07)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(body_material(body_rgb))
    import mathutils
    for tex, zoff, flip in [(texfile, 0.041, False),
                            (texfile.replace(".png", "_flip.png"), -0.041, True)]:
        bpy.ops.mesh.primitive_plane_add(size=1)
        pl = bpy.context.active_object
        pl.dimensions = (2.6, 1.7, 0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        pl.data.materials.append(face_material(tex))
        pl.parent = ob
        pl.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        pl.location = (0, 0, zoff)
        if flip:
            pl.rotation_euler = (0, math.radians(180), 0)
    return ob

def ease_in_quad(x): return x * x
def clamp01(x): return max(0.0, min(1.0, x))

cards_spec = [
    ("card_blue.png", (0.10, 0.16, 0.45), -2.4, 0.7, 0.00, 1.0, 0.7),
    ("card_gold.png", (0.45, 0.28, 0.06), 2.6, -0.5, 0.55, -0.8, 1.0),
    ("card_teal.png", (0.05, 0.35, 0.28), 0.3, 1.3, 1.10, 1.1, -0.7),
]
for texfile, rgb, x1, y1, delay, rx_rate, ry_rate in cards_spec:
    ob = make_card(texfile, rgb)
    dur = 1.5  # seconds of flight
    for f in range(1, FRAMES + 1):
        t = f / FPS
        lt = t - delay
        p = clamp01(lt / dur)
        ep = ease_in_quad(p)
        z = -17 + 20.5 * ep                     # -17 -> +3.5 (passes camera)
        x = x1 * (1 - ep * 0.55)
        y = y1 * (1 - ep * 0.4) + math.sin(p * 5.0) * 0.12
        ob.location = (x, y, z)
        ob.rotation_euler = (rx_rate * p * 1.9, ry_rate * p * 1.9,
                             0.6 * p * (1 if rx_rate > 0 else -1))
        # fade near camera by scaling down after passing
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)

# ---------- light streaks ----------
em = bpy.data.materials.new("Streak")
em.use_nodes = True
eb = em.node_tree.nodes["Principled BSDF"]
eb.inputs["Base Color"].default_value = (0.62, 0.45, 1.0, 1.0)
eb.inputs["Emission Color"].default_value = (0.45, 0.2, 1.0, 1.0)
eb.inputs["Emission Strength"].default_value = 0.85

streak_data = []
for i in range(90):
    ln = random.uniform(0.35, 1.15)
    bpy.ops.mesh.primitive_cube_add(size=1)
    s = bpy.context.active_object
    s.dimensions = (0.016, ln, 0.016)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    s.data.materials.append(em)
    x = random.uniform(-7.5, 7.5); y = random.uniform(-4.2, 4.2)
    z = random.uniform(-17, 1.5)
    sp = random.uniform(0.7, 2.0)
    s.location = (x, y, z)
    streak_data.append((s, y, sp))
for f in (1, FRAMES):
    t = f / FPS
    for s, y0, sp in streak_data:
        yy = ((y0 - sp * t + 4.2) % 8.4) - 4.2
        s.location.y = yy
        s.keyframe_insert("location", frame=f)
try:  # linear interpolation for the streak drift
    for s, y0, sp in streak_data:
        act = s.animation_data.action
        curves = act.layers[0].strips[0].channelbag.fcurves
        for kc in curves:
            for kp in kc.keyframe_points:
                kp.interpolation = "LINEAR"
except Exception as e:
    print("streak interp skipped:", e)

print("SCENE_BUILT", flush=True)
if os.environ.get("BUILD_ONLY"):
    try:
        scene.cycles.samples = int(os.environ.get("SMP", "16"))
        scene.cycles.max_bounces = 4
        scene.cycles.use_denoising = False
    except Exception:
        pass
    scene.render.resolution_percentage = int(os.environ.get("RESPCT", "75"))
    _p = os.path.expanduser("~/workspace/video-edit/ref-agent-test/purple.blend")
    bpy.ops.wm.save_as_mainfile(filepath=_p)
    print("BLEND_SAVED", _p, flush=True)
    sys.exit(0)
_bf = os.environ.get("BF")
if _bf:
    _f = int(_bf)
    scene.frame_start = scene.frame_end = _f
    scene.render.resolution_percentage = int(os.environ.get("RESPCT", "75"))
    try:
        scene.cycles.samples = int(os.environ.get("SMP", "16"))
        scene.cycles.max_bounces = 4
    except Exception:
        pass
    bpy.ops.render.render(animation=True)
    print("SINGLE_DONE", _f, flush=True)
else:
    bpy.ops.render.render(animation=True)
    print("RENDER3D_DONE", flush=True)
