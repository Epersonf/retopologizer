"""Reuses an approved part elsewhere (rear paw from a front paw, the other side): moves the artist's topology, does not invent one.
Inside Blender (needs the Ref of retopo/ref.py). V = vertices, F = faces (lists), as in projects/<p>/draft/<part>_mesh.json.
  from transplant import transplant, mirror_matrix
  V2, F2, rep = transplant(V, F, ref, M=mirror_matrix(0.0))          # mirror across x = 0 (winding is flipped by itself)
  V2, F2, rep = transplant(V, F, ref, M=my_4x4, fixed={0: p0, ...})  # fixed: vertices that stay where the target seam is
Steps: transform by M, correct the winding so normals point out, snap each free vertex onto ref along its vertex normal
(`ref.snap(p, n)`), report mm moved and vertices that ended inside. `rep` has mean/p95/max_mm, inward, flipped."""
import math
from mathutils import Matrix, Vector


def mirror_matrix(x0=0.0):
    return [[-1, 0, 0, 2 * x0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def _normals(V, F):
    N = [Vector() for _ in V]
    for f in F:
        pts = [Vector(V[i]) for i in f]  # normal de Newell: serve para quad torto
        n = sum(((pts[i].cross(pts[(i + 1) % len(f)])) for i in range(len(f))), Vector())
        for v in f: N[v] += n
    return [n.normalized() if n.length > 1e-12 else Vector((0, 0, 1)) for n in N]


def _flip_if_inward(V, F):
    c = sum((Vector(p) for p in V), Vector()) / len(V)
    N = _normals(V, F)
    return F if sum(N[i].dot(Vector(V[i]) - c) for i in range(len(V))) >= 0 else [f[::-1] for f in F]


def icp(P, ref, iters=12, maxd=0.04):
    """Rigid refinement (Kabsch) of the moved copy toward the ref: the other leg is rarely posed exactly like the mirror."""
    import numpy as np
    A = np.array([tuple(p) for p in P]); 
    for _ in range(iters):
        H = [ref.nearest(Vector(a), maxd) for a in A]
        ok = [i for i, h in enumerate(H) if h]
        if len(ok) < 6: break
        B = np.array([tuple(H[i][0]) for i in ok]); X = A[ok]
        ca, cb = X.mean(0), B.mean(0)
        U, _, Vt = np.linalg.svd((X - ca).T @ (B - cb))
        R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        A = (A - ca) @ R.T + cb
    return [Vector(a) for a in A]


def transplant(V, F, ref, M, fixed=None, maxd=0.04, refine=True):
    """Returns (V2, F2, report). refine: rigid ICP onto the ref before snapping (keeps the topology, only places the copy)."""
    M = Matrix(M); fixed = fixed or {}
    P = [M @ Vector(p) for p in V]
    if refine: P = icp(P, ref, maxd=maxd)
    F2 = [list(f) for f in F]
    if M.determinant() < 0: F2 = [f[::-1] for f in F2]
    F2 = _flip_if_inward(P, F2)
    N = _normals(P, F2)
    Q, moved = [], []
    for i, p in enumerate(P):
        if i in fixed:
            q = Vector(fixed[i])
        else:
            q = Vector(ref.snap(p, N[i], maxd))
        Q.append(q); moved.append((q - p).length * 1000)
    rep = _report(Q, F2, N, ref, moved)
    return [tuple(q) for q in Q], F2, rep


def _report(Q, F2, N, ref, moved):
    s = sorted(moved); n = len(s)
    inward = 0; flipped = 0
    for q, nq in zip(Q, N):
        h = ref.nearest(q, 0.05)
        if h and (q - h[0]).dot(h[1]) < -0.0015: inward += 1
    for f in F2:
        if len(f) == 4:
            a, b, c, d = (Q[i] for i in f)
            if (b - a).cross(d - a).dot((d - c).cross(b - c)) < 0: flipped += 1
    return {"mean_mm": round(sum(s) / n, 2), "p95_mm": round(s[int(n * 0.95)], 2), "max_mm": round(s[-1], 2),
            "inward": inward, "flipped": flipped, "verts": n, "faces": len(F2)}
