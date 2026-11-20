"""QA: a tube that is connected but not really attached. qa_floating accepts a tube whose end just touches (3 mm) another part; it then
looks like a loose tip stuck on, or its end cap pokes through the surface of the parent and shows its back to anyone looking close
(the red spot in Face Orientation that no far-away ray sees). A tube must be BURIED where it joins: its cap vertex must lie inside another part and at most 25 % of the first ring outside it, and the deepest vertex `depth` (0.5) x the tube radius below that part's surface.
Each tube needs at least ONE such end, unless it is a separate piece in the original.
Needs qa_shape.py (parts, tube ends). Inside Blender: exec(open(ROOT+r"\tools\03-qa\qa_attach.py").read())
  r = qa_attach("LowPoly")    # r["pass"], r["loose"] = [{"part", "at", "radius_cm", "depth_r", "outside", "end_at"}], r["tubes"]
"outside" = vertices of the best end that are not inside the parent; "end_at" = world position of that end's cap vertex."""
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_DIRS = [Vector(d).normalized() for d in ((1, 0.37, 0.21), (-0.3, 1, 0.45), (0.2, -0.5, 1))]


def _inside(tree, p):
    """Majority vote of 3 ray parities against a closed surface."""
    votes = 0
    for d in _DIRS:
        n = 0; o = p + d * 1e-5
        for _ in range(64):
            h = tree.ray_cast(o, d)
            if h[0] is None:
                break
            n += 1; o = h[0] + d * 1e-5
        votes += n % 2
    return votes >= 2


def qa_attach(name, depth=0.5):
    ob = bpy.data.objects[name]; bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); M = ob.matrix_world
    parts = _parts(bm); vs = [M @ v.co for v in bm.verts]; trees = []
    for comp in parts:
        fs = {f for v in comp for f in v.link_faces}
        trees.append(BVHTree.FromPolygons(vs, [tuple(l.vert.index for l in f.loops) for f in fs], epsilon=0.0))
    loose = []; tubes = 0
    for k, comp in enumerate(parts):
        if len(comp) < 20 or not _is_tube(np.array([vs[v.index][:] for v in comp])):
            continue
        ends = _tube_ends(comp)
        if not ends:
            continue
        tubes += 1; others = [t for i, t in enumerate(trees) if i != k]; r_mid = ends[0][2]; best = None
        for end, r_end, _, layers in ends:
            ins = lambda p: next((t for t in others if _inside(t, p)), None)
            outside = 0; dep = 0.0; cap_out = 0
            for li, l in enumerate(layers):
                for v in l:
                    t = ins(vs[v.index])
                    if t is None:
                        outside += 1; cap_out += li == 0
                    else:
                        dep = max(dep, t.find_nearest(vs[v.index])[3] / r_mid)
            outside = 99 if cap_out else (outside if outside > 0.25 * len(layers[1]) else 0)              # the cap in the air, or > 25 % of the first ring out
            cand = {"outside": outside, "depth_r": round(dep, 2), "end_at": [round(x, 3) for x in vs[end.index]]}
            best = cand if best is None or (cand["outside"], -cand["depth_r"]) < (best["outside"], -best["depth_r"]) else best
        if best["outside"] or best["depth_r"] < depth:
            loose.append({"part": k, "radius_cm": round(r_mid * 100, 1), **best})
    bm.free()
    return {"pass": not loose, "tubes": tubes, "loose": loose}
