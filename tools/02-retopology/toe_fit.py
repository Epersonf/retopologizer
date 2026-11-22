r"""Fits each toe of a transplanted fused-toe block on its OWN toe of the ref (the rear toes are not spread like the front ones).
A global anchor + untangle squeezes toes that sit on the wrong place (collapsed toe = 'toe does not exist'); here every toe moves as a
rigid body with scale (similarity ICP against the ref), so its 6-ring tube keeps its shape and ends on the right toe.
  from toe_fit import toe_groups, fit_toes
  V2, rep = fit_toes(V, F, ref, seam=range(108, 120))       # rep: per toe {"n", "scale", "moved_mm", "dist_mm"}
Toes = connected parts of the vertices that are neither seam ring nor the 14-ring knuckle (BFS level 1 from the seam)."""
import numpy as np
from mathutils import Vector


def _adj(F):
    nb = {}
    for f in F:
        for i, a in enumerate(f): nb.setdefault(a, set()).add(f[(i + 1) % len(f)]); nb.setdefault(f[(i + 1) % len(f)], set()).add(a)
    return nb


def toe_groups(F, seam=range(108, 120), first=120):
    lvl = levels(F, seam, first); rest = {v for v, l in lvl.items() if l >= 2}; nb = _adj(F); groups = []
    while rest:
        s = rest.pop(); st = [s]; g = [s]
        while st:
            for b in nb[st.pop()]:
                if b in rest: rest.discard(b); st.append(b); g.append(b)
        groups.append(sorted(g))
    return sorted(v for v, l in lvl.items() if l == 1), groups


def levels(F, seam=range(108, 120), first=120):
    """BFS level of every toe vertex counted from the seam ring (1 = 14-ring knuckle, 2.. = toes); the leg never enters."""
    nb = _adj(F); lvl = {v: 0 for v in seam}; fr = list(seam)
    while fr:
        nxt = []
        for a in fr:
            for b in nb[a]:
                if b not in lvl and b >= first: lvl[b] = lvl[a] + 1; nxt.append(b)  # a perna (indices < first) nao entra
        fr = nxt
    return lvl


def _sim(A, B):
    ca, cb = A.mean(0), B.mean(0); U, S, Vt = np.linalg.svd((A - ca).T @ (B - cb)); R = Vt.T @ U.T
    if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
    return R, float(S.sum() / ((A - ca) ** 2).sum()), ca, cb


def split_toes(V, idx, k=3):
    """The template toes are fused (shared vertices), so connectivity cannot separate them: 1-D k-means along the line the toes are spread on."""
    P = np.array([V[i] for i in idx]); Q = P - P.mean(0); u = np.linalg.svd(Q, full_matrices=False)[2]
    # eixo de espalhamento = o eixo principal perpendicular ao eixo mais longo dos dedos (Y do mundo)
    q = np.array([(p[0], p[2]) for p in Q]); a = np.linalg.svd(q, full_matrices=False)[2][0]; t = q @ a
    c = np.quantile(t, [(j + 0.5) / k for j in range(k)])
    for _ in range(30):
        lab = np.argmin(abs(t[:, None] - c[None]), 1); c = np.array([t[lab == j].mean() if (lab == j).any() else c[j] for j in range(k)])
    return [sorted(int(idx[i]) for i in np.where(lab == j)[0]) for j in range(k)]


def fit_toes(V, F, ref, seam=range(108, 120), first=120, with_knuckle=True, iters=25, maxd=0.012, scale_lim=(0.8, 1.25)):
    knuckle, groups = toe_groups(F, seam, first); groups = split_toes(V, sorted(v for g in groups for v in g) + (knuckle if with_knuckle else [])); out = [tuple(v) for v in V]; rep = []
    for g in groups:
        A = np.array([out[i] for i in g]); A0 = A.copy(); tot = 1.0
        for _ in range(iters):
            H = [ref.nearest(Vector(tuple(a)), maxd) for a in A]; ok = [i for i, h in enumerate(H) if h]
            if len(ok) < 6: break
            B = np.array([tuple(H[i][0]) for i in ok]); R, s, ca, cb = _sim(A[ok], B)
            s = min(max(s, scale_lim[0] / tot), scale_lim[1] / tot); tot *= s
            A = ((A - ca) @ R.T) * s + cb
        for i, p in zip(g, A): out[i] = tuple(p)
        hs = [(Vector(tuple(a)), ref.nearest(Vector(tuple(a)), 0.03)) for a in A]; dist = np.mean([(a - h[0]).length for a, h in hs if h] or [0])
        rep.append({"n": len(g), "scale": round(tot, 3), "moved_mm": round(float(np.linalg.norm(A - A0, axis=1).mean()) * 1000, 1), "dist_mm": round(dist * 1000, 2)})
    return out, rep
