#!/usr/bin/env python3
"""glb_cleanup.py - headless Blender cleanup / decimate / bake / LOD for AI-generated GLBs.

Pipeline (in this order):
  1. import GLB (glTF Y-up is converted to Blender Z-up and back on export)
  2. join all meshes into one object (rigged models keep their armature)
  3. weld: merge vertices by distance (--weld, metres; 0 disables)
  4. remove loose vertices/edges, optionally tiny floating islands (--min-island-tris)
  5. optional recalc normals outward (--recalc-normals)
  6. apply scale/rotation (static models only), optional uniform rescale (--height)
  7. set origin to bottom-centre and place at world origin (+Y up in the GLB)
  8. decimate (Collapse) to --target-tris, then re-shade smooth with sharp edges by angle
  9. optional --bake: Smart-UV-project the low-poly, bake base colour (and --bake-normal
     normal map) from the ORIGINAL high-poly with Cycles on CPU, rebuild the material
 10. optional LODs (--lods 0.5,0.25,0.1)
 11. export GLB; print one line `GLB_CLEANUP_SUMMARY {json}` to stdout (tris before/after,
     bbox, materials, ...) and write the same JSON to <output>.summary.json

Usage
-----
  # Blender binary (any 4.x / 5.x):
  blender -b -P glb_cleanup.py -- in.glb out.glb --target-tris 5000 [options]
  # or the pip module (Python version must match the bpy wheel, 3.11 for 4.x, 3.13 for 5.x):
  pip install bpy numpy
  python glb_cleanup.py in.glb out.glb --target-tris 5000 [options]

Options
  --target-tris N        decimate to about N triangles (omit = no decimation)
  --weld D               merge-by-distance threshold in metres (default 0.0001)
  --min-island-tris N    delete connected pieces with < N triangles (default 0 = off)
  --recalc-normals       recalculate normals consistently outward (closed meshes only)
  --height H             uniformly scale so the model is H metres tall
  --smooth-angle DEG     edges sharper than this stay hard after decimation (default 40)
  --keep-normals         do not touch shading (custom normals are usually lost by decimation)
  --bake                 Smart UV project + bake base colour from the original high-poly
  --bake-normal          also bake a tangent-space normal map (needs --bake)
  --bake-size PX         bake texture size (default 1024)
  --bake-samples N       Cycles samples (default 1; colour bakes are noise free)
  --lods 0.5,0.25,0.1    extra LODs as ratios of the final LOD0 triangle count
  --lod-mode files|nodes|both
                         files: write out_LOD1.glb, out_LOD2.glb ... (default)
                         nodes: one GLB holding Name_LOD0, Name_LOD1 ... meshes
  --jpeg                 export textures as JPEG (smaller, no alpha) instead of PNG
  --no-animations        drop animations on export

LOD naming - what the engines expect (researched 2026-10-21)
  * Unity: an imported FBX containing meshes named Name_LOD0, Name_LOD1, Name_LOD2
    (LOD0 = most detailed) automatically gets a LODGroup
    (https://docs.unity3d.com/6000.0/Documentation/Manual/importing-lod-meshes.html;
    the page only names FBX). For GLB, Unity's glTFast importer does NOT build
    LODGroups from names (unverified) - so import LOD files separately and add a
    LODGroup by hand/script, or convert to FBX.
  * Godot 4: the glTF importer has no LOD name suffix (the suffix list in
    https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/node_type_customization.html
    has -col, -convcol, -colonly, -occ, -navmesh, -noimp, -loop ... but no LOD). Godot already
    generates LODs automatically on import for glTF
    (https://docs.godotengine.org/en/stable/tutorials/3d/mesh_lod.html); for
    artist-made LODs it recommends Visibility Ranges (HLOD) on separate nodes.
  Choice: default --lod-mode files writes separate GLBs (out_LOD1.glb ...); this works in
  both engines (Godot: set visibility_range_begin/end per MeshInstance3D; Unity: add a
  LODGroup). --lod-mode nodes also writes the Unity-style Name_LOD# names in one GLB, so
  a Unity FBX workflow or a post-import script can pick them up; in Godot they appear as
  overlapping sibling MeshInstance3D nodes you must give visibility ranges.

Rigged models (armature present): meshes are joined and decimated with weights kept, the
armature object (not the mesh) is moved to the origin, and scale is NOT applied (applying
scale to an armature breaks animation translation). Animations are exported.

Dependencies: Blender 4.x/5.x (or `pip install bpy`), numpy (bundled with both).
Bake uses Cycles on CPU - no GPU needed.

Tested 2026-10-21, CPU only, Linux x86_64:
  * `pip install bpy` 5.2.2 LTS (Python 3.13.16): DamagedHelmet.glb (static, textured; weld,
    decimate, --bake --bake-normal, --lods files), Fox.glb (skinned, 3 animations; decimate +
    bake), CesiumMan.glb (skinned; decimate + LODs files/nodes), Avocado.glb (--height),
    a synthetic GLB with a floating island (--min-island-tris).
  * Blender 4.5.9 LTS binary (`blender -b -P glb_cleanup.py -- ...`): DamagedHelmet with
    bake + LODs and Fox with decimation (animations kept).
Numbers are in scripts/README.md.
Known limits: loose vertices/edges rarely survive a GLB round trip anyway, so the loose-removal
step mostly cleans up after the weld; LOD meshes are decimated from LOD0 and reuse its UVs and
baked texture (slight UV stretching at high reduction); bake on rigged meshes was tested on
Fox only (rest pose); the importer's helper "bone shape" icospheres are deleted before joining.
"""
import argparse
import json
import math
import os
import sys
import time

try:
    import bpy
    import bmesh
    from mathutils import Matrix, Vector
    import numpy as np
except ImportError as e:  # pragma: no cover
    sys.stderr.write("ERROR: needs Blender's Python or `pip install bpy numpy` (%s)\n" % e)
    sys.exit(2)


# ----------------------------------------------------------------- helpers
def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    ap = argparse.ArgumentParser(prog="glb_cleanup.py", description=__doc__.split("\n")[0])
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--target-tris", type=int)
    ap.add_argument("--weld", type=float, default=0.0001)
    ap.add_argument("--min-island-tris", type=int, default=0)
    ap.add_argument("--recalc-normals", action="store_true")
    ap.add_argument("--height", type=float)
    ap.add_argument("--smooth-angle", type=float, default=40.0)
    ap.add_argument("--keep-normals", action="store_true")
    ap.add_argument("--bake", action="store_true")
    ap.add_argument("--bake-normal", action="store_true")
    ap.add_argument("--bake-size", type=int, default=1024)
    ap.add_argument("--bake-samples", type=int, default=1)
    ap.add_argument("--lods", default="")
    ap.add_argument("--lod-mode", choices=("files", "nodes", "both"), default="files")
    ap.add_argument("--jpeg", action="store_true")
    ap.add_argument("--no-animations", action="store_true")
    a = ap.parse_args(argv)
    a.lod_ratios = [float(x) for x in a.lods.split(",") if x.strip()]
    for r in a.lod_ratios:
        if not 0 < r < 1:
            ap.error("--lods ratios must be between 0 and 1 (exclusive)")
    if a.bake_normal and not a.bake:
        ap.error("--bake-normal requires --bake")
    return a


def log(*m):
    print("[glb_cleanup]", *m, file=sys.stderr, flush=True)


def tri_count(obj):
    me = obj.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def world_bounds(obj):
    me = obj.data
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    m = np.array(obj.matrix_world)
    w = co @ m[:3, :3].T + m[:3, 3]
    return w.min(axis=0), w.max(axis=0)


def gltf_bbox(lo, hi):
    """Blender Z-up bounds -> glTF Y-up (x, z, -y) as min/max/size."""
    lo, hi = list(lo), list(hi)
    gmin = [lo[0], lo[2], -hi[1]]
    gmax = [hi[0], hi[2], -lo[1]]
    return dict(min=[round(float(v), 4) for v in gmin], max=[round(float(v), 4) for v in gmax],
                size=[round(float(b - a), 4) for a, b in zip(gmin, gmax)])


def select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    if objs:
        bpy.context.view_layer.objects.active = objs[0]


def ctx(obj, selected=None):
    return bpy.context.temp_override(object=obj, active_object=obj,
                                     selected_objects=selected or [obj],
                                     selected_editable_objects=selected or [obj])


def bm_edit(obj, fn):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    res = fn(bm)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return res


def mat_names(objs):
    seen = []
    for o in objs:
        for s in o.material_slots:
            if s.material and s.material.name not in seen:
                seen.append(s.material.name)
    return seen


def image_sizes(objs):
    out = {}
    for o in objs:
        for s in o.material_slots:
            if not s.material or not s.material.use_nodes:
                continue
            for n in s.material.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image:
                    out[n.image.name] = list(n.image.size)
    return out


# ----------------------------------------------------------------- steps
def import_glb(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    # The glTF importer adds helper "bone shape" meshes (icospheres) for armatures: drop them
    shapes = {pb.custom_shape for a in arms for pb in a.pose.bones if pb.custom_shape}
    for a in arms:
        for pb in a.pose.bones:
            pb.custom_shape = None
    for o in shapes:
        bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("ERROR: no mesh objects in " + path)
    return meshes, arms


def join_meshes(meshes, rigged):
    if not rigged:
        # flatten hierarchy so world transforms bake into the joined mesh
        for o in meshes:
            if o.parent:
                m = o.matrix_world.copy()
                o.parent = None
                o.matrix_world = m
    select_only(meshes)
    active = meshes[0]
    if len(meshes) > 1:
        with ctx(active, meshes):
            bpy.ops.object.join()
    active.name = os.path.splitext(os.path.basename(bpy.path.abspath(
        bpy.data.filepath or "model")))[0] or "model"
    return active


def weld_and_clean(obj, dist, min_island_tris, recalc):
    stats = {}

    def fn(bm):
        v0 = len(bm.verts)
        if dist > 0:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
        stats["welded_verts"] = v0 - len(bm.verts)
        # loose geometry: loose edges first (no faces), then loose verts
        le = [e for e in bm.edges if not e.link_faces]
        bmesh.ops.delete(bm, geom=le, context="EDGES")
        lv = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=lv, context="VERTS")
        stats["loose_removed"] = len(le) + len(lv)
        removed_faces = 0
        if min_island_tris > 0:
            bm.faces.ensure_lookup_table()
            seen, kill = set(), []
            for f in bm.faces:
                if f.index in seen:
                    continue
                comp, stack = [], [f]
                seen.add(f.index)
                while stack:
                    cur = stack.pop()
                    comp.append(cur)
                    for e in cur.edges:
                        for nf in e.link_faces:
                            if nf.index not in seen:
                                seen.add(nf.index)
                                stack.append(nf)
                if sum(len(c.verts) - 2 for c in comp) < min_island_tris:
                    kill.extend(comp)
            if kill:
                bmesh.ops.delete(bm, geom=kill, context="FACES")
                lv = [v for v in bm.verts if not v.link_faces]
                bmesh.ops.delete(bm, geom=lv, context="VERTS")
            removed_faces = len(kill)
        stats["island_faces_removed"] = removed_faces
        if recalc:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return None

    bm_edit(obj, fn)
    return stats


def apply_xforms(obj, rigged, arm, height, scale=True):
    """Apply scale (static only), rescale to height, put bottom-centre at origin."""
    warnings = []
    if not rigged:
        if scale:
            with ctx(obj):
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        if height:
            lo, hi = world_bounds(obj)
            cur = hi[2] - lo[2]
            if cur > 0:
                obj.data.transform(Matrix.Scale(height / cur, 4))
                obj.data.update()
        lo, hi = world_bounds(obj)
        off = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))
        obj.data.transform(Matrix.Translation(-off))
        obj.data.update()
        obj.location = (0, 0, 0)
    else:
        sc = arm.scale
        if max(abs(sc[i] - 1) for i in range(3)) > 1e-4 or abs(arm.matrix_world.to_scale()[0] - 1) > 1e-4:
            warnings.append("armature has non-unit scale %s; not applied (would break animation)" % tuple(round(x, 4) for x in sc))
        if height:
            warnings.append("--height ignored for rigged models (would need animation rescale); scale in engine")
        lo, hi = world_bounds(obj)
        off = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))
        top = arm
        while top.parent:
            top = top.parent
        top.location -= off
        bpy.context.view_layer.update()
    return warnings, off


def decimate_to(obj, target, passes=3):
    """Collapse decimate to ~target triangles. Returns final tri count."""
    # triangulate first so the ratio maps to triangles
    bm_edit(obj, lambda bm: bmesh.ops.triangulate(bm, faces=bm.faces))
    cur = tri_count(obj)
    for _ in range(passes):
        if cur <= target * 1.03:
            break
        mod = obj.modifiers.new("dec", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = max(min(target / cur, 1.0), 0.0001)
        mod.use_collapse_triangulate = True
        with ctx(obj):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        cur = tri_count(obj)
    return cur


def reshade(obj, angle_deg):
    """Smooth shading with hard edges above angle (works without custom normals)."""
    me = obj.data
    if me.has_custom_normals:
        with ctx(obj):
            bpy.ops.mesh.customdata_custom_splitnormals_clear()

    def fn(bm):
        thr = math.radians(angle_deg)
        for f in bm.faces:
            f.smooth = True
        for e in bm.edges:
            e.smooth = True
            if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > thr:
                e.smooth = False

    bm_edit(obj, fn)


def smart_uv(obj, margin=0.003):
    me = obj.data
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name="UVMap")
    with ctx(obj):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=margin)
        bpy.ops.object.mode_set(mode="OBJECT")


def bake_textures(high, low, size, samples, do_normal):
    """Bake base colour (+normal) from high onto low; returns info dict."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = max(1, samples)
    scn.cycles.use_denoising = False
    dims = high.dimensions
    extr = 0.02 * max(dims)
    info = {}

    # fresh material on the low-poly with image targets
    mat = bpy.data.materials.new("baked_" + low.name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = nt.nodes["Material Output"]
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    low.data.materials.clear()
    low.data.materials.append(mat)

    def target_image(name, colorspace, alpha=False):
        img = bpy.data.images.new(name, size, size, alpha=alpha, float_buffer=False)
        img.colorspace_settings.name = colorspace
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = img
        node.interpolation = "Linear"
        return img, node

    img_c, node_c = target_image(low.name + "_basecolor", "sRGB")
    img_n = node_n = None
    if do_normal:
        img_n, node_n = target_image(low.name + "_normal", "Non-Color")

    select_only([high])
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low

    def run(kind, node, **kw):
        for n in nt.nodes:  # select first, then set active (reverse order resets selection)
            n.select = False
        node.select = True
        nt.nodes.active = node
        with ctx(low, [high, low]):
            bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=extr,
                                max_ray_distance=extr * 4, margin=16, margin_type="EXTEND",
                                target="IMAGE_TEXTURES", **kw)

    run("DIFFUSE", node_c, pass_filter={"COLOR"})
    nt.links.new(node_c.outputs["Color"], bsdf.inputs["Base Color"])
    info["basecolor"] = [size, size]
    if do_normal:
        run("NORMAL", node_n, normal_space="TANGENT")
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(node_n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        info["normal"] = [size, size]
    for img in (img_c, img_n):
        if img:
            img.pack()
    info["cage_extrusion_m"] = round(extr, 5)
    return info


def export_glb(path, objs, args, animations):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    select_only(objs)
    kw = dict(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
              export_apply=False, export_animations=animations,
              export_image_format="JPEG" if args.jpeg else "AUTO")
    if animations:
        kw["export_animation_mode"] = "ACTIONS"
    bpy.ops.export_scene.gltf(**kw)
    return os.path.getsize(path)


def duplicate(obj, name):
    d = obj.copy()
    d.data = obj.data.copy()
    d.name = name
    d.data.name = name
    for c in obj.users_collection:
        c.objects.link(d)
    return d


# ----------------------------------------------------------------- main
def main():
    args = parse_args()
    t0 = time.time()
    meshes, arms = import_glb(os.path.abspath(args.input))
    rigged = bool(arms)
    base = os.path.splitext(os.path.basename(args.input))[0]
    n_meshes_in = len(meshes)
    tris_in = sum(tri_count(m) for m in meshes)
    verts_in = sum(len(m.data.vertices) for m in meshes)
    mats_in = mat_names(meshes)
    allv = [world_bounds(m) for m in meshes]
    lo0 = np.min([a for a, _ in allv], axis=0)
    hi0 = np.max([b for _, b in allv], axis=0)
    log("imported %d mesh object(s), %d armature(s), %d tris" % (n_meshes_in, len(arms), tris_in))

    obj = join_meshes(meshes, rigged)
    obj.name = base
    obj.data.name = base
    cleaned = weld_and_clean(obj, args.weld, args.min_island_tris, args.recalc_normals)
    warnings, _ = apply_xforms(obj, rigged, arms[0] if rigged else None, args.height)

    tris_clean = tri_count(obj)
    result_low = obj
    bake_info = None
    high = None
    if args.bake:
        # high-poly reference = cleaned mesh, triangulated, before decimation
        bm_edit(obj, lambda bm: bmesh.ops.triangulate(bm, faces=bm.faces))
        high = duplicate(obj, base + "_high")
        high.hide_render = False
        if rigged:
            for a in arms:
                a.data.pose_position = "REST"

    if args.target_tris:
        tris_out = decimate_to(obj, args.target_tris)
    else:
        tris_out = tri_count(obj)
    if not args.keep_normals:
        reshade(obj, args.smooth_angle)
    if args.target_tris:  # decimation shifts the bounds slightly: re-place bottom-centre
        _, off = apply_xforms(obj, rigged, arms[0] if rigged else None, None, scale=False)
        if high and not rigged:  # keep the bake reference aligned with the shifted low-poly
            high.data.transform(Matrix.Translation(-off))
            high.data.update()

    if args.bake:
        smart_uv(obj)
        t1 = time.time()
        bake_info = bake_textures(high, obj, args.bake_size, args.bake_samples, args.bake_normal)
        bake_info["seconds"] = round(time.time() - t1, 1)
        bpy.data.objects.remove(high, do_unlink=True)
        if rigged:
            for a in arms:
                a.data.pose_position = "POSE"

    export_roots = ([a for a in arms if not a.parent] if rigged else []) + [obj]
    if rigged:
        # armature + mesh (children are included via selection of both)
        export_roots = list(dict.fromkeys(arms + [obj]))

    # ---- LODs
    lod_info = []
    out_base, out_ext = os.path.splitext(args.output)
    if args.lod_ratios:
        lod0 = tri_count(obj)
        lod_objs = []
        for i, r in enumerate(args.lod_ratios, start=1):
            d = duplicate(obj, "%s_LOD%d" % (base, i))
            if rigged and obj.parent:
                d.parent = obj.parent
                d.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
                for m in obj.modifiers:
                    if m.type == "ARMATURE":
                        nm = d.modifiers.new(m.name, "ARMATURE")
                        nm.object = m.object
            elif rigged:
                pass
            for vg in obj.vertex_groups:
                if vg.name not in d.vertex_groups:
                    d.vertex_groups.new(name=vg.name)
            n = decimate_to(d, max(4, int(lod0 * r)))
            if not args.keep_normals:
                reshade(d, args.smooth_angle)
            lod_objs.append((i, r, d, n))
        if args.lod_mode in ("files", "both"):
            for i, r, d, n in lod_objs:
                p = "%s_LOD%d%s" % (out_base, i, out_ext or ".glb")
                for o in list(bpy.context.scene.objects):
                    o.hide_set(False)
                sel = (arms if rigged else []) + [d]
                size = export_glb(p, sel, args, not args.no_animations and rigged)
                lod_info.append(dict(lod=i, ratio=r, tris=n, file=p, bytes=size))
        if args.lod_mode in ("nodes", "both"):
            obj.name = "%s_LOD0" % base
            obj.data.name = obj.name
            sel = (arms if rigged else []) + [obj] + [d for _, _, d, _ in lod_objs]
            p = args.output if args.lod_mode == "nodes" else "%s_lods%s" % (out_base, out_ext or ".glb")
            size = export_glb(p, sel, args, not args.no_animations and rigged)
            lod_info.append(dict(lod="nodes", names=[o.name for o in sel if o.type == "MESH"], file=p, bytes=size))
            obj.name = base
        for i, r, d, n in lod_objs:
            bpy.data.objects.remove(d, do_unlink=True)

    # ---- main export
    if args.lod_mode != "nodes" or not args.lod_ratios:
        size = export_glb(args.output, export_roots, args, not args.no_animations)
    else:
        size = os.path.getsize(args.output)

    lo1, hi1 = world_bounds(obj)
    anim_count = len(bpy.data.actions)
    summary = dict(
        input=args.input, output=args.output, blender=bpy.app.version_string,
        rigged=rigged, meshes_in=n_meshes_in,
        tris_before=tris_in, tris_after=tri_count(obj), tris_after_cleanup_before_decimate=tris_clean,
        verts_before=verts_in, verts_after=len(obj.data.vertices),
        cleanup=cleaned,
        bbox_before=gltf_bbox(lo0, hi0), bbox_after=gltf_bbox(lo1, hi1),
        materials_before=mats_in, materials_after=mat_names([obj]),
        images=image_sizes([obj]), animations=anim_count,
        bake=bake_info, lods=lod_info, output_bytes=size,
        warnings=warnings, seconds=round(time.time() - t0, 1),
    )
    summary_path = os.path.splitext(args.output)[0] + ".summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print("GLB_CLEANUP_SUMMARY " + json.dumps(summary))
    log("summary also written to " + summary_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
