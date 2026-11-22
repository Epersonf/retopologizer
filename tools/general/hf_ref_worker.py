r"""Runs INSIDE Blender (background): samples the reference meshes of the .blend a recording started from and writes ref.npz + ref.json.
  blender -b <file.blend> --python hf_ref_worker.py -- <out_dir> <comma,separated,edited,object,names>
Reference = every mesh object that is not edited in the recording and has >= 20000 vertices (the 2 biggest). 60000 area-weighted surface points with
normals, in WORLD space (same space as the recording's `world` coordinates), plus the world matrix of every object and the vertex/triangle counts."""
import bpy, sys, os, json
import numpy as np

out, edited = sys.argv[sys.argv.index("--") + 1], set(sys.argv[sys.argv.index("--") + 2].split(","))
os.makedirs(out, exist_ok=True); dg = bpy.context.evaluated_depsgraph_get()
cands = [o for o in bpy.data.objects if o.type == "MESH" and o.name not in edited and len(o.data.vertices) >= 20000]
cands.sort(key=lambda o: -len(o.data.vertices)); cands = cands[:2]; arrs = {}; info = {"refs": [], "edited": {}}
rng = np.random.default_rng(0)
for o in cands:
    me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles()
    nv = len(me.vertices); V = np.empty(nv * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    M = np.array(o.matrix_world); V = V @ M[:3, :3].T + M[:3, 3]
    nt = len(me.loop_triangles); T = np.empty(nt * 3, dtype=np.int64); me.loop_triangles.foreach_get("vertices", T); T = T.reshape(-1, 3)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]; cr = np.cross(b - a, c - a); ar = np.linalg.norm(cr, axis=1)
    idx = rng.choice(nt, 60000, p=ar / ar.sum()); u = rng.random((60000, 2)); f = u.sum(1) > 1; u[f] = 1 - u[f]
    P = a[idx] + u[:, :1] * (b[idx] - a[idx]) + u[:, 1:] * (c[idx] - a[idx]); N = cr[idx] / np.maximum(ar[idx, None], 1e-12)
    arrs[o.name + "__points"] = P.astype(np.float32); arrs[o.name + "__normals"] = N.astype(np.float16)
    info["refs"].append({"name": o.name, "verts": nv, "tris": nt, "area_m2": float(ar.sum() / 2), "matrix_world": [list(r) for r in o.matrix_world]})
    o.evaluated_get(dg).to_mesh_clear()
for n in edited:
    o = bpy.data.objects.get(n)
    if o: info["edited"][n] = {"verts_at_start": len(o.data.vertices), "matrix_world": [list(r) for r in o.matrix_world]}
np.savez_compressed(os.path.join(out, "ref.npz"), **arrs); json.dump(info, open(os.path.join(out, "ref.json"), "w"), indent=1)
