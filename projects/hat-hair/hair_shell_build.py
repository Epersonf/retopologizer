"""Hair shell part, step 4 (Blender worker): rings from hair_field.py (draft/hair_<PART>_rings.npz) become vertices on the
reference and quads only: rim 48 -> rings 48 -> 4:2 band -> 24 -> 4:2 band -> 12 -> top vertex (6 quads). The rim stays
open. Set PART before running; writes the object "Hair_<PART>" and returns topo_qa.
  PART = "dome"; exec(open(".../hair_shell_build.py").read())"""
import sys
import numpy as np
sys.path.insert(0, r"C:\Users\epers\Desktop\retopologizer\tools\02-retopologia")
import importlib, retopo
importlib.reload(retopo)
from retopo import *
from mathutils import Vector

PART = globals()["PART"]
d = np.load(r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft\hair_%s_rings.npz" % PART)
sizes, TIP = d["sizes"], Vector(d["tip"])
pts = np.split(d["flat"], np.cumsum(sizes)[:-1])
R = Ref("HairFull")
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
    rings.append(T.vs(P, snap=False)); prev = P
for Aa, Cc in zip(rings, rings[1:]):
    if len(Aa) == len(Cc):
        T.strip(Aa, Cc, closed=True)
    else:
        band(Aa, Cc)
T.fan(rings[-1], TIP)
T.relax([v for v in T.bm.verts if v not in rings[0]], iters=3, k=0.4)
T.orient()
T.write("Hair_" + PART)
result = topo_qa("Hair_" + PART, R)
