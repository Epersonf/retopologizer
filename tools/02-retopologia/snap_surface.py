"""Snap-to-surface helpers (Surface, simplify). Loaded by snap_retopo.py."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


class Surface:
    def __init__(self, name):
        o = bpy.data.objects[name]
        self.bv = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())

    def nearest(self, p, dist=0.05):
        r = self.bv.find_nearest(Vector(p), dist)
        return tuple(r[0]) if r[0] is not None else tuple(p)

    def ray(self, p, d, both=True, dist=0.2):
        p, d = Vector(p), Vector(d).normalized()
        best = None
        for s in ((1, -1) if both else (1,)):
            h = self.bv.ray_cast(p, d * s, dist)
            if h[0] is not None and (best is None or h[3] < best[1]):
                best = (tuple(h[0]), h[3])
        return best[0] if best else tuple(p)

    def _dir(self, a):
        return Vector((0, math.cos(math.radians(a)), math.sin(math.radians(a))))

    def outer(self, x, c, a, far=0.8):
        d = self._dir(a); o = Vector((x, c[0], c[1])) + d * far
        h = self.bv.ray_cast(o, -d, far + 0.1)
        return None if h[0] is None else (h[0].y, h[0].z)

    def inner(self, x, c, a):
        d = self._dir(a); h = self.bv.ray_cast(Vector((x, c[0], c[1])), d, 1.0)
        return None if h[0] is None else (h[0].y, h[0].z)


def simplify(p, eps):
    p = np.array(p, float)

    def rec(i, j):
        if j <= i + 1:
            return [i]
        a, b = p[i], p[j]; ab = b - a; L = np.linalg.norm(ab) + 1e-12
        d = np.abs(ab[0] * (p[i + 1:j, 1] - a[1]) - ab[1] * (p[i + 1:j, 0] - a[0])) / L
        k = int(d.argmax())
        if d[k] > eps:
            m = i + 1 + k
            return rec(i, m) + rec(m, j)
        return [i]
    return sorted(set(rec(0, len(p) - 1) + [len(p) - 1]))
