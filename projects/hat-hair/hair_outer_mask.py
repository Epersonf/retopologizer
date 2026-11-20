"""Outer surface of the hair reference, measured outside Blender (numpy + scipy): voxelize the reference, flood the air
from outside, keep the vertices whose surface faces that air. Hollow lumens and the inner walls of the locks are
dropped. Reads draft/hair_in.npz (hair_export.py); writes draft/hair_outer.npz (V, N, F of the outer faces, welded).
  python -I projects/hat-hair/hair_outer_mask.py"""
import numpy as np
from scipy import ndimage as ndi
from pathlib import Path

D = Path(__file__).resolve().parent / "draft"
H = 0.003                                           # voxel size, m
d = np.load(D / "hair_in.npz"); V, N, F = d["V"].astype(np.float64), d["N"].astype(np.float64), d["F"]
lo = V.min(0) - 12 * H; shape = np.ceil((V.max(0) + 12 * H - lo) / H).astype(int)
vox = lambda P: np.clip(np.floor((P - lo) / H).astype(int), 0, shape - 1)
wall = np.zeros(shape, bool)
T = V[F]
for w in ((1/3, 1/3, 1/3), (.5, .5, 0), (0, .5, .5), (.5, 0, .5), (.8, .1, .1), (.1, .8, .1), (.1, .1, .8)):
    i = vox(T[:, 0] * w[0] + T[:, 1] * w[1] + T[:, 2] * w[2]); wall[i[:, 0], i[:, 1], i[:, 2]] = True
wall = ndi.binary_dilation(wall, iterations=1)
air, n = ndi.label(~wall)
ext = air == air[0, 0, 0]
off = vox(V + N * 2.2 * H)
out = ext[off[:, 0], off[:, 1], off[:, 2]]
keep = out[F].all(1); Fo = F[keep]
idx = np.unique(Fo); rm = -np.ones(len(V), np.int64); rm[idx] = np.arange(len(idx))
np.savez(D / "hair_outer.npz", V=V[idx].astype(np.float32), N=N[idx].astype(np.float32), F=rm[Fo].astype(np.int32),
         lo=lo, H=H, shape=shape, ext=ext, wall=wall)
print("voxel grid", shape, "air components", n, "outer verts", len(idx), "of", len(V), "tris", len(Fo), "of", len(F))
