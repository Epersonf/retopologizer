# N-sided tubes along a path in the XZ plane (guard, grip), rings snapped by rays onto REFERENCE.
# Use: exec after snap_retopo.py, with P set (the project folder with draft/raster.npz); build_tube(S, name, points, rings, ...).
# Guide: docs/02-retopology/retopo-tube-path.md
import numpy as np
from mathutils import Vector
d = np.load(P + "draft/raster.npz"); T = d["yf"] - d["yb"]; xs, zs = d["xs"], d["zs"]
SIDES = 8
FLOOR = 0.3                                                       # max diagonal reach = half width / FLOOR


def inside(q):
    j = int(round((q[0] - xs[0]) / 0.002)); i = int(round((q[1] - zs[0]) / 0.002))
    return 0 <= i < len(zs) and 0 <= j < len(xs) and np.isfinite(T[i, j])


def chaikin(pts, k=2):
    for _ in range(k):
        q = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        pts = np.array(q + [pts[-1]])
    return pts


def resample(pts, n):
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    u = np.linspace(0, seg[-1], n)
    return np.c_[np.interp(u, seg, pts[:, 0]), np.interp(u, seg, pts[:, 1])]


def halfwidth(p, n, r=0.04, wide=0.016):
    s = np.arange(-r, r, 0.002); m = np.array([inside(p + n * k) for k in s])
    if not m[len(s) // 2]:
        return 0.015
    lo = hi = len(s) // 2
    while lo > 0 and m[lo - 1]:
        lo -= 1
    while hi < len(s) - 1 and m[hi + 1]:
        hi += 1
    w = min(-s[lo], s[hi])
    return wide if wide and w >= r - 0.01 else w                  # continuous silhouette (blade crossing): typical width of the part


def tube_ring(S, c, t, r, wide):
    # Rays along Y go far (nothing crosses them); in the XZ plane the reach is the silhouette half width, or the ray runs into the blade.
    n = np.array([-t[1], t[0]]); hw = halfwidth(c, n, r, wide) + 0.004; C3 = Vector((c[0], 0.0, c[1]))
    a, u, v = basis((t[0], 0.0, t[1]), (0, 1, 0)); pts = []
    for k in range(SIDES):
        ang = np.radians(22.5 + 360 * k / SIDES); dvec = u * np.cos(ang) + v * np.sin(ang)
        reach = 0.08 if abs(dvec.y) > 0.7 else hw / max(abs(dvec.x * n[0] + dvec.z * n[1]), FLOOR)
        h = S.bv.ray_cast(C3, dvec, reach)
        pts.append(tuple(h[0]) if h[0] is not None else S.nearest(tuple(C3 + dvec * reach), 0.03))
    return pts


def recenter(p, n, r=0.04):
    s = np.arange(-r, r, 0.002); m = np.array([inside(p + n * k) for k in s])
    if not m.any():
        return p
    lo = hi = int(np.argmin(np.where(m, abs(s), 9)))
    while lo > 0 and m[lo - 1]:
        lo -= 1
    while hi < len(s) - 1 and m[hi + 1]:
        hi += 1
    return p + n * (s[lo] + s[hi]) / 2 if s[hi] - s[lo] < 0.06 else p



def build_tube(S, name, pts, n, bury=(0.0, 0.0), r=0.04, wide=0.016):
    C = resample(chaikin(np.array(pts)), n)
    tg = np.gradient(C, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
    C = np.array([recenter(c, np.array([-t[1], t[0]])) if 0 < i < n - 1 else c for i, (c, t) in enumerate(zip(C, tg))])
    tg = np.gradient(C, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
    M = Mesh(); rings = [[M.v(tuple(p)) for p in tube_ring(S, c, t, r, wide)] for c, t in zip(C, tg)]
    for k, sgn, dist in ((0, -1, bury[0]), (-1, 1, bury[1])):   # end buried in the neighbouring part
        if dist:
            g = tg[k] * sgn * dist
            new = [M.v((v.co.x + g[0], v.co.y, v.co.z + g[1])) for v in rings[k]]
            rings.insert(0, new) if k == 0 else rings.append(new)
    for A, B in zip(rings, rings[1:]):
        M.strip_closed(A, B)
    for rg, flip in ((rings[0], True), (rings[-1], False)):        # octagon closed with 3 quads
        for q in ((rg[0], rg[1], rg[2], rg[3]), (rg[0], rg[3], rg[4], rg[7]), (rg[4], rg[5], rg[6], rg[7])):
            M.f(*(q[::-1] if flip else q))
    o = M.to_object(name)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode="OBJECT")
    o.select_set(False)
    return o
