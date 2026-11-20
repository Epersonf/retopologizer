"""Blockout of the hair, the artist's first step (worker; needs draft/hair_radial.npz from hair_radial.py): a SOLID base with very few polygons, only for
the form. A closed quad-only cylindrical shell about the vertical axis: NT0 columns (uniform; those near the face window are replaced by two narrow pairs
that put a column edge exactly on each window edge, so the wall between hair and window is thin and radial) x NZ rows between the hem and the top of
each column (the PCT_Z-th percentile of the lowest / the (100-PCT_Z)-th of the highest hair there; rows are denser near the top, where the dome bends).
The radius of a vertex = the PCT-th percentile of the field r(t, z) over its cell, minus MARGIN (100 = the outer envelope, 30 = about the valley level:
the locks drawn on it then stand proud of the base). A cell with little hair (the face window) gets FILL, the head hides it (material "headfill").
Two quad fans close the top and the bottom. Object "Hair_hood" (the name hair_join.py joins). NT0, NZ, PCT, PCT_Z, MARGIN, FILL may be set before running.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_base.py"""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector
G = globals(); NT0 = G.get("NT0", 24); NZ = G.get("NZ", 9); PCT = G.get("PCT", 55); PCT_Z = G.get("PCT_Z", 25); MARGIN = G.get("MARGIN", 0.005); FILL = G.get("FILL", 0.085); EDGE = 1.5
Q = r"C:\Users\epers\Desktop\retopologizer\tools\03-qa"; HD = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft"
D = np.load(HD + r"\hair_radial.npz"); F, zs, A = D["R"], D["zs"], Vector(D["A"]); nt = F.shape[0]; deg = 360.0 / nt
mid = np.isfinite(F[:, (zs > 0.2) & (zs < 0.4)]).mean(1); win = mid < 0.3                  # fine columns of the face window (around the front, 180 deg)
i = j = int(180 / deg)
while win[(i - 1) % nt]:
    i -= 1
while win[(j + 1) % nt]:
    j += 1
aL, aR = i * deg - deg / 2, j * deg + deg / 2                                         # the two window edges (azimuth deg)
U = 360.0 / NT0; TH = [a for a in np.arange(0, 360, U) if min(abs(a - aL), abs(a - aR)) > U / 2 + 1] + [aL - EDGE, aL + EDGE, aR - EDGE, aR + EDGE]
TH = sorted(TH)
if len(TH) % 2:                                                                        # the quad fans need an even count: split the widest gap
    gaps = [(TH[(k + 1) % len(TH)] - TH[k]) % 360 for k in range(len(TH))]; k = int(np.argmax(gaps)); TH.insert(k + 1, (TH[k] + gaps[k] / 2) % 360); TH = sorted(TH)
NT = len(TH); T = [math.radians(a) for a in TH]; edges = [((TH[k] + ((TH[(k + 1) % NT] - TH[k]) % 360) / 2) % 360) for k in range(NT)]   # edges[k] = between k and k+1
def cell(k):                                                                           # fine columns of base column k
    lo, hi = edges[k - 1], edges[k]; c = np.arange(nt) * deg + deg / 2
    return np.nonzero(((c - lo) % 360) < ((hi - lo) % 360))[0]
zb = np.full(NT, np.nan); zt = np.full(NT, np.nan); cols = [cell(k) for k in range(NT)]
for k in range(NT):
    lo, hi = [], []
    for c in cols[k]:
        r = np.nonzero(np.isfinite(F[c]))[0]
        if len(r):
            lo.append(zs[r[0]]); hi.append(zs[r[-1]])
    if len(lo) > len(cols[k]) / 2:
        zb[k], zt[k] = np.percentile(lo, PCT_Z), np.percentile(hi, 100 - PCT_Z)
        if np.isfinite(F[np.ix_(cols[k], np.nonzero((zs > 0.15) & (zs < 0.40))[0])]).mean() < 0.35:
            zb[k] = np.nan                                                             # only the arch over the forehead has hair: the hem runs on between the curtains
for a in (zb, zt):                                                                     # window columns: interpolate around the circle (by azimuth); smooth the ragged ends
    bad = ~np.isfinite(a); a[bad] = np.interp(np.array(TH)[bad], np.array(TH)[~bad], a[~bad], period=360)
    for _ in range(2):
        a[:] = (np.roll(a, 1) + 2 * a + np.roll(a, -1)) / 4
s = 1 - (1 - np.arange(NZ) / (NZ - 1)) ** 1.4                                          # rows: denser near the top
Z = np.array([[zb[k] + (zt[k] - zb[k]) * s[j] for j in range(NZ)] for k in range(NT)]); R = np.full((NT, NZ), np.nan)
for k in range(NT):
    for j in range(NZ):
        z0 = (Z[k, max(j - 1, 0)] + Z[k, j]) / 2 if j else Z[k, 0] - 0.01; z1 = (Z[k, min(j + 1, NZ - 1)] + Z[k, j]) / 2 if j < NZ - 1 else Z[k, j] + 0.01
        v = F[np.ix_(cols[k], np.nonzero((zs >= z0) & (zs <= z1))[0])]; n = v.size; v = v[np.isfinite(v)]
        if n and v.size >= 0.35 * n:
            R[k, j] = np.percentile(v, PCT) - MARGIN
miss = ~np.isfinite(R); alone = np.zeros_like(miss)
for k in range(NT):                                                                    # a lone hair cell inside the window is noise
    for j in range(NZ):
        nb = [miss[(k + a) % NT, j + b] for a in (-1, 0, 1) for b in (-1, 0, 1) if (a or b) and 0 <= j + b < NZ]
        alone[k, j] = sum(nb) >= len(nb) - 1 and not miss[k, j]
miss |= alone
R[miss] = FILL
for j in range(1, NZ - 1):                                                             # light smoothing along z only (the columns are not uniform)
    S = (R[:, j - 1] + 2 * R[:, j] + R[:, j + 1]) / 4; R[:, j] = np.where(miss[:, j], R[:, j], S)
bm = bmesh.new(); V = [[bm.verts.new(A + Vector((R[k, j] * math.sin(T[k]), R[k, j] * math.cos(T[k]), Z[k, j]))) for j in range(NZ)] for k in range(NT)]
apex = bm.verts.new(A + Vector((0, 0, float(zt.mean()) + 0.02))); low = bm.verts.new(A + Vector((0, 0, float(zb.mean()))))
side = [bm.faces.new((V[k][j], V[(k + 1) % NT][j], V[(k + 1) % NT][j + 1], V[k][j + 1])) for k in range(NT) for j in range(NZ - 1)]
for k in range(0, NT, 2):                                                              # top and bottom: quad fans (two ring edges + the centre)
    bm.faces.new((V[k][NZ - 1], V[(k + 1) % NT][NZ - 1], V[(k + 2) % NT][NZ - 1], apex)); bm.faces.new((V[(k + 2) % NT][0], V[(k + 1) % NT][0], V[k][0], low))
bm.normal_update(); f0 = side[(NT // 4) * (NZ - 1) + NZ // 2]; out = f0.calc_center_median() - A; out.z = 0
if f0.normal.dot(out) < 0:
    bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
for o in [o for o in bpy.data.objects if o.name == "Hair_hood"]:
    bpy.data.objects.remove(o)
me = bpy.data.meshes.new("Hair_hood"); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new("Hair_hood", me); bpy.context.scene.collection.objects.link(ob)
for m in ("hair", "headfill"):
    me.materials.append(bpy.data.materials.get(m) or bpy.data.materials.new(m))
for p in me.polygons:                                                                  # headfill: the two fans, and every side quad whose vertices are all at FILL radius
    vs = [me.vertices[v].co for v in p.vertices]; fan = any(abs(v.x - A.x) < 1e-6 and abs(v.y - A.y) < 1e-6 for v in vs)
    p.material_index = 1 if fan or all(abs(math.hypot(v.x - A.x, v.y - A.y) - FILL) < 1e-6 for v in vs) else 0
exec(open(Q + r"\qa_faces.py").read()); exec(open(Q + r"\qa_shape.py").read())
heal = heal_spikes("Hair_hood", rounds=40)                                             # the jump between hair and fill radius reads as a spike: relax it
result = {"quads": len(me.polygons), "columns": NT, "window_deg": [round(aL, 1), round(aR, 1)], "triangles_equiv": 2 * len(me.polygons), "z": [round(float(zb.min()), 3), round(float(zt.max()), 3)], "heal": heal}
