"""Locks of the hair as ridge lines of the unrolled height field (normal python + numpy; measurement only): the first step of drawing a
Bezier curve on every lock. A crest is where the tangential normal n_t of hair_radial.npz changes sign from - to + along the azimuth
(the surface turns from facing left to facing right), a valley where it changes from + to -; crests of neighbouring heights are linked
into chains (a lock), each with the distance to the valleys on both sides (the lock's width) and the radius r of the surface. A jump
of r between neighbours (one lock passing in front of another) is not a crest.
Writes draft/hair_ridges.npz (chain k: c<k> = [theta_deg, z, r, half_width]); hair_unwrap.py draws them on the unrolled map.
  python -I projects/hat-hair/hair_ridges.py [min_height_m=0.10] [max_jump_deg=3]"""
import sys
import numpy as np
from pathlib import Path
H = Path(__file__).resolve().parent / "draft"
MINH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.10; JUMP = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
d = np.load(H / "hair_radial.npz"); R, NT_, NZ_, zs = d["R"], d["NT_"], d["NZ_"], d["zs"]; nt, nz = R.shape; dth = 360.0 / nt; dz = zs[1] - zs[0]


def sm(a):                                                          # [1 2 1] along the azimuth, NaN stays NaN
    return (np.roll(a, 1, 0) + 2 * a + np.roll(a, -1, 0)) / 4


S = sm(sm(NT_)); Rs = sm(R); JR = 0.012
crest, valley = [], []                                              # per row: [(theta_deg, r)], [theta_deg]
for j in range(nz):
    c, v = [], []
    for i in range(nt):
        k = (i + 1) % nt; a, b = S[i, j], S[k, j]
        if not (np.isfinite(a) and np.isfinite(b)) or abs(Rs[k, j] - Rs[i, j]) > JR:
            continue
        f = abs(a) / (abs(a) + abs(b) + 1e-12); th = (i + f) * dth
        if a < 0 <= b and b - a > 0.03:
            c.append((th, Rs[i, j] * (1 - f) + Rs[k, j] * f))
        elif a > 0 >= b:
            v.append(th)
    crest.append(c); valley.append(v)


def width(th, j):                                                   # half the distance between the valleys on both sides (degrees of azimuth)
    v = np.array(valley[j]);
    if len(v) < 2:
        return np.nan
    dd = (v - th + 180) % 360 - 180; lo, hi = dd[dd < 0], dd[dd > 0]
    return (hi.min() - lo.max()) / 2 if len(lo) and len(hi) else np.nan


chains = []; open_ = []                                             # open chain: list of (j, theta, r, half_width)
for j in range(nz):
    taken = set(); nxt = []
    for ch in open_:
        best = None
        for n, (th, r) in enumerate(crest[j]):
            dd = abs((th - ch[-1][1] + 180) % 360 - 180)
            if n not in taken and dd <= JUMP and abs(r - ch[-1][2]) < 0.03 and (best is None or dd < best[0]):
                best = (dd, n)
        if best:
            taken.add(best[1]); th, r = crest[j][best[1]]; ch.append((j, th, r, width(th, j))); nxt.append(ch)
        elif len(ch) * dz >= MINH:
            chains.append(ch)
    for n, (th, r) in enumerate(crest[j]):
        if n not in taken:
            nxt.append([(j, th, r, width(th, j))])
    open_ = nxt
chains += [c for c in open_ if len(c) * dz >= MINH]
out = {}
for k, ch in enumerate(chains):
    a = np.array(ch); out["c%d" % k] = np.column_stack([a[:, 1], zs[a[:, 0].astype(int)], a[:, 2], a[:, 3]])
np.savez(H / "hair_ridges.npz", n=len(chains), **out)
for k, ch in enumerate(chains):
    a = out["c%d" % k]; print("%2d  theta %5.1f..%5.1f  z %.2f..%.2f  r %.0f..%.0f cm  half-width %.1f deg" % (k, a[0, 0], a[-1, 0], a[:, 1].min(), a[:, 1].max(), a[:, 2].min() * 100, a[:, 2].max() * 100, np.nanmean(a[:, 3])))
