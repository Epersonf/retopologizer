"""Cow torso + neck: closed-ring loft along X, every vertex snapped on the reference (hand-retopo style).
Rings are 12 points around X (first one on top). Station x list follows the form: rump, haunch, back, withers, neck.
Belly between the legs is flat at zb(x) (legs are separate tubes that enter from below)."""
from mathutils import Vector
YC = 0.017                                                    # body centre line (statue as generated)
XS = [-0.455, -0.40, -0.32, -0.24, -0.16, -0.08, 0.0, 0.08, 0.16, 0.23, 0.29]
N = 12


def vert_hits(S, x):
    o = Vector((x, YC, 2.0)); zs = []
    for _ in range(4):
        h = S.bv.ray_cast(o, Vector((0, 0, -1)), 3.0)
        if h[0] is None:
            break
        zs.append(h[0].z); o = h[0] - Vector((0, 0, 0.002))
    return zs


def torso_rings(S):
    rings = []
    for x in XS:
        zs = vert_hits(S, x); top = zs[0]; bot = max(0.2, zs[1]) if len(zs) > 1 else top - 0.3
        rings.append(ring(S, (x, YC, (top + bot) / 2), (1, 0, 0), (0, 0, 1), N, zmin=bot))
    return rings


def build_torso(S, M):
    R = [[M.v(p) for p in r] for r in torso_rings(S)]
    for a, b in zip(R, R[1:]):
        M.strip_closed(a, b)
    r0 = torso_rings(S)[0]; zc = sum(p[2] for p in r0) / len(r0)
    M.cap(R[0], centre=S.ray((XS[0] + 0.03, YC, zc), (-1, 0, 0), both=False, dist=0.2))   # rump: fan to the surface
    M.cap(R[-1], flip=True)
    return R
