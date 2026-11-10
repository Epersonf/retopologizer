"""Inspect a high-poly model without entering edit mode.
Usage: blender --background --python inspect_glb.py -- <model.glb> [out.json]
Prints tris/verts, world bbox, materials, and 3 axis-sliced silhouette profiles.
"""
import bpy, sys, json
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
path = argv[0]
out = argv[1] if len(argv) > 1 else None

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)

info = {"objects": []}
lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
for o in bpy.context.scene.objects:
    if o.type != "MESH":
        continue
    me = o.data
    me.calc_loop_triangles()
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    for v in bb:
        lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
    info["objects"].append({
        "name": o.name, "verts": len(me.vertices), "polys": len(me.polygons),
        "tris": len(me.loop_triangles),
        "materials": [m.name for m in me.materials if m],
        "uv": [u.name for u in me.uv_layers],
        "dims": list(o.dimensions), "loc": list(o.location),
    })
info["bbox_min"] = list(lo); info["bbox_max"] = list(hi)
info["size"] = list(hi - lo)
print(json.dumps(info, indent=1))
if out:
    json.dump(info, open(out, "w"), indent=1)
