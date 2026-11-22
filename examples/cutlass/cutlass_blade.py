# Cutlass blade: 6-vertex rings along the curved centre line, every vertex snapped onto the reference.
import bpy, numpy as np
import os
ROOT = os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd()).replace("\\", "/").rstrip("/") + "/"
P = ROOT + "projects/cutlass/"
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=P + "draft/cutlass.blend")
exec(open(ROOT + "tools/02-retopology/snap_retopo.py").read())
d = np.load(P + "draft/raster.npz"); yf, yb, xs, zs = d["yf"], d["yb"], d["xs"], d["zs"]; T = yf - yb
STEP = 0.002


def thick(q):
    j = int(round((q[0] - xs[0]) / STEP)); i = int(round((q[1] - zs[0]) / STEP))
    return T[i, j] if 0 <= i < len(zs) and 0 <= j < len(xs) else np.nan


def span(p, n, r=0.2):
    s = np.arange(-r, r, STEP); t = np.array([thick(p + n * k) for k in s]); m = np.isfinite(t)
    idx = np.where(m)[0]
    if len(idx) == 0:
        return None
    lo = hi = idx[np.argmin(abs(s[idx]))]
    while lo - 1 >= 0 and m[lo - 1]:
        lo -= 1
    while hi + 1 < len(s) and m[hi + 1]:
        hi += 1
    return s[lo:hi + 1], t[lo:hi + 1]


C = np.load(P + "draft/blade_center.npy")
seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
F0, F1, N = 0.045, 0.985, 21
ts = F0 + (F1 - F0) * (1 - (1 - np.linspace(0, 1, N)) ** 1.4)      # rings denser near the tip
S = Surface("REFERENCE"); M = Mesh(); rings = []; frames = []
for u in ts * seg[-1]:
    p = np.array([np.interp(u, seg, C[:, 0]), np.interp(u, seg, C[:, 1])])
    tg = np.array([np.interp(u + 0.01, seg, C[:, 0]), np.interp(u + 0.01, seg, C[:, 1])]) - \
        np.array([np.interp(u - 0.01, seg, C[:, 0]), np.interp(u - 0.01, seg, C[:, 1])])
    tg /= np.linalg.norm(tg); n = np.array([-tg[1], tg[0]])
    s, t = span(p, n)
    frames.append([p, n, s, t, tg])
for i in range(len(frames) - 2, -1, -1):                          # next to the guard the cut catches the guard: inherit the neighbour's profile
    w, wn = np.ptp(frames[i][2]), np.ptp(frames[i + 1][2])
    if ts[i] < 0.15 and w > 1.12 * wn:
        step = np.dot(frames[i + 1][0] - frames[i][0], frames[i + 1][4])
        frames[i][0] = frames[i + 1][0] - frames[i + 1][4] * step   # centre on the neighbour's line, or the spine pokes out of the blade
        frames[i][1:] = frames[i + 1][1:]
for p, n, s, t, tg in frames:
    tmax = np.percentile(t, 80)
    k_bev = int(np.argmax(t >= 0.9 * tmax))                       # end of the edge bevel
    pts = {"edge": (s[1], t[1]), "bev": (s[k_bev], t[k_bev]), "back": (s[-2], t[-2])}
    ring = []
    for key, sign in (("edge", 1), ("bev", 1), ("back", 1), ("back", -1), ("bev", -1), ("edge", -1)):
        ss, tt = pts[key]; q = p + n * ss
        ring.append(M.v(S.nearest((q[0], sign * tt / 2, q[1]), 0.03)))
    rings.append(ring)
g = frames[0][4] * -0.02                                         # base buried in the guard, where it is hidden
rings.insert(0, [M.v((v.co.x + g[0], v.co.y, v.co.z + g[1])) for v in rings[0]])
for A, B in zip(rings, rings[1:]):
    M.strip_closed(A, B)
for r, flip in ((rings[0], True), (rings[-1], False)):
    M.f(*([r[0], r[1], r[2], r[3]][::-1] if flip else [r[0], r[1], r[2], r[3]]))
    M.f(*([r[3], r[4], r[5], r[0]][::-1] if flip else [r[3], r[4], r[5], r[0]]))
o = M.to_object("Blade")
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode="OBJECT")
exec(open(ROOT + "tools/02-retopology/wire_overlay.py").read())
for v in ("front", "persp"):
    wire_overlay(["Blade"], P + f"draft/blade_{v}.png", view=v, shade=["REFERENCE"], center=(-0.12, 0, 0.55), size=0.85, res=900)
exec(open(ROOT + "tools/02-retopology/fit_report.py").read())
fr = fit_report("Blade", "REFERENCE", ref_max=2000)
bpy.ops.wm.save_as_mainfile(filepath=P + "draft/cutlass_blade.blend")
result = {"quads": len(o.data.polygons), "tris": sum(len(p.vertices) - 2 for p in o.data.polygons),
          "ngons": sum(len(p.vertices) != 4 for p in o.data.polygons), "new_to_ref_mm": fr["new_to_ref_mm"]}
