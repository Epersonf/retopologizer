"""N-sided quad patches with one pole in the middle (how an artist fills a 3- or 5-sided hole with quads only).
  s = solve_spokes([5, 4, 3, 5, 3])           # edges per side -> edges per spoke (side k: n_k = s[k-1] + s[k+1])
  poly_patch(T, sides, s, centre)              # sides[k] = vertex chain from corner k to corner k+1
The centre vertex gets valence N (5-pole or 3-pole); every sub-patch at a corner is a Coons grid.
Side k is split at Q_k, s[k-1] edges after its first corner; spoke k joins the centre to Q_k with s[k] edges."""
import numpy as np
from .curves import line


def solve_spokes(ns):
    n = len(ns); A = np.zeros((n, n))
    for k in range(n):
        A[k, (k - 1) % n] += 1; A[k, (k + 1) % n] += 1
    s = np.linalg.lstsq(A, np.array(ns, float), rcond=None)[0]
    si = [int(round(x)) for x in s]
    if any(x < 1 for x in si) or any(si[(k - 1) % n] + si[(k + 1) % n] != ns[k] for k in range(n)):
        raise ValueError(f"no valid spokes for sides {ns}: {np.round(s, 2).tolist()}")
    return si


def poly_patch(T, sides, s, centre, nrm=None, vias=None, inside=None):
    """Fill an N-sided region. sides: N chains of BMVerts, each starting at the corner where the previous ended.
    vias: {k: [points]} waypoints for spoke k (e.g. over the top of a shoulder). inside: a point inside the volume
    that sees the region: spokes and grids are then projected from it (see Topo.grid). Returns (pole, spokes)."""
    n = len(sides)
    for k in range(n):
        assert sides[k][-1] is sides[(k + 1) % n][0], f"side {k} does not end where side {k + 1} starts"
        assert len(sides[k]) - 1 == s[(k - 1) % n] + s[(k + 1) % n], f"side {k}: {len(sides[k]) - 1} edges"
    P = T.v(centre, nrm)
    Q = [sides[k][s[(k - 1) % n]] for k in range(n)]
    spokes = []
    for k in range(n):
        pts = line(T.ref, P.co, Q[k].co, s[k], nrm, via=(vias or {}).get(k, ()), center=inside)
        spokes.append([P] + T.vs(pts[1:-1], nrm, snap=inside is None) + [Q[k]])
    for k in range(n):
        j = (k + 1) % n
        B = sides[k][s[(k - 1) % n]:]                 # Q_k -> corner k+1
        R = sides[j][:s[k] + 1]                       # corner k+1 -> Q_{k+1}
        L = spokes[k][::-1]                           # Q_k -> centre
        Tp = spokes[j]                                # centre -> Q_{k+1}
        T.grid(B, Tp, L, R, center=inside)
    return P, spokes
