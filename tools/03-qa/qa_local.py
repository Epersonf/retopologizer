"""QA: reversed faces seen from a camera in the air near the surface. qa_strict.py shoots from far away; a reversed face in a pit, a fold or
behind a window can be hidden from every far ray and still turn red in Blender's face-orientation overlay when the eye is near. Here the
cameras hover in front of every exposed face, at distances `dists` along its normal. A point counts as "in the air" when it is inside none of the
loose parts (ray parity, 3 directions, per part: closed parts overlap freely), so a buried tube root or the buried half of a tube has no camera
in front of it. From each camera `n_dirs` rays go over the whole sphere; a ray whose first hit is the BACK of a face (|cos| > `graze`) is a
sighting of that face. A face with `min_votes` sightings fails. A union of closed, outward-wound parts can not fail this; a window that shows
the inside of the shell, a fold, an inverted part do (the old hair hood: 5 to 27 faces; a clean union: 0).
Inside Blender (after qa_faces.py): exec(open(ROOT+r"\tools\03-qa\qa_local.py").read())
  r = qa_local("LowPoly")    # r["pass"], r["faces"] = [{"face", "votes", "at"}] worst first, r["cameras"]"""
import bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_DIRS = [Vector(v).normalized() for v in ((0.31, 0.52, 0.79), (-0.67, 0.21, -0.71), (0.12, -0.93, 0.35))]


def _sphere(n):
    g = math.pi * (3 - math.sqrt(5)); out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n; r = math.sqrt(1 - z * z); out.append(Vector((r * math.cos(g * i), r * math.sin(g * i), z)))
    return out


def _part_trees(ob):
    """[(BVH, (lo, hi))] one per loose part of the mesh, in world space."""
    me = ob.data; M = ob.matrix_world; V = [M @ v.co for v in me.vertices]; parent = list(range(len(V)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for p in me.polygons:
        r = find(p.vertices[0])
        for v in p.vertices[1:]:
            parent[find(v)] = r
    groups = {}
    for p in me.polygons:
        groups.setdefault(find(p.vertices[0]), []).append(tuple(p.vertices))
    out = []
    for polys in groups.values():
        xs, ys, zs = zip(*[tuple(V[i]) for t in polys for i in t])
        out.append((BVHTree.FromPolygons(V, polys, epsilon=0.0), (Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs))))))
    return out


def _inside_part(t, o):                                                # ray parity, majority of 3 directions
    odd = 0
    for d in _DIRS:
        k = 0; p = o
        while k < 60:
            h = t.ray_cast(p, d, 1e3)
            if h[0] is None:
                break
            k += 1; p = h[0] + d * 1e-5
        odd += k & 1
    return odd >= 2


def qa_local(name, dists=(0.02, 0.06, 0.15), n_dirs=64, graze=0.1, min_votes=2, eps=1e-3):
    ob = bpy.data.objects[name]; tree, tri_poly, R = _tree(ob); me = ob.data; M = ob.matrix_world; dirs = _sphere(n_dirs); parts = _part_trees(ob); votes = {}; cams = 0

    def in_air(o):
        return not any(lo.x <= o.x <= hi.x and lo.y <= o.y <= hi.y and lo.z <= o.z <= hi.z and _inside_part(t, o) for t, (lo, hi) in parts)
    for p in me.polygons:
        n = R @ p.normal; n.normalize(); c = M @ p.center + n * eps
        if not in_air(c):
            continue                                                   # buried in another part: nobody stands in front of this face
        for d in dists:
            o = c + n * d
            if not in_air(o):
                continue
            cams += 1
            for w in dirs:
                hh = tree.ray_cast(o, w, 1e3)
                if hh[0] is not None and hh[1].dot(w) > 0 and abs(hh[1].dot(w)) > graze:
                    q = tri_poly[hh[2]]; votes[q] = votes.get(q, 0) + 1
    bad = sorted(((v, q) for q, v in votes.items() if v >= min_votes), reverse=True)
    return {"pass": not bad, "cameras": cams, "faces": [{"face": q, "votes": v, "at": [round(x, 3) for x in (M @ me.polygons[q].center)]} for v, q in bad[:30]], "reversed_faces": len(bad)}
