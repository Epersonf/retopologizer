"""Joints on edge loops: a low-poly digit bends only where it has a ring of vertices, so a joint between two rings
leaves a bone with no vertices of its own (the heat skin gives it nothing). When a bone of the chain is empty, each
joint slides along the chain to the nearest ring of the chain's own vertices, when one is close."""
from collections import deque
import numpy as np

TOL = 0.2            # a joint moves at most this fraction of the chain's length
GAP = 0.06           # rings are separated by gaps of this fraction of the length (or more) along the chain
SPAN = 0.12          # a ring spans less than this along the chain
MIN_GAP = 0.15       # joints of a chain stay this fraction of its length apart


def snap_chain(M, P, tip, radius, first=0):
    """P: joints (k, 3) from the root to the tip; joints first..k-2 may move (the tip stays); tip: a vertex at the
    chain's tip; radius: of the tube around the chain that holds its vertices.
    Returns the joints moved onto the rings, and the ring positions (fractions of the chain)."""
    a, d = P[0], P[-1] - P[0]; L2 = float(d @ d)
    s = ((M.V - a) @ d) / L2
    r = np.linalg.norm(M.V - (a + s[:, None] * d), axis=1)
    inside = (s > -0.35) & (s < 1.15) & (r < radius)
    seen, q = {tip}, deque([tip])                     # this chain's vertices: reached from its tip inside the tube
    while q:
        v = q.popleft()
        for w in M.nbr[v]:
            if inside[w] and w not in seen:
                seen.add(w); q.append(w)
    idx = np.array(sorted(seen, key=lambda i: s[i]))
    cut = np.nonzero(np.diff(s[idx]) > GAP)[0] + 1
    rings = [g for g in np.split(idx, cut) if len(g) >= 3 and np.ptp(s[g]) < SPAN]
    rs = [float(s[g].mean()) for g in rings]
    t = [float((p - a) @ d / L2) for p in P]
    if all(((s[idx] >= t[k]) & (s[idx] < t[k + 1])).sum() >= 3 for k in range(len(P) - 2)):
        return P, rs                                   # every bone holds vertices of its own: nothing to fix
    for k in range(first, len(P) - 1):
        near = [x for x in rs if abs(x - t[k]) < TOL and (k == 0 or x > t[k - 1] + MIN_GAP) and x < t[-1] - MIN_GAP]
        if near:
            t[k] = min(near, key=lambda x: abs(x - t[k]))
    return np.array([a + x * d for x in t]), rs
