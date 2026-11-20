"""Loads draft/hair_tubes.npz into the worker as one object per tube (Hair_tube_NN), replaces Hair_locks, prints per-tube QA
(quads, mean/max distance of the vertices to HairFull in mm, closed + outward by signed volume). Then renders via hair_views.py.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_tubes_load.py"""
import bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
for o in list(bpy.data.objects):
    if o.name.startswith("Hair_tube_") or o.name in ("Hair_locks", "Hair_t"):
        bpy.data.objects.remove(o)
D = np.load(r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft\hair_tubes.npz")
ref = bpy.data.objects["HairFull"]; me = ref.data; me.calc_loop_triangles()
bvh = BVHTree.FromPolygons([tuple(ref.matrix_world @ v.co) for v in me.vertices], [tuple(t.vertices) for t in me.loop_triangles])
rows = []; names = []
for k in D.files:
    if k[0] != "v":
        continue
    V, F = D[k], D["f" + k[1:]]; nm = "Hair_tube_%02d" % (int(k[1:]) + 1); mesh = bpy.data.meshes.new(nm)
    mesh.from_pydata(V.tolist(), [], F.tolist()); mesh.update(); ob = bpy.data.objects.new(nm, mesh)
    bpy.context.scene.collection.objects.link(ob); names.append(nm)
    d = np.array([np.linalg.norm(np.array(bvh.find_nearest(tuple(v))[0]) - v) for v in V]) * 1000
    vol = sum(np.dot(V[f[0]], np.cross(V[f[i]], V[f[i + 1]])) / 6 for f in F for i in (1, 2))
    rows.append((nm, len(F), round(d.mean(), 1), round(d.max(), 1), vol > 0))
result = {"tubes": rows, "quads": sum(r[1] for r in rows), "names": names}
