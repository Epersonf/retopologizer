"""Makes every hair tube BURIED in what it grows from (normal python; the worker is up with the capped Hair_hood).
Loop: hair_tubes.py -> load the tubes in Blender -> two checks -> fix -> again, until both pass (max 8 passes):
  qa_floating   a tube that floats: its nearest end is moved to a point 1.3 radius BELOW the nearest surface (along the inward normal)
                (draft/hair_ext.json, read by hair_tubes.py)
  qa_attach     a tube that only touches, or whose end cap pokes out of the parent: the same, 0.4 radius deeper each pass (max 3)
  python -I projects/hat-hair/hair_connect.py [min_len=0.06] [budget=450]"""
import json, subprocess, sys
import numpy as np
from pathlib import Path
H = Path(__file__).resolve().parent; ROOT = H.parent.parent; ARGS = sys.argv[1:] or ["0.06", "450"]
EXT = H / "draft" / "hair_ext.json"; EXT.unlink(missing_ok=True)
Q = ROOT / "tools" / "03-qa"
QA = r"""
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
for f in ("qa_faces", "qa_shape", "qa_floating", "qa_attach"):
    exec(open(r'%s' + "\\" + f + ".py").read())
names = ["Hair_hood"] + sorted(o.name for o in bpy.data.objects if o.name.startswith("Hair_tube_"))
r = qa_floating(names)
V, F = [], []                                                              # one temp object with the parts in order: part k is Hair_tube_k
for n in names:
    o = bpy.data.objects[n]; b = len(V); V += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]; F += [tuple(b + i for i in p.vertices) for p in o.data.polygons]
me = bpy.data.meshes.new("_qa_tmp"); me.from_pydata(V, [], F); me.update(); tmp = bpy.data.objects.new("_qa_tmp", me); bpy.context.scene.collection.objects.link(tmp)
loose = qa_attach("_qa_tmp")["loose"]; bpy.data.objects.remove(tmp); bpy.data.meshes.remove(me)
own = [n for n in names for _ in bpy.data.objects[n].data.polygons]            # owner of every face of the temp object
def nearest_other(name, pt):
    # (point, outward normal) of the surface of everything but `name` nearest to pt: a tube must be buried PERPENDICULAR to it
    t = BVHTree.FromPolygons(V, [f for f, o in zip(F, own) if o != name], epsilon=0.0); h = t.find_nearest(Vector(pt))
    back = t.ray_cast(h[0] - h[1] * 1e-4, -h[1], 0.3)                       # the far wall of that part: how deep it is, so we stop at its middle
    return [round(x, 5) for x in h[0]], [round(x, 5) for x in h[1]], round(back[3], 4) if back[0] is not None else 9.0
for f in r["floating"]:
    me = bpy.data.objects[f["object"]].data; W = [v.co for v in me.vertices]; ends = W[-2:]       # tip cap vertex, root cap vertex
    f["near"] = "tip" if (ends[0] - Vector(f["end"])).length < (ends[1] - Vector(f["end"])).length else "root"
    f["radius"] = (W[0] - W[1]).length; f["to"], f["n"], f["th"] = nearest_other(f["object"], f["end"])
for l in loose:
    W = bpy.data.objects[names[l["part"]]].data.vertices; e = Vector(l["end_at"]); l["object"] = names[l["part"]]
    l["near"] = "tip" if (W[-2].co - e).length < (W[-1].co - e).length else "root"; l["to"], l["n"], l["th"] = nearest_other(l["object"], l["end_at"])
result = {"pass": r["pass"] and not loose, "floating": r["floating"], "loose": loose}
""" % Q


def rpc(*a):
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools/general/blender_rpc.py"), "--port", "9877", *a], capture_output=True, text=True)
    return r.stdout


ext = {}; dep = {}
for it in range(4):
    subprocess.run([sys.executable, "-I", str(H / "hair_tubes.py"), *ARGS], capture_output=True)
    rpc(str(H / "hair_tubes_load.py"))
    tmp = H / "draft" / "_qa.py"; tmp.write_text(QA, encoding="utf-8")
    out = rpc(str(tmp)); r = json.loads(out[out.index("{"):out.rindex("}") + 1])
    print("connect pass %d: floating %d, not buried %d %s" % (it, len(r["floating"]), len(r["loose"]), [l["object"][-2:] for l in r["loose"]]))
    if r["pass"]:
        break
    for f in r["floating"] + r["loose"]:                 # bury the end perpendicular to the surface it must grow from, deeper each pass
        rad = f.get("radius") or f["radius_cm"] / 100; i = str(int(f["object"].split("_")[-1]) - 1); e = ext.setdefault(i, [1.6 * rad, 0.0, None, None])
        dep[i] = 1.5
        q, n = np.array(f["to"]), np.array(f["n"]); inner, outer = q - n * min(dep[i] * rad, 0.5 * f["th"]), q + n * 1.2 * rad    # leave the parent along its normal
        e[2 if f["near"] == "root" else 3] = [list(inner), list(outer)] if f["near"] == "root" else [list(outer), list(inner)]
    EXT.write_text(json.dumps(ext))
