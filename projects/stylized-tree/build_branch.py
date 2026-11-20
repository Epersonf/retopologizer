"""Ramos e tronco superior: tubos de n lados ao longo de um eixo medido; cada vértice é colado
na referência (snap, até `tol`). Depende de build_tree.py (Mesh, BV)."""
import math
from mathutils import Vector


def frame(a):
    a = Vector(a).normalized()
    h = Vector((0, 0, 1)) if abs(a.z) < 0.9 else Vector((1, 0, 0))
    u = a.cross(h).normalized(); return u, a.cross(u).normalized()


def snap_near(p, tol):
    r = BV.find_nearest(Vector(p), tol)
    return tuple(r[0]) if r[0] is not None else tuple(p)


def tube_rings(m, pts, radii, n, tol=0.03, rot=0.0, ref=Vector((1, 0, 0))):
    rings = []
    for i, (c, r) in enumerate(zip(pts, radii)):
        c = Vector(c)
        a = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)]))
        u, w = frame(a)
        a = a.normalized(); u = (ref - a * ref.dot(a)).normalized(); w = a.cross(u)
        ring = []
        for k in range(n):
            t = rot + 2 * math.pi * k / n
            ring.append(m.v(snap_near(c + (u * math.cos(t) + w * math.sin(t)) * r, tol)))
        rings.append(ring)
    return rings


def tube(name, pts, radii, n=4, tol=0.03, cap_end=False):
    m = Mesh(); R = tube_rings(m, pts, radii, n, tol)
    for lo, hi in zip(R, R[1:]):
        m.strip_closed(lo, hi)
    if cap_end:
        m.f(*R[-1])
    return m.to_object(name)


BRANCHES = {
    "tree_branch_l": ([(-0.02, -0.17, 0.82), (-0.28, -0.26, 0.98), (-0.5, -0.34, 1.15)], [0.07, 0.055, 0.04]),
    "tree_twig_l": ([(-0.28, -0.26, 0.97), (-0.33, -0.27, 1.14)], [0.04, 0.03]),
    "tree_branch_r": ([(0.03, -0.17, 0.85), (0.3, -0.22, 0.98), (0.58, -0.25, 1.08)], [0.07, 0.055, 0.04]),
    "tree_twig_r": ([(0.34, -0.22, 0.99), (0.49, -0.24, 1.2)], [0.04, 0.03]),
}
