"""QA: no two faces may fight for the same pixels (z-fighting / flickering while the camera moves).
Pairs of triangles that are (near) parallel, closer than `eps` metres and whose overlap in the plane
is larger than `min_area` are reported. Uses BVH self-overlap (broad phase) + numpy filters +
exact 2D triangle clipping only for the few survivors, so it takes well under a second.
  exec(open(...).read()); r = qa_zfight(["chest_base","chest_lid"])   # r["pass"]
Adjacent faces that only touch along an edge are fine (overlap area ~ 0)."""
import bpy, numpy as np
from mathutils.bvhtree import BVHTree


def _gather(names):
    V, T, own = [], [], []
    off = 0
    for k, n in enumerate(names):
        o = bpy.data.objects[n]; me = o.data; me.calc_loop_triangles()
        M = np.array(o.matrix_world, np.float64)
        co = np.empty(len(me.vertices) * 3, np.float64); me.vertices.foreach_get("co", co)
        V.append(co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3])
        t = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", t)
        pi = np.empty(len(me.loop_triangles), np.int32); me.loop_triangles.foreach_get("polygon_index", pi)
        T.append(t.reshape(-1, 3) + off); own.append(np.stack([np.full(len(pi), k), pi], 1)); off += len(co) // 3
    return np.vstack(V), np.vstack(T), np.vstack(own)


def _clip_area(sub, clip):
    """Area of triangle `sub` clipped by convex triangle `clip` (2D arrays 3x2), Sutherland-Hodgman."""
    poly = [p for p in sub]
    if np.cross(clip[1] - clip[0], clip[2] - clip[0]) < 0:
        clip = clip[::-1]
    for i in range(3):
        a, b = clip[i], clip[(i + 1) % 3]
        out = []
        for j in range(len(poly)):
            p, q = poly[j], poly[(j + 1) % len(poly)]
            sp = np.cross(b - a, p - a) >= -1e-12; sq = np.cross(b - a, q - a) >= -1e-12
            if sp:
                out.append(p)
            if sp != sq:
                d = (q - p); t = np.cross(b - a, a - p) / np.cross(b - a, d)
                out.append(p + d * t)
        poly = out
        if not poly:
            return 0.0
    x = np.array([p[0] for p in poly]); y = np.array([p[1] for p in poly])
    return 0.5 * abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def qa_zfight(names, eps=0.001, par=1e-3, min_area=1e-6, limit=40):
    V, T, own = _gather(names)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    nn = np.cross(b - a, c - a); ar = np.linalg.norm(nn, axis=1); ok = ar > 1e-14
    nn[ok] /= ar[ok, None]
    tree = BVHTree.FromPolygons(V.tolist(), T.tolist(), epsilon=eps)
    pr = np.array(tree.overlap(tree), np.int64).reshape(-1, 2)
    pr = pr[pr[:, 0] < pr[:, 1]]
    i, j = pr[:, 0], pr[:, 1]
    keep = ~((own[i, 0] == own[j, 0]) & (own[i, 1] == own[j, 1])) & ok[i] & ok[j]
    keep &= np.abs(np.einsum("ij,ij->i", nn[i], nn[j])) > 1 - par
    i, j = i[keep], j[keep]
    d1 = np.max(np.abs(np.einsum("ij,ikj->ik", nn[i], V[T[j]] - a[i][:, None, :])), axis=1)
    d2 = np.max(np.abs(np.einsum("ij,ikj->ik", nn[j], V[T[i]] - a[j][:, None, :])), axis=1)
    near = (d1 < eps) & (d2 < eps)
    i, j = i[near], j[near]
    found = {}
    for ti, tj in zip(i, j):
        n = nn[ti]; u = b[ti] - a[ti]; u /= np.linalg.norm(u); v = np.cross(n, u)
        def p2(t):
            return np.array([[(V[k] - a[ti]) @ u, (V[k] - a[ti]) @ v] for k in T[t]])
        area = _clip_area(p2(tj), p2(ti))
        if area > min_area:
            key = (tuple(own[ti]), tuple(own[tj]))
            found[key] = found.get(key, 0.0) + area
    pairs = [{"a": f"{names[k[0][0]]}#{k[0][1]}", "b": f"{names[k[1][0]]}#{k[1][1]}",
              "overlap_cm2": round(v * 1e4, 2)} for k, v in found.items()]
    pairs.sort(key=lambda p: -p["overlap_cm2"])
    return {"pass": not pairs, "coplanar_overlapping_pairs": len(pairs), "pairs": pairs[:limit],
            "eps_mm": eps * 1000, "tris": int(len(T))}
