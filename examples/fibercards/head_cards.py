"""Blonde hair of the Cuca as fiber cards (one-shot Blender script): opens her rigged body, builds strip planes whose UV = a cell of the sheet
(fibercards/out/hair_color.png + hair_normal.png, 4x3 cells, root at the top of a cell), fitted to her head, saves draft/cuca_hair.blend.
  blender -b --factory-startup --python tools/general/blender_once.py -- examples/fibercards/head_cards.py
A card is a strip of SEG quads along its length (so it bends over the skull), 1 across. Its centreline walks down the head surface: from a root at polar
angle TH0 (about the head centre C, 0 = top, azimuth 0 = front) the points follow the surface (ray from C, offset outward by the layer's lift) down to
TH_END, then hang straight down; a point inside the body is pushed out. Layers go from dense (near the scalp) to sparse (outer wisps), the material shows both faces."""
import math, random, os
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT = os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd()); H = ROOT + "/projects/cuca-hair"
C = Vector((0, -0.02, 0.95)); TH_END, SEG = math.radians(98), 16
CROP = (0.15, 0.85, 0.04, 0.97)                                   # the part of a cell the strands occupy: u0, u1, v0, v1 (v from the top)
SHEET = "hair_long"                                               # fibercards/out/<SHEET>_color.png: long, dense, straight pale strands (docs/07-fibercards)
# layers, dense near the scalp to sparse wisps outside: cells of the sheet, number, lift (m), width, length factor, root polar angle range (deg), sway (rad)
LAYERS = [dict(cells=(8, 9, 10, 11), n=16, lift=0.014, W=0.12, k=1.0, th=(4, 24), sway=0.04), dict(cells=(6, 7, 9, 10), n=18, lift=0.024, W=0.12, k=1.0, th=(10, 38), sway=0.06),
          dict(cells=(8, 9, 10, 11), n=12, lift=0.034, W=0.11, k=0.95, th=(16, 46), sway=0.08), dict(cells=(3, 4, 5, 6), n=6, lift=0.026, W=0.08, k=0.85, th=(10, 40), sway=0.15)]


def length(phi):                                                  # short over the forehead (the eyes stay free), to the shoulders on the sides and at the back
    t = min(1.0, max(0.0, (abs(phi) - 0.7) / 1.0)); return 0.08 + 0.19 * t * t * (3 - 2 * t)


def uv(cell, a, b):                                               # a across 0..1, b along 0 (root) .. 1 (tip), in the crop of the cell
    c, r = cell % 4, cell // 4; u = (c + CROP[0] + a * (CROP[1] - CROP[0])) / 4; v = 1 - (r + CROP[2] + b * (CROP[3] - CROP[2])) / 3
    return u, v


def surface(tree, th, phi, lift):
    d = Vector((math.sin(th) * math.sin(phi), -math.sin(th) * math.cos(phi), math.cos(th)))
    h = tree.ray_cast(C + d * 0.3, -d, 0.4)                       # from outside toward C: the outer skin
    return (h[0] + d * lift if h[0] is not None else C + d * (0.11 + lift)), d


def push(tree, p, lift):
    loc, n, i, dist = tree.find_nearest(p, 0.05)
    if loc is not None and ((p - loc).dot(n) < 0 or dist < lift * 0.6):
        p = loc + n * lift * 0.8
    return p


def wrap(tree, q, lift):
    """The edge of a card is wrapped onto the skull too (a flat 12 cm card on a 10 cm dome leaves the surface by ~2 cm at its edges: that is what floats)."""
    d = (q - C).normalized(); h = tree.ray_cast(C + d * 0.3, -d, 0.4)
    return h[0] + d * lift * 0.8 if h[0] is not None and d.z > -0.2 and (h[0] - C).length < 0.16 else q


def centreline(tree, rnd, phi, th0, L, lift, sway):
    """The path: wanders sideways (drift + two sines) and lifts off the skull toward the tip, so no two cards bend the same way."""
    part = (0.6 if phi > 0 else -0.6) * max(0.0, 1 - abs(phi) / 1.1)
    drift, a1, f1, p1, a2, f2, p2, flare = rnd.uniform(-1, 1) * sway + part, rnd.uniform(0.4, 1) * sway, rnd.uniform(2.5, 5), rnd.uniform(0, 6.3), rnd.uniform(0, 0.5) * sway, rnd.uniform(5, 8), rnd.uniform(0, 6.3), rnd.uniform(0.2, 0.6)
    pts = []; ds = L / SEG; th = th0; p = None
    for i in range(SEG + 1):
        s = i / SEG; ph = phi + drift * s + a1 * math.sin(f1 * s + p1) * s + a2 * math.sin(f2 * s + p2) * s; lf = min(lift * (1 + 1.0 * s), 0.016)
        if th <= TH_END:
            p, d = surface(tree, th, ph, lf)
        else:
            out = Vector((p.x - C.x, p.y - C.y, 0)).normalized(); side = Vector((-out.y, out.x, 0)); p = p + Vector((0, 0, -ds)) + out * ds * flare * 0.5 + side * ds * (ph - phi) * 0.6
        pts.append(push(tree, p, lf)); th += ds / 0.11
    for _ in range(6):                                            # the skull is low poly and the push-out snaps: smooth the path ([1 2 1], root and tip stay) so the card bends softly
        pts = [pts[0]] + [(pts[i - 1] + 2 * pts[i] + pts[i + 1]) / 4 for i in range(1, SEG)] + [pts[-1]]
    return [push(tree, p, lift * 0.6) for p in pts]


def card(name, tree, rnd, phi, th0, L, lift, W, cell, sway, mat):
    pts = centreline(tree, rnd, phi, th0, L, lift, sway); bm = bmesh.new(); lay = bm.loops.layers.uv.new("UVMap"); rows = []; prev = None; twist = rnd.uniform(-0.25, 0.25)
    for i, p in enumerate(pts):                                   # three verts across: the middle one is lifted a little (a cupped card, no hard flat fold)
        t = (pts[min(i + 1, SEG)] - pts[max(i - 1, 0)]).normalized(); rad = (p - C).normalized(); across = t.cross(rad)
        across = across.normalized() if across.length > 1e-4 else prev                      # the card is as wide as it is across the travel on the skull (never along it)
        if prev is not None and across.dot(prev) < 0 or prev is None and across.dot(Vector((math.cos(phi), math.sin(phi), 0))) < 0:
            across = -across
        prev = across; tw = twist * i / SEG; across = across * math.cos(tw) + t.cross(across) * math.sin(tw); out = across.cross(t).normalized()
        if out.dot(rad) < 0:
            out = -out
        w = W * (1.0 - 0.2 * i / SEG) / 2; rows.append([bm.verts.new(wrap(tree, p - across * w + out * w * 0.12, lift)), bm.verts.new(p + out * w * 0.12), bm.verts.new(wrap(tree, p + across * w + out * w * 0.12, lift))])
    for i in range(SEG):
        for j in range(2):
            f = bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
            for loop, (a, b) in zip(f.loops, ((j / 2, i / SEG), ((j + 1) / 2, i / SEG), ((j + 1) / 2, (i + 1) / SEG), (j / 2, (i + 1) / SEG))):
                loop[lay].uv = uv(cell, a, b)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat); me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob


def material():
    m = bpy.data.materials.new("hair_cards"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]; m.use_backface_culling = False
    for k, fn, cs in (("Base Color", SHEET + "_color.png", "sRGB"), ("Normal", SHEET + "_normal.png", "Non-Color")):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(H + "/fibercards/out/" + fn); t.image.colorspace_settings.name = cs; t.interpolation = "Smart"
        if k == "Base Color":
            nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
        else:
            n = nt.nodes.new("ShaderNodeNormalMap"); n.inputs["Strength"].default_value = 0.25; nt.links.new(t.outputs["Color"], n.inputs["Color"]); nt.links.new(n.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.45; b.inputs["Specular IOR Level"].default_value = 0.5; return m


bpy.ops.wm.open_mainfile(filepath=ROOT + "/projects/stylized-cuca/draft/cuca_rig.blend")
body = bpy.data.objects["Cuca_Body"]; bpy.context.view_layer.update(); tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get()); mat = material(); rnd = random.Random(11); made = []
for li, ly in enumerate(LAYERS):
    for k in range(ly["n"]):
        phi = 2 * math.pi * (k + rnd.uniform(0, 1)) / ly["n"]; phi = (phi + math.pi) % (2 * math.pi) - math.pi
        th0 = math.radians(rnd.uniform(*ly["th"])); L = length(phi) * ly["k"] * rnd.uniform(0.85, 1.15)
        made.append(card("hair_%d_%02d" % (li, k), tree, rnd, phi, th0, L, ly["lift"] * rnd.uniform(0.7, 1.4), ly["W"] * rnd.uniform(0.8, 1.2), rnd.choice(ly["cells"]), ly["sway"], mat))
bpy.ops.wm.save_as_mainfile(filepath=H + "/draft/cuca_hair.blend")
far, bad = 0.0, []                                                         # gate: no vertex of the scalp region farther than 4 cm from the skin (a floating card; a fringe may bridge the brow by ~3.6 cm)
for o in made:
    for v in o.data.vertices:
        if v.co.z > 0.95 and (v.co - C).length < 0.2:
            g = tree.find_nearest(v.co)[3]; far = max(far, g); bad += [(round(g, 3), o.name, [round(x, 2) for x in v.co])] if g > 0.03 else []
assert far < 0.04, "floating card: %.3f m from the skull %s" % (far, sorted(bad)[-4:])
result = {"cards": len(made), "tris": 4 * SEG * len(made), "max_gap_cm": round(far * 100, 1)}
