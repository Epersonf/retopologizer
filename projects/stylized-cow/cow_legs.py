"""Four legs: 8-point horizontal rings snapped on the reference, from the belly down to the hoof sole.
Each leg is a separate tube whose top ring is a slightly bigger copy pushed up INTO the torso (hidden overlap)."""
from mathutils import Vector
LEGS = dict(HL=(-0.366, 0.133), HR=(-0.366, -0.100), FL=(0.155, 0.134), FR=(0.155, -0.101))
ZS = [0.15, 0.11, 0.075, 0.055, 0.03, 0.006]
NL = 8


def leg_rings(S, c):
    c = list(c); out = []
    for z in ZS:
        for _ in range(2):
            pts = ring(S, (c[0], c[1], z), (0, 0, 1), (1, 0, 0), NL, maxr=0.2)
            c = [sum(p[0] for p in pts) / NL, sum(p[1] for p in pts) / NL]
        out.append(ring(S, (c[0], c[1], z), (0, 0, 1), (1, 0, 0), NL, maxr=0.2))
    return out


def build_legs(S, M, which=("HL", "HR", "FL", "FR")):
    for k in which:
        rings = leg_rings(S, LEGS[k])
        up = 0.38 if LEGS[k][0] < 0 else 0.30                   # top ring buried inside the torso (belly is higher at the haunch)
        top = [(x, y, up) for x, y, z in rings[0]]
        R = [[M.v(p) for p in r] for r in [top] + rings]
        for a, b in zip(R, R[1:]):
            M.strip_closed(a, b, flip=True)
        M.cap(R[0]); M.cap(R[-1], flip=True)
