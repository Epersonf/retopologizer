"""Upper torso (half, x >= 0), box layout: front face 4 columns, side 2, back 4 -> 20 around the full body.
  arm hole  = 2x2 hole at the top of the side face (8 verts = the arm root ring, L["arm_root"])
  neck hole = 2x2 hole at the seam on the top face (7 verts per half, 12 around, L["neck_base"])
Rows: r0 waist (top of the sash) .. r2 under the armpit (full half rings, 11 verts), r3 armpit, r4 mid arm hole,
r5 top (neck base / clavicle line). Above the armpit the rows split into a front part (cols 0-4) and a back part
(cols 6-10) around the arm hole. Poles: the 2 lower corners of the arm hole, the 2 outer corners of the neck hole.
Exports L["waist"] (11 verts, front centre -> back centre) for the sash."""
from mathutils import Vector

Z_LOW = [0.627, 0.655, 0.69]                 # r0 sash top edge, r1 waist (narrowest), r2 bust
Z_UP = [0.73, 0.775]                          # r3 upper bust, r4 where the chest turns into the neck
Z_NECK = 0.82                                 # neck base ring (clean neck section)
C_ARM = Vector((0.10, 0.008, 0.775))          # arm root ring: around the arm axis, perpendicular to it


def centre(z):
    f = R.exit(Vector((0, -0.02, z)), Vector((0, -1, 0))); b = R.exit(Vector((0, -0.02, z)), Vector((0, 1, 0)))
    return Vector((0, (f.y + b.y) / 2, z)), f, b


A = T.vs(cring(R, C_ARM, (1, 0, 0), (0, 0, 1), 8), snap=False)     # top, top-front, front, ... , top-back
N = T.vs(chalf(R, centre(Z_NECK)[0], (0, 0, 1), (0, -1, 0), 6), snap=False)

# rows below the armpit: columns 4 and 6 line up under the arm hole corners, the rest evenly spaced
rows = []
for k, z in enumerate(Z_LOW):
    c = centre(z)[0]
    dense = chalf(R, c, (0, 0, 1), (0, -1, 0), 128)
    s = [0.0]
    for p, q in zip(dense, dense[1:]):
        s.append(s[-1] + (q - p).length)
    t = lambda v: s[min(range(len(dense)), key=lambda i: ((dense[i] - v.co) * Vector((1, 1, 0))).length)] / s[-1]
    t4, t6 = t(A[3]), t(A[5]); w = k / (len(Z_LOW) - 1)         # top row follows the arm hole, bottom row even
    t4, t6 = (1 - w) * 0.4 + w * t4, (1 - w) * 0.6 + w * t6
    fr = [t4 * i / 4 for i in range(5)] + [(t4 + t6) / 2] + [t6 + (1 - t6) * i / 4 for i in range(5)]
    rows.append(T.vs(chalf(R, c, (0, 0, 1), (0, -1, 0), 10, fracs=fr), snap=False))

# rows above the armpit: seam point -> arm hole vertex (front), arm hole vertex -> seam point (back)
up = []
for z, af, ab in zip(Z_UP, (A[3], A[2]), (A[5], A[6])):
    c, f, b = centre(z)
    fr = T.vs(line(R, f, af.co, 4, center=c)[:-1], snap=False) + [af]
    bk = [ab] + T.vs(line(R, ab.co, b, 4, center=c)[1:], snap=False)
    up.append((fr, bk))
# top face: a column between the neck and the arm (front, top, back of the shoulder)
cs = centre(0.80)[0]
S = [T.v(line(R, N[k].co, A[j].co, 2, center=cs + Vector((0.03, 0, -0.04)))[1], snap=False)
     for k, j in ((2, 1), (3, 0), (4, 7))]
top_f = [N[0], N[1], N[2], S[0], A[1]]
top_b = [A[7], S[2], N[4], N[5], N[6]]

for a, b in zip(rows, rows[1:]):
    T.strip(a, b)
r2, r3f, r3b = rows[-1], up[0][0], up[0][1]
T.strip(r2[:5], r3f); T.strip(r2[6:], r3b)
T.f(r2[4], r2[5], A[4], A[3]); T.f(r2[5], r2[6], A[5], A[4])          # side face under the arm hole
T.strip(r3f, up[1][0]); T.strip(r3b, up[1][1])
T.strip(up[1][0], top_f); T.strip(up[1][1], top_b)
T.f(N[2], S[0], S[1], N[3]); T.f(N[3], S[1], S[2], N[4])
T.f(S[0], A[1], A[0], S[1]); T.f(S[1], A[0], A[7], S[2])
for v in [r[0] for r in rows] + [r[-1] for r in rows] + [up[0][0][0], up[1][0][0], up[0][1][-1], up[1][1][-1], N[0], N[6]]:
    v.co.x = 0.0
L["arm_root"] = A
L["neck_base"] = N
L["waist"] = rows[0]
