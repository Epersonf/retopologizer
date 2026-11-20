"""Hand-retopo mesh builder: the caller decides every vertex and every face; vertices are snapped to the reference.
  T = Topo(ref, start="cuca_user")     # optional: continue the artist's own mesh (its vertex indices stay valid)
  a = T.vs(points); T.strip(a, b); G = T.grid(B, Tp, L, R); T.fan(ring, tip)
  T.relax(verts); T.orient(); T.write("Cuca_retopo")
Grid = Coons patch (like Blender's Grid Fill) whose interior points are snapped along the patch normal."""
import bpy, bmesh
from mathutils import Vector
from .topo_ops import TopoOps
from .curves import sample


def _arclen(P):
    s = [0.0]
    for a, b in zip(P, P[1:]):
        s.append(s[-1] + (b - a).length)
    return [x / (s[-1] or 1) for x in s]


class Topo(TopoOps):
    def __init__(self, ref=None, start=None):
        self.ref, self.bm, self.named = ref, bmesh.new(), {}
        self._orig = self.bm.verts.layers.int.new("orig")      # start-mesh index + 1 (0 = vertex added here)
        if start:
            self.bm.from_mesh(bpy.data.meshes[start] if start in bpy.data.meshes else bpy.data.objects[start].data)
            self._orig = self.bm.verts.layers.int.get("orig") or self.bm.verts.layers.int.new("orig")
            for v in self.bm.verts:
                v[self._orig] = v.index + 1
        self.bm.verts.ensure_lookup_table()

    def old(self, *idx):
        """Vertices of the start mesh by their ORIGINAL index (still valid after merges/deletes)."""
        m = {v[self._orig] - 1: v for v in self.bm.verts if v[self._orig] > 0}
        return [m[i] for i in idx]

    def normal(self, p):
        h = self.ref.nearest(Vector(p), 0.2)
        return h[1] if h else Vector((0, 0, 1))

    def v(self, p, n=None, snap=True):
        if hasattr(p, "co"):
            return p
        p = Vector(p)
        if snap and self.ref is not None:
            p = self.ref.snap(p, n)
        return self.bm.verts.new(p)

    def vs(self, pts, n=None, snap=True):
        return [self.v(p, n, snap) for p in pts]

    def f(self, *vs):
        vs = [self.v(p) for p in vs]
        out = [vs[0]] + [b for a, b in zip(vs, vs[1:]) if b is not a]
        if len(out) > 1 and out[-1] is out[0]:
            out.pop()
        if len(out) < 3 or len(set(out)) != len(out):
            return None
        return self.bm.faces.get(out) or self.bm.faces.new(out)

    def strip(self, A, B, closed=False):
        """Quads between two chains with the same vertex count."""
        assert len(A) == len(B), (len(A), len(B))
        n = len(A)
        for i in range(n if closed else n - 1):
            j = (i + 1) % n; self.f(A[i], A[j], B[j], B[i])

    def fan(self, ring, tip, closed=True):
        """Triangles from a ring to one vertex (claw tips, poles)."""
        tip = self.v(tip); n = len(ring)
        for i in range(n if closed else n - 1):
            self.f(ring[i], ring[(i + 1) % n], tip)
        return tip

    def grid(self, B, Tp, L, R, snap=True, row=None, center=None):
        """Quad patch. B bottom, Tp top (left->right, same count); L left, R right (bottom->top, same count).
        Corners must be shared (B[0] is L[0], B[-1] is R[0], Tp[0] is L[-1], Tp[-1] is R[-1]). Returns G[j][i].
        center: a point INSIDE the volume that sees the whole patch; the blend is done on the directions from it and
        each interior vertex is where that ray leaves the surface (shoulder, skull, torso: no cutting through).
        row(a, b) -> polyline on the surface: interior rows follow it (e.g. curves.arcline around a limb)."""
        nu, nv = len(B) - 1, len(L) - 1
        assert len(Tp) == nu + 1 and len(R) == nv + 1, (len(B), len(Tp), len(L), len(R))
        P = lambda c: [Vector(x.co) for x in c]
        b, t, l, r = P(B), P(Tp), P(L), P(R)
        ub, ut, vl, vr = _arclen(b), _arclen(t), _arclen(l), _arclen(r)
        nrm = sum((self.normal(x) for x in (b[0], b[-1], t[0], t[-1], b[nu // 2], t[nu // 2])), Vector()).normalized()
        c = Vector(center) if center is not None else None
        if c is not None:
            b, t, l, r = [[(x - c).normalized() for x in ch] for ch in (b, t, l, r)]
        G = [[None] * (nu + 1) for _ in range(nv + 1)]
        G[0], G[nv] = list(B), list(Tp)
        for j in range(nv + 1):
            G[j][0], G[j][nu] = L[j], R[j]
        for j in range(1, nv):
            if row is not None:
                f = j / nv; S = sample(row(l[j], r[j]), [(1 - f) * ub[i] + f * ut[i] for i in range(nu + 1)])
                for i in range(1, nu):
                    G[j][i] = self.v(S[i], snap=False)
                continue
            for i in range(1, nu):
                u = w = 0.5
                for _ in range(3):
                    u = (1 - w) * ub[i] + w * ut[i]; w = (1 - u) * vl[j] + u * vr[j]
                p = ((1 - w) * b[i] + w * t[i] + (1 - u) * l[j] + u * r[j]
                     - ((1 - u) * (1 - w) * b[0] + u * (1 - w) * b[-1] + (1 - u) * w * t[0] + u * w * t[-1]))
                if c is not None:
                    q = self.ref.exit(c, p.normalized())
                    G[j][i] = self.v(q if q is not None else c + p, snap=q is None)
                else:
                    G[j][i] = self.v(p, nrm if snap else None, snap)
        for j in range(nv):
            for i in range(nu):
                self.f(G[j][i], G[j][i + 1], G[j + 1][i + 1], G[j + 1][i])
        return G

    def write(self, name, collection=None):
        o = bpy.data.objects.get(name)
        if o is None:
            o = bpy.data.objects.new(name, bpy.data.meshes.new(name))
            (collection or bpy.context.scene.collection).objects.link(o)
        if o.mode != 'OBJECT':
            raise RuntimeError(name + " is in Edit Mode: leave it before writing")
        self.bm.to_mesh(o.data); o.data.update()
        return o
