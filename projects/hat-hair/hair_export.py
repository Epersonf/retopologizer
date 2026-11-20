"""Hair part of the reference (world space) for analysis outside Blender: draft/hair_in.npz (V, F, N). The hair is the
part at x < X_CUT (the hat is at x > 0.15). Runs in the worker on draft/hair_work.blend:
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_export.py"""
import numpy as np
import bpy

OUT = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft\hair_in.npz"
X_CUT = 0.12
H = bpy.data.objects["HiPoly"]; me = H.data; M = np.array(H.matrix_world)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
no = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("normal", no); no = no.reshape(-1, 3)
V = co @ M[:3, :3].T + M[:3, 3]; N = no @ M[:3, :3].T; N /= np.linalg.norm(N, axis=1)[:, None]
me.calc_loop_triangles(); F = np.empty(len(me.loop_triangles) * 3, np.int32)
me.loop_triangles.foreach_get("vertices", F); F = F.reshape(-1, 3)
keep = V[:, 0] < X_CUT; F = F[keep[F].all(1)]
idx = np.unique(F); remap = -np.ones(len(V), np.int64); remap[idx] = np.arange(len(idx))
np.savez(OUT, V=V[idx].astype(np.float32), N=N[idx].astype(np.float32), F=remap[F].astype(np.int32))
result = {"verts": int(len(idx)), "tris": int(len(F)), "bbox": [V[idx].min(0).tolist(), V[idx].max(0).tolist()]}
