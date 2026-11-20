"""Lock spines of the hair, found automatically (normal python + scipy; measurement only). The tips of the locks are the
maxima of the geodesic distance over the reference surface counted from the dome (hair_dome_faces.npz); a merge tree with
persistence (a tip counts if it stands >= PERSIST above the saddle where its lock joins a bigger one) separates real locks from
bumps. Each branch = the surface path tip -> saddle, then every sample is pulled onto the medial axis of the volume by climbing
the Euclidean distance transform (hair_outer.npz), so the spine runs along the middle of the tube. Writes draft/hair_locks.npz
(spine i: points (n,3), radius (n,), root point) and a numbered plot.
  python -I projects/hat-hair/hair_locks.py [persistence_m=0.05] [z]
With `z` the tips are the LOWEST points of the hair instead of the farthest from the dome, persistence counted in height: finds the
hanging strands whose ends are not far from the dome when measured over the surface (the geodesic mode merges them).
Written to draft/hair_locks_z.npz."""
import sys
import numpy as np
from pathlib import Path
from scipy import ndimage as ndi
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.csgraph import dijkstra

PERSIST = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
ZMODE = len(sys.argv) > 2 and sys.argv[2] == "z"
STEP = 0.010                                                          # spine sample spacing along a lock
D = Path(__file__).resolve().parent / "draft"
o = np.load(D / "hair_in.npz"); V, F = o["V"].astype(np.float64), o["F"]
_, first, inv = np.unique(np.round(V * 1e5).astype(np.int64), axis=0, return_index=True, return_inverse=True)
inv = inv.ravel(); V, F = V[first], inv[F]; nv = len(V)                # weld the UV-seam duplicates
src = np.unique(F[np.load(D / "hair_dome_faces.npz")["faces"]])
E = np.unique(np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0)
w = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
G = coo_matrix((np.r_[w, w, np.full(len(src), 1e-9)], (np.r_[E[:, 0], E[:, 1], src], np.r_[E[:, 1], E[:, 0], np.full(len(src), nv)])),
               shape=(nv + 1, nv + 1)).tocsr()
g, pred = dijkstra(G, directed=False, indices=nv, return_predecessors=True); g, pred = g[:nv], pred[:nv]
g[~np.isfinite(g)] = -1
print("welded verts", nv, "dome sources", len(src), "max geodesic %.2f m" % g.max())

A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(nv, nv))
ptr, nb = A.indptr, A.indices
hh = 0.6 - V[:, 2] if ZMODE else g                # height the merge tree runs on
order = np.argsort(-hh); parent = np.arange(nv); peak = np.arange(nv); done = np.zeros(nv, bool); tips = []


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x


for v in order:                                                       # merge tree: highest first, a vertex joins its higher neighbours
    if hh[v] < 0:
        break
    comps = {find(u) for u in nb[ptr[v]:ptr[v + 1]] if done[u]}
    done[v] = True
    if not comps:
        continue
    comps = sorted(comps, key=lambda c: -hh[peak[c]]); keep = comps[0]
    for c in comps[1:]:
        if hh[peak[c]] - hh[v] >= PERSIST:
            tips.append((peak[c], g[v]))                                # a tip that stands out: (peak vertex, saddle height)
        parent[c] = keep
    parent[v] = keep
tips.append((peak[find(order[0])], 0.0))                               # the highest peak ends at the dome
print("tips", len(tips))

solid = ~np.load(D / "hair_outer.npz")["ext"]; lo, H = np.load(D / "hair_outer.npz")["lo"], float(np.load(D / "hair_outer.npz")["H"])
edt = ndi.distance_transform_edt(solid) * H; gr = np.stack(np.gradient(edt, H), -1)
vox = lambda p: (p - lo) / H - 0.5
samp = lambda a, p: ndi.map_coordinates(a, vox(p).T, order=1, mode="nearest")


def to_axis(p):
    """Climb the distance transform from a surface point to the medial axis of the tube it sits on."""
    p = p.copy()
    for _ in range(40):
        gv = np.stack([samp(gr[..., k], p) for k in range(3)], -1); n = np.linalg.norm(gv, axis=1, keepdims=True)
        p = p + gv / np.maximum(n, 1e-9) * H * 0.5 * (n > 0.2)
    return p


out = []
for pk, sad in tips:
    path = [pk]
    while pred[path[-1]] >= 0 and pred[path[-1]] < nv and g[path[-1]] > sad:
        path.append(pred[path[-1]])
    P = V[path[::-1]]
    if len(P) < 4:
        continue
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; t = np.arange(0, s[-1], STEP)
    P = np.array([np.interp(t, s, P[:, k]) for k in range(3)]).T
    A_ = to_axis(P)
    for _ in range(3):
        A_[1:-1] = (A_[:-2] + 2 * A_[1:-1] + A_[2:]) / 4
    out.append((A_, samp(edt, A_), s[-1]))
out.sort(key=lambda x: -x[2])
np.savez(D / ("hair_locks_z.npz" if ZMODE else "hair_locks.npz"), n=len(out), **{"p%d" % i: a for i, (a, r, L) in enumerate(out)}, **{"r%d" % i: r for i, (a, r, L) in enumerate(out)})
for i, (a, r, L) in enumerate(out):
    print(i + 1, "len %.2f m" % L, "root", np.round(a[0], 3), "tip", np.round(a[-1], 3), "r %.1f..%.1f cm" % (r.min() * 100, r.max() * 100))
