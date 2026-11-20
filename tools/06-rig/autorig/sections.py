"""Exact plane sections of a triangle mesh (numpy): the closed loops where a plane cuts it, each with its centroid,
area and points. Every cut point lies on a mesh edge, so loops are chained through shared edges (no tolerance)."""
import numpy as np


class Mesh:
    """World-space vertices V (n, 3) and triangles F (m, 3); E = unique edges, FE = the 3 edge ids of each triangle,
    nbr = vertex adjacency (for geodesics)."""

    def __init__(self, V, F):
        self.V, self.F = np.asarray(V, float), np.asarray(F, int)
        E = np.sort(np.stack([self.F[:, [0, 1]], self.F[:, [1, 2]], self.F[:, [2, 0]]], 1).reshape(-1, 2), axis=1)
        self.E, inv = np.unique(E, axis=0, return_inverse=True)
        self.FE = inv.reshape(-1, 3)
        self.nbr = [[] for _ in range(len(self.V))]
        for a, b in self.E:
            self.nbr[a].append(b); self.nbr[b].append(a)
        self.lo, self.hi = self.V.min(0), self.V.max(0)


class Loop:
    def __init__(self, P, n):
        self.P = P                                    # (k, 3) ordered points on the plane
        u = np.cross(n, [1.0, 0, 0] if abs(n[0]) < 0.9 else [0, 1.0, 0]); u /= np.linalg.norm(u); v = np.cross(n, u)
        x, y = P @ u, P @ v; x1, y1 = np.roll(x, -1), np.roll(y, -1); cr = x * y1 - x1 * y
        a = cr.sum() / 2
        if abs(a) < 1e-12:
            self.c, self.area = P.mean(0), 0.0
        else:
            cx, cy = ((x + x1) * cr).sum() / (6 * a), ((y + y1) * cr).sum() / (6 * a)
            off = P[0] - (x[0] * u + y[0] * v)       # plane offset (the part of P along n)
            self.c, self.area = cx * u + cy * v + off, abs(a)
        self._uv, self._xy = (u, v), np.stack([x, y], 1)
        self.r = float(np.sqrt(self.area / np.pi))   # radius of the circle with the same area
        self.size = float(max(np.ptp(x), np.ptp(y), np.ptp(x + y) / 1.4142, np.ptp(x - y) / 1.4142))   # widest extent

    def contains(self, q):
        """q (3D, on or near the plane) inside the polygon (even-odd rule)."""
        u, v = self._uv; px, py = np.dot(q, u), np.dot(q, v); x, y = self._xy[:, 0], self._xy[:, 1]
        x1, y1 = np.roll(x, -1), np.roll(y, -1)
        hit = ((y > py) != (y1 > py)) & (px < (x1 - x) * (py - y) / (y1 - y + 1e-30) + x)
        return bool(hit.sum() % 2)

    def extent(self, axis):
        s = self.P @ np.asarray(axis, float); return float(s.max() - s.min())


def section(M, p, n):
    """Closed loops where the plane (point p, normal n) cuts the mesh."""
    n = np.asarray(n, float); n = n / np.linalg.norm(n)
    d = (M.V - p) @ n
    d[np.abs(d) < 1e-9] = 1e-9
    s = d > 0; a, b = M.E[:, 0], M.E[:, 1]
    cross = s[a] != s[b]
    t = d[a] / np.where(cross, d[a] - d[b], 1.0)
    X = M.V[a] + (M.V[b] - M.V[a]) * t[:, None]
    fc = cross[M.FE]
    tri = fc.sum(1) == 2
    seg = M.FE[tri][fc[tri]].reshape(-1, 2)
    at = {}
    for i, (e0, e1) in enumerate(seg):
        at.setdefault(e0, []).append(i); at.setdefault(e1, []).append(i)
    used, loops = np.zeros(len(seg), bool), []
    for i0 in range(len(seg)):
        if used[i0]:
            continue
        chain, i, e = [seg[i0][0]], i0, seg[i0][1]
        used[i0] = True
        while True:
            chain.append(e)
            nxt = [j for j in at.get(e, []) if not used[j]]
            if not nxt:
                break
            i = nxt[0]; used[i] = True
            e = seg[i][1] if seg[i][0] == e else seg[i][0]
        if len(chain) > 3:                              # open chains too (holes in the mesh): closed by a straight edge
            loops.append(Loop(X[chain[:-1]] if chain[-1] == chain[0] else X[chain], n))
    return loops


def pick(loops, q, near=None):
    """The loop that contains q (smallest such), else the one whose centroid is nearest to q (within `near`)."""
    inside = [L for L in loops if L.contains(q)]
    if inside:
        return min(inside, key=lambda L: L.area)
    if not loops:
        return None
    best = min(loops, key=lambda L: np.linalg.norm(L.c - q))
    return best if near is None or np.linalg.norm(best.c - q) <= near else None
