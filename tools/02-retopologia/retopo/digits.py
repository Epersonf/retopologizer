"""Digits (fingers, toes, thumb, claws, horns): a tube grown from a root ring already in the mesh to a tip point.
  digit(T, ref, root, p_in, tip)        root: closed ring of verts on the hand/foot; p_in: a point inside the digit
                                         near its root; tip: the claw tip on the reference
The spine is marched from p_in toward the tip and re-centred in every cross-section, so it follows a curved claw
(a straight chord leaves a hooked claw). Rings: one or two on the body, one each side of the claw base (the biggest
drop of the cross-section radius) and one near the tip; the tip is a vertex with quads around it (len(root)/2
quads, so the root ring must be even). Returns (rings, tip vertex)."""
from mathutils import Vector
from .curves import arc, ring
from .contour import centred, align


def spine(ref, p_in, tip, step=0.003, up=(0, 0, 1)):
    """[(centre, direction, radius)] from p_in to the tip, each centre moved to the centroid of its section."""
    c, d, out = Vector(p_in), (Vector(tip) - Vector(p_in)).normalized(), []
    while (tip - c).length > step * 1.5:
        c = centred(ref, c, d, up)
        P = arc(ref, c, d, up, 0.0, 360.0, 16)[:-1]
        out.append((c.copy(), d.copy(), sum((p - c).length for p in P) / len(P)))
        d = ((tip - c).normalized() + d).normalized(); c = c + d * step
    return out


def at(sp, t):
    """Spine point at arc-length fraction t: (centre, direction)."""
    s = [0.0]
    for a, b in zip(sp, sp[1:]):
        s.append(s[-1] + (b[0] - a[0]).length)
    x = t * s[-1]; i = max(k for k in range(len(s)) if s[k] <= x or k == 0)
    i = min(i, len(sp) - 2); f = (x - s[i]) / ((s[i + 1] - s[i]) or 1)
    return sp[i][0].lerp(sp[i + 1][0], f), sp[i][1].lerp(sp[i + 1][1], f).normalized()


def claw_base(sp, lo=0.25, hi=0.85):
    """Arc-length fraction where the radius drops the most between two spine samples (finger end -> claw)."""
    n = len(sp) - 1; k0, k1 = max(1, int(lo * n)), int(hi * n)
    i = max(range(k0, k1), key=lambda i: sp[i][2] - sp[i + 1][2])
    return (i + 0.5) / n


def digit(T, ref, root, p_in, tip, up=(0, 0, 1), body=None, gap=(0.04, 0.05), near_tip=0.86, start=None):
    """body: arc-length fractions of extra rings on the finger body (default: one in the middle when it is longer
    than 2.5 cm). gap: rings at t_base - gap[0] (end of the finger) and t_base + gap[1] (claw)."""
    p_in, tip = Vector(p_in), Vector(tip); n = len(root)
    sp = spine(ref, p_in, tip, up=up); tb = claw_base(sp)
    length = sum((b[0] - a[0]).length for a, b in zip(sp, sp[1:]))
    if body is None:
        body = [tb * 0.5] if tb * length > 0.025 else []
    start = 180.0 / n if start is None else start
    rings, prev = [root], root
    for t in list(body) + [tb - gap[0], tb + gap[1], near_tip]:
        c, d = at(sp, t)
        cur = T.vs(align(ring(ref, c, d, up, n, start=start), prev), snap=False)
        T.strip(prev, cur, closed=True); rings.append(cur); prev = cur
    tv = T.v(tip, snap=False)
    for k in range(0, n, 2):
        T.f(prev[k], prev[k + 1], prev[(k + 2) % n], tv)
    return rings, tv
