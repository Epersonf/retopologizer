"""What the joint rules read from the mesh: height H above the ground z0, the mirror plane x0, horizontal sections
(cached, one every H/200) and the tips found by geodesic distance from the belly: head top, hands, feet and a tail.
The character stands along +Z, faces -Y and its LEFT is +X (Mixamo's frame), arms in T- or A-pose."""
import numpy as np
from .sections import section, pick
from . import geodesic as G

N = 200                                            # horizontal levels
TIP = 0.12                                         # a tip stands this much (H) above the saddle to a farther one


class Body:
    def __init__(self, M):
        self.M, self.z0, self.H = M, float(M.lo[2]), float(M.hi[2] - M.lo[2])
        self.x0, self.dz, self._lv = float(M.lo[0] + M.hi[0]) / 2, self.H / N, {}
        self.tips = tips(self)

    def z(self, f):
        return self.z0 + f * self.H

    def zi(self, i):
        return self.z0 + (i + 0.5) * self.dz

    def index(self, z):
        return int(np.clip(round((z - self.z0) / self.dz - 0.5), 0, N - 1))

    def level(self, i):
        if i not in self._lv:
            self._lv[i] = section(self.M, np.array([self.x0, 0.0, self.zi(i)]), (0, 0, 1))
        return self._lv[i]

    def centre(self, i):
        """The biggest loop of level i on the mirror plane (torso, neck or head; not a skirt flap or a snout)."""
        loops = self.level(i)
        mid = [L for L in loops if abs(L.c[0] - self.x0) < 0.05 * self.H]
        return max(mid, key=lambda L: L.area) if mid else min(loops, key=lambda L: abs(L.c[0] - self.x0), default=None)

    def track(self, i, q, step, stop, near=0.05):
        """Follow the tube around q (x, y) level by level from level i (step +1 up, -1 down) until stop(loop,
        previous loop) or the tube ends: ([(level, loop)], the level where it stopped)."""
        out, q = [], np.array([q[0], q[1], 0.0])
        while 0 <= i < N:
            q[2] = self.zi(i)
            L = pick(self.level(i), q, near * self.H)
            if L is None or (out and stop(L, out[-1][1])):
                break
            out.append((i, L)); q = L.c.copy(); i += step
        return out, i


def tips(B):
    """{"top": v, "hands": {side: v}, "feet": {side: v}, "tail": v or None}: vertex ids, side = +1 left (x > x0),
    -1 right. Hands are the tips farthest to the sides, feet the ones on the ground, a tail the one far behind."""
    M, H = B.M, B.H
    belly = B.centre(B.index(B.z(0.5))).c
    D = G.dijkstra(M, [int(np.argmin(np.linalg.norm(M.V - belly, axis=1)))])
    out = {"top": int(np.argmax(M.V[:, 2])), "hands": {}, "feet": {}, "tail": None}
    for v, p in G.peaks(M, D, TIP * H):
        x, y, z = M.V[v]; side = 1 if x > B.x0 else -1
        if z > B.z(0.3) and abs(x - B.x0) > 0.25 * H:
            if side not in out["hands"] or abs(x - B.x0) > abs(M.V[out["hands"][side], 0] - B.x0):
                out["hands"][side] = v
        elif z < B.z(0.12) and y < belly[1] + 0.15 * H:
            out["feet"].setdefault(side, v)
        elif out["tail"] is None and abs(x - B.x0) < 0.08 * H and y > belly[1] + 0.15 * H and z < B.z(0.7):
            out["tail"] = v
    return out


def faces_back(B):
    """True when the toes point to +Y: the model faces +Y and has to be turned around (the rules expect -Y)."""
    i, d = B.index(B.z(0.15)), []
    for v in B.tips["feet"].values():
        toe = B.M.V[v]
        shin = min(B.level(i), key=lambda L: np.linalg.norm(L.c[:2] - toe[:2])).c
        d.append(toe[1] - shin[1])
    return bool(d) and float(np.mean(d)) > 0
