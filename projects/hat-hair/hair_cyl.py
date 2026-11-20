"""Hair as a CYLINDRICAL shell (worker, "HairFull" loaded): the hybrid of manual choices and parametric fitting.
Manual choices: the vertical axis A (through the head centre), NT columns, NZ rows, the head-fill radius FILL.
Parametric fit: per column (azimuth t from +y toward +x) the lowest and highest height the hair reaches there (zb, zt, from horizontal
rays) give the column its own extent, NZ rows between them; for every grid vertex a ray comes horizontally from outside to the axis and
the first hit of the reference gives the radius (mean of 5 rays around the vertex, then lightly smoothed). Hanging hair is star-shaped
about a vertical axis, so the grid can not fold: no lid to place, no pole except the two fans. Where the reference has no hair (the face
window, gaps) the radius is FILL, the size of the head: a wall the head hides. Those faces and the two fans are material "headfill"
(qa_fit does not count them as lumps).
The object is named "Hair_hood" so the tube steps (hair_connect.py, hair_join.py) treat it as the parent shell.
Quads only, closed, wound outward. Set NT (even), NZ, FILL, SMOOTH before running to change.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_cyl.py"""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
NT = globals().get("NT", 56); NZ = globals().get("NZ", 18); FILL = globals().get("FILL", 0.085); SMOOTH = globals().get("SMOOTH", 1); SMOOTHE = globals().get("SMOOTHE", 3)
A = Vector((-0.185, -0.03, 0.0)); Q = r"C:\Users\epers\Desktop\retopologizer\tools\03-qa"
bv = BVHTree.FromObject(bpy.data.objects["HairFull"], bpy.context.evaluated_depsgraph_get())


def radius(t, z, dt=0.0, dz=0.0):
    """Mean first-hit radius of 5 rays around (t, z); None when fewer than 3 hit."""
    rs = []
    for a, b in ((0, 0), (-dt, 0), (dt, 0), (0, -dz), (0, dz)):
        d = Vector((math.sin(t + a), math.cos(t + a), 0)); h = bv.ray_cast(A + Vector((0, 0, z + b)) + d * 0.7, -d, 0.7)
        if h[0] is not None:
            rs.append(0.7 - h[3])
    return sum(rs) / len(rs) if len(rs) >= 3 else None


T = [2 * math.pi * i / NT for i in range(NT)]; zf = np.arange(0.01, 0.60, 0.01)
ext = [[z for z in zf if radius(t, z) is not None] for t in T]                       # heights with hair, per column
zb = np.array([min(e) if e else np.nan for e in ext]); zt = np.array([max(e) if e else np.nan for e in ext])
for a in (zb, zt):                                                                    # window columns (no hair): the mean of the neighbours; smooth the ragged ends
    bad = ~np.isfinite(a); idx = np.arange(NT)
    a[bad] = np.interp(idx[bad], idx[~bad], a[~bad], period=NT)
    for _ in range(SMOOTHE):
        a[:] = (np.roll(a, 1) + 2 * a + np.roll(a, -1)) / 4
zb -= 0.01; zt += 0.005; zt = np.minimum(zt, zt.mean() + 0.05)           # no tent: the top ring stays near the mean height
Z = np.array([[zb[i] + (zt[i] - zb[i]) * j / (NZ - 1) for j in range(NZ)] for i in range(NT)]); dz = float(np.mean(zt - zb)) / (NZ - 1) * 0.5
R = np.array([[radius(T[i], Z[i, j], math.pi / NT * 0.5, dz) or np.nan for j in range(NZ)] for i in range(NT)])
miss = ~np.isfinite(R)
for _ in range(2):                                         # majority filter on the miss mask (wraps in azimuth): the face window becomes one clean region
    n = sum(np.roll(np.roll(miss, a, 0), b, 1) for a in (-1, 0, 1) for b in (-1, 0, 1)); new = n >= 5
    for i, j in zip(*np.nonzero(miss & ~new)):             # miss -> hit: mean of the hit neighbours
        nb = [R[(i + a) % NT, j + b] for a in (-1, 0, 1) for b in (-1, 0, 1) if 0 <= j + b < NZ and np.isfinite(R[(i + a) % NT, j + b])]
        R[i, j] = np.mean(nb) if nb else FILL
    R[new] = FILL; miss = new
R[miss] = FILL
for _ in range(SMOOTH):                                    # light smoothing across columns and rows (wraps in azimuth): no folds
    S = (np.roll(R, 1, 0) + 2 * R + np.roll(R, -1, 0)) / 4; S[:, 1:-1] = (S[:, :-2] + 2 * S[:, 1:-1] + S[:, 2:]) / 4; R = np.where(miss, R, S)
bm = bmesh.new(); V = [[bm.verts.new(A + Vector((R[i, j] * math.sin(T[i]), R[i, j] * math.cos(T[i]), Z[i, j]))) for j in range(NZ)] for i in range(NT)]
apex = bm.verts.new(A + Vector((0, 0, float(zt.mean()) + 0.03))); low = bm.verts.new(A + Vector((0, 0, float(zb.mean()))))
side = []
for i in range(NT):
    k = (i + 1) % NT
    for j in range(NZ - 1):
        side.append(bm.faces.new((V[i][j], V[k][j], V[k][j + 1], V[i][j + 1])))
for i in range(0, NT, 2):                                  # top and bottom: quad fans (two ring edges + the centre)
    bm.faces.new((V[i][NZ - 1], V[(i + 1) % NT][NZ - 1], V[(i + 2) % NT][NZ - 1], apex))
    bm.faces.new((V[(i + 2) % NT][0], V[(i + 1) % NT][0], V[i][0], low))
bm.normal_update()
f0 = side[(NT // 4) * (NZ - 1) + NZ // 2]; out = f0.calc_center_median() - A; out.z = 0
if f0.normal.dot(out) < 0:
    bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
me = bpy.data.meshes.new("Hair_hood"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("Hair_hood", me); bpy.context.scene.collection.objects.link(ob)
for m in ("hair", "headfill"):
    me.materials.append(bpy.data.materials.get(m) or bpy.data.materials.new(m))
share = 0
for p in me.polygons:                                      # headfill: the two fans, and every side quad whose vertices are all at FILL radius
    vs = [me.vertices[v].co for v in p.vertices]; fan = any(abs(v.x - A.x) < 1e-6 and abs(v.y - A.y) < 1e-6 for v in vs)
    p.material_index = 1 if fan or all(abs(math.hypot(v.x - A.x, v.y - A.y) - FILL) < 1e-6 for v in vs) else 0
    share += p.material_index
exec(open(Q + r"\qa_faces.py").read()); exec(open(Q + r"\qa_shape.py").read())
heal = heal_spikes("Hair_hood", rounds=40)                 # the step between hair and fill radius reads as a spike: relax it (after the tagging above)
result = {"quads": len(me.polygons), "fill_quads": share, "triangles_equiv": 2 * len(me.polygons), "heal": heal}
