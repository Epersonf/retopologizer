r"""Quad strip between two closed loops of a bmesh (see hole_fill.py, whose helpers it loads). Inside Blender:
  exec(open(".../loop_bridge.py").read());  faces, new = loop_bridge(bm, A, B, ref, rings=1)"""
import os
from mathutils import Vector
if "_snap_relax" not in globals():
    exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else r"tools/02-retopology", "hole_fill.py"), encoding="utf-8").read())


def loop_bridge(bm, A, B, ref=None, rings=1, relax=8):
    """Quad strip between two closed loops with the SAME number of vertices (ordered vertex lists), with `rings` new rings in between, snapped on the ref.
    Direction and start of B are chosen to minimise the total rung length. Different counts raise: change the count first (pole pair by hand, see topology.md)."""
    n = len(A)
    if len(B) != n: raise ValueError("loops have %d and %d vertices: bridge needs the same count" % (n, len(B)))
    best = None
    for rev in (False, True):
        Bs = B[::-1] if rev else B
        for s in range(n):
            d = sum((A[i].co - Bs[(i + s) % n].co).length for i in range(n))
            if best is None or d < best[0]: best = (d, rev, s)
    _, rev, s = best; Bs = (B[::-1] if rev else B); Bs = [Bs[(i + s) % n] for i in range(n)]
    R = [A]; new = []
    for r in range(1, rings + 1):
        t = r / (rings + 1); ring = []
        for i in range(n):
            c = A[i].co.lerp(Bs[i].co, t); v = bm.verts.new(Vector(ref.snap(c, None, 0.03)) if ref else c); ring.append(v); new.append(v)
        R.append(ring)
    R.append(Bs); faces = []
    for k in range(len(R) - 1):
        for i in range(n): faces.append(bm.faces.new((R[k][i], R[k][(i + 1) % n], R[k + 1][(i + 1) % n], R[k + 1][i])))
    # winding: edge A[0]->A[1] of an old face must run the other way in the new face
    e0 = bm.edges.get((A[0], A[1])); old = [f for f in e0.link_faces if f not in faces]; nf = [f for f in e0.link_faces if f in faces][0]
    def fwd(f, a, b):
        vs = list(f.verts); return any(vs[i] is a and vs[(i + 1) % len(vs)] is b for i in range(len(vs)))
    if old and fwd(old[0], A[0], A[1]) == fwd(nf, A[0], A[1]):
        for f in faces: f.normal_flip()
    bm.verts.index_update(); bm.faces.index_update()
    fixed = {v.index for v in A} | {v.index for v in B}
    _snap_relax(new, ref, fixed, relax)
    return faces, new
