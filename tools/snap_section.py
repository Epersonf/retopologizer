"""Cross-section rings snapped on a reference, by raycast from a centre (hand-retopo helpers, loaded by snap_retopo.py).
  S = Surface("REFERENCE"); pts = ring(S, c, axis, up, n)      # n points around `axis`, first one toward `up`
Each point is the first surface hit leaving the centre (exit hit) so thin neighbours (legs, ears) are not picked
unless they are on the ray; `zmin` flattens points that would dip below a plane (belly between legs).
`despike` replaces points whose radius jumps vs both neighbours (an ear/horn on the ray) by the neighbours' mean."""
import math
from mathutils import Vector


def basis(axis, up):
    a = Vector(axis).normalized(); u = (Vector(up) - a * Vector(up).dot(a)).normalized(); return a, u, a.cross(u)


def ring(S, c, axis, up, n, start=0.0, zmin=None, maxr=1.5, spike=1.35):
    a, u, v = basis(axis, up); c = Vector(c); pts, rad = [], []
    for k in range(n):
        t = math.radians(start) + 2 * math.pi * k / n; d = u * math.cos(t) + v * math.sin(t)
        h = S.bv.ray_cast(c, d, maxr); p = h[0] if h[0] is not None else None
        if p is not None and zmin is not None and p.z < zmin and d.z < -1e-6:
            p = c + d * ((zmin - c.z) / d.z)
        pts.append(p); rad.append((p - c).length if p is not None else None)
    for k in range(n):                                    # despike / fill misses
        l, r = rad[k - 1], rad[(k + 1) % n]
        if l is None or r is None:
            continue
        m = (l + r) / 2
        if rad[k] is None or rad[k] > m * spike or rad[k] < m / spike:
            t = math.radians(start) + 2 * math.pi * k / n; d = u * math.cos(t) + v * math.sin(t)
            pts[k] = c + d * m
    ok = [r for r in rad if r is not None]
    if not ok:
        raise ValueError("ring: centre %s is outside the reference (no ray hit)" % (tuple(round(x, 3) for x in c),))
    for k in range(n):                                    # still missing: use the mean radius
        if pts[k] is None:
            t = math.radians(start) + 2 * math.pi * k / n; pts[k] = c + (u * math.cos(t) + v * math.sin(t)) * (sum(ok) / len(ok))
    return [tuple(p) for p in pts]
