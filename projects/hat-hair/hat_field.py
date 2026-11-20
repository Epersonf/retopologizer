"""Ring layout of the hat (normal python + scipy; measurement only, the mesh is built by hat_outer.py).
On the OUTER cloth surface of the reference (hat_measure.py: visible from open space) solve Laplace with 0 on its
boundary around the opening (the cloth's edge) and 1 at the tip: its level lines run around the cap like the rows of a sock
cap and never split. Rings are level lines spaced so the quads come out square (spacing = perimeter / vertex count);
the count halves (48 -> 24 -> 12) when the edges get short. Writes draft/hat_rings.npz.
  python projects/hat-hair/hat_field.py"""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

D = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft"
NAME = sys.argv[1] if len(sys.argv) > 1 else "hat"        # hat -> draft/hat_field_in.npz; hair_dome -> hair_dome_field_in.npz
COUNTS, MIN_EDGE, STEP_MIN = (48, 24, 12), 0.020, 0.025   # halve the count when edges get shorter than MIN_EDGE
d = np.load(D + "/" + NAME + "_field_in.npz"); V, N, F, OUT, TIP = (d[k] for k in ("V", "N", "F", "outer", "tip"))
_, first, inv = np.unique(np.round(V, 6), axis=0, return_index=True, return_inverse=True)   # the GLB splits vertices
inv = inv.ravel(); Nw = np.zeros((len(first), 3)); np.add.at(Nw, inv, N)                   # at UV seams: weld them
Ow = np.zeros(len(first), bool); np.logical_or.at(Ow, inv, OUT)
V, N, F = V[first], Nw / np.linalg.norm(Nw, axis=1)[:, None], inv[F]
F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]


def rim_loop(F):
    """Vertices of the longest boundary loop of the outer surface: the cloth's edge around the opening."""
    e = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    ue, cnt = np.unique(e, axis=0, return_counts=True); b = ue[cnt == 1]
    g = coo_matrix((np.ones(len(b)), (b[:, 0], b[:, 1])), shape=(len(V), len(V)))
    _, lab = connected_components(g, directed=False); lb = lab[b[:, 0]]
    return np.unique(b[lb == np.bincount(lb).argmax()])


def laplace(F):
    """Cotangent weights (clamped), symmetric."""
    I, J, W = [], [], []
    for k in range(3):
        i, j, o = F[:, k], F[:, (k + 1) % 3], F[:, (k + 2) % 3]
        u, v = V[i] - V[o], V[j] - V[o]
        cot = (u * v).sum(1) / np.maximum(np.linalg.norm(np.cross(u, v), axis=1), 1e-12)
        w = np.clip(cot, 1e-3, 50) / 2; I += [i, j]; J += [j, i]; W += [w, w]
    return coo_matrix((np.concatenate(W), (np.concatenate(I), np.concatenate(J))), shape=(len(V), len(V))).tocsr()


def crossings(u, lv):
    """All points where the level line u = lv crosses an edge (any order)."""
    i, j = E.T; m = (u[i] > lv) != (u[j] > lv); i, j = i[m], j[m]
    t = ((lv - u[i]) / (u[j] - u[i]))[:, None]
    return V[i] + t * (V[j] - V[i])


def ring(P, n, toward):
    """Crossing points -> closed ring of n points: angle bins around the centroid in the best-fit plane (stray bits of
    holes in the mask fall into a bin with the real ring and are outvoted), turning positively around `toward`."""
    c = P.mean(0); w = np.linalg.svd(P - c)[2]; nz = w[2] if w[2] @ toward > 0 else -w[2]
    e1 = w[0]; e2 = np.cross(nz, e1); q = P - c
    ang = np.arctan2(q @ e2, q @ e1); B = 4 * n; k = ((ang + np.pi) / (2 * np.pi) * B).astype(int) % B
    pts = np.array([np.median(P[k == b], 0) if (k == b).any() else np.full(3, np.nan) for b in range(B)])
    ok = ~np.isnan(pts[:, 0]); idx = np.arange(B)
    pts = np.array([np.interp(idx, idx[ok], pts[ok, d], period=B) for d in range(3)]).T
    for _ in range(2):
        pts = (np.roll(pts, 1, 0) + 2 * pts + np.roll(pts, -1, 0)) / 4
    seg = np.linalg.norm(np.diff(np.vstack([pts, pts[:1]]), axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
    t = np.linspace(0, s[-1], n, endpoint=False); cl = np.vstack([pts, pts[:1]])
    return np.array([np.interp(t, s, cl[:, d]) for d in range(3)]).T, s[-1]


F = F[Ow[F].all(1)]
n_c, lab = connected_components(coo_matrix((np.ones(len(F) * 3), (F.ravel(), np.roll(F, 1, 1).ravel())),
                                           shape=(len(V), len(V))), directed=False)
main = np.bincount(lab[F[:, 0]]).argmax(); F = F[lab[F[:, 0]] == main]
used = np.unique(F)
zero = rim_loop(F); MOUTH = V[zero]
one = used[np.linalg.norm(V[used] - TIP, axis=1) < 0.015]
L = laplace(F); L = L - coo_matrix((np.asarray(L.sum(1)).ravel(), (np.arange(len(V)), np.arange(len(V))))).tocsr()
fixed = np.zeros(len(V), bool); fixed[zero] = fixed[one] = True; ub = np.zeros(len(V)); ub[one] = 1.0
free = np.setdiff1d(used, np.nonzero(fixed)[0])
u = np.zeros(len(V)); u[one] = 1.0
u[free] = spsolve(L[free][:, free].tocsc(), -L[free][:, fixed[:]].dot(ub[fixed]))

E = np.unique(np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0)   # for crossings
levels = np.quantile(u[used], np.linspace(0.02, 0.995, 400))
levels = np.unique(np.r_[levels, np.linspace(0.9, 0.995, 40)])
cs = [crossings(u, lv) for lv in levels]
gap = [np.median(cKDTree(V[zero]).query(cs[0][::7])[0])]
gap += [np.median(cKDTree(a).query(b[::7])[0]) for a, b in zip(cs, cs[1:])]
s = np.cumsum(gap)                                     # distance along the cap: spacing between neighbouring levels
plan, cur, k = [], 0.0, 0
mp = ring(MOUTH, 192, TIP - MOUTH.mean(0))[1]
n = COUNTS[0]
while True:
    nxt = cur + max((plan[-1][2] if plan else mp) / n, STEP_MIN)
    j = int(np.searchsorted(s, nxt))
    if j >= len(s) - 3:
        break
    P, per = ring(cs[j], n, TIP - cs[j].mean(0))
    if k + 1 < len(COUNTS) and per / n < MIN_EDGE:
        k += 1; n = COUNTS[k]; P, per = ring(cs[j], n, TIP - cs[j].mean(0))
    plan.append((j, n, per, P)); cur = s[j]
rings = [ring(MOUTH, COUNTS[0], TIP - MOUTH.mean(0))[0]] + [P for *_, P in plan]
np.savez(D + "/" + NAME + "_rings.npz", counts=np.array([COUNTS[0]] + [n for _, n, _, _ in plan]), tip=TIP,
         flat=np.vstack(rings), sizes=np.array([len(r) for r in rings]))
print("mouth perimeter", round(mp, 3), "total s", round(s[-1], 3), "rings", len(rings),
      "quads ~", sum(n for _, n, _, _ in plan))
print([(round(s[j], 3), round(per, 3), n) for j, n, per, _ in plan])
