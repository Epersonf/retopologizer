"""Upper back + top of the shoulder (half, x >= 0): one 5-sided region closed with quads around a 5-pole on the
upper back. Corners: 53 (neck base, front side), 61 (armhole front top), 67 (armpit back), 70 (back centre on
ring B), cn (back centre at the neck base). Edges per side: 4 front shoulder line (artist: 53-49-59-60-61) | 4 armhole
top + back (new) | 3 ring B back (artist: 67-66-72-70) | 4 back centre (new) | 3 neck base back (new).
Interior points are projected from a point inside the upper chest (rays leave the surface on the shoulder top, the
back and the neck base), so the patch does not cut through the body.
Loops for the next parts: L["armhole"] (10 verts, front top -> bottom -> back -> top), L["neck_back"]."""
from mathutils import Vector

v53, v49, v59, v60, v61, v62, v63, v64, v65, v68, v67, v66, v72, v70 = T.old(
    53, 49, 59, 60, 61, 62, 63, 64, 65, 68, 67, 66, 72, 70)
at = lambda p, n=None: T.v(Vector(p), n)
IN = (0.03, 0.0, 0.74)

# armhole top and back (arm root at x ~ 0.093; the shoulder top is flat at z ~ 0.812)
t = at((0.095, -0.005, 0.814), (0, 0, 1))
b2 = at((0.094, 0.036, 0.805), (0, 0.6, 0.8))
b1 = at((0.093, 0.052, 0.779), (0, 1, 0))
# neck base behind 53 (the neck leaves the shoulders at z ~ 0.81) and the back centre line
n1 = at((0.052, 0.0, 0.815), (1, 0, 0.3))
n2 = at((0.036, 0.034, 0.809), (0.7, 0.7, 0.2))
cn = at((0.0, 0.045, 0.80), (0, 1, 0))
cs = [at((0.0, 0.05, 0.694 + (0.80 - 0.694) * k / 4), (0, 1, 0)) for k in (1, 2, 3)]
for v in [cn] + cs:
    v.co.x = 0.0

sides = [[v53, v49, v59, v60, v61], [v61, t, b2, b1, v67], [v67, v66, v72, v70], [v70] + cs + [cn], [cn, n2, n1, v53]]
P, spokes = poly_patch(T, sides, solve_spokes([len(x) - 1 for x in sides]), (0.045, 0.055, 0.772), inside=IN,
                       vias={0: [(0.065, 0.0, 0.812)]})
inner = {v for f in T.bm.faces for v in f.verts if not v[T._orig]} - {v for sd in sides for v in sd}
T.relax(inner - {P}, iters=3, k=0.4)
L["armhole"] = [v61, v62, v63, v64, v65, v68, v67, b1, b2, t]
L["neck_back"] = [v53, n1, n2, cn]
