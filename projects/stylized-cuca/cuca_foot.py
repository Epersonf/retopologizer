"""Right foot (x > 0) from the ankle loop of the leg (12, vertex 0 at the front), built like the hand:
  A ankle (theirs) -> B1, B2 the bend (an elbow: heel = outside of the bend, instep = inside) -> C mid foot (12) ->
  D toe base (14, 1->3 on the instep) -> cap 5 x 2 with the 3 toes (6-rings) in columns 0, 2, 4, webs in 1 and 3.
Rings B1..D are box rings (contour.box_ring, w = inner side): top 3 edges, sides 2, sole 5 (D: top 5)."""
import math
from mathutils import Vector

F = [0.265, 0.334, 0.645, 0.722]           # toe sides at the toe base, fractions of the foot width (inner -> outer)
TOES = [(0.072, 0.03), (0.1255, 0.032), (0.18, 0.03)]                 # toe centres (x, z) just past the web
TIPS = [Vector((0.0619, -0.1397, 0.016)), Vector((0.126, -0.1543, 0.0187)), Vector((0.1915, -0.1361, 0.015))]
Y_C, Y_D = -0.045, -0.075                   # mid foot, toe base (before the toes separate)
WEB_HALF = 0.003                            # the two web vertices of a gap: crotch +- this (x)
FWD, UPZ, BEND_UP = Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, -1, 1))

A = T.old(*range(732, 744))                 # ankle loop of the leg in the artist's mesh: front, inner, back, outer
cA = sum((v.co for v in A), Vector()) / 12
cC = centred(R, Vector((cA.x, Y_C, 0.035)), FWD)
cD = centred(R, Vector((cA.x, Y_D, 0.03)), FWD)
ry, rz = cA.y - cC.y, cA.z - cC.z
ring_pts, cs = [], []
for th in (30, 60, 90):                     # elbow from the ankle (down) to the mid foot (forward)
    t = math.radians(th)
    c = Vector((cA.x + (cC.x - cA.x) * th / 90, cC.y + ry * math.cos(t), cA.z - rz * math.sin(t)))
    ax = Vector((0, -ry * math.sin(t), -rz * math.cos(t))).normalized()
    c = centred(R, c, ax, BEND_UP); cs.append((c, ax))
    ring_pts.append(box_ring(R, c, ax, BEND_UP, [F[0], F[3]], F))
B1, B2, C = [T.vs(P, snap=False) for P in ring_pts]
D = T.vs(box_ring(R, cD, FWD, UPZ, F, F), snap=False)
T.strip(align(A, B1), B1, closed=True); T.strip(B1, B2, closed=True); T.strip(B2, C, closed=True)

for k in range(10):                         # C -> D, then the 1->3 on the instep (top 3 -> 5 edges)
    T.f(C[k], C[k + 1], D[k + 1], D[k])
T.f(C[11], C[0], D[0], D[13])
cm = (cC + cD) / 2
m0, m1 = [T.v(at_width(R, cm, FWD, UPZ, F[3] + (F[0] - F[3]) * f), snap=False) for f in (1 / 3, 2 / 3)]
a0, a1, b0, b1, b2, b3 = C[10], C[11], D[10], D[11], D[12], D[13]
T.f(a0, a1, m1, m0); T.f(a0, m0, b1, b0); T.f(m0, m1, b2, b1); T.f(m1, a1, b3, b2)

# toe cap: columns i = 0..5 (inner -> outer), rows top / mid / sole; web points = rays forward from inside
top = [D[0], D[13], D[12], D[11], D[10], D[9]]
bot = [D[2], D[3], D[4], D[5], D[6], D[7]]
xs = [R.exit(cC, Vector((-1, 0, 0))).x, R.exit(cC, Vector((1, 0, 0))).x]
web = []
for f0, f1 in ((F[0], F[1]), (F[2], F[3])):                # crotch = where a ray forward leaves the foot soonest
    x0, x1 = xs[0] + (xs[1] - xs[0]) * (f0 - 0.06), xs[0] + (xs[1] - xs[0]) * (f1 + 0.06)
    hits = [R.exit(Vector((x0 + (x1 - x0) * i / 24, Y_C, cD.z)), FWD) for i in range(25)]
    p = max((h for h in hits if h is not None), key=lambda h: h.y)
    web += [R.snap(p + Vector((-WEB_HALF, 0, 0))), R.snap(p + Vector((WEB_HALF, 0, 0)))]
mid = [D[1]] + T.vs(web, snap=False) + [D[8]]
for g in (1, 3):
    T.f(top[g], top[g + 1], mid[g + 1], mid[g]); T.f(mid[g], mid[g + 1], bot[g + 1], bot[g])
web_y = min(p.y for p in web)
toes = []
for k in range(3):
    i = 2 * k; root = [top[i], top[i + 1], mid[i + 1], bot[i + 1], bot[i], mid[i]]
    toes.append(digit(T, R, root, Vector((TOES[k][0], web_y - 0.01, TOES[k][1])), TIPS[k], body=[0.12]))
L["foot_info"] = [tuple(round(x, 3) for x in p) for p in web] + [tuple(round(x, 3) for x in c) for c, a in cs]
