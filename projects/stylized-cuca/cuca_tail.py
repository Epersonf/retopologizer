"""Tail (half, x >= 0, on the mirror plane) with its dorsal scutes, segmented the way an artist does it: one segment
per scute. A half ring (6 edges, 12 around with the Mirror) sits in every gap between two scutes (GAPS_Y: the sharp
dips of the dorsal height along the spine), plus one hidden under the skirt (left open: L["tail_top"]); no ring
between the scutes or after the last one (the tip closes the last segment).
Half ring: seam top, column 1 (the band edge, just outside the scutes), then 5 even columns to the seam below.
Scute: a ridge of 2 seam vertices raised to the scute top, 2 base vertices on column 1; the strip between columns
1 and 2 takes the 2 extra vertices with a fan (a 3-pole on column 1, a 5-pole on column 2). Tip: 1 vertex, 3 quads."""
import math
from mathutils import Vector

START, DIR = Vector((0, 0.06, 0.40)), Vector((0, 0.35, -1))     # inside the tail, under the skirt
TIP = Vector((0, 0.4255, 0.0381))
BAND = 16.0                                                     # column 1, degrees from the top
GAPS_Y = [0.0886, 0.1154, 0.1633, 0.2026, 0.2383, 0.2776, 0.317, 0.351]   # gaps between scutes (sharp dips of the
RIDGE = (0.3, 0.75)                                             # dorsal height); ridge of a scute, segment fractions

coarse = [(c, d) for c, d, r in track(R, START, DIR, 0.03, 24) if c.y < TIP.y - 0.012]


def station(y):
    """Spine point where it reaches this y (y grows along the tail): coarse spine interpolated, re-centred."""
    k = max([0] + [i for i in range(len(coarse) - 1) if coarse[i][0].y <= y])
    k = min(k, len(coarse) - 2); (c0, d0), (c1, d1) = coarse[k], coarse[k + 1]
    f = (y - c0.y) / (c1.y - c0.y); d = d0.lerp(d1, f).normalized()
    c = centred(R, c0.lerp(c1, f), d); c.x = 0.0
    return c, d


def dirs(d):
    a, u = frame(d, (0, 0, 1)); return u, a.cross(u)            # dorsal, +x side


def at(c, d, deg):
    u, w = dirs(d); t = math.radians(deg)
    return R.exit(c, u * math.cos(t) + w * math.sin(t))


def half(y):
    c, d = station(y); P = [at(c, d, 0)] + [at(c, d, BAND + (180 - BAND) * k / 5) for k in range(6)]
    P[0].x = P[-1].x = 0.0
    return T.vs(P, snap=False)


stations = [coarse[0][0].y] + GAPS_Y
rings = [half(y) for y in stations]
scuted = set(range(1, len(GAPS_Y)))                            # segments between two gaps carry a scute
for k, (A, B) in enumerate(zip(rings, rings[1:])):
    if k not in scuted:
        T.strip(A, B); continue
    ya, yb = [stations[k] + (stations[k + 1] - stations[k]) * f for f in RIDGE]
    a, b = [T.v(Vector((0,) + tuple(at(*station(y), 0))[1:]), snap=False) for y in (ya, yb)]
    c1, c2 = [T.v(at(*station(y), BAND), snap=False) for y in (ya, yb)]
    T.f(A[0], A[1], c1, a); T.f(a, c1, c2, b); T.f(b, c2, B[1], B[0])
    T.f(A[1], c1, B[2], A[2]); T.f(c1, c2, B[1], B[2])
    for j in range(2, 6):
        T.f(A[j], A[j + 1], B[j + 1], B[j])
tv = T.v(TIP, snap=False); D = rings[-1]
for k in range(0, 6, 2):
    T.f(D[k], D[k + 1], D[k + 2], tv)
L["tail_top"] = rings[0]
L["tail_info"] = [tuple(round(x, 3) for x in station(y)[0]) for y in stations]
