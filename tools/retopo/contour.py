"""Contours (as in RetopoFlow): the rings an artist strokes across a tube (limb, finger, tail, neck, torso), each one
evenly spaced along the REAL cross-section, plus the spine of the tube.
  S = track(ref, p0, d0, step, count)          spine: [(centre, axis, mean radius)] marching along the tube
  c = centred(ref, c, axis)                    c moved to the centroid of its cross-section
  P = cring(ref, c, axis, up, n)               closed ring: n points evenly spaced by arc length, P[0] toward up
  P = chalf(ref, c, axis, up, n)               mirror half ring: n edges from up (on x=0) around +x to -up (x=0)
  P = align(P, Q)                              closed ring P shifted/reversed so that P[i] is next to Q[i]
  P = box_ring(ref, c, axis, up, top, bottom)  ring of a flat section (palm, foot) laid out as a box
  frame(axis, up)                              up made perpendicular to axis (fallbacks when they are parallel)
Angles turn from `up` toward axis x up, so pick axis/up so that this goes toward +x for the half rings."""
from mathutils import Vector
from .curves import arc, resample, sample


def co(x):
    return Vector(x.co) if hasattr(x, "co") else Vector(x)


def frame(axis, up):
    a = Vector(axis).normalized(); u = Vector(up)
    if abs(u.normalized().dot(a)) > 0.95:
        u = Vector((0, 0, 1)) if abs(a.z) < 0.9 else Vector((0, -1, 0))
    return a, (u - a * u.dot(a)).normalized()


def cring(ref, c, axis, up, n, dense=96, maxr=0.5, fracs=None):
    """fracs: arc-length fractions (0..1) instead of n even steps (e.g. to put a vertex on a crease)."""
    a, u = frame(axis, up)
    P = arc(ref, c, a, u, 0.0, 360.0, dense, "exit", maxr)
    if fracs is not None:
        return sample(P, fracs)
    return resample(P, n)[:-1]


def chalf(ref, c, axis, up, n, dense=64, maxr=0.5, fracs=None):
    """First and last points are put exactly on x=0 (c must lie on x=0)."""
    a, u = frame(axis, up)
    P = arc(ref, c, a, u, 0.0, 180.0, dense, "exit", maxr)
    P = sample(P, fracs) if fracs is not None else resample(P, n)
    P[0].x = P[-1].x = 0.0
    return P


def track(ref, p0, d0, step, count, up=(0, 0, 1), dense=32, stop=None):
    """March along a tube from p0 (inside it) in direction d0: at each station the centre is moved to the centroid
    of the cross-section and the axis follows the centres. stop(radius, prev_radius) -> True ends the march
    (e.g. a jump in radius = the tube merged into the body)."""
    c, d, out = Vector(p0), Vector(d0).normalized(), []
    for _ in range(count):
        for _ in range(2):
            a, u = frame(d, up)
            P = arc(ref, c, a, u, 0.0, 360.0, dense, "exit")[:-1]
            m = sum(P, Vector()) / len(P)
            c = m - a * (m - c).dot(a)
        r = sum((p - c).length for p in P) / len(P)
        if stop and out and stop(r, out[-1][2]):
            break
        if out:
            d = ((c - out[-1][0]).normalized() + d).normalized()
        out.append((c.copy(), d.copy(), r))
        c = c + d * step
    return out


def centred(ref, c, axis, up=(0, 0, 1), iters=2, dense=32):
    """c moved (within its plane) to the centroid of the cross-section around axis."""
    c = Vector(c); a, u = frame(axis, up)
    for _ in range(iters):
        P = arc(ref, c, a, u, 0.0, 360.0, dense, "exit")[:-1]
        m = sum(P, Vector()) / len(P); c = m - a * (m - c).dot(a)
    return c


def align(P, Q):
    """Closed rings with the same count: P rotated (and reversed if that fits better) to follow Q vertex by vertex."""
    n = len(P); best = None
    for R in (list(P), list(P)[::-1]):
        for s in range(n):
            cost = sum((co(R[(i + s) % n]) - co(Q[i])).length for i in range(n))
            if best is None or cost < best[0]:
                best = (cost, [R[(i + s) % n] for i in range(n)])
    return best[1]


def box_ring(ref, c, axis, up, top, bottom, corner=(0.8, 0.7)):
    """Ring around a flat section (palm, sole, toe base) laid out as a box, w = axis x up: +w top corner, +w side,
    +w bottom corner, bottom row, -w bottom corner, -w side, -w top corner, top row. top / bottom: the row vertices
    as fractions of the width (0 = +w side, 1 = -w side), ascending; the bottom row is listed +w -> -w and the top
    row -w -> +w (the ring goes round). Every point is where a ray from inside the section leaves the surface."""
    a, u = frame(axis, up); w = a.cross(u); c = Vector(c)
    sp, sn, t, b = ref.exit(c, w), ref.exit(c, -w), ref.exit(c, u), ref.exit(c, -u)
    cor = lambda s, cap: ref.exit(c, ((s - c) * corner[0] + (cap - c) * corner[1]).normalized())
    wp, wn = (sp - c).dot(w), (sn - c).dot(w)
    row = lambda fs, d: [ref.exit(c + w * (wp + (wn - wp) * f), d) for f in fs]
    return [cor(sp, t), sp, cor(sp, b)] + row(bottom, -u) + [cor(sn, b), sn, cor(sn, t)] + row(top[::-1], u)


def at_width(ref, c, axis, up, f, side=1):
    """Point on the top (side=1) or bottom (-1) of a flat section at width fraction f (as in box_ring)."""
    a, u = frame(axis, up); w = a.cross(u); c = Vector(c)
    wp, wn = (ref.exit(c, w) - c).dot(w), (ref.exit(c, -w) - c).dot(w)
    return ref.exit(c + w * (wp + (wn - wp) * f), u * side)
