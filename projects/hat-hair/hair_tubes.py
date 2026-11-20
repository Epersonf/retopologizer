"""Hair locks as separate swept tubes (normal python + numpy, no Blender, runs in seconds). One closed quad tube per spine of
hair_locks.py: rings of 6/8 verts along the smoothed spine, radius from the EDT radius (smoothed), a 3/4-quad cap vertex at both
ends. Faces are wound outward by construction and checked per face. Tubes are separate objects (hair_connect.py makes each reach what it grows from). Spines: draft/hair_locks.npz, then the new
ones of draft/hair_locks_z.npz.
Radius never below 0.75 x the median or RMIN (2.4 cm): no thin necks, no thin pins (strands under RDROP are dropped). A FREE tip
tapers over its last 30 % only to TIP (0.65) of the radius and ends in a flat-ish cap (0.25 r), never a point; a tip that was made to reach something (hair_connect.py) keeps its full radius. Ring spacing grows (x1.08 steps) until the
quad total fits BUDGET.
  python -I projects/hat-hair/hair_tubes.py [min_len_m=0.06] [budget_quads=820]   ->  draft/hair_tubes.npz, output/hair_tubes.obj"""
import sys, json
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree

MIN_LEN = float(sys.argv[1]) if len(sys.argv) > 1 else 0.06
BUDGET = int(sys.argv[2]) if len(sys.argv) > 2 else 820
TIP = 0.65
RMIN = 0.024                                       # no tube thinner than 2.4 cm radius; strands thinner than RDROP are dropped
RDROP = 0.013
H = Path(__file__).resolve().parent
EXT = json.loads((H / "draft" / "hair_ext.json").read_text()) if (H / "draft" / "hair_ext.json").exists() else {}   # {index: [root_ext_m, tip_ext_m, root_point|null, tip_point|null]}


def smooth(a, k=2):
    for _ in range(k):
        b = a.copy(); b[1:-1] = (a[:-2] + 2 * a[1:-1] + a[2:]) / 4; a = b
    return a


def tube(p, r, k=1.0, e0=0.0, e1=0.0, p0=None, p1=None):
    """e0 / e1: metres the spine is extended at the root / tip (so the tube reaches into what it grows from); p0 / p1: instead,
    points the root / tip must pass through, in order along the curve (hair_connect.py: [inside the parent, just outside it on its normal]: the tube leaves its parent perpendicular)."""
    u0 = (p[0] - p[1]) / np.linalg.norm(p[0] - p[1]); u1 = (p[-1] - p[-2]) / np.linalg.norm(p[-1] - p[-2])
    a0 = p[:1] + u0 * e0 if p0 is None else np.array(p0, float).reshape(-1, 3); a1 = p[-1:] + u1 * e1 if p1 is None else np.array(p1, float).reshape(-1, 3)
    p = np.vstack([a0, p, a1]); r = np.r_[[r[0]] * len(a0), r, [r[-1]] * len(a1)]
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    r = smooth(np.maximum(r.astype(float), max(0.75 * np.median(r), RMIN)), 2); n = 8 if np.median(r) >= 0.032 else 6
    step = k * max(0.025, 2 * np.pi * np.median(r) / n); m = max(3, int(round(L[-1] / step)) + 1)
    t = np.linspace(0, L[-1], m)
    c = smooth(np.stack([np.interp(t, L, p[:, i]) for i in range(3)], 1), 2); rr = np.interp(t, L, r)
    if p1 is None:                                                                  # only a free tip tapers, never a junction
        s = t / t[-1]; rr = rr * (1 - (1 - TIP) * np.clip((s - 0.7) / 0.3, 0, 1))
    rr = np.maximum(rr, 0.55 * rr.max())                                            # no end thinner than 55 % of the fattest ring
    d = np.gradient(c, axis=0); d /= np.linalg.norm(d, axis=1)[:, None]
    u = np.cross(d[0], [0, 0, 1.0]); u = u if np.linalg.norm(u) > 1e-3 else np.cross(d[0], [1.0, 0, 0])
    V = []
    for i in range(m):
        u = u - d[i] * u.dot(d[i]); u /= np.linalg.norm(u); w = np.cross(d[i], u)       # u x w = d (right-handed)
        a = 2 * np.pi * np.arange(n) / n
        V.append(c[i] + rr[i] * (np.cos(a)[:, None] * u + np.sin(a)[:, None] * w))
    V = np.vstack(V + [c[-1] + d[-1] * 0.25 * rr[-1], c[0] - d[0] * 0.25 * rr[0]]); tip, root = m * n, m * n + 1
    F = [[i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k] for i in range(m - 1) for k in range(n)]
    F += [[tip, (m - 1) * n + 2 * j, (m - 1) * n + 2 * j + 1, (m - 1) * n + (2 * j + 2) % n] for j in range(n // 2)]
    F += [[root, (2 * j + 2) % n, 2 * j + 1, 2 * j] for j in range(n // 2)]
    F = np.array(F); ctr = V[F].mean(1); near = np.argmin(((ctr[:, None] - c[None]) ** 2).sum(2), 1)
    nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 3]] - V[F[:, 0]])
    bad = (nrm * (ctr - c[near])).sum(1) < 0                                           # report only: windings are built consistent
    return V, F, int(bad.sum())                                                   # faces the nearest-axis test disagrees with


spines = []                                                      # geodesic spines first, then those of the z mode that are new
for f in ("hair_locks.npz", "hair_locks_z.npz"):
    if (H / "draft" / f).exists():
        S = np.load(H / "draft" / f)
        for j in range(int(S["n"])):
            p_, r_ = S["p%d" % j], S["r%d" % j]
            new = not spines or np.mean([tree.query(q)[0] < 0.015 for q in p_ for tree in [cKDTree(np.vstack([s[1] for s in spines]))]]) < 0.7
            if np.linalg.norm(np.diff(p_, axis=0), axis=1).sum() >= MIN_LEN and np.median(r_) >= RDROP and new:
                spines.append((len(spines), p_, r_))
from hair_chain import chain
joined = chain([(p, r) for _, p, r in spines])                  # pieces that continue each other become one spine
print("spines", len(spines), "->", len(joined), "after joining chains")
spines = [(n, p, r) for n, (p, r) in enumerate(joined)]
k = 1.0
while True:
    built = [(i,) + tube(p, r, k, *EXT.get(str(i), [1.6 * float(r[0]), 0.0, None, None])) for i, p, r in spines]
    tot = sum(len(F) for _, _, F, _ in built)
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
