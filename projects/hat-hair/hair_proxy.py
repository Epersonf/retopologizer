"""Adds a measuring mesh to the worker's scene from an npz (V, F in world space): "HairOuter" (outer faces only,
hair_outer_mask.py) by default, or any NPZ / NAME set before running ("HairFull" = hair_in.npz, every face of the hair,
for selections that must see the grooves). Hidden from render; the reference itself is untouched.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_proxy.py"""
import numpy as np
import bpy

DRAFT = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft"
NAME = globals().get("NAME", "HairOuter"); NPZ = globals().get("NPZ", DRAFT + r"\hair_outer.npz")
d = np.load(NPZ); V, F = d["V"].astype(np.float32), d["F"].astype(np.int32)
if NAME in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects[NAME])
me = bpy.data.meshes.new(NAME)
me.vertices.add(len(V)); me.vertices.foreach_set("co", V.ravel())
me.loops.add(len(F) * 3); me.loops.foreach_set("vertex_index", F.ravel())
me.polygons.add(len(F)); me.polygons.foreach_set("loop_start", np.arange(0, len(F) * 3, 3, dtype=np.int32))
me.polygons.foreach_set("loop_total", np.full(len(F), 3, np.int32)); me.update(); me.validate()
o = bpy.data.objects.new(NAME, me); bpy.context.scene.collection.objects.link(o); o.hide_render = True
result = {"name": NAME, "verts": len(V), "polys": len(F)}
