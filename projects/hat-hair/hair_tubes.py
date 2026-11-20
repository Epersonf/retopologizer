"""Hair locks as separate swept tubes (normal python + numpy, no Blender, runs in seconds). One closed quad tube per spine of
hair_locks.py: rings of 6/8 verts along the smoothed spine, radius from the EDT radius (smoothed), a 3/4-quad cap vertex at both
ends. Faces are wound outward by construction and checked per face. Tubes are NOT connected (each is its own object).
Tip taper: from half the length on, the radius falls linearly to TIP (0.3) of itself. Ring spacing grows (x1.08 steps) until the
quad total fits BUDGET.
  python -I projects/hat-hair/hair_tubes.py [min_len_m=0.06] [budget_quads=820]   ->  draft/hair_tubes.npz, output/hair_tubes.obj"""
import sys
import numpy as np
from pathlib import Path

MIN_LEN = float(sys.argv[1]) if len(sys.argv) > 1 else 0.06
BUDGET = int(sys.argv[2]) if len(sys.argv) > 2 else 820
TIP = 0.3
H = Path(__file__).resolve().parent
S = np.load(H / "draft" / "hair_locks.npz")


def smooth(a, k=2):
    for _ in range(k):
        b = a.copy(); b[1:-1] = (a[:-2] + 2 * a[1:-1] + a[2:]) / 4; a = b
    return a


def tube(p, r, k=1.0):
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    r = smooth(r.astype(float), 2); n = 8 if np.median(r) >= 0.032 else 6
    step = k * max(0.025, 2 * np.pi * np.median(r) / n); m = max(3, int(round(L[-1] / step)) + 1)
    t = np.linspace(0, L[-1], m)
    c = smooth(np.stack([np.interp(t, L, p[:, i]) for i in range(3)], 1), 2); rr = np.interp(t, L, r)
    s = t / t[-1]; rr = rr * np.where(s < 0.5, 1.0, 1 - (1 - TIP) * (s - 0.5) / 0.5)                  # taper to the tip
    d = np.gradient(c, axis=0); d /= np.linalg.norm(d, axis=1)[:, None]
    u = np.cross(d[0], [0, 0, 1.0]); u = u if np.linalg.norm(u) > 1e-3 else np.cross(d[0], [1.0, 0, 0])
    V = []
    for i in range(m):
        u = u - d[i] * u.dot(d[i]); u /= np.linalg.norm(u); w = np.cross(d[i], u)       # u x w = d (right-handed)
        a = 2 * np.pi * np.arange(n) / n
        V.append(c[i] + rr[i] * (np.cos(a)[:, None] * u + np.sin(a)[:, None] * w))
    V = np.vstack(V + [c[-1] + d[-1] * 0.6 * rr[-1], c[0] - d[0] * 0.6 * rr[0]]); tip, root = m * n, m * n + 1
    F = [[i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k] for i in range(m - 1) for k in range(n)]
    F += [[tip, (m - 1) * n + 2 * j, (m - 1) * n + 2 * j + 1, (m - 1) * n + (2 * j + 2) % n] for j in range(n // 2)]
    F += [[root, (2 * j + 2) % n, 2 * j + 1, 2 * j] for j in range(n // 2)]
    F = np.array(F); ctr = V[F].mean(1); near = np.argmin(((ctr[:, None] - c[None]) ** 2).sum(2), 1)
    nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 3]] - V[F[:, 0]])
    bad = (nrm * (ctr - c[near])).sum(1) < 0                                           # report only: windings are built consistent
    return V, F, int(bad.sum())                                                   # faces the nearest-axis test disagrees with


spines = [(i, S["p%d" % i], S["r%d" % i]) for i in range(int(S["n"]))
          if np.linalg.norm(np.diff(S["p%d" % i], axis=0), axis=1).sum() >= MIN_LEN]
k = 1.0
while True:
    built = [(i,) + tube(p, r, k) for i, p, r in spines]; tot = sum(len(F) for _, _, F, _ in built)
    if tot <= BUDGET:
        break
    k *= 1.08
out = {}; obj = []; off = 0
for i, V, F, flipped in built:
    out["v%d" % i], out["f%d" % i] = V, F
    obj.append("o Hair_tube_%02d" % (i + 1)); obj += ["v %.5f %.5f %.5f" % tuple(v) for v in V]
    obj += ["f " + " ".join(str(j + 1 + off) for j in f) for f in F]; off += len(V)
    print("tube %2d: %3d verts, %3d quads, faces failing outward test %d" % (i + 1, len(V), len(F), flipped))
np.savez(H / "draft" / "hair_tubes.npz", **out); (H / "output").mkdir(exist_ok=True)
(H / "output" / "hair_tubes.obj").write_text("\n".join(obj) + "\n"); print("total quads", tot, "spacing x%.2f" % k)
