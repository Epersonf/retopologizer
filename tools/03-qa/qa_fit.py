"""QA: does the low poly look like the original? Clean normals and contacts do not make a good model: a hood with a hole in
front, a notch the original does not have, or a limb that sticks out passes every other gate. Measured against the reference:
  iou      silhouette overlap (low vs ref) from 14 directions (6 axes + 8 diagonals), orthographic 96x96 rays each
  missing  share of reference surface points farther than `miss` (5 cm) from the low poly = holes / uncovered mass, with clusters
  excess   share of low poly points (faces centres + vertices) farther than `excess` (4 cm) from the reference = lumps that are not
           in the original, with clusters
Pass: mean iou >= 0.88, worst iou >= 0.80, missing <= 4 %, excess <= 1 %. Clusters = 8 cm cells, biggest first, with a word for where
they are (front is -Y, character's left is +X).
Inside Blender (after qa_faces.py for _sphere_dirs): exec(open(ROOT+r"\tools\03-qa\qa_fit.py").read())
  r = qa_fit("LowPoly", "HairFull")"""
import bpy, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _world_tree(ob):
    me = ob.data; me.calc_loop_triangles(); M = np.array(ob.matrix_world)
    v = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", v); v = v.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    t = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", t)
    return BVHTree.FromPolygons([Vector(x) for x in v.tolist()], t.reshape(-1, 3).tolist(), epsilon=0.0), v


def _mask(tree, d, lo, hi, res):
    d = Vector(d).normalized(); u = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized(); w = d.cross(u)
    c = (lo + hi) / 2; s = (hi - lo).length / 2; out = np.zeros((res, res), bool)
    for i in range(res):
        for j in range(res):
            o = c + u * ((i + 0.5) / res * 2 - 1) * s + w * ((j + 0.5) / res * 2 - 1) * s - d * s * 2
            out[i, j] = tree.ray_cast(o, d, s * 4)[0] is not None
    return out


def _where(p):
    return "%s%s%s" % ("front-" if p[1] < -0.12 else "back-" if p[1] > 0.0 else "", "low" if p[2] < 0.25 else "top" if p[2] > 0.42 else "mid",
                       "-left" if p[0] > -0.185 + 0.08 else "-right" if p[0] < -0.185 - 0.08 else "")


def _clusters(P, cell=0.08, top=6):
    k = np.floor(P / cell).astype(int); u, inv, cnt = np.unique(k, axis=0, return_inverse=True, return_counts=True)
    return [{"at": [round(float(x), 2) for x in P[inv.ravel() == i].mean(0)], "where": _where(P[inv.ravel() == i].mean(0)), "points": int(cnt[i])}
            for i in np.argsort(-cnt)[:top]]


def qa_fit(name, ref, res=96, miss=0.05, excess=0.04, n_ref=15000, seed=1):
    low = bpy.data.objects[name]; tl, vl = _world_tree(low); tr, vr = _world_tree(bpy.data.objects[ref])
    lo = Vector(vr.min(0).tolist()); hi = Vector(vr.max(0).tolist()); ious = []
    for d in [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)] + [(a, b, c) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]:
        a, b = _mask(tl, d, lo, hi, res), _mask(tr, d, lo, hi, res); ious.append(round(float((a & b).sum() / max((a | b).sum(), 1)), 3))
    rng = np.random.default_rng(seed); R = vr[rng.choice(len(vr), min(n_ref, len(vr)), replace=False)]
    d_ref = np.array([tl.find_nearest(Vector(p.tolist()))[3] for p in R])
    me = low.data; M = np.array(low.matrix_world); cen = np.array([(M @ np.append(p.center, 1))[:3] for p in me.polygons])
    L = np.vstack([vl, cen]); d_new = np.array([tr.find_nearest(Vector(p.tolist()))[3] for p in L])
    m_share = float((d_ref > miss).mean()); e_share = float((d_new > excess).mean())
    ok = float(np.mean(ious)) >= 0.88 and min(ious) >= 0.80 and m_share <= 0.04 and e_share <= 0.01
    return {"pass": ok, "iou_mean": round(float(np.mean(ious)), 3), "iou_worst": min(ious), "iou": ious,
            "missing_share": round(m_share, 3), "missing_clusters": _clusters(R[d_ref > miss]),
            "excess_share": round(e_share, 4), "excess_clusters": _clusters(L[d_new > excess], top=4) if e_share else [],
            "ref_to_low_cm_p50_p90": [round(float(np.percentile(d_ref, q)) * 100, 1) for q in (50, 90)]}
