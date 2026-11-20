"""Shows a (V, F) mesh from an npz as an object next to the hair reference, rendered over it from several views. Set NPZ and
NAME (and optionally TAG, VIEWS) before running (worker):  NPZ = "<repo>/projects/hat-hair/draft/x.npz"; NAME = "HairDome"
Renders to draft/renders/<TAG>_<i>.png; the object stays in the scene for wire_overlay."""
import numpy as np
import bpy
NPZ = globals()["NPZ"]; NAME = globals().get("NAME", "HairShow")
d = np.load(NPZ); V, F = d["V"].astype(np.float32), d["F"].astype(np.int32)
if NAME in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects[NAME])
me = bpy.data.meshes.new(NAME)
me.vertices.add(len(V)); me.vertices.foreach_set("co", V.ravel())
me.loops.add(len(F) * 3); me.loops.foreach_set("vertex_index", F.ravel())
me.polygons.add(len(F)); me.polygons.foreach_set("loop_start", np.arange(0, len(F) * 3, 3, dtype=np.int32))
me.polygons.foreach_set("loop_total", np.full(len(F), 3, np.int32)); me.update(); me.validate()
o = bpy.data.objects.new(NAME, me); bpy.context.scene.collection.objects.link(o)
TAG = globals().get("TAG", "show"); LOW = [NAME]; VIEWS = globals().get("VIEWS") or ["front", "back", "left", (65, 0, 35)]
exec(open(r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\hair_views.py", encoding="utf-8").read())
