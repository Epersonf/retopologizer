"""Right leg (x > 0): contour rings of 12 (like the artist's arm) from a ring hidden under the skirt down to the ankle,
3 rings around the knee. Both ends stay open: L["leg_top"] (under the skirt, to be joined to the hips) and
L["ankle"] (the foot starts there). Columns keep constant angles around the leg axis, vertex 0 at the front."""
from mathutils import Vector

Z = [0.41, 0.36, 0.315, 0.278, 0.257, 0.236, 0.20, 0.16, 0.125, 0.095]   # under the skirt .. knee (3) .. ankle
N = 12

cs, c = [], Vector((0.087, -0.03, Z[0]))
for z in Z:
    c = centred(R, Vector((c.x, c.y, z)), (0, 0, 1)); cs.append(c.copy())
rings = []
for k, c in enumerate(cs):
    a = (cs[min(k + 1, len(cs) - 1)] - cs[max(k - 1, 0)]).normalized()          # down the leg
    c = centred(R, c, a, (0, -1, 0))
    P = ring(R, c, a, (0, -1, 0), N)
    rings.append(T.vs(align(P, rings[-1]) if rings else P, snap=False))
for A, B in zip(rings, rings[1:]):
    T.strip(A, B, closed=True)
L["leg_top"], L["ankle"] = rings[0], rings[-1]
L["leg_centres"] = [tuple(round(x, 3) for x in c) for c in cs]
