"""Right hand (x > 0) on the artist's LowPoly, box-modelled the way they would (every count decided here):
  W  wrist ring (12, theirs): front side 2 edges, bottom 5, back 2, top 3 (+ the 2 faces they started at the front)
  P1, P2 palm contours with the same layout; the thumb leaves through the 6-hole at the front-bottom corner
  P2 -> P3 (knuckles, 14): 1->3 on the back of the hand (top 3 -> 5 edges: two 3-poles, two 5-poles)
  knuckle cap 5 x 2: fingers out of columns 0, 2, 4 (6-rings), web quads in columns 1 and 3
  each digit (tools/retopo/digits.py): contours to the claw, a ring each side of the claw base, tip vertex."""
import numpy as np
from mathutils import Vector

X1, X2, X3 = 0.388, 0.41, 0.452             # palm rings (x of the sections): after the wrist, past the thumb, knuckles
WEB_X = 0.46                                 # the fingers separate here (rays +X from inside the palm, both gaps)
YCOL = [-0.022, -0.0123, 0.0107, 0.0185]     # finger sides at the knuckles = columns 1..4 of the cap
FING = [(-0.0355, 0.7653), (-0.0008, 0.7726), (0.0308, 0.7634)]   # finger centres (y, z) just past the web
THUMB_IN = Vector((0.398, -0.06, 0.738))     # inside the thumb, next to the palm
UP, FR = Vector((0, 0, 1)), Vector((0, -1, 0))

_hi = bpy.data.objects["HiPoly"]; _A = np.empty(len(_hi.data.vertices) * 3); _hi.data.vertices.foreach_get("co", _A)
_M = np.array(_hi.matrix_world); _H = _A.reshape(-1, 3) @ _M[:3, :3].T + _M[:3, 3]; _H = _H[_H[:, 0] > 0.36]


def far(mask, d):
    P = _H[mask]; return Vector(P[(P @ np.array(d)).argmax()].tolist())


tips = [far((np.abs(_H[:, 1] - y) < 0.01) & (_H[:, 0] > 0.47), (1, 0, 0)) for y, z in FING]
thumb_tip = far(_H[:, 0] > 0.36, (0, 0, -1))


def sect(x):
    """centre, front and back side points, top and bottom (at the centre) of the palm section at x."""
    c = centred(R, Vector((x, -0.004, 0.772)), (1, 0, 0))
    return c, R.exit(c, FR), R.exit(c, -FR), R.exit(c, UP), R.exit(c, -UP)


def surf(c, y, s):
    return R.exit(Vector((c.x, y, c.z)), UP * s)


def corner(c, side, cap):
    return R.exit(c, ((side - c) * 0.8 + (cap - c) * 0.7).normalized())


def palm_ring(x, top):
    """front-top corner, front mid, front-bottom corner, bottom row (YCOL), back-bottom, back mid, back-top, top row
    back -> front at the given y's (2 for the 12-rings, 4 for the knuckle ring)."""
    c, f, b, t, d = sect(x)
    return T.vs([corner(c, f, t), f, corner(c, f, d)] + [surf(c, y, -1) for y in YCOL]
                + [corner(c, b, d), b, corner(c, b, t)] + [surf(c, y, 1) for y in top], snap=False)


v397, v394 = T.old(397, 394)
X = [v for v in (e.other_vert(v397) for e in v397.link_edges) if v in {e.other_vert(v394) for e in v394.link_edges}][0]
W = [v397, X] + T.old(394, 406, 407, 405, 404, 403, 402, 401, 400, 399)
P2 = palm_ring(X2, [YCOL[3], YCOL[0]])
P3 = palm_ring(X3, YCOL[::-1])
c1 = sect(X1)[0]
P1 = T.old(398, 395, 396)
for k in range(3, 12):
    q = W[k].co.lerp(P2[k].co, (X1 - W[k].co.x) / (X2 - W[k].co.x)); dd = q - c1; dd.x = 0
    P1.append(T.v(R.exit(c1, dd.normalized()), snap=False))

T.strip(W, P1, closed=True)                                   # the 2 faces of the artist are found, not doubled
for k in [0] + list(range(3, 12)):                            # P1 -> P2 around the thumb hole (front-bottom, k = 1, 2)
    T.f(P1[k], P1[(k + 1) % 12], P2[(k + 1) % 12], P2[k])
for k in range(10):                                           # P2 -> P3, then the 1->3 on the back of the hand
    T.f(P2[k], P2[k + 1], P3[k + 1], P3[k])
T.f(P2[11], P2[0], P3[0], P3[13])
cm = (sect(X2)[0] + sect(X3)[0]) / 2
m0, m1 = [T.v(surf(cm, YCOL[3] + (YCOL[0] - YCOL[3]) * f, 1), snap=False) for f in (1 / 3, 2 / 3)]
a0, a1, b0, b1, b2, b3 = P2[10], P2[11], P3[10], P3[11], P3[12], P3[13]
T.f(a0, a1, m1, m0); T.f(a0, m0, b1, b0); T.f(m0, m1, b2, b1); T.f(m1, a1, b3, b2)

# knuckle cap: grid columns i = 0..5 (front -> back), rows top / mid / bottom
c3 = sect(X3)[0]
top = [P3[0], P3[13], P3[12], P3[11], P3[10], P3[9]]
bot = [P3[2], P3[3], P3[4], P3[5], P3[6], P3[7]]
yw = [YCOL[0] + (YCOL[1] - YCOL[0]) * 0.3, YCOL[0] + (YCOL[1] - YCOL[0]) * 0.7,
      YCOL[2] + (YCOL[3] - YCOL[2]) * 0.3, YCOL[2] + (YCOL[3] - YCOL[2]) * 0.7]
mid = [P3[1]] + [T.v(R.exit(Vector((0.42, y, c3.z)), Vector((1, 0, 0))), snap=False) for y in yw] + [P3[8]]
for g in (1, 3):
    T.f(top[g], top[g + 1], mid[g + 1], mid[g]); T.f(mid[g], mid[g + 1], bot[g + 1], bot[g])
fingers = []
for k in range(3):
    i = 2 * k; root = [top[i], top[i + 1], mid[i + 1], bot[i + 1], bot[i], mid[i]]
    p_in = Vector((WEB_X + 0.01,) + FING[k])
    fingers.append(digit(T, R, root, p_in, tips[k]))
thumb = digit(T, R, [P1[1], P1[2], P1[3], P2[3], P2[2], P2[1]], THUMB_IN, thumb_tip, body=[0.2])
L["hand"] = {"palm": [W, P1, P2, P3], "fingers": fingers, "thumb": thumb}
