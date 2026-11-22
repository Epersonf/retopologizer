r"""Faces whose OWN geometry is wrong even though nothing crosses and every vertex sits on the surface. Zero tolerance in a retopology.
  exec(open(r"<repo>\tools\general\face_shape.py", encoding="utf-8").read())
  r = qa_faceshape("Obj", ref=Ref("HiPoly"))     # r["pass"], r["twisted"], r["stamped"], r["inverted"], r["faces"]
  twisted_quads(V, F) / stamped_pairs(V, F) / inverted_vs_ref(V, F, ref)      # same tests on lists
Tests (thresholds calibrated on the artist's own paw, worst good value in brackets; bad rear paw in braces):
  twisted   a quad whose two triangulations disagree (min cosine of the normals of its triangles < 0): a bow-tie / a quad folded onto itself,
            "two faces stamped on each other" [artist +0.16] {-0.99, -0.88, -0.84}. Crisp: needs no reference.
  inverted  face normal against the normal of the reference surface under it < -0.2: the face looks INTO the model, its corners sit on different
            sheets of the surface [artist +0.22] {-0.88, -0.84}. Needs the ref.
  stamped   two faces of one part, not sharing a vertex, opposite normals, overlapping, closer than 0.35 x the smaller edge: a pinched wall
            [artist 0.43, good front 0.81] {0.20-0.38}. Heuristic, with a thin margin: a hit must be looked at, but it is not allowed."""
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


def _n(a, b, c):
    n = (b - a).cross(c - a); return n.normalized() if n.length > 1e-15 else Vector()


def _fn(V, f):
    p = [V[i] for i in f]; n = sum((p[i].cross(p[(i + 1) % len(p)]) for i in range(len(p))), Vector())
    return (n.normalized() if n.length > 1e-15 else Vector()), sum(p, Vector()) / len(p), sum((p[i] - p[(i + 1) % len(p)]).length for i in range(len(p))) / len(p)


def twisted_quads(V, F, thr=0.0):
    out = []
    for fi, f in enumerate(F):
        if len(f) != 4: continue
        p = [Vector(V[i]) for i in f]
        c = min(_n(p[0], p[1], p[2]).dot(_n(p[0], p[2], p[3])), _n(p[1], p[2], p[3]).dot(_n(p[1], p[3], p[0])))
        if c < thr: out.append((fi, round(c, 2)))
    return out


def stamped_pairs(V, F, ratio=0.35, lateral=0.8):
    V = [Vector(v) for v in V]; D = [_fn(V, f) for f in F]; kd = KDTree(len(F))
    for i, d in enumerate(D): kd.insert(d[1], i)
    kd.balance(); out = set()
    for i, (ni, ci, ei) in enumerate(D):
        for _, j, _ in kd.find_range(ci, 2.5 * ei):
            if j <= i or set(F[i]) & set(F[j]): continue
            nj, cj, ej = D[j]
            if ni.dot(nj) > -0.5: continue
            dc = cj - ci; gap = (abs(dc.dot(ni)) + abs(dc.dot(nj))) / 2; lat = (dc - ni * dc.dot(ni)).length
            if lat <= lateral * max(ei, ej) and gap < ratio * min(ei, ej): out.add((i, j, round(gap / min(ei, ej), 2)))
    return sorted(out)


def inverted_vs_ref(V, F, ref, thr=-0.2, maxd=0.02):
    out = []
    for fi, f in enumerate(F):
        n, c, _ = _fn([Vector(v) for v in V], f); h = ref.nearest(c, maxd)
        if h and n.dot(h[1]) < thr: out.append((fi, round(n.dot(h[1]), 2)))
    return out


def _as_ref(ref):
    if isinstance(ref, str):
        import os, sys
        root = os.environ.get("RETOPOLOGIZER_ROOT", r"C:\Users\epers\Desktop\retopologizer")
        sys.path[:0] = [os.path.join(root, "tools", "02-retopology")]
        from retopo import Ref
        return Ref(ref)
    return ref


def qa_faceshape(name, ref=None):
    ref = _as_ref(ref); o = bpy.data.objects[name]; M = o.matrix_world; me = o.data
    V = [M @ v.co for v in me.vertices]; F = [list(p.vertices) for p in me.polygons]
    tw, st = twisted_quads(V, F), stamped_pairs(V, F); inv = inverted_vs_ref(V, F, ref) if ref is not None else []
    faces = sorted({a for a, _ in tw} | {a for a, _ in inv} | {x for p in st for x in p[:2]})
    return {"pass": not (tw or st or inv), "twisted": tw, "stamped": st, "inverted": inv, "faces": faces, "faces_n": len(faces)}
