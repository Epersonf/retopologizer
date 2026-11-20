"""Joins Hair_hood and every Hair_tube_NN of the worker scene into one object "LowPoly", checks winding (edges whose two
faces run the same way), runs the STRICT gates (qa_strict.py reversed faces, qa_floating.py; rejected = nothing is saved), saves draft/hair_lowpoly_v3.blend and exports output/hair_lowpoly.obj. Prints quads / triangles.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_join.py"""
import bpy, bmesh
H = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair"
parts = [bpy.data.objects["Hair_hood"]] + sorted(
    [o for o in bpy.data.objects if o.name.startswith("Hair_tube_")], key=lambda o: o.name)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active; ob.name = ob.data.name = "LowPoly"
for n in ("Hair_locks", "Hair_t"):
    if n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[n])
bm = bmesh.new(); bm.from_mesh(ob.data); bad = 0
for e in bm.edges:
    if len(e.link_faces) == 2:
        a, b = e.link_faces; la = [l for l in a.loops if l.edge == e][0]; lb = [l for l in b.loops if l.edge == e][0]
        bad += la.vert == lb.vert
exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\03-qa\qa_faces.py").read())
exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\03-qa\qa_strict.py").read())
healed = qa_strict([ob.name])
assert healed["pass"], "REJECTED: faces seen from the back %s" % healed["faces"]       # not one ray may hit the back of a face
healed.pop("_all")
exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\03-qa\qa_floating.py").read())
fl = qa_floating([ob.name])
assert fl["pass"], "REJECTED: floating parts %s" % fl["floating"]       # the relaxing must not detach a tube
bpy.ops.wm.save_as_mainfile(filepath=H + r"\draft\hair_lowpoly_v3.blend")
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
bpy.ops.wm.obj_export(filepath=H + r"\output\hair_lowpoly.obj", export_selected_objects=True)
m = ob.data
result = {"quads": sum(len(p.vertices) == 4 for p in m.polygons), "not_quads": sum(len(p.vertices) != 4 for p in m.polygons),
          "triangles_equiv": 2 * len(m.polygons), "bad_winding_edges": bad, "strict_qa": healed}
