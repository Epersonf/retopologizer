"""Locks (hair clumps, tentacles, horns, cables): a closed tube grown along a given spine, rings laid on the real cross-section.
  rings, tip = lock(T, ref, pts, radii, n=None, step=None, up=(0,0,1), root=True)
pts: spine points root -> tip (e.g. from projects/hat-hair/hair_locks.py, already on the medial axis); radii: tube radius per
point. Stations are spaced so the quads come out square (2*pi*r/n, 1.2..4 cm); each ring is cring() around the spine
tangent, started from the previous ring's first direction (no twist), then align(). The tip is a vertex with n/2 quads around
it (n even), the root is capped the same way with a vertex inside the tube (hidden in whatever the lock grows from).
Returns (rings, tip vertex). Every vertex is a ray hit on the reference; faces are quads only."""
import math
from mathutils import Vector
from .contour import cring, align, frame


def stations(pts, radii, n, step=None, lo=0.012, hi=0.04):
    """[(point, tangent, radius)] along the polyline, spaced by 2*pi*r/n (or `step`)."""
    P = [Vector(p) for p in pts]; s = [0.0]
    for a, b in zip(P, P[1:]):
        s.append(s[-1] + (b - a).length)
    rad = lambda t: radii[min(len(radii) - 1, max(0, int(round(t / s[-1] * (len(radii) - 1)))))]
    out, t, k = [], 0.0, 0
    while t <= s[-1]:
        while k < len(P) - 2 and s[k + 1] < t:
            k += 1
        c = P[k].lerp(P[k + 1], (t - s[k]) / ((s[k + 1] - s[k]) or 1))
        i0, i1 = max(0, k - 1), min(len(P) - 1, k + 2)
        d = (P[i1] - P[i0]).normalized(); r = float(rad(t))
        out.append((c, d, r)); t += step or min(hi, max(lo, 2 * math.pi * r / n))
    return out


def section(ref, c, d, up, n, r, lo=0.45, hi=3.2, oversample=3):
    """n points around the tube at c (axis d, measured radius r): along each of n*oversample rays the first surface point
    the ray LEAVES through whose distance lies in [lo*r, hi*r]; a ray that leaves through a fused neighbour or hits nothing
    in that window takes the radius interpolated from its valid neighbours (a circle of 1.1*r if none is valid)."""
    a, u = frame(d, up); w = a.cross(u); m = n * oversample; D, hit = [], []
    for k in range(m):
        t = 2 * math.pi * k / m; v = u * math.cos(t) + w * math.sin(t); D.append(v); h = None
        for q, nq, dist in ref.hits(c, v, hi * r + 0.01):
            if nq.dot(v) > 0 and dist >= lo * r:
                h = dist; break
        hit.append(h)
    ok = [k for k in range(m) if hit[k] is not None]
    if len(ok) < m // 3:
        rho = [1.1 * r] * m
    else:
        rho = []
        for k in range(m):
            if hit[k] is not None:
                rho.append(hit[k]); continue
            p = max((j for j in ok if j < k), default=ok[-1] - m); q = min((j for j in ok if j > k), default=ok[0] + m)
            f = (k - p) / ((q - p) or 1); rho.append(hit[p % m] * (1 - f) + hit[q % m] * f)
    return [c + D[k] * rho[k] for k in range(0, m, oversample)]


def lock(T, ref, pts, radii, n=None, step=None, up=(0, 0, 1), root=True):
    n = n or (8 if sorted(radii)[len(radii) // 2] >= 0.02 else 6)
    st = stations(pts, radii, n, step)
    rings, prev, upv = [], None, Vector(up)
    for c, d, r in st:
        P = section(ref, c, d, upv, n, r)
        if prev is not None:
            P = align(P, prev)
        upv = (P[0] - c); upv = upv - d * upv.dot(d)
        if upv.length < 1e-6:
            upv = Vector(up)
        rings.append(T.vs(P, snap=False)); prev = P
    c, d, r = st[-1]
    tip = ref.exit(c, d, 3 * r + 0.05) or c + d * r
    tv = T.fan(rings[-1], tip)
    for a, b in zip(rings, rings[1:]):
        T.strip(a, b, closed=True)
    if root:
        c0, d0, r0 = st[0]
        T.fan(rings[0], c0 - d0 * 0.5 * r0)
    return rings, tv
