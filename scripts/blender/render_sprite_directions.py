#!/usr/bin/env python3
"""render_sprite_directions.py - render a GLB to N-direction sprites with Blender (CPU, headless).

Imports a GLB, puts an orthographic camera around it, renders with a transparent
background, and writes PNGs named  {action}_{dir}_{frame:03d}.png  (frame = running
index 000, 001, ... of the *rendered* frames; the source Blender frame number is in the
JSON). Optionally packs everything into a sprite sheet + JSON of frame rectangles.

Usage
-----
  # Blender binary:
  blender -b -P render_sprite_directions.py -- model.glb out_dir [options]
  # or pip module (`pip install bpy numpy pillow`; Python must match the bpy wheel):
  python render_sprite_directions.py model.glb out_dir [options]

Examples
  # 8-direction 3/4 view, 256 px cells, every 2nd frame of each animation, sheet + JSON
  python render_sprite_directions.py hero.glb out --directions 8 --elevation 30 \\
      --size 256 --frame-step 2 --spritesheet
  # isometric 4-direction, flat unlit colours, no anti-aliasing (pixel-art pipelines)
  python render_sprite_directions.py prop.glb out --directions 4 --isometric \\
      --yaw-offset 45 --look flat --aa OFF --size 128

Options
  --directions N       number of camera azimuths (default 8)
  --elevation DEG      camera elevation above the horizon (default 30; 0 = side view)
  --isometric          elevation = 35.264 (true isometric); combine with --yaw-offset 45
  --yaw-offset DEG     rotate all camera azimuths (default 0)
  --front-yaw DEG      extra rotation if the model's front is not glTF +Z
  --size PX            square cell size in pixels (default 256)
  --padding F          extra margin around the model as a fraction (default 0.05)
  --look shaded|flat|toon
                       shaded: Workbench studio lighting (default); flat: unlit texture
                       colours; toon: shaded then posterised into --toon-levels bands
  --toon-levels N      brightness bands for toon (default 3)
  --outline            Workbench object outline (dark edge) around the model
  --engine workbench|eevee|cycles
                       workbench (default, fastest, needs OpenGL: see Notes), eevee, or
                       cycles (pure CPU path tracer, works with no GPU/GL at all)
  --samples N          samples for eevee/cycles (default 16)
  --aa 8|OFF|...       Workbench anti-aliasing samples (default 8, OFF for crisp pixels)
  --actions a,b        render only these actions (default: every action in the GLB; static
                       models are rendered once as action "static")
  --frame-step K       render every K-th frame of each action (default 1)
  --spritesheet        write sheet.png + sheet.json. Layout: each action is a block of rows
                       (one row per direction), columns = frames. No Pillow needed.

Conventions
  * Direction 0 is the model's front facing the camera (glTF faces +Z). When every azimuth is
    a multiple of 45 degrees the names are screen-compass labels: S (facing camera), SW, W,
    NW, N (back), NE, E, SE, where W = the model faces screen-left (verified with the Fox
    sample, which faces +Z). Otherwise d00, d01, ... are used.
  * The camera is fixed size for every frame and direction (one ortho scale computed from
    all frames), so sprites align and `pixels_per_unit` in the JSON is constant.
  * The key light is attached to the camera (upper left), so lighting is the same in every
    direction, which is what hand-drawn sprite sets do.

Notes
  * Workbench and EEVEE need an OpenGL context. In a headless container with no GPU the
    script tries the requested engine and, if the render fails, tells you to use
    --engine cycles (CPU only). See scripts/README.md for what was tested.
  * Dependencies: Blender 4.x/5.x or `pip install bpy`, numpy. No Pillow (toon + sheet use
    numpy and Blender's image API, so they work inside Blender's bundled Python).

Tested 2026-10-21, Linux CPU-only: bpy 5.2.2 LTS (pip, Python 3.13.16) with workbench (shaded,
flat-via-cycles, toon, outline, isometric, spritesheet), eevee (works but ~50 s for 8 frames at
192 px on software GL) and cycles; Blender 4.5.9 binary with workbench + sheet + toon and eevee.
Workbench/EEVEE needed libEGL + Mesa (`apt-get install libegl1 libgl1 libglx-mesa0
libgl1-mesa-dri libegl-mesa0`) in this container; without them only --engine cycles works.
Harmless "EGL_BAD_MATCH" lines on stderr appear with the Mesa software driver. See README.
"""
import argparse
import json
import math
import os
import sys

try:
    import bpy
    from mathutils import Vector
    import numpy as np
except ImportError as e:  # pragma: no cover
    sys.stderr.write("ERROR: needs Blender's Python or `pip install bpy numpy` (%s)\n" % e)
    sys.exit(2)

COMPASS8 = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
COMPASS4 = ["S", "W", "N", "E"]


def log(*m):
    print("[sprites]", *m, file=sys.stderr, flush=True)


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    ap = argparse.ArgumentParser(prog="render_sprite_directions.py")
    ap.add_argument("input")
    ap.add_argument("out_dir")
    ap.add_argument("--directions", type=int, default=8)
    ap.add_argument("--elevation", type=float, default=30.0)
    ap.add_argument("--isometric", action="store_true")
    ap.add_argument("--yaw-offset", type=float, default=0.0)
    ap.add_argument("--front-yaw", type=float, default=0.0)
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--padding", type=float, default=0.05)
    ap.add_argument("--look", choices=("shaded", "flat", "toon"), default="shaded")
    ap.add_argument("--toon-levels", type=int, default=3)
    ap.add_argument("--outline", action="store_true")
    ap.add_argument("--engine", choices=("workbench", "eevee", "cycles"), default="workbench")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--aa", default="8")
    ap.add_argument("--actions", default="")
    ap.add_argument("--frame-step", type=int, default=1)
    ap.add_argument("--spritesheet", action="store_true")
    a = ap.parse_args(argv)
    if a.isometric:
        a.elevation = math.degrees(math.atan(1 / math.sqrt(2)))  # 35.264
    if a.directions < 1 or a.frame_step < 1:
        ap.error("--directions and --frame-step must be >= 1")
    return a


def dir_names(n, yaw_offset=0.0):
    """Compass labels when every azimuth is a multiple of 45 degrees, else d00, d01, ..."""
    azs = [yaw_offset + i * 360.0 / n for i in range(n)]
    if all(abs(az / 45.0 - round(az / 45.0)) < 1e-6 for az in azs):
        return [COMPASS8[int(round(az / 45.0)) % 8] for az in azs]
    return ["d%02d" % i for i in range(n)]


# ------------------------------------------------------------------ scene
def import_scene(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    shapes = {pb.custom_shape for a in arms for pb in a.pose.bones if pb.custom_shape}
    for a in arms:
        for pb in a.pose.bones:
            pb.custom_shape = None
    for o in shapes:
        bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("ERROR: no meshes in " + path)
    return meshes


def assign_action(act):
    """Make `act` the active action on every object that can be animated by it."""
    n = 0
    for o in bpy.context.scene.objects:
        if o.type not in ("ARMATURE", "MESH", "EMPTY"):
            continue
        if o.animation_data is None:
            o.animation_data_create()
        ad = o.animation_data
        # Blender 4.4+ slotted actions: pick the slot that matches this object, if any
        try:
            ad.action = act
            slots = getattr(act, "slots", None)
            if slots and hasattr(ad, "action_slot"):
                match = [s for s in slots if s.target_id_type == o.id_type]
                if match:
                    ad.action_slot = match[0]
        except Exception:
            continue
        n += 1
    return n


def collect_actions(filter_names):
    acts = list(bpy.data.actions)
    if filter_names:
        want = [x.strip() for x in filter_names.split(",") if x.strip()]
        acts = [a for a in acts if a.name in want]
    return acts


def sanitize(name):
    return "".join(c if c.isalnum() or c in "-" else "-" for c in name).strip("-") or "action"


def frames_for(act, step):
    f0, f1 = act.frame_range
    f0, f1 = int(round(f0)), int(round(f1))
    fr = list(range(f0, f1 + 1, step))
    return fr or [f0]


def eval_vertices(meshes):
    """World-space vertex array of all meshes at the current frame."""
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        n = len(me.vertices)
        co = np.empty(n * 3, dtype=np.float64)
        me.vertices.foreach_get("co", co)
        m = np.array(ev.matrix_world)
        pts.append(co.reshape(n, 3) @ m[:3, :3].T + m[:3, 3])
        ev.to_mesh_clear()
    return np.vstack(pts)


def cam_basis(az, el):
    """Return (position direction, right, up) for a camera at azimuth az / elevation el (rad)."""
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    look = -d
    right = look.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(look).normalized()
    return d, right, up


def setup_render(a):
    scn = bpy.context.scene
    r = scn.render
    r.resolution_x = r.resolution_y = a.size
    r.resolution_percentage = 100
    r.film_transparent = True
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "8"
    scn.view_settings.view_transform = "Standard"
    scn.view_settings.look = "None"
    if a.engine == "workbench":
        r.engine = "BLENDER_WORKBENCH"
        sh = scn.display.shading
        sh.color_type = "TEXTURE"
        sh.light = "FLAT" if a.look == "flat" else "STUDIO"
        sh.show_specular_highlight = False
        sh.show_object_outline = bool(a.outline)
        sh.show_cavity = False
        scn.display.render_aa = a.aa.upper() if a.aa.upper() == "OFF" else a.aa
    elif a.engine == "eevee":
        # Blender 4.2-4.5 call it BLENDER_EEVEE_NEXT, 5.x BLENDER_EEVEE
        for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
            try:
                r.engine = eng
                break
            except TypeError:
                continue
        try:
            scn.eevee.taa_render_samples = a.samples
        except Exception:
            pass
    else:
        r.engine = "CYCLES"
        scn.cycles.device = "CPU"
        scn.cycles.samples = a.samples
        scn.cycles.use_denoising = False
    if a.engine != "workbench":
        world = bpy.data.worlds.new("w")
        world.use_nodes = True
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs["Color"].default_value = (1, 1, 1, 1)
            bg.inputs["Strength"].default_value = 0.0 if a.look == "flat" else 0.35
        scn.world = world
        if a.look == "flat":
            # emission-only: replace Principled with the base colour so no lighting is needed
            for m in bpy.data.materials:
                if not m.use_nodes:
                    continue
                nt = m.node_tree
                bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
                out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
                if not bsdf or not out:
                    continue
                em = nt.nodes.new("ShaderNodeEmission")
                bc = bsdf.inputs["Base Color"]
                if bc.links:
                    nt.links.new(bc.links[0].from_socket, em.inputs["Color"])
                else:
                    em.inputs["Color"].default_value = bc.default_value
                nt.links.new(em.outputs["Emission"], out.inputs["Surface"])


def make_camera_and_light(a):
    scn = bpy.context.scene
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.clip_start, cam_data.clip_end = 0.01, 10000
    cam = bpy.data.objects.new("cam", cam_data)
    scn.collection.objects.link(cam)
    scn.camera = cam
    light = None
    if a.engine != "workbench" and a.look != "flat":
        ld = bpy.data.lights.new("key", "SUN")
        ld.energy = 3.0
        ld.angle = math.radians(10)
        light = bpy.data.objects.new("key", ld)
        scn.collection.objects.link(light)
        light.parent = cam
        # upper-left of the camera, pointing into the scene
        light.rotation_euler = (math.radians(35), 0, math.radians(-30))
    return cam, light


def place_camera(cam, target, az, el, dist):
    d, _, _ = cam_basis(az, el)
    cam.location = target + d * dist
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()


def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def load_rgba(path):
    """PNG -> float32 array (H, W, 4), top row first. Uses Blender only (no Pillow)."""
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = "Non-Color"   # byte-exact passthrough
    img.alpha_mode = "STRAIGHT"
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[::-1]


def save_rgba(path, arr):
    h, w = arr.shape[:2]
    img = bpy.data.images.new("out_tmp", w, h, alpha=True)
    img.colorspace_settings.name = "Non-Color"
    img.alpha_mode = "STRAIGHT"
    img.pixels.foreach_set(np.ascontiguousarray(arr[::-1], dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def posterize(path, levels):
    """Quantise brightness (max of RGB) into `levels` bands, keep hue and alpha."""
    arr = load_rgba(path)
    rgb, alpha = arr[..., :3], arr[..., 3:]
    v = rgb.max(axis=-1, keepdims=True)
    lv = max(2, levels)
    band = np.minimum(np.floor(v * lv), lv - 1)
    newv = (band + 1) / lv          # darkest band is 1/lv, never pure black
    scale = np.where(v > 1e-6, newv / np.maximum(v, 1e-6), 0.0)
    out = np.concatenate([np.clip(rgb * scale, 0, 1), alpha], axis=-1)
    out[alpha[..., 0] <= 0] = 0
    save_rgba(path, out)


def build_sheet(frames, out_dir, size, directions, a_names):
    """Rows = directions, columns = frames; one block of rows per action."""
    order = []
    for f in frames:
        if f["action"] not in order:
            order.append(f["action"])
    ncols = max(f["frame"] for f in frames) + 1
    width, height = ncols * size, len(order) * directions * size
    sheet = np.zeros((height, width, 4), dtype=np.float32)
    block_y = {name: i * directions * size for i, name in enumerate(order)}
    for f in frames:
        row = a_names.index(f["dir"])
        x, y = f["frame"] * size, block_y[f["action"]] + row * size
        sheet[y:y + size, x:x + size] = load_rgba(os.path.join(out_dir, f["file"]))
        f["rect"] = dict(x=x, y=y, w=size, h=size)
    save_rgba(os.path.join(out_dir, "sheet.png"), sheet)
    return (width, height)


def main():
    a = parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    meshes = import_scene(os.path.abspath(a.input))
    names = dir_names(a.directions, a.yaw_offset)
    acts = collect_actions(a.actions)
    plan = []  # (action_name, action_or_None, [frame numbers])
    if acts:
        for act in acts:
            plan.append((sanitize(act.name), act, frames_for(act, a.frame_step)))
    else:
        plan.append(("static", None, [bpy.context.scene.frame_current]))

    setup_render(a)
    cam, light = make_camera_and_light(a)

    # ---- pass 1: bounds over every frame to render
    scn = bpy.context.scene
    el = math.radians(a.elevation)
    azs = [math.radians(a.yaw_offset + i * 360.0 / a.directions) for i in range(a.directions)]
    pts_all = []
    for name, act, frs in plan:
        if act:
            assign_action(act)
        for f in frs:
            scn.frame_set(f)
            pts_all.append(eval_vertices(meshes))
    P = np.vstack(pts_all)
    lo, hi = P.min(axis=0), P.max(axis=0)
    target = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2))
    t = np.array(target)
    half = 0.0
    for az in azs:
        _, right, up = cam_basis(az, el)
        rel = P - t
        half = max(half, np.abs(rel @ np.array(right)).max(), np.abs(rel @ np.array(up)).max())
    ortho = 2 * half * (1 + a.padding)
    cam.data.ortho_scale = ortho
    dist = float(np.linalg.norm(hi - lo)) * 2 + 1
    log("model bounds %s .. %s, ortho_scale %.4f, %d actions" % (
        np.round(lo, 3).tolist(), np.round(hi, 3).tolist(), ortho, len(plan)))

    # rotate model about Z if front is not +Z (apply to camera azimuth instead)
    front = math.radians(a.front_yaw)
    frames = []
    for name, act, frs in plan:
        if act:
            assign_action(act)
        for fi, f in enumerate(frs):
            scn.frame_set(f)
            for di, az in enumerate(azs):
                place_camera(cam, target, az - front, el, dist)
                fn = "%s_%s_%03d.png" % (name, names[di], fi)
                path = os.path.join(a.out_dir, fn)
                try:
                    render_to(path)
                except Exception as e:
                    raise SystemExit("ERROR: render failed with engine %s (%s). Try --engine cycles." % (a.engine, e))
                if not os.path.exists(path):
                    raise SystemExit("ERROR: no image written by engine %s. Try --engine cycles." % a.engine)
                if a.look == "toon":
                    posterize(path, a.toon_levels)
                frames.append(dict(file=fn, action=name, dir=names[di], dir_index=di,
                                   azimuth_deg=round(math.degrees(az), 3), frame=fi, source_frame=f))
    meta = dict(source=os.path.basename(a.input), blender=bpy.app.version_string, engine=a.engine,
                look=a.look, size=a.size, directions=names, elevation_deg=round(a.elevation, 3),
                ortho_scale=round(ortho, 5), pixels_per_unit=round(a.size / ortho, 3),
                fps=scn.render.fps, frames=frames)
    if a.spritesheet:
        meta["sheet"] = dict(file="sheet.png",
                             size=list(build_sheet(frames, a.out_dir, a.size, a.directions, names)))
    with open(os.path.join(a.out_dir, "sheet.json" if a.spritesheet else "frames.json"), "w") as fh:
        json.dump(meta, fh, indent=2)
    print("SPRITES_SUMMARY " + json.dumps(dict(
        out_dir=a.out_dir, frames=len(frames), actions=[p[0] for p in plan], directions=names,
        engine=a.engine, ortho_scale=meta["ortho_scale"], sheet=meta.get("sheet"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
