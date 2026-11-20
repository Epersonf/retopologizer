"""Surface deviation between a high-poly reference and a low-poly result.
Inside Blender: exec(open(...).read()); r = compare(["REF"], ["chest_base","chest_lid"])
Returns mean/p50/p95/max distance (meters + % of ref bbox diagonal) both directions:
  ref->new  (does the new mesh cover every part of the reference? finds missing details)
  new->ref  (does new mesh stay on the reference? finds floating/extra geometry)
Also hot(): clusters of worst ref points, to know WHERE to fix.
"""
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _world(names):
    V, P, off = [], [], 0
    for n in names:
        o = bpy.data.objects[n]
        me = o.data
        a = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", a)
        m = np.array(o.matrix_world, np.float32)
        w = a.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        me.calc_loop_triangles()
        t = np.empty(len(me.loop_triangles) * 3, np.int32)
        me.loop_triangles.foreach_get("vertices", t)
        V.append(w); P.append(t.reshape(-1, 3) + off); off += len(w)
    return np.vstack(V), np.vstack(P)


def _tree(V, T):
    return BVHTree.FromPolygons([Vector(v) for v in V.tolist()], T.tolist())


def _sample_surface(V, T, n, rng):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1)
    idx = rng.choice(len(T), n, p=area / area.sum())
    r1, r2 = rng.random(n), rng.random(n)
    s = np.sqrt(r1)[:, None]
    return a[idx] * (1 - s) + b[idx] * (s * (1 - r2)[:, None]) + c[idx] * (s * r2[:, None])


def _dist(points, tree):
    d = np.empty(len(points), np.float32)
    for i, p in enumerate(points.tolist()):
        loc = tree.find_nearest(Vector(p))[0]
        d[i] = (Vector(p) - loc).length if loc else 9
    return d


def _stats(d, diag):
    q = np.percentile(d, [50, 95])
    return {"mean_mm": round(float(d.mean()) * 1000, 2), "p50_mm": round(float(q[0]) * 1000, 2),
            "p95_mm": round(float(q[1]) * 1000, 2), "max_mm": round(float(d.max()) * 1000, 2),
            "mean_pct_diag": round(float(d.mean()) / diag * 100, 3),
            "p95_pct_diag": round(float(q[1]) / diag * 100, 3)}


def compare(ref_names, new_names, n=6000, seed=1, hot_k=0):
    rng = np.random.default_rng(seed)
    Vr, Tr = _world(ref_names); Vn, Tn = _world(new_names)
    diag = float(np.linalg.norm(Vr.max(0) - Vr.min(0)))
    pr = _sample_surface(Vr, Tr, n, rng); pn = _sample_surface(Vn, Tn, n, rng)
    d_rn = _dist(pr, _tree(Vn, Tn)); d_nr = _dist(pn, _tree(Vr, Tr))
    out = {"tris_new": int(len(Tn)), "diag_m": round(diag, 3),
           "ref_to_new": _stats(d_rn, diag), "new_to_ref": _stats(d_nr, diag)}
    if hot_k:
        order = np.argsort(-d_rn)[: max(1, n // 50)]
        cells = {}
        for p, d in zip(pr[order], d_rn[order]):
            k = tuple((np.round(p / 0.05) * 0.05).round(2))
            cells.setdefault(k, []).append(d)
        top = sorted(cells.items(), key=lambda kv: -len(kv[1]))[:hot_k]
        out["hot_ref_cells"] = [[list(k), len(v), round(max(v) * 1000, 1)] for k, v in top]
    return out
