"""Hand-drawn locks -> Bezier control points (normal python + numpy): the second step of the hybrid. For every lock of hair_locks_def.py:
1. the polyline (azimuth, height) is resampled every 1 cm and snapped to the nearest crest of the height field (the highest radius within
   SNAP degrees), then smoothed; 2. the surface radius r comes from hair_radial.npz; the radius of the lock is its half width, at least half of how far it stands proud of the base
   (hair_radial_base.npz) so it is half buried, else RHO (OPT[name]["rho"] overrides); the axis is that radius deeper (the tube's crest is the surface),
   the radius tapers over the last 30 % to TIP of its value; 3. Douglas-Peucker keeps the control points that matter (TOL), none closer than MINSEG to its neighbour.
Writes draft/hair_curves.json: [{name, pts [[x,y,z]..], rad [..], sides}] root first. hair_curves_build.py makes the Blender curves from it.
  python -I projects/hat-hair/hair_curves.py [only,names]"""
import json, sys
import numpy as np
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H))
from hair_locks_def import LOCKS, OPT, RHO
SNAP = 5.0; TOL = 0.008; MINSEG = 0.04; TIP = 0.65; STEP = 0.01; RMIN = 0.025; RMAX = 0.042
d = np.load(H / "draft" / "hair_radial.npz"); R, zs, A = d["R"], d["zs"], d["A"]; nt = R.shape[0]; dz = zs[1] - zs[0]
B = H / "draft" / "hair_radial_base.npz"; Rb = np.load(B)["R"] if B.exists() else None            # the base seen the same way (hair_build.py): how far each lock stands proud of it
Rs = R.copy()
for _ in range(2):                                                       # smoothed along the azimuth for the crest search
    Rs = (np.roll(Rs, 1, 0) + 2 * Rs + np.roll(Rs, -1, 0)) / 4


def at(M, th, z):                                                        # nearest finite sample around (azimuth deg, z): the cell, else its 5x5 neighbourhood
    i = int(round(th * nt / 360)) % nt; j = int(np.clip(round((z - zs[0]) / dz), 0, len(zs) - 1))
    for w in (0, 2, 5):
        v = M[np.ix_(np.arange(i - w, i + w + 1) % nt, np.arange(max(j - w, 0), min(j + w + 1, len(zs))))]; v = v[np.isfinite(v)]
        if v.size:
            return float(np.median(v)) if w else float(v[0])
    return np.nan


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


def thin(k, P, gap):                                                      # drop control points closer than `gap` to the last kept one (the end point stays)
    out = [k[0]]
    for i in k[1:-1]:
        if np.linalg.norm(P[i] - P[out[-1]]) >= gap and np.linalg.norm(P[k[-1]] - P[i]) >= gap:
            out.append(i)
    return out + [k[-1]]


def lock(name, pts):
    p = np.array(pts, float); arc = np.r_[0, np.cumsum(np.hypot(np.diff(p[:, 0]) * np.pi / 180 * 0.2, np.diff(p[:, 1])))]      # arc length, azimuth scaled by r = 0.2
    s = np.arange(0, arc[-1], STEP); th = np.interp(s, arc, p[:, 0]); z = np.interp(s, arc, p[:, 1])
    for k in range(len(s)):                                              # snap to the crest of the surface within SNAP degrees
        c = [(at(Rs, th[k] + o, z[k]), o) for o in np.arange(-SNAP, SNAP + 0.1, 1.0)]; c = [x for x in c if np.isfinite(x[0])]
        if c:
            best = max(c); th[k] += best[1] if abs(best[1]) < SNAP else 0.0
    for _ in range(3):                                                   # smooth the snapped azimuth along the lock (ends stay)
        th[1:-1] = (th[:-2] + 2 * th[1:-1] + th[2:]) / 4
    r = np.array([at(R, a, b) for a, b in zip(th, z)]); ok = np.isfinite(r); r = np.interp(np.arange(len(r)), np.nonzero(ok)[0], r[ok])
    rb = np.array([at(Rb, a, b) for a, b in zip(th, z)]) if Rb is not None else np.full(len(s), np.nan); proud = np.where(np.isfinite(rb), r - rb, 0.06)   # how far the surface stands out of the base
    rho = OPT.get(name, {}).get("rho") or float(np.clip(max(RHO, 0.5 * np.mean(proud) + 0.012), RMIN, RMAX)); t = np.linspace(0, 1, len(s)); rad = rho * (1 - (1 - TIP) * np.clip((t - 0.7) / 0.3, 0, 1))
    a = r - rad; ang = np.radians(th); P = np.column_stack([A[0] + a * np.sin(ang), A[1] + a * np.cos(ang), z])
    k = thin(dp(P, TOL), P, MINSEG); vis = float(np.mean(a + rad > np.where(np.isfinite(rb), rb, 0) + 0.005))
    return {"name": name, "pts": P[k].round(5).tolist(), "rad": rad[k].round(5).tolist(), "sides": OPT.get(name, {}).get("sides", 6), "visible": round(vis, 2)}


only = sys.argv[1].split(",") if len(sys.argv) > 1 else None
out = [lock(n, pts) for n, pts in LOCKS.items() if only is None or n in only]
(H / "draft" / "hair_curves.json").write_text(json.dumps(out))
for c in out:
    P = np.array(c["pts"]); print("%-4s %2d control points, length %.2f m, radius %.1f..%.1f cm, %d%% of it stands out of the base" % (c["name"], len(P), np.linalg.norm(np.diff(P, axis=0), axis=1).sum(), min(c["rad"]) * 100, max(c["rad"]) * 100, 100 * c["visible"]))
