"""Hat measurements for the ring field (runs in Blender, worker on draft/hat-hair.blend): the hat part of the reference
(vertices, normals, triangles, world space), the tip of the drooping tube and which vertices are on the OUTER side of
the cloth (some ray along the normal escapes to open space without passing through the opening). Writes draft/hat_field_in.npz for hat_field.py.
  python tools/blender_rpc.py --port 9877 projects/hat-hair/hat_measure.py"""
import sys, math
import numpy as np
sys.path.insert(0, r"C:\Users\epers\Desktop\retopologizer\tools")
import importlib, retopo
importlib.reload(retopo)
from retopo import Ref, track
import bpy
from mathutils import Vector

OUT = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft\hat_field_in.npz"
A = Vector((0, -0.6, -0.8)).normalized()        # the opening faces front-down
X_HAT = 0.15                                    # the hair is at x < 0.1
R = Ref("HiPoly")


def outer_side(V, N, ndir=96):
    """Visible from outside: a ray from the vertex escapes, using only directions that do not look out of the
    opening (d . A < -0.1), so the inside of the cavity seen through the opening does not count."""
    g = math.pi * (3 - math.sqrt(5)); D = []
    for i in range(ndir):
        z = 1 - 2 * (i + 0.5) / ndir; r = math.sqrt(1 - z * z); d = Vector((r * math.cos(g * i), r * math.sin(g * i), z))
        if d.dot(A) < -0.1:
            D.append(d)
    out = np.zeros(len(V), bool)
    for k, (p, n) in enumerate(zip(V, N)):
        n = Vector(n); o = Vector(p) + n * 0.002
        out[k] = any(R.ray(o, d, 2.0) is None for d in D if d.dot(n) > 0.15)
    return out


H = bpy.data.objects["HiPoly"]; me = H.data; M = np.array(H.matrix_world)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
no = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("normal", no); no = no.reshape(-1, 3)
V = co @ M[:3, :3].T + M[:3, 3]; N = no @ M[:3, :3].T; N /= np.linalg.norm(N, axis=1)[:, None]
me.calc_loop_triangles(); F = np.empty(len(me.loop_triangles) * 3, np.int32)
me.loop_triangles.foreach_get("vertices", F); F = F.reshape(-1, 3)
keep = V[:, 0] > X_HAT; F = F[keep[F].all(1)]
idx = np.unique(F); remap = -np.ones(len(V), np.int64); remap[idx] = np.arange(len(idx))
ST = track(R, (0.212, 0.255, 0.06), (0, 0, 1), 0.01, 26, stop=lambda r, p: r > 1.5 * p)
tail = V[idx][np.linalg.norm(V[idx][:, :2] - np.array(ST[0][0])[:2], axis=1) < 0.05]
tip = tail[np.argmin(tail[:, 2])]
np.savez(OUT, V=V[idx].astype(np.float64), N=N[idx], outer=outer_side(V[idx], N[idx]), F=remap[F], tip=tip)
result = {"verts": int(len(idx)), "tris": int(len(F)), "tip": tip.tolist()}
