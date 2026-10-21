#!/usr/bin/env python3
"""check_glb.py - inspect a .glb / .gltf and flag problems against a budget.

Reports: triangle and vertex counts (counting every node instance), meshes,
materials, texture sizes and formats, skins (joint counts), animations,
world-space bounding box / size, and extensions in use.  Then compares against
a budget profile and prints WARN / FAIL lines.  Exit code is 1 if any FAIL.

Usage
-----
    python check_glb.py model.glb
    python check_glb.py model.glb --budget mobile
    python check_glb.py model.glb --budget pc --json          # machine-readable
    python check_glb.py model.glb --budget mobile --max-tris 8000 --max-texture 512

Budgets (starting points, override with --max-* flags; tune per project)
    mobile: <=15,000 tris, <=4 materials, textures <=1024 px, <=60 joints/skin,
            <=32 animations
    pc:     <=100,000 tris, <=16 materials, textures <=4096 px, <=256 joints/skin
Budget numbers are rules of thumb for one hero prop/character, not engine
limits.  Sources: Godot docs "Optimizing 3D performance"
(https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html),
Unity "Optimize mobile graphics"
(https://docs.unity3d.com/6000.0/Documentation/Manual/mobile-optimization.html).

Dependencies: Python 3.8+ standard library only (no pygltflib/trimesh needed).
Texture sizes are read from PNG/JPEG/WebP headers; KTX2 is read for pixel size.
Draco- or meshopt-compressed meshes cannot be counted from the accessors that
carry the geometry; the script then uses the accessor counts that glTF still
declares (they stay valid), and prints a note.

Tested (2026-10-21, Python 3.13.16, Linux): KhronosGroup glTF-Sample-Assets
DamagedHelmet.glb, Fox.glb (skinned+animated), CesiumMan.glb, Avocado.glb, and
a Blender-exported output of glb_cleanup.py.  See scripts/README.md for numbers.
"""
import argparse
import json
import math
import os
import struct
import sys
import base64

PROFILES = {
    "mobile": dict(max_tris=15000, max_verts=30000, max_materials=4,
                   max_texture=1024, max_joints=60, max_anims=32,
                   max_textures=8),
    "pc": dict(max_tris=100000, max_verts=200000, max_materials=16,
               max_texture=4096, max_joints=256, max_anims=64,
               max_textures=32),
}

COMPONENT_SIZE = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
TYPE_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
              "MAT2": 4, "MAT3": 9, "MAT4": 16}


# ---------------------------------------------------------------- loading
def load_gltf(path):
    """Return (json_dict, bin_chunk_or_None, base_dir)."""
    base = os.path.dirname(os.path.abspath(path))
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] == b"glTF":
        version, length = struct.unpack_from("<II", data, 4)
        if version != 2:
            raise ValueError("unsupported GLB version %d" % version)
        off, js, binc = 12, None, None
        while off + 8 <= len(data):
            clen, ctype = struct.unpack_from("<II", data, off)
            chunk = data[off + 8: off + 8 + clen]
            if ctype == 0x4E4F534A:
                js = json.loads(chunk.decode("utf-8"))
            elif ctype == 0x004E4942 and binc is None:
                binc = chunk
            off += 8 + clen + (-clen % 4)
        if js is None:
            raise ValueError("GLB has no JSON chunk")
        return js, binc, base
    return json.loads(data.decode("utf-8")), None, base


def buffer_bytes(g, binc, base, idx):
    b = g["buffers"][idx]
    uri = b.get("uri")
    if uri is None:
        return binc
    if uri.startswith("data:"):
        return base64.b64decode(uri.split(",", 1)[1])
    from urllib.parse import unquote
    with open(os.path.join(base, unquote(uri)), "rb") as f:
        return f.read()


def image_bytes(g, binc, base, img, cache):
    if "bufferView" in img:
        bv = g["bufferViews"][img["bufferView"]]
        key = bv["buffer"]
        if key not in cache:
            cache[key] = buffer_bytes(g, binc, base, key)
        buf = cache[key]
        o = bv.get("byteOffset", 0)
        return buf[o:o + bv["byteLength"]]
    uri = img.get("uri", "")
    if uri.startswith("data:"):
        return base64.b64decode(uri.split(",", 1)[1])
    from urllib.parse import unquote
    p = os.path.join(base, unquote(uri))
    if os.path.exists(p):
        with open(p, "rb") as f:
            return f.read()
    return None


def image_info(b):
    """Return (format, w, h) from header bytes, or (format, None, None)."""
    if b is None:
        return "missing", None, None
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", b[16:24])
        return "png", w, h
    if b[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(b):
            if b[i] != 0xFF:
                i += 1
                continue
            m = b[i + 1]
            if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                i += 2
                continue
            seglen = struct.unpack(">H", b[i + 2:i + 4])[0]
            if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return "jpeg", w, h
            i += 2 + seglen
        return "jpeg", None, None
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        t = b[12:16]
        if t == b"VP8 " and len(b) >= 30:
            w, h = struct.unpack("<HH", b[26:30])
            return "webp", w & 0x3FFF, h & 0x3FFF
        if t == b"VP8L" and len(b) >= 25:
            v = struct.unpack("<I", b[21:25])[0]
            return "webp", (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1
        if t == b"VP8X" and len(b) >= 30:
            w = int.from_bytes(b[24:27], "little") + 1
            h = int.from_bytes(b[27:30], "little") + 1
            return "webp", w, h
        return "webp", None, None
    if b[:12] == b"\xabKTX 20\xbb\r\n\x1a\n":
        w, h = struct.unpack("<II", b[20:28])
        return "ktx2", w, h
    return "unknown", None, None


# ---------------------------------------------------------------- math
def mat_identity():
    return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def mat_mul(a, b):  # column-major 4x4
    r = [0.0] * 16
    for c in range(4):
        for rr in range(4):
            r[c * 4 + rr] = sum(a[k * 4 + rr] * b[c * 4 + k] for k in range(4))
    return r


def node_local(n):
    if "matrix" in n:
        return list(n["matrix"])
    t = n.get("translation", [0, 0, 0])
    q = n.get("rotation", [0, 0, 0, 1])
    s = n.get("scale", [1, 1, 1])
    x, y, z, w = q
    r = [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w),
         2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w),
         2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)]
    m = [r[0] * s[0], r[1] * s[0], r[2] * s[0], 0,
         r[3] * s[1], r[4] * s[1], r[5] * s[1], 0,
         r[6] * s[2], r[7] * s[2], r[8] * s[2], 0,
         t[0], t[1], t[2], 1]
    return m


def xform_point(m, p):
    return [m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
            m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13],
            m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14]]


def mat_scale(m):
    return [math.sqrt(sum(m[c * 4 + i] ** 2 for i in range(3))) for c in range(3)]


# ---------------------------------------------------------------- accessors
_FMT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
_NORM = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}


def read_accessor(g, binc, base, idx, cache):
    """Return list of tuples for a (non-sparse) accessor."""
    acc = g["accessors"][idx]
    if "bufferView" not in acc:
        return [tuple([0.0] * TYPE_COUNT[acc["type"]])] * acc["count"]
    bv = g["bufferViews"][acc["bufferView"]]
    if bv["buffer"] not in cache:
        cache[bv["buffer"]] = buffer_bytes(g, binc, base, bv["buffer"])
    buf = cache[bv["buffer"]]
    ncomp = TYPE_COUNT[acc["type"]]
    ct = acc["componentType"]
    csz = COMPONENT_SIZE[ct]
    stride = bv.get("byteStride") or csz * ncomp
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    fmt = "<" + _FMT[ct] * ncomp
    norm = acc.get("normalized") and ct in _NORM
    out = []
    for i in range(acc["count"]):
        t = struct.unpack_from(fmt, buf, off + i * stride)
        if norm:
            t = tuple(max(v / _NORM[ct], -1.0) for v in t)
        out.append(t)
    return out


def skinned_bounds(g, binc, base, node_idx, world, cache):
    """Rest-pose bounds of a skinned mesh node (applies joint matrices * IBM,
    ignoring the mesh node's own transform as the glTF spec requires).
    """
    n = g["nodes"][node_idx]
    skin = g["skins"][n["skin"]]
    joints = skin["joints"]
    ibms = None
    if "inverseBindMatrices" in skin:
        flat = read_accessor(g, binc, base, skin["inverseBindMatrices"], cache)
        ibms = [list(t) for t in flat]
    jm = []
    for k, j in enumerate(joints):
        jw = world.get(j, mat_identity())
        ib = ibms[k] if ibms else mat_identity()
        jm.append(mat_mul(jw, ib))
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for p in g["meshes"][n["mesh"]]["primitives"]:
        at = p["attributes"]
        if "JOINTS_0" not in at or "WEIGHTS_0" not in at:
            continue
        pos = read_accessor(g, binc, base, at["POSITION"], cache)
        jj = read_accessor(g, binc, base, at["JOINTS_0"], cache)
        ww = read_accessor(g, binc, base, at["WEIGHTS_0"], cache)
        for pv, j4, w4 in zip(pos, jj, ww):
            x = y = z = 0.0
            for j, w in zip(j4, w4):
                if w == 0:
                    continue
                m = jm[int(j)]
                x += w * (m[0] * pv[0] + m[4] * pv[1] + m[8] * pv[2] + m[12])
                y += w * (m[1] * pv[0] + m[5] * pv[1] + m[9] * pv[2] + m[13])
                z += w * (m[2] * pv[0] + m[6] * pv[1] + m[10] * pv[2] + m[14])
            for k, v in enumerate((x, y, z)):
                if v < lo[k]: lo[k] = v
                if v > hi[k]: hi[k] = v
    return lo, hi


# ---------------------------------------------------------------- analysis
def prim_tris(g, prim):
    mode = prim.get("mode", 4)
    if "indices" in prim:
        n = g["accessors"][prim["indices"]]["count"]
    else:
        n = g["accessors"][prim["attributes"]["POSITION"]]["count"]
    if mode == 4:
        return n // 3
    if mode in (5, 6):
        return max(n - 2, 0)
    return 0  # points / lines


def analyze(path):
    g, binc, base = load_gltf(path)
    notes = []
    exts_used = g.get("extensionsUsed", [])
    exts_req = g.get("extensionsRequired", [])
    compressed = [e for e in exts_used if e in ("KHR_draco_mesh_compression", "EXT_meshopt_compression")]
    if compressed:
        notes.append("Geometry uses %s: counts come from declared accessor counts." % ", ".join(compressed))

    nodes = g.get("nodes", [])
    meshes = g.get("meshes", [])
    scene_idx = g.get("scene", 0)
    scenes = g.get("scenes", [])
    roots = scenes[scene_idx]["nodes"] if scenes else list(range(len(nodes)))

    totals = dict(tris=0, verts=0, instances=0, prims=0)
    used_mats = set()
    bb_min = [math.inf] * 3
    bb_max = [-math.inf] * 3
    nonuniform = []
    neg_scale = []
    missing_normals = set()
    missing_uv = set()
    extra_joint_sets = False
    skinned_nodes = []
    seen_nodes = set()
    world = {}
    acc_cache = {}

    def visit(i, parent):
        nonlocal extra_joint_sets
        if i in seen_nodes:
            return
        seen_nodes.add(i)
        n = nodes[i]
        m = mat_mul(parent, node_local(n))
        world[i] = m
        sc = mat_scale(m)
        if max(sc) > 0 and (max(sc) - min(sc)) / max(sc) > 0.01:
            nonuniform.append(n.get("name", "node%d" % i))
        det_sign = (m[0] * (m[5] * m[10] - m[6] * m[9]) - m[1] * (m[4] * m[10] - m[6] * m[8])
                    + m[2] * (m[4] * m[9] - m[5] * m[8]))
        if det_sign < 0:
            neg_scale.append(n.get("name", "node%d" % i))
        if "mesh" in n:
            mesh = meshes[n["mesh"]]
            totals["instances"] += 1
            if "skin" in n:
                skinned_nodes.append(i)
            for p in mesh["primitives"]:
                totals["prims"] += 1
                totals["tris"] += prim_tris(g, p)
                pos = g["accessors"][p["attributes"]["POSITION"]]
                totals["verts"] += pos["count"]
                if "material" in p:
                    used_mats.add(p["material"])
                if "NORMAL" not in p["attributes"] and p.get("mode", 4) == 4:
                    missing_normals.add(mesh.get("name", "mesh%d" % n["mesh"]))
                if "TEXCOORD_0" not in p["attributes"] and "material" in p:
                    missing_uv.add(mesh.get("name", "mesh%d" % n["mesh"]))
                if "JOINTS_1" in p["attributes"]:
                    extra_joint_sets = True
                if "skin" in n:
                    continue  # bounds computed after traversal (needs all joint matrices)
                if "min" in pos and "max" in pos:
                    lo, hi = pos["min"], pos["max"]
                    for cx in (lo[0], hi[0]):
                        for cy in (lo[1], hi[1]):
                            for cz in (lo[2], hi[2]):
                                w = xform_point(m, [cx, cy, cz])
                                for k in range(3):
                                    bb_min[k] = min(bb_min[k], w[k])
                                    bb_max[k] = max(bb_max[k], w[k])
        for c in n.get("children", []):
            visit(c, m)

    for r in roots:
        visit(r, mat_identity())

    # Skinned meshes: node transform is ignored by the spec; skin the vertices with
    # the rest-pose joint matrices instead.
    for ni in skinned_nodes:
        try:
            lo, hi = skinned_bounds(g, binc, base, ni, world, acc_cache)
        except Exception as e:  # noqa
            notes.append("Could not skin node %d for bounds: %s" % (ni, e))
            continue
        if lo[0] != math.inf:
            for k in range(3):
                bb_min[k] = min(bb_min[k], lo[k])
                bb_max[k] = max(bb_max[k], hi[k])
    if skinned_nodes:
        notes.append("Skinned mesh: bounding box is the rest pose (no animation applied); animated extents can differ.")

    # materials
    mats = []
    for mi, mt in enumerate(g.get("materials", [])):
        pbr = mt.get("pbrMetallicRoughness", {})
        slots = []
        if "baseColorTexture" in pbr: slots.append("baseColor")
        if "metallicRoughnessTexture" in pbr: slots.append("metalRough")
        if "normalTexture" in mt: slots.append("normal")
        if "occlusionTexture" in mt: slots.append("occlusion")
        if "emissiveTexture" in mt: slots.append("emissive")
        mats.append(dict(index=mi, name=mt.get("name", ""), used=mi in used_mats,
                         alphaMode=mt.get("alphaMode", "OPAQUE"),
                         doubleSided=mt.get("doubleSided", False),
                         textures=slots, extensions=sorted(mt.get("extensions", {}).keys())))

    # textures
    cache = {}
    imgs = []
    for ii, im in enumerate(g.get("images", [])):
        raw = image_bytes(g, binc, base, im, cache)
        fmt, w, h = image_info(raw)
        imgs.append(dict(index=ii, name=im.get("name", im.get("uri", "")[:40] if not im.get("uri", "").startswith("data:") else ""),
                         format=fmt, width=w, height=h,
                         bytes=len(raw) if raw else None, mime=im.get("mimeType")))
    # texture slot -> image sizes via materials
    # skins / anims
    skins = []
    for si, sk in enumerate(g.get("skins", [])):
        skins.append(dict(index=si, joints=len(sk["joints"]), name=sk.get("name", "")))
    anims = []
    for ai, an in enumerate(g.get("animations", [])):
        tmax = 0.0
        for s in an.get("samplers", []):
            acc = g["accessors"][s["input"]]
            if "max" in acc:
                tmax = max(tmax, acc["max"][0])
        anims.append(dict(index=ai, name=an.get("name", "anim%d" % ai),
                          channels=len(an.get("channels", [])), duration_s=round(tmax, 3)))

    have_bb = bb_min[0] != math.inf
    bbox = None
    if have_bb:
        size = [bb_max[k] - bb_min[k] for k in range(3)]
        bbox = dict(min=[round(v, 4) for v in bb_min], max=[round(v, 4) for v in bb_max],
                    size=[round(v, 4) for v in size])

    return dict(
        file=os.path.basename(path), file_bytes=os.path.getsize(path),
        generator=g.get("asset", {}).get("generator"),
        gltf_version=g.get("asset", {}).get("version"),
        triangles=totals["tris"], vertices=totals["verts"],
        mesh_instances=totals["instances"], primitives=totals["prims"],
        meshes=len(meshes), nodes=len(nodes),
        materials=mats, material_count_used=len(used_mats),
        images=imgs, textures=len(g.get("textures", [])),
        skins=skins, animations=anims,
        has_skin=bool(skins), has_animation=bool(anims),
        bbox=bbox,
        extensions_used=exts_used, extensions_required=exts_req,
        _flags=dict(nonuniform=nonuniform, neg_scale=neg_scale,
                    missing_normals=sorted(missing_normals), missing_uv=sorted(missing_uv),
                    extra_joint_sets=extra_joint_sets),
        notes=notes,
    )


def is_pot(n):
    return n > 0 and (n & (n - 1)) == 0


def evaluate(r, lim):
    issues = []  # (level, msg)
    add = lambda lvl, msg: issues.append((lvl, msg))
    if r["triangles"] > lim["max_tris"]:
        add("FAIL", "triangles %d > budget %d" % (r["triangles"], lim["max_tris"]))
    elif r["triangles"] > 0.8 * lim["max_tris"]:
        add("WARN", "triangles %d is over 80%% of budget %d" % (r["triangles"], lim["max_tris"]))
    if r["vertices"] > lim["max_verts"]:
        add("WARN", "vertices %d > %d (vertex count can exceed tris-based budget due to split UV/normals)"
            % (r["vertices"], lim["max_verts"]))
    if r["triangles"] == 0:
        add("FAIL", "no triangles found (empty scene, point/line-only, or unsupported primitive mode)")
    if r["material_count_used"] > lim["max_materials"]:
        add("FAIL", "%d materials in use > budget %d (each is a draw call; atlas them)"
            % (r["material_count_used"], lim["max_materials"]))
    unused = [m["index"] for m in r["materials"] if not m["used"]]
    if unused:
        add("WARN", "unused materials: %s" % unused)
    for im in r["images"]:
        label = "image %d (%s)" % (im["index"], im["name"] or im["format"])
        if im["format"] == "missing":
            add("FAIL", "%s: external file not found" % label)
            continue
        w, h = im["width"], im["height"]
        if w is None:
            add("WARN", "%s: could not read size (%s)" % (label, im["format"]))
            continue
        if max(w, h) > lim["max_texture"]:
            add("FAIL", "%s is %dx%d > max texture %d" % (label, w, h, lim["max_texture"]))
        if not (is_pot(w) and is_pot(h)):
            add("WARN", "%s is %dx%d, not power-of-two (breaks mipmaps/compression on some mobile GPUs)" % (label, w, h))
        if im["format"] in ("png", "jpeg") and lim is PROFILES["mobile"]:
            pass
    if len(r["images"]) > lim["max_textures"]:
        add("WARN", "%d images > %d" % (len(r["images"]), lim["max_textures"]))
    for sk in r["skins"]:
        if sk["joints"] > lim["max_joints"]:
            add("FAIL", "skin %d has %d joints > budget %d" % (sk["index"], sk["joints"], lim["max_joints"]))
    if r["_flags"]["extra_joint_sets"]:
        add("WARN", "JOINTS_1 present: >4 bone influences per vertex; Unity/Godot mobile cap at 4")
    if len(r["animations"]) > lim["max_anims"]:
        add("WARN", "%d animations > %d" % (len(r["animations"]), lim["max_anims"]))
    if r["has_skin"] and not r["has_animation"]:
        add("WARN", "skinned but no animations in file (fine if animations are separate files)")
    if r["has_animation"] and not r["has_skin"]:
        add("WARN", "animations present but no skin (node-transform animation only)")
    fl = r["_flags"]
    if fl["nonuniform"]:
        add("WARN", "non-uniform node scale on: %s (apply scale before export)" % ", ".join(fl["nonuniform"][:5]))
    if fl["neg_scale"]:
        add("WARN", "mirrored (negative-determinant) node transform on: %s (flipped winding risk)" % ", ".join(fl["neg_scale"][:5]))
    if fl["missing_normals"]:
        add("WARN", "no NORMAL attribute on meshes: %s (engines will recompute flat/auto normals)" % ", ".join(fl["missing_normals"][:5]))
    if fl["missing_uv"]:
        add("WARN", "textured material but no TEXCOORD_0 on: %s" % ", ".join(fl["missing_uv"][:5]))
    bb = r["bbox"]
    if bb:
        size = bb["size"]
        big = max(size)
        if big > 100:
            add("WARN", "largest dimension %.2f m: probably cm or mm units baked in (glTF is metres)" % big)
        elif 0 < big < 0.01:
            add("WARN", "largest dimension %.4f m: probably tiny / wrong unit scale" % big)
        cx = (bb["min"][0] + bb["max"][0]) / 2
        cz = (bb["min"][2] + bb["max"][2]) / 2
        if abs(bb["min"][1]) > 0.02 * max(big, 1e-9) or abs(cx) > 0.1 * max(big, 1e-9) or abs(cz) > 0.1 * max(big, 1e-9):
            add("INFO", "pivot is not bottom-center (min Y=%.3f, center X=%.3f, Z=%.3f); fine for props that "
                "should pivot elsewhere, otherwise use glb_cleanup.py" % (bb["min"][1], cx, cz))
    else:
        add("WARN", "bounding box unavailable (POSITION accessors lack min/max)")
    for e in r["extensions_required"]:
        if e in ("KHR_draco_mesh_compression", "EXT_meshopt_compression", "KHR_texture_basisu"):
            add("WARN", "required extension %s: Godot 4 import supports meshopt/basisu only in recent "
                "versions and Unity needs a package (glTFast); check your engine version" % e)
    return issues


def print_report(r, issues, budget, lim):
    p = print
    p("File: %s (%.2f MB)  generator: %s" % (r["file"], r["file_bytes"] / 1e6, r["generator"]))
    p("Triangles: %d   Vertices: %d   Meshes: %d (instances %d, primitives %d)   Nodes: %d"
      % (r["triangles"], r["vertices"], r["meshes"], r["mesh_instances"], r["primitives"], r["nodes"]))
    p("Materials: %d defined, %d used" % (len(r["materials"]), r["material_count_used"]))
    for m in r["materials"]:
        p("  [%d] %-24s alpha=%-6s tex=%s%s" % (m["index"], m["name"], m["alphaMode"],
                                                  ",".join(m["textures"]) or "-",
                                                  "" if m["used"] else "  (unused)"))
    p("Images: %d" % len(r["images"]))
    for im in r["images"]:
        sz = "%sx%s" % (im["width"], im["height"]) if im["width"] else "?"
        p("  [%d] %-8s %-11s %s KB" % (im["index"], im["format"], sz,
                                       "?" if im["bytes"] is None else "%.0f" % (im["bytes"] / 1024)))
    p("Skins: %s   Animations: %d" % (
        ", ".join("%d joints" % s["joints"] for s in r["skins"]) or "none", len(r["animations"])))
    for a in r["animations"]:
        p("  [%d] %-20s %.2fs, %d channels" % (a["index"], a["name"], a["duration_s"], a["channels"]))
    if r["bbox"]:
        b = r["bbox"]
        p("Bounding box (m): min %s max %s size %s" % (b["min"], b["max"], b["size"]))
    if r["extensions_used"]:
        p("Extensions used: %s" % ", ".join(r["extensions_used"]))
    for n in r["notes"]:
        p("Note: " + n)
    p("")
    p("Budget: %s  %s" % (budget, json.dumps(lim)))
    if not issues:
        p("OK: no issues")
    for lvl, msg in issues:
        p("%-4s %s" % (lvl, msg))
    fails = sum(1 for l, _ in issues if l == "FAIL")
    warns = sum(1 for l, _ in issues if l == "WARN")
    p("Result: %s (%d fail, %d warn)" % ("FAIL" if fails else "PASS", fails, warns))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Report stats for a GLB/glTF and flag issues vs a budget.")
    ap.add_argument("path", help=".glb or .gltf file")
    ap.add_argument("--budget", choices=sorted(PROFILES), default="mobile")
    ap.add_argument("--max-tris", type=int)
    ap.add_argument("--max-verts", type=int)
    ap.add_argument("--max-materials", type=int)
    ap.add_argument("--max-texture", type=int, help="max texture edge in pixels")
    ap.add_argument("--max-joints", type=int)
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    a = ap.parse_args(argv)

    lim = dict(PROFILES[a.budget])
    for k in ("max_tris", "max_verts", "max_materials", "max_texture", "max_joints"):
        v = getattr(a, k)
        if v is not None:
            lim[k] = v
    try:
        r = analyze(a.path)
    except Exception as e:  # noqa
        print("ERROR: cannot read %s: %s" % (a.path, e), file=sys.stderr)
        return 2
    issues = evaluate(r, lim)
    fails = sum(1 for l, _ in issues if l == "FAIL")
    if a.json:
        out = {k: v for k, v in r.items() if not k.startswith("_")}
        out["budget"] = dict(name=a.budget, **lim)
        out["issues"] = [dict(level=l, message=m) for l, m in issues]
        out["pass"] = fails == 0
        print(json.dumps(out, indent=2))
    else:
        print_report(r, issues, a.budget, lim)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
