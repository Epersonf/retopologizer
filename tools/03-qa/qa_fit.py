"""QA: does the low poly look like the original? Clean normals and contacts do not make a good model: a hole in front, a notch the
original does not have, or a limb that sticks out passes every other gate. Compared with the reference from 14 directions (6 axes + 8
diagonals), orthographic `res`x`res` rays, only what an eye can SEE (the first hit), so the hollow inside of a hair ref does not count.
A visible point is covered when the OTHER surface has a point within `tol` (3 cm, in 3D: an edge that is a centimetre off is not a defect):
  iou      silhouette overlap
  missing  share of the ref's visible points farther than `tol` from the low poly (uncovered mass, holes, "should be filled", dents the ref does not have)
  excess   share of the low poly's visible points farther than `tol` from the ref (lumps, stuck-out parts that the original does not have). Points on a
           face of material "headfill" (the stand-in for the head, the bottom lid) are ignored.
Pass: mean iou >= 0.88, worst iou >= 0.80, missing <= 6 %, excess <= 4 %. Clusters = 8 cm cells of the 3D points, biggest first, with a word for
where (front is -Y, the character's left is +X).
Inside Blender: exec(open(ROOT+r"\tools\03-qa\qa_fit.py").read());  r = qa_fit("LowPoly", "HairFull")"""
import bpy, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _world_tree(ob):
    """(BVH in world space, world vertices, polygon index of each BVH triangle)."""
    me = ob.data; me.calc_loop_triangles(); M = np.array(ob.matrix_world)
    v = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", v); v = v.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    t = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", t)
    pi = np.empty(len(me.loop_triangles), np.int32); me.loop_triangles.foreach_get("polygon_index", pi)
    return BVHTree.FromPolygons([Vector(x) for x in v.tolist()], t.reshape(-1, 3).tolist(), epsilon=0.0), v, pi


def _depth(tree, d, lo, hi, res, ignore=None, tri2poly=None):
    """(depth map, points map) of the first hit of an orthographic grid along d; nan where nothing is hit or the hit face is ignored."""
    d = Vector(d).normalized(); u = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized(); w = d.cross(u)
    c = (lo + hi) / 2; s = (hi - lo).length / 2; D = np.full((res, res), np.nan); P = np.zeros((res, res, 3)); hit = np.zeros((res, res), bool)
    for i in range(res):
        for j in range(res):
            o = c + u * ((i + 0.5) / res * 2 - 1) * s + w * ((j + 0.5) / res * 2 - 1) * s - d * s * 2; h = tree.ray_cast(o, d, s * 4)
            if h[0] is not None:
                hit[i, j] = True
                if ignore is None or tri2poly[h[2]] not in ignore:
                    D[i, j] = h[3]; P[i, j] = h[0]
    return D, P, hit


def _where(p):
    return "%s%s%s" % ("front-" if p[1] < -0.12 else "back-" if p[1] > 0.0 else "", "low" if p[2] < 0.25 else "top" if p[2] > 0.42 else "mid",
                       "-left" if p[0] > -0.185 + 0.08 else "-right" if p[0] < -0.185 - 0.08 else "")


def _clusters(P, cell=0.08, top=6):
    if not len(P):
        return []
    k = np.floor(P / cell).astype(int); u, inv, cnt = np.unique(k, axis=0, return_inverse=True, return_counts=True); inv = inv.ravel()
    return [{"at": [round(float(x), 2) for x in P[inv == i].mean(0)], "where": _where(P[inv == i].mean(0)), "points": int(cnt[i])} for i in np.argsort(-cnt)[:top]]


def _far(tree, P, ok, tol):
    """Mask of the points of P[ok] that have no surface of `tree` within tol."""
    out = np.zeros(ok.shape, bool)
    for i, j in zip(*np.nonzero(ok)):
        out[i, j] = tree.find_nearest(Vector(P[i, j].tolist()), tol)[0] is None
    return out


def qa_fit(name, ref, res=96, tol=0.03):
    low = bpy.data.objects[name]; tl, vl, pl = _world_tree(low); tr, vr, _ = _world_tree(bpy.data.objects[ref])
    fill = {i for i, m in enumerate(low.data.materials) if m and m.name == "headfill"}; ign = {p.index for p in low.data.polygons if p.material_index in fill}
    lo = Vector(vr.min(0).tolist()); hi = Vector(vr.max(0).tolist()); ious = []; mis = exc = nr = nl = 0; MP, EP = [], []
    for d in [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)] + [(a, b, c) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]:
        Dl, Pl, hl = _depth(tl, d, lo, hi, res, ign, pl); Dr, Pr, hr = _depth(tr, d, lo, hi, res)
        ious.append(round(float((hl & hr).sum() / max((hl | hr).sum(), 1)), 3)); fr = np.isfinite(Dr); fl = np.isfinite(Dl)
        m = _far(tl, Pr, fr, tol); e = _far(tr, Pl, fl, tol)                          # ref point far from the low poly / low point far from the ref
        mis += m.sum(); nr += fr.sum(); exc += e.sum(); nl += fl.sum(); MP.append(Pr[m]); EP.append(Pl[e])
    ms, es = mis / max(nr, 1), exc / max(nl, 1); MP = np.vstack(MP); EP = np.vstack(EP)
    ok = float(np.mean(ious)) >= 0.88 and min(ious) >= 0.80 and ms <= 0.06 and es <= 0.04
    return {"pass": ok, "iou_mean": round(float(np.mean(ious)), 3), "iou_worst": min(ious), "iou": ious, "missing_share": round(float(ms), 3),
            "missing_clusters": _clusters(MP), "excess_share": round(float(es), 4), "excess_clusters": _clusters(EP, top=4)}
