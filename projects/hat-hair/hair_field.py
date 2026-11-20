"""Ring layout of a hair shell (normal python + scipy; measurement only, the mesh is built in Blender). Same idea as
hat_field.py (Laplace field, 0 on the rim, 1 at the top point, rings = level lines) but the level lines are traced
exactly (chained along the triangle edges, longest closed loop), so a rim that is not planar or not star-shaped
(the U-shaped edge of the dome) still gives ordered rings. Reads draft/<NAME>_field_in.npz, writes draft/<NAME>_rings.npz.
  python -I projects/hat-hair/hair_field.py hair_dome [counts e.g. 48,24,12]"""
import sys
import numpy as np
from pathlib import Path
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import spsolve

NAME = sys.argv[1] if len(sys.argv) > 1 else "hair_dome"
COUNTS = tuple(int(x) for x in sys.argv[2].split(",")) if len(sys.argv) > 2 else (48, 24, 12)
MIN_EDGE, STEP_MIN, NLEV = 0.020, 0.022, 300
D = Path(__file__).resolve().parent / "draft"
d = np.load(D / (NAME + "_field_in.npz")); V, F, TIP = d["V"], d["F"], d["tip"]
nv = len(V)
E2 = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
E, eid, cnt = np.unique(E2, axis=0, return_inverse=True, return_counts=True); FE = eid.ravel().reshape(3, -1).T   # edge ids per tri


def walk(nodes, pairs):
    """Closed (or open) chains from adjacency pairs: list of node lists, each in order."""
    adj = {}
    for a, b in pairs:
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for s in sorted(adj, key=lambda k: len(adj[k])):
        if s in seen:
            continue
        ch, prev, cur = [s], None, s; seen.add(s)
        while True:
            nxt = [x for x in adj[cur] if x != prev and x not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]; ch.append(cur); seen.add(cur)
        out.append(ch)
    return out


def level_loop(u, lv):
    """Longest chain of the level line u = lv: points on the edges, in order."""
    side = u > lv; ec = side[E[:, 0]] != side[E[:, 1]]
    m = ec[FE].sum(1) == 2; T = FE[m]
    pairs = [tuple(r[ec[r]]) for r in T]
    if not pairs:
        return None
    chs = walk(None, pairs)
    ch = max(chs, key=len); i, j = E[ch, 0], E[ch, 1]
    t = ((lv - u[i]) / (u[j] - u[i]))[:, None]
    return V[i] + t * (V[j] - V[i])


def resample(P, n, closed=True):
    Q = np.vstack([P, P[:1]]) if closed else P
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    t = np.linspace(0, s[-1], n, endpoint=not closed)
    return np.array([np.interp(t, s, Q[:, k]) for k in range(3)]).T, s[-1]


def smooth(P, k=4):
    """Moving average along a closed loop (+-k points): takes the 3 mm jaggies out of a contour."""
    return sum(np.roll(P, i, 0) for i in range(-k, k + 1)) / (2 * k + 1)


def toward(P, tip):
    """Loop turned so that its (Newell) normal looks at the tip: the same turning for every ring."""
    q = P - P.mean(0); nrm = np.cross(q, np.roll(q, -1, 0)).sum(0)
    return P if nrm @ (tip - P.mean(0)) > 0 else P[::-1]


bnd = E[cnt == 1]
_, lab = connected_components(coo_matrix((np.ones(len(bnd)), (bnd[:, 0], bnd[:, 1])), shape=(nv, nv)), directed=False)
lb = lab[bnd[:, 0]]; main = lb == np.bincount(lb).argmax()
rim_edges = bnd[main]; zero = np.unique(rim_edges)
one = np.nonzero(np.linalg.norm(V - TIP, axis=1) < 0.015)[0]
I, J, W = [], [], []
for k in range(3):
    i, j, o = F[:, k], F[:, (k + 1) % 3], F[:, (k + 2) % 3]
    a, b = V[i] - V[o], V[j] - V[o]
    w = np.clip((a * b).sum(1) / np.maximum(np.linalg.norm(np.cross(a, b), axis=1), 1e-12), 1e-3, 50) / 2
    I += [i, j]; J += [j, i]; W += [w, w]
L = coo_matrix((np.concatenate(W), (np.concatenate(I), np.concatenate(J))), shape=(nv, nv)).tocsr()
L = L - coo_matrix((np.asarray(L.sum(1)).ravel(), (np.arange(nv), np.arange(nv)))).tocsr()
fixed = np.zeros(nv, bool); fixed[zero] = fixed[one] = True; ub = np.zeros(nv); ub[one] = 1.0
free = np.nonzero(~fixed)[0]; u = ub.copy()
u[free] = spsolve(L[free][:, free].tocsc(), -L[free][:, fixed].dot(ub[fixed]))

levels = np.unique(np.r_[np.quantile(u, np.linspace(0.01, 0.995, NLEV)), np.linspace(0.9, 0.995, 30)])
loops = {}
for lv in levels:
    P = level_loop(u, lv)
    if P is not None and len(P) > 12:
        loops[lv] = toward(smooth(P), TIP)
lv_ok = sorted(loops)
R0 = smooth(loops[lv_ok[0]], 12)                                   # first ring: the level line next to the rim (the rim itself pinches)
per = lambda P: np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1).sum()
s = np.r_[0, np.cumsum([np.median(np.linalg.norm(loops[b][::5][:, None] - loops[a][::5][None], axis=2).min(1))
                       for a, b in zip(lv_ok, lv_ok[1:])])]
print("rim perimeter %.3f m" % per(R0), "levels", len(lv_ok), "s total %.3f m" % s[-1])
plan, cur, k, n = [], 0.0, 0, COUNTS[0]
while True:
    nxt = cur + max((plan[-1][1] if plan else per(R0)) / n, STEP_MIN)
    j = int(np.searchsorted(s, nxt))
    if j >= len(lv_ok) - 2:
        break
    P = loops[lv_ok[j]]
    if k + 1 < len(COUNTS) and per(P) / n < MIN_EDGE:
        k += 1; n = COUNTS[k]
    plan.append((n, per(P), resample(P, n)[0])); cur = s[j]
rings = [resample(R0, COUNTS[0])[0]] + [p[2] for p in plan]
np.savez(D / (NAME + "_rings.npz"), counts=np.array([len(r) for r in rings]), tip=TIP, flat=np.vstack(rings),
         sizes=np.array([len(r) for r in rings]))
print("rings", len(rings), "counts", [len(r) for r in rings], "perimeters", [round(p[1], 2) for p in plan])
