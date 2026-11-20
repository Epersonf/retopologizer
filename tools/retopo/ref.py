"""Reference surface (the high-poly) for snapping, in WORLD space.
The BVH is built in the object's local space (no copy of 1.5M triangles) and cached in
bpy.app.driver_namespace, so later MCP calls reuse it. matrix_world may be rotated (GLB import: +90 deg X)."""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_CACHE = bpy.app.driver_namespace.setdefault("_retopo_ref_cache", {})


class Ref:
    def __init__(self, name):
        o = bpy.data.objects[name]
        key = (o.data.name, len(o.data.vertices), tuple(round(x, 6) for r in o.matrix_world for x in r))
        c = _CACHE.get(name)
        if c is None or c[0] != key:
            c = (key, BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get()))
            _CACHE[name] = c
        self.name, self.bv = name, c[1]
        self.M = o.matrix_world.copy(); self.Mi = self.M.inverted()
        self.s = self.M.to_scale()[0]; self.R = self.M.to_3x3().normalized()

    def _w(self, h, origin=None):
        if h[0] is None:
            return None
        p = self.M @ h[0]; n = (self.R @ h[1]).normalized()
        return p, n, (h[3] * self.s if origin is None else (p - origin).length)

    def nearest(self, p, maxd=1.0):
        """(point, normal, dist) of the closest surface point, or None."""
        return self._w(self.bv.find_nearest(self.Mi @ Vector(p), maxd / self.s))

    def ray(self, o, d, maxd=10.0):
        """(point, normal, dist) of the first hit from o along d (world), or None."""
        o = Vector(o); d = Vector(d).normalized()
        return self._w(self.bv.ray_cast(self.Mi @ o, (self.Mi.to_3x3() @ d).normalized(), maxd / self.s), o)

    def hits(self, o, d, maxd=10.0):
        """All hits along the ray (entry and exit surfaces), as a list of (point, normal, dist)."""
        out, o0, d = [], Vector(o), Vector(d).normalized(); cur, left = Vector(o), maxd
        while left > 0:
            h = self.ray(cur, d, left)
            if h is None:
                break
            out.append((h[0], h[1], (h[0] - o0).length)); cur = h[0] + d * 1e-5; left = maxd - out[-1][2]
        return out

    def snap(self, p, n=None, maxd=0.06):
        """Snap to face. Without n: closest point. With n (expected outward normal): the closest hit along +-n
        whose surface faces the same way (no jumping onto a neighbour: arm next to torso, leg next to skirt)."""
        p = Vector(p)
        if n is None:
            h = self.nearest(p, maxd)
            return h[0] if h else p
        n = Vector(n).normalized(); best = None
        for s in (1, -1):
            for q, nq, d in self.hits(p, n * s, maxd):
                if nq.dot(n) > 0.2:
                    if best is None or d < best[1]:
                        best = (q, d)
                    break
        if best:
            return best[0]
        h = self.nearest(p, maxd)
        return h[0] if h and h[1].dot(n) > 0 else p

    def exit(self, c, d, maxd=2.0):
        """From a point INSIDE the volume, the surface where the ray leaves it (first back-facing hit)."""
        for q, nq, dist in self.hits(c, d, maxd):
            if nq.dot(Vector(d)) > 0:
                return q
        return None

    def outer(self, c, d, far=1.0):
        """Outermost surface point along direction d from c (ray shot back from far away)."""
        d = Vector(d).normalized(); h = self.ray(Vector(c) + d * far, -d, far)
        return h[0] if h else None
