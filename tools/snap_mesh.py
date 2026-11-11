"""Ring/strip mesh builder with mirror (Mesh). Loaded by snap_retopo.py."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree




class Mesh:
    def __init__(self, tol=1e-5):
        self.bm = bmesh.new(); self.tol = tol; self.map = {}

    def v(self, p):
        k = tuple(round(c / self.tol) for c in p)
        if k not in self.map:
            self.map[k] = self.bm.verts.new(p)
        return self.map[k]

    def f(self, *vs):
        vs = [self.v(p) if not hasattr(p, "co") else p for p in vs]
        if len(set(vs)) == len(vs):
            try:
                return self.bm.faces.new(vs)
            except ValueError:
                return None

    def strip(self, A, B, flip=False):
        for i in range(len(A) - 1):
            q = (A[i], A[i + 1], B[i + 1], B[i])
            self.f(*(q[::-1] if flip else q))

    def prism(self, ring, n, h, embed=0.004, top_scale=1.0, closed_top=True, snap=None):
        """Raised slab on a surface: `ring` = footprint points ON the surface, CCW seen from +n.
        Base is pushed `embed` inside (no bottom face, hidden in the wall; snap(p, n) projects it onto the shell), top at +h.
        Returns the top ring (for dimples / holes)."""
        n = Vector(n).normalized(); P = [Vector(p) for p in ring]; ctr = sum(P, Vector()) / len(P)
        B = [self.v(tuple((Vector(snap(p, n)) if snap else p) - n * embed)) for p in P]  # base sits INSIDE the shell
        T = [self.v(tuple(ctr + (p - ctr) * top_scale + n * h)) for p in P]
        for i in range(len(B)):
            j = (i + 1) % len(B); self.f(B[i], B[j], T[j], T[i])
        if closed_top:
            self.f(*T)
        return T

    def dimple(self, top, depth, scale=0.5):
        """Sink an inset of a face ring (hole/recess): strip down + floor. top = ring from prism(closed_top=False)."""
        P = [Vector(v.co) for v in top]; ctr = sum(P, Vector()) / len(P)
        nrm = (P[1] - P[0]).cross(P[2] - P[1]).normalized()
        I = [self.v(tuple(ctr + (p - ctr) * scale - nrm * depth)) for p in P]
        for i in range(len(top)):
            j = (i + 1) % len(top); self.f(top[i], top[j], I[j], I[i])
        self.f(*I)

    @staticmethod
    def ngon(c, n, up, r, k=5, rot=0.0):
        """k-gon ring around c in the plane normal to n, CCW seen from +n, first vertex toward `up`."""
        n = Vector(n).normalized(); u = (Vector(up) - n * Vector(up).dot(n)).normalized(); w = n.cross(u)
        return [tuple(Vector(c) + (u * math.cos(rot + 2 * math.pi * i / k) + w * math.sin(rot + 2 * math.pi * i / k)) * r)
                for i in range(k)]

    def boundary_loops(self):
        """Ordered vertex loops of the boundary edges."""
        adj = {}
        for e in self.bm.edges:
            if e.is_boundary:
                a, b = e.verts; adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
        loops, seen = [], set()
        for s in adj:
            if s in seen:
                continue
            loop, cur, prev = [s], s, None
            seen.add(s)
            while True:
                nxt = [w for w in adj[cur] if w != prev and w not in seen]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]; seen.add(cur); loop.append(cur)
            loops.append(loop)
        return loops

    def fill_flat_ring(self):
        """Flat rim between the outer loop and the hole (cavity): ear-clipping triangulation of the
        polygon-with-hole (never crosses), then zero-area ears (3 collinear boundary verts) are removed
        by re-splitting the neighbour triangle, so the rim stays watertight."""
        from mathutils.geometry import tessellate_polygon
        L = sorted(self.boundary_loops(), key=lambda l: -(max(v.co.x for v in l) - min(v.co.x for v in l)))
        outer, holes = L[0], L[1:]
        verts = outer + [v for h in holes for v in h]
        tris = [list(t) for t in tessellate_polygon([[v.co.to_3d() for v in outer]] +
                                                    [[v.co.to_3d() for v in h] for h in holes])]
        area = lambda t: ((verts[t[1]].co - verts[t[0]].co).cross(verts[t[2]].co - verts[t[0]].co)).length / 2
        for t in [t for t in tris if area(t) < 1e-9]:
            if t not in tris:
                continue
            d = {(i, j): (verts[i].co - verts[j].co).length for i in t for j in t if i < j}
            (a, c), _ = max(d.items(), key=lambda kv: kv[1]); b = [i for i in t if i not in (a, c)][0]
            for n in tris:
                if n is not t and a in n and c in n:
                    e = [i for i in n if i not in (a, c)][0]
                    tris.remove(n); tris.remove(t); tris += [[a, b, e], [b, c, e]]
                    break
        for t in tris:
            self.f(*[verts[i] for i in t])

    def mirror_x(self):
        bm = self.bm
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        ret = bmesh.ops.mirror(bm, geom=geom, axis='X', merge_dist=1e-5)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)

    def to_object(self, name, collection=None):
        me = bpy.data.meshes.new(name); self.bm.to_mesh(me); self.bm.free()
        o = bpy.data.objects.new(name, me)
        (collection or bpy.context.scene.collection).objects.link(o)
        return o
