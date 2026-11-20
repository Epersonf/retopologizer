"""Point chains on the reference: the loops an artist would draw before filling (rings, lines on the surface).
  ring(ref, c, axis, up, n)              closed loop around an axis (limbs, neck, tail, fingers)
  arc(ref, c, axis, up, a0, a1, n)       open part of a loop (half rings for the mirror: front centre -> back centre)
  line(ref, a, b, n, nrm)                n segments from a to b lying on the surface, evenly spaced
  resample(P, n)                         n segments by arc length
Angles: 0 = toward `up`, positive turning toward axis x up (right-handed)."""
import math
from mathutils import Vector


def basis(axis, up):
    a = Vector(axis).normalized(); u = (Vector(up) - a * Vector(up).dot(a)).normalized()
    return a, u, a.cross(u)


def resample(P, n):
    P = [Vector(p) for p in P]; s = [0.0]
    for a, b in zip(P, P[1:]):
        s.append(s[-1] + (b - a).length)
    out, k = [], 0
    for i in range(n + 1):
        t = s[-1] * i / n
        while k < len(P) - 2 and s[k + 1] < t:
            k += 1
        seg = (s[k + 1] - s[k]) or 1
        out.append(P[k].lerp(P[k + 1], (t - s[k]) / seg))
    return out


def _hit(ref, c, d, mode, maxr):
    if mode == "outer":
        return ref.outer(c, d, maxr)
    h = ref.exit(c, d, maxr) if mode == "exit" else None
    if h is None:
        r = ref.ray(c, d, maxr); h = r[0] if r else None
    return h


def arc(ref, c, axis, up, a0, a1, n, mode="exit", maxr=0.5, radius=None):
    """n+1 points from angle a0 to a1 (degrees) around `axis` through c. mode: 'exit' = where a ray from the
    inside leaves the surface (ignores neighbours not on the ray); 'outer' = outermost hit (convex hull side).
    Misses are filled with the mean radius (or `radius`)."""
    a, u, w = basis(axis, up); c = Vector(c); pts = []
    for k in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * k / n); d = u * math.cos(t) + w * math.sin(t)
        pts.append((d, _hit(ref, c, d, mode, maxr)))
    rs = [(p - c).length for d, p in pts if p is not None]
    r0 = radius or (sum(rs) / len(rs) if rs else 0.02)
    return [p if p is not None else c + d * r0 for d, p in pts]


def ring(ref, c, axis, up, n, start=0.0, mode="exit", maxr=0.5):
    """Closed loop of n points (first one toward `up` rotated by `start` degrees)."""
    return arc(ref, c, axis, up, start, start + 360.0, n, mode, maxr)[:-1]


def line(ref, a, b, n, nrm=None, iters=2, via=(), center=None):
    """n segments from a to b on the surface (snap along nrm when given), re-spaced by arc length.
    via: waypoints the line must pass near (over a shoulder instead of through it).
    center: a point inside the volume; the line is drawn by rays from it (where they leave the surface)."""
    a, b = Vector(a), Vector(b)
    if center is not None:
        c = Vector(center); D = [(Vector(p) - c).normalized() for p in [a, *via, b]]
        dense = []
        for d0, d1 in zip(D, D[1:]):
            dense += [d0.slerp(d1, k / 16) for k in range(16)]
        dense.append(D[-1])
        P = [a] + [ref.exit(c, d) or c + d * 0.05 for d in dense[1:-1]] + [b]
        return [a] + sample(P, [k / n for k in range(1, n)]) + [b]
    P = resample([a] + [ref.snap(Vector(w), nrm) for w in via] + [b], n)
    for _ in range(iters):
        P = [P[0]] + [ref.snap(p, nrm) for p in P[1:-1]] + [P[-1]]
        P = resample(P, n)
    return [P[0]] + [ref.snap(p, nrm) for p in P[1:-1]] + [P[-1]]


def arcline(ref, a, b, c, axis, n=24, longway=False):
    """Dense polyline from a to b going AROUND an axis (through c): angle, height and radius are interpolated in
    cylindrical coordinates, each point snapped along its radial direction. For loops wrapping a neck, torso, limb."""
    ax = Vector(axis).normalized(); c = Vector(c); a, b = Vector(a), Vector(b)
    da, db = a - c, b - c; ha, hb = da.dot(ax), db.dot(ax); ra, rb = da - ax * ha, db - ax * hb
    u = ra.normalized(); w = ax.cross(u); tb = math.atan2(rb.dot(w), rb.dot(u))
    if longway:
        tb = tb - 2 * math.pi if tb > 0 else tb + 2 * math.pi
    out = [a]
    for i in range(1, n):
        f = i / n; t = tb * f; r = ra.length * (1 - f) + rb.length * f; d = u * math.cos(t) + w * math.sin(t)
        out.append(Vector(ref.snap(c + ax * (ha * (1 - f) + hb * f) + d * r, d)))
    return out + [b]


def sample(P, ts):
    """Points of polyline P at arc-length fractions ts (0..1)."""
    P = [Vector(p) for p in P]; s = [0.0]
    for p, q in zip(P, P[1:]):
        s.append(s[-1] + (q - p).length)
    out, k = [], 0
    for t in ts:
        t *= s[-1]
        while k < len(P) - 2 and s[k + 1] < t:
            k += 1
        k = min(k, len(P) - 2)
        while k > 0 and s[k] > t:
            k -= 1
        out.append(P[k].lerp(P[k + 1], (t - s[k]) / ((s[k + 1] - s[k]) or 1)))
    return out


def centroid(P):
    return sum((Vector(p) for p in P), Vector()) / len(P)
