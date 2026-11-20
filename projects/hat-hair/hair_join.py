"""Joins Hair_hood and every Hair_tube_NN of the worker scene into one object "LowPoly", runs the whole QA battery (tools/03-qa/qa_suite.py:
mesh, budget, shape, floating, attach, local, strict, fit), and only if all pass saves draft/hair_lowpoly_v3.blend and exports
output/hair_lowpoly.obj. A failure raises with the report lines; the file is then kept as draft/hair_lowpoly_rejected.blend.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_join.py"""
import bpy
H = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair"
if "LowPoly" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["LowPoly"])
src = [bpy.data.objects["Hair_hood"]] + sorted([o for o in bpy.data.objects if o.name.startswith("Hair_tube_")], key=lambda o: o.name)
parts = []
for o in src:                                            # join COPIES: Hair_hood and the tubes stay for the next iteration (hair_build.py tubes)
    c = o.copy(); c.data = o.data.copy(); c.name = "J_" + o.name; bpy.context.scene.collection.objects.link(c); parts.append(c)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active; ob.name = ob.data.name = "LowPoly"
for n in ("Hair_locks", "Hair_t"):
    if n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[n])
exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\03-qa\qa_suite.py").read())
qa = qa_suite(ob.name, ref="HairFull")
if not qa["pass"]:                                       # rejected: inspect it under another name, never as the deliverable
    bpy.ops.wm.save_as_mainfile(filepath=H + r"\draft\hair_lowpoly_rejected.blend")
    raise AssertionError("REJECTED %s\n%s" % (qa["failed"], "\n".join(qa["lines"])))
bpy.ops.wm.save_as_mainfile(filepath=H + r"\draft\hair_lowpoly_v3.blend")
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
bpy.ops.wm.obj_export(filepath=H + r"\output\hair_lowpoly.obj", export_selected_objects=True)
m = ob.data
result = {"quads": sum(len(p.vertices) == 4 for p in m.polygons), "triangles_equiv": 2 * len(m.polygons), "qa": qa["lines"]}
