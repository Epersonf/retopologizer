r"""Faces of the SAME loose part that cut through each other (or lie folded over each other). Not allowed in a retopology: a mesh
with this is rejected. Pure mathutils, no UI; used by qa_suite ("intersect"), topo_qa ("self_intersections"), Topo.write and the
live overlay (live_intersect.py).
  exec(open(r"<repo>\tools\general\face_intersect.py", encoding="utf-8").read())
  r = qa_intersect("Obj")            # r["pass"], r["faces"] (polygon ids), r["pairs"], r["per_part"], r["cross_part"]
  select_faces("Obj", r["faces"])    # selects them in the mesh (Object Mode) so the artist sees them
  face_intersections(V, F)           # same test on lists: -> pairs of face ids (any part), parts = loose_parts(F)
Tests (triangulated quads; faces of the same polygon never count):
  no shared vertex   : an edge of one triangle pierces the other, or coplanar overlap
  one shared vertex  : the opposite edge of one pierces the other
  shared edge        : folded back on itself (normals opposite, dihedral > ~166 degrees)
Faces of different loose parts (a tube buried in another piece) are reported as `cross_part`, they do not fail."""
import bpy
from mathutils import Vector, geometry
from mathutils.bvhtree import BVHTree


def loose_parts(F, n):
    """Loose part id of each FACE (union of vertices)."""
    p = list(range(n))
    def find(a):
        while p[a] != a: p[a] = p[p[a]]; a = p[a]
        return a
    for f in F:
        for v in f[1:]: p[find(v)] = find(f[0])
    return [find(f[0]) for f in F]


def _tris(F):
    T, owner = [], []
    for i, f in enumerate(F):
        for k in range(1, len(f) - 1): T.append((f[0], f[k], f[k + 1])); owner.append(i)
    return T, owner


def _seg_tri(p, q, tri, V, e=1e-6):
    a, b, c = (V[i] for i in tri); d = q - p
    if d.length < 1e-12: return False
    h = geometry.intersect_ray_tri(a, b, c, d, p, True)
    if h is None: return False
    t = (h - p).dot(d) / d.dot(d)
    return e < t < 1 - e


def _normal(t, V): return (V[t[1]] - V[t[0]]).cross(V[t[2]] - V[t[0]]).normalized()


def _coplanar_overlap(ta, tb, V):
    na, nb = _normal(ta, V), _normal(tb, V)
    if abs(na.dot(nb)) < 0.9999 or abs(na.dot(V[tb[0]] - V[ta[0]])) > 1e-5: return False
    for x, y in ((ta, tb), (tb, ta)):
        for i in x:
            if i not in y and geometry.intersect_point_tri(V[i], V[y[0]], V[y[1]], V[y[2]]) and \
               (V[i] - geometry.intersect_point_tri(V[i], V[y[0]], V[y[1]], V[y[2]])).length < 1e-6 and \
               min((V[i] - V[j]).length for j in y) > 1e-6: return True
    return False


def _pair_hits(ta, tb, V):
    sh = set(ta) & set(tb)
    ea = [(ta[i], ta[(i + 1) % 3]) for i in range(3)]; eb = [(tb[i], tb[(i + 1) % 3]) for i in range(3)]
    if len(sh) == 2: return _normal(ta, V).dot(_normal(tb, V)) < -0.97
    if len(sh) == 1: ea = [e for e in ea if not set(e) & sh]; eb = [e for e in eb if not set(e) & sh]
    return any(_seg_tri(V[a], V[b], tb, V) for a, b in ea) or any(_seg_tri(V[a], V[b], ta, V) for a, b in eb) or \
        (not sh and _coplanar_overlap(ta, tb, V))


def face_intersections(V, F):
    """-> list of (face_a, face_b) whose triangles cut or fold over each other (V: Vectors, F: vertex-id lists)."""
    V = [Vector(v) for v in V]; T, owner = _tris(F)
    if not T: return []
    out = set()
    for i, j in _candidates(V, T):
        if owner[i] != owner[j] and _pair_hits(T[i], T[j], V): out.add((min(owner[i], owner[j]), max(owner[i], owner[j])))
    return sorted(out)


def _candidates(V, T, big=6000):
    """Triangle pairs whose boxes overlap. numpy sweep (finds coplanar pairs too: the BVH overlap of Blender drops them);
    BVH for very large meshes (coplanar overlaps are then only found where the BVH reports them)."""
    if len(T) > big:
        tree = BVHTree.FromPolygons([tuple(v) for v in V], T, epsilon=1e-6)
        return [(i, j) for i, j in tree.overlap(tree) if i < j]
    import numpy as np
    P = np.array([[tuple(V[k]) for k in t] for t in T]); lo = P.min(1) - 1e-6; hi = P.max(1) + 1e-6; out = []
    for i in range(len(T) - 1):
        m = ((lo[i + 1:] <= hi[i]) & (hi[i + 1:] >= lo[i])).all(1)
        out += [(i, i + 1 + int(k)) for k in np.nonzero(m)[0]]
    return out


def qa_intersect(name, limit=200):
    o = bpy.data.objects[name]; me = o.data; M = o.matrix_world
    V = [M @ v.co for v in me.vertices]; F = [list(p.vertices) for p in me.polygons]
    pairs = face_intersections(V, F); part = loose_parts(F, len(V))
    same = [(a, b) for a, b in pairs if part[a] == part[b]]
    per = {}
    for a, b in same: per.setdefault(part[a], []).append((a, b))
    faces = sorted({f for ab in same for f in ab})
    return {"pass": not same, "pairs": same[:limit], "n_pairs": len(same), "faces": faces, "faces_n": len(faces),
            "parts": len(set(part)), "per_part": {k: len(v) for k, v in per.items()}, "cross_part": len(pairs) - len(same)}


def select_faces(name, faces):
    me = bpy.data.objects[name].data; s = set(faces)
    for p in me.polygons: p.select = p.index in s
