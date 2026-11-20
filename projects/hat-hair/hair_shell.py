"""Hair shell part, step 2 (normal python + scipy): selected faces -> a clean disk for hair_field.py. Close the cracks
and pinholes (CLOSE rings of faces), open away the thin ends (OPEN rings: strands narrower than ~2*OPEN faces go), keep
the main component, pick the top point (farthest from the rim). Reads draft/hair_<part>_faces.npz and hair_in.npz,
writes draft/hair_<part>_field_in.npz.
  python -I projects/hat-hair/hair_shell.py dome [CLOSE=4] [OPEN=0]"""
import sys
import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from pathlib import Path

PART = sys.argv[1]; CLOSE = int(sys.argv[2]) if len(sys.argv) > 2 else 4; OPEN = int(sys.argv[3]) if len(sys.argv) > 3 else 0
D = Path(__file__).resolve().parent / "draft"
o = np.load(D / "hair_in.npz"); V, N, F = o["V"].astype(np.float64), o["N"].astype(np.float64), o["F"]
sel = np.zeros(len(F), bool); sel[np.load(D / ("hair_%s_faces.npz" % PART))["faces"]] = True
_, first, inv = np.unique(np.round(V * 1e5).astype(np.int64), axis=0, return_index=True, return_inverse=True)   # the GLB splits
inv = inv.ravel(); Nw = np.zeros((len(first), 3)); np.add.at(Nw, inv, N)                                       # vertices at UV
V, N, F = V[first], Nw / np.maximum(np.linalg.norm(Nw, axis=1), 1e-12)[:, None], inv[F]                        # seams: weld them
B = csr_matrix((np.ones(F.size), (np.repeat(np.arange(len(F)), 3), F.ravel())), shape=(len(F), len(V)))
dil = lambda s: (B @ (B.T @ s.astype(np.float64))) > 0
for _ in range(CLOSE): sel = dil(sel)
for _ in range(CLOSE): sel = ~dil(~sel)                         # closing: fills the pinholes between ray samples
for _ in range(OPEN): sel = ~dil(~sel)
for _ in range(OPEN): sel = dil(sel)                            # opening: drops what is thinner than ~2*OPEN faces
Fs = F[sel]
g = coo_matrix((np.ones(Fs.size), (Fs.ravel(), np.roll(Fs, 1, 1).ravel())), shape=(len(V),) * 2)
_, lab = connected_components(g, directed=False); Fs = Fs[lab[Fs[:, 0]] == np.bincount(lab[Fs[:, 0]]).argmax()]
idx = np.unique(Fs); rm = -np.ones(len(V), np.int64); rm[idx] = np.arange(len(idx)); Fs = rm[Fs]; Vs, Ns = V[idx], N[idx]
e = np.sort(np.vstack([Fs[:, [0, 1]], Fs[:, [1, 2]], Fs[:, [2, 0]]]), 1)
ue, cnt = np.unique(e, axis=0, return_counts=True); be = ue[cnt == 1]
gb = coo_matrix((np.ones(len(be)), (be[:, 0], be[:, 1])), shape=(len(Vs),) * 2)
_, lb = connected_components(gb, directed=False); l0 = lb[be[:, 0]]
rim = np.unique(be[l0 == np.bincount(l0).argmax()])             # the longest boundary loop; the rest are small holes
dist = cKDTree(Vs[rim]).query(Vs)[0]
tip = Vs[np.argmax(dist)]
np.savez(D / ("hair_%s_field_in.npz" % PART), V=Vs, N=Ns, F=Fs, outer=np.ones(len(Vs), bool), tip=tip)
print(PART, "verts", len(Vs), "tris", len(Fs), "rim verts", len(rim), "boundary loops", len(np.unique(l0)),
      "tip", np.round(tip, 3), "tip->rim %.1f cm" % (dist.max() * 100))
