"""Hat (sock cap) outer shell, hand-retopo style: concentric rings from the opening to the drooping tip, like the knit
rows of a sock cap. The ring positions come from hat_field.py (level lines on the outer cloth, draft/hat_rings.npz);
here they become vertices snapped on the reference and quads only:
  lid 12 x 12 (closed underneath) | mouth 48 -> rings 48 -> 4:2 band -> 24 -> 4:2 band -> 12 -> tip vertex (6 quads)
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hat_outer.py"""
import sys
import numpy as np
sys.path.insert(0, r"C:\Users\epers\Desktop\retopologizer\tools\02-retopologia")
import importlib, retopo
importlib.reload(retopo)
from retopo import *
from mathutils import Vector

D = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft"
d = np.load(D + r"\hat_rings.npz")
counts, sizes, TIP = d["counts"], d["sizes"], Vector(d["tip"])
pts = np.split(d["flat"], np.cumsum(sizes)[:-1])
R = Ref("HiPoly")
T = Topo(R)


def band(Aa, Cc):
    """4:2 reduction around a closed ring, 3 quads per group: a 3-pole on the wide ring, a 5-pole on the narrow one."""
    for g in range(len(Cc) // 2):
        a = [Aa[(4 * g + i) % len(Aa)] for i in range(5)]; c = [Cc[(2 * g + i) % len(Cc)] for i in range(3)]
        T.f(a[0], a[1], c[1], c[0]); T.f(a[1], a[2], a[3], c[1]); T.f(a[3], a[4], c[2], c[1])


rings, prev = [], None
for P in pts:
    P = [Vector(p) for p in P]
    if prev is not None:                       # same start and turn as the ring before (every 2nd vertex on a band)
        P = align(P, prev if len(prev) == len(P) else prev[::len(prev) // len(P)])
    rings.append(T.vs(P, snap=len(rings) > 0)); prev = P
for Aa, Cc in zip(rings, rings[1:]):
    if len(Aa) == len(Cc):
        T.strip(Aa, Cc, closed=True)
    else:
        band(Aa, Cc)
T.fan(rings[-1], TIP)
T.relax([v for v in T.bm.verts if v not in rings[0]], iters=3, k=0.4)


def lid(ring):
    """Closes the opening underneath (nobody sees it): a 12 x 12 quad grid over the 48-ring, not snapped (it spans
    air). The grid's bottom side is the quarter of the ring lowest in z (the back of the opening)."""
    q = len(ring) // 4
    s = min(range(len(ring)), key=lambda s: sum(ring[(s + i) % len(ring)].co.z for i in range(q + 1)))
    r = [ring[(s + i) % len(ring)] for i in range(len(ring))] + [ring[s]]
    T.grid(r[0:q + 1], r[3 * q:2 * q - 1:-1], r[4 * q:3 * q - 1:-1], r[q:2 * q + 1], snap=False)


lid(rings[0])
T.orient()
T.write("Hat_retopo")
result = topo_qa("Hat_retopo", R)
