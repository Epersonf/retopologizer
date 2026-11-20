"""Fit of a low-poly part against a reference piece (both in the same local space).
  exec(open(...).read()); r = fit_report("LID_NEW", "REF_LID")
new->ref: distance from points sampled on the low-poly to the reference surface (floating/wrong faces).
ref->new: distance from reference vertices to the low-poly (missing details). Values in mm.
`worst_ref` lists the clusters (5 cm cells) where the reference is farthest from the low-poly."""
import bpy, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector


def _bvh(o):
    me = o.data; me.calc_loop_triangles()
    V = [tuple(o.matrix_world @ v.co) for v in me.vertices]
    return BVHTree.FromPolygons(V, [tuple(t.vertices) for t in me.loop_triangles]), V, me


def fit_report(new, ref, n=6000, ref_max=30000, seed=1):
    rng = np.random.default_rng(seed)
    On, Or = bpy.data.objects[new], bpy.data.objects[ref]
    bn, Vn, men = _bvh(On); br, Vr, mer = _bvh(Or)
    tri = np.array([t.vertices[:] for t in men.loop_triangles]); P = np.array(Vn)
    a, b, c = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    ar = np.linalg.norm(np.cross(b - a, c - a), axis=1)
    k = rng.choice(len(tri), n, p=ar / ar.sum())
    u, v = rng.random(n), rng.random(n); f = u + v > 1; u[f], v[f] = 1 - u[f], 1 - v[f]
    S = a[k] + (b[k] - a[k]) * u[:, None] + (c[k] - a[k]) * v[:, None]
    d1 = np.array([(br.find_nearest(Vector(p))[3] or 0) for p in S])
    R = np.array(Vr); R = R[rng.choice(len(R), min(ref_max, len(R)), replace=False)]
    d2 = np.array([(bn.find_nearest(Vector(p))[3] or 0) for p in R])
    cell = np.floor(R / 0.05).astype(int); worst = {}
    for ci, dd in zip(map(tuple, cell), d2):
        if dd > 0.02:
            w = worst.setdefault(ci, [0, 0.0]); w[0] += 1; w[1] = max(w[1], dd)
    top = sorted(worst.items(), key=lambda kv: -kv[1][0])[:8]
    q = lambda d: {"mean": round(d.mean() * 1e3, 1), "p95": round(np.percentile(d, 95) * 1e3, 1),
                   "max": round(d.max() * 1e3, 1)}
    return {"new_to_ref_mm": q(d1), "ref_to_new_mm": q(d2),
            "worst_ref": [{"cell_m": [round(c * 0.05, 2) for c in ci], "pts": n_, "max_mm": round(m * 1e3, 0)}
                          for ci, (n_, m) in top]}
