"""ring_tube: closed tube along a curved band that is open on one side (headband, bracelet, collar, belt strap).
The spine is the centroid of angular slices of the ref (so it works on a thin horseshoe where `track` has nothing to follow);
each ring is the angular hull of a thin slab of the ref, on the PCA major axis of the slab, so the tube keeps the real
(flat, oval, bean) section instead of a circle. Used for the Curupira headband (448 tris): docs/02-retopology/retopo-ring-tubes.md."""
import math
import numpy as np
from mathutils import Vector


def arc_spine(V, gap_dir=(0.0, -1.0), bins=180, min_pts=50, smooth=2):
    """Spine points of an arc around the vertical (Z) axis. V: Nx3 ref vertices in world space; gap_dir: XY direction of the
    opening (the seam of the angle is put there, so the spine starts and ends at the two tips of the arc)."""
    cen = V[:, :2].mean(0)
    ang = np.arctan2(V[:, 1] - cen[1], V[:, 0] - cen[0]) - math.atan2(gap_dir[1], gap_dir[0])
    ang = ang % (2 * np.pi)
    idx = np.minimum((ang / (2 * np.pi) * bins).astype(int), bins - 1)
    used = [b for b in range(bins) if (idx == b).sum() > min_pts]
    sp = np.array([V[idx == b].mean(0) for b in used])
    out = sp.copy()
    for i in range(len(sp)):
        out[i] = sp[max(0, i - smooth):i + smooth + 1].mean(0)
    out[0], out[-1] = sp[0], sp[-1]
    return out


def resample_path(P, n):
    t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    u = np.linspace(0, t[-1], n)
    return np.stack([np.interp(u, t, P[:, k]) for k in range(3)], 1)


def hull_section(V, c, d, n_sides, prev_u=None, slab=0.004, reach=0.06, window_deg=14):
    """One ring: ref points within `slab` of the plane (c, d) and within `reach` of c, projected on the plane; the ring radius at
    each of the n_sides angles is the farthest point inside +-window_deg. `reach` rejects the other tip of the arc.
    Returns (points as Vectors, u) where u is the major axis (sign kept continuous with prev_u)."""
    off = V - c
    P = off[(np.abs(off @ d) < slab) & (np.linalg.norm(off, axis=1) < reach)]
    P = P - np.outer(P @ d, d)
    u = np.linalg.eigh(np.cov(P.T))[1][:, -1]
    u = u - d * (u @ d)
    u /= np.linalg.norm(u)
    if prev_u is not None and u @ prev_u < 0:
        u = -u
    w = np.cross(d, u)
    X, Y = P @ u, P @ w
    th, rr = np.arctan2(Y, X), np.hypot(X, Y)
    pts = []
    for k in range(n_sides):
        t0 = 2 * math.pi * k / n_sides
        m = np.abs((th - t0 + math.pi) % (2 * math.pi) - math.pi) < math.radians(window_deg)
        r = rr[m].max() if m.any() else rr.mean()
        pts.append(Vector(c + (u * math.cos(t0) + w * math.sin(t0)) * r))
    return pts, u


def ring_tube(T, V, n_rings=28, n_sides=8, **spine_kw):
    """Builds the tube into Topo `T` (rings + strips + a fan cap at each tip) and returns the list of rings.
    Call T.orient() and T.write(name) afterwards, then topo_qa."""
    C = resample_path(arc_spine(V, **spine_kw), n_rings)
    tang = np.gradient(C, axis=0)
    tang /= np.linalg.norm(tang, axis=1)[:, None]
    rings, prev = [], None
    for i in range(n_rings):
        pts, prev = hull_section(V, C[i], tang[i], n_sides, prev)
        rings.append(T.vs(pts))
    for a, b in zip(rings, rings[1:]):
        T.strip(a, b, closed=True)
    for ring in (rings[0], rings[-1]):
        T.fan(ring, sum((Vector(v.co) for v in ring), Vector()) / len(ring))
    return rings
