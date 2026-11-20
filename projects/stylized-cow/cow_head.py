"""Cow head: loft of closed rings perpendicular to the head axis (head is turned/tilted in the statue: kept as is).
Axis = from the neck centre B to the muzzle centre NOSE (measured on the reference). Each ring is re-centred on its own
points (2 passes) so rings stay on the head even where the axis drifts. Ears/horns are separate shells (cow_extras)."""
from mathutils import Vector
NOSE = Vector((0.512, -0.101, 0.564))     # centre of the muzzle front (mean of the points within 2.5 cm of max x)
FRAC = [-0.12, 0.10, 0.26, 0.42, 0.58, 0.72, 0.84, 0.93, 0.99]
NH = 10


def head_rings(S, B, nh=NH):
    B = Vector(B); L = (NOSE - B).length; A = (NOSE - B).normalized(); out = []
    for f in FRAC:
        c = B + A * (L * f)
        for _ in range(2):
            pts = ring(S, c, A, (0, 0, 1), nh); c = sum((Vector(p) for p in pts), Vector()) / len(pts)
        out.append(ring(S, c, A, (0, 0, 1), nh))
    return out, A


def build_head(S, M, B):
    rings, A = head_rings(S, B)
    R = [[M.v(p) for p in r] for r in rings]
    for a, b in zip(R, R[1:]):
        M.strip_closed(a, b)
    tip = S.ray(NOSE - A * 0.05, A, both=False, dist=0.2)
    M.cap(R[-1], centre=tip)                                  # muzzle face (fan to the surface point)
    M.cap(R[0], flip=True)                                    # hidden inside the neck
    return R
