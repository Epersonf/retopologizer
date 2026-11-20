"""Operations on a mesh being built (mixin of Topo): relax with snap, outward winding, boundary paths, mirror."""
import bmesh
from mathutils import Vector


class TopoOps:
    def relax(self, verts, iters=4, k=0.5, pin=()):
        """Even out the spacing (umbrella average) and snap back; boundary and pinned vertices stay put."""
        pin = set(pin); vs = [v for v in set(verts) if not v.is_boundary and v not in pin and v.link_edges]
        for _ in range(iters):
            new = {v: v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges), k)
                   for v in vs}
            for v, p in new.items():
                v.co = self.ref.snap(p, self.normal(v.co))

    def orient(self):
        """Consistent winding per connected piece (walk across manifold edges), then outward by an area-weighted
        vote against the reference normals. Returns the number of pieces that were flipped as a whole."""
        bm = self.bm; bm.normal_update(); seen, flipped = set(), 0
        for f0 in list(bm.faces):
            if f0 in seen:
                continue
            comp, stack = [], [f0]; seen.add(f0)
            while stack:
                f = stack.pop(); comp.append(f)
                for lp in f.loops:
                    if len(lp.edge.link_faces) != 2:
                        continue
                    g = lp.edge.link_faces[0] if lp.edge.link_faces[1] is f else lp.edge.link_faces[1]
                    if g in seen:
                        continue
                    lg = [x for x in g.loops if x.edge is lp.edge][0]
                    if lg.vert is lp.vert:
                        g.normal_flip()
                    seen.add(g); stack.append(g)
            bm.normal_update(); vote = 0.0
            for f in comp:
                h = self.ref.nearest(f.calc_center_median(), 0.1)
                if h:
                    vote += f.calc_area() * (1 if f.normal.dot(h[1]) > 0 else -1)
            if vote < 0:
                for f in comp:
                    f.normal_flip()
                flipped += 1
        bm.normal_update()
        return flipped

    def chain(self, a, b, avoid=None):
        """Boundary path from vertex a to vertex b (the side not passing through `avoid`)."""
        for first in [e.other_vert(a) for e in a.link_edges if e.is_boundary]:
            path, prev, cur = [a, first], a, first
            while cur is not b and cur is not a:
                nxt = [e.other_vert(cur) for e in cur.link_edges if e.is_boundary and e.other_vert(cur) is not prev]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]; path.append(cur)
            if cur is b and (avoid is None or avoid not in path):
                return path
        raise ValueError("no boundary path between the two vertices")

    def mirror_x(self, tol=0.002):
        """Apply the Mirror: border vertices within tol of x=0 (the seam) go exactly to the plane, the half is
        mirrored and the seam welded, so the result is one piece."""
        bm = self.bm
        for v in bm.verts:
            if v.is_boundary and abs(v.co.x) < tol:
                v.co.x = 0.0
        bmesh.ops.mirror(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), axis='X', merge_dist=1e-5)
        bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if abs(v.co.x) < 1e-6], dist=1e-5)

