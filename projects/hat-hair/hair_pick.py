"""Which pieces of the reference become locks, and their Bezier control points (normal python + numpy): the second step of the hybrid when the lock list
comes from the reference's own pieces (hair_pieces.py, hair_piece_axes.py) instead of hand-drawn polylines (hair_curves.py). The base (hair_base.py) is
the blockout; a piece is worth a tube where it stands PROUD of the base: its visible cells (the first hit of the horizontal rays of hair_radial.py) that are more
than PROUD metres farther out than the base (hair_radial_base.npz) or where the base is absent. Cost = the quads of its tube (SIDES x control points, rings only at
the control points). Greedy by proud cells per quad until QUADS are spent. The centreline of each (1.5 cm rings) is cut to control points by Douglas-Peucker
(TOL, none closer than MINSEG); the radius of a point is the half width a of the piece there (blunt: at least half of the biggest), the cross-section ratio is its half thickness b over
a (at least BMIN, at most round), `u` the wide axis laid along the scalp (tangent x away from the head centre), the points pushed in by the half thickness so the outer face is the surface. Writes draft/hair_curves.json like hair_curves.py, plus
{ratio, u, rank, proud}. The root end is the end nearer to the base surface (hair_curves_build.py decides, it has the BVH).
  python -I projects/hat-hair/hair_pick.py [QUADS=1100] [SIDES=6] [TOL=0.008] [MINSEG=0.03] [PROUD=0.01] [BMIN=0.008]"""
import json, sys
import numpy as np
from pathlib import Path
H = Path(__file__).resolve().parent / "draft"
kv = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a); QUADS = int(kv.get("QUADS", 1100)); SIDES = int(kv.get("SIDES", 6)); TOL = float(kv.get("TOL", 0.008)); MINSEG = float(kv.get("MINSEG", 0.03))
PROUD = float(kv.get("PROUD", 0.01)); BMIN = float(kv.get("BMIN", 0.008)); C = np.array([-0.185, -0.03, 0.30])            # the head centre
L = np.load(H / "hair_pieces.npz")["L"]; R = np.load(H / "hair_radial.npz")["R"]; Rb = np.load(H / "hair_radial_base.npz")["R"]; ax = json.load(open(H / "hair_piece_axes.json"))


def dp(P, tol):                                                          # Douglas-Peucker: indices of the points that matter
    keep = [0, len(P) - 1]; stack = [(0, len(P) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        u = P[b] - P[a]; u = u / (np.linalg.norm(u) + 1e-12); q = P[a + 1:b] - P[a]; dist = np.linalg.norm(q - np.outer(q @ u, u), axis=1); k = int(np.argmax(dist))
        if dist[k] > tol:
            keep.append(a + 1 + k); stack += [(a, a + 1 + k), (a + 1 + k, b)]
    return sorted(keep)


def thin(k, P, gap):                                                     # drop control points closer than `gap` to the last kept one (the end points stay)
    out = [k[0]]
    for i in k[1:-1]:
        if np.linalg.norm(P[i] - P[out[-1]]) >= gap and np.linalg.norm(P[k[-1]] - P[i]) >= gap:
            out.append(i)
    return out + [k[-1]]


def smooth(v, n=2):                                                      # [1 2 1] along the first axis, ends stay
    v = v.copy()
    for _ in range(n):
        v[1:-1] = (v[:-2] + 2 * v[1:-1] + v[2:]) / 4
    return v


proud = np.isfinite(R) & (~np.isfinite(Rb) | (R - Rb > PROUD)); cands = []
for p in ax:
    P = np.array(p["pts"]); a = smooth(np.array(p["a"])); b = smooth(np.array(p["b"])); n = int(((L == p["rank"]) & proud).sum()); k = thin(dp(P, TOL), P, MINSEG)
    if len(k) < 2 or n == 0:
        continue
    Q = P[k]; ak = np.maximum(a[k], 0.012); ak = np.maximum(ak, 0.5 * ak.max())                    # blunt ends: no radius under half of the biggest
    ratio = float(np.clip(max(np.median(b), BMIN) / max(float(np.median(a)), 1e-3), 0.1, 1.0)); t = np.gradient(Q, axis=0); t /= np.linalg.norm(t, axis=1)[:, None] + 1e-12
    r = Q - C; r /= np.linalg.norm(r, axis=1)[:, None]; u = np.cross(t, r); m = np.linalg.norm(u, axis=1)                  # the wide axis lies along the scalp: t x (away from the head centre)
    u /= m[:, None] + 1e-12; m0 = np.nonzero(m > 0.3)[0]
    for i in range(len(u)):                                                                          # lock pointing straight out of the head: keep the neighbour's axis
        if m[i] <= 0.3:
            u[i] = u[m0[np.argmin(abs(m0 - i))]] if len(m0) else np.cross(t[i], [0, 0, 1.0])
        if i and u[i] @ u[i - 1] < 0:
            u[i] = -u[i]
    nrm = r - (r * t).sum(1)[:, None] * t; nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12; Q = Q - nrm * (ratio * ak)[:, None]    # the outer face is the surface of the reference
    cands.append({"name": "p%03d" % p["rank"], "rank": p["rank"], "proud": n, "quads": SIDES * len(k), "pts": Q.round(5).tolist(), "rad": ak.round(4).tolist(), "ratio": round(ratio, 3),
                  "u": u.round(4).tolist(), "sides": SIDES})
out, spent, got = [], 0, 0
for c in sorted(cands, key=lambda c: -c["proud"] / c["quads"]):
    if spent + c["quads"] <= QUADS:
        out.append(c); spent += c["quads"]; got += c["proud"]
(H / "hair_curves.json").write_text(json.dumps(out))
print("%d pieces of %d candidates, %d quads, %.0f%% of the %d proud cells; control points %d..%d, half width %.1f..%.1f cm, ratio %.2f..%.2f" % (len(out), len(cands), spent, 100 * got / max(int(proud.sum()), 1), int(proud.sum()),
      min(len(c["pts"]) for c in out), max(len(c["pts"]) for c in out), 100 * min(min(c["rad"]) for c in out), 100 * max(max(c["rad"]) for c in out), min(c["ratio"] for c in out), max(c["ratio"] for c in out)))
