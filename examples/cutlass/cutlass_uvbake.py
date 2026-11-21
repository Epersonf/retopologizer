# One UV atlas for the 4 parts and bake from the reference (albedo, normal, roughness, metallic, AO).
import bpy, os
import os
ROOT = os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd()).replace("\\", "/").rstrip("/") + "/"
P = ROOT + "projects/cutlass/"
bpy.ops.wm.open_mainfile(filepath=P + "draft/cutlass_grip.blend")
LOW = ["Blade", "Crossguard", "KnuckleBow", "Grip"]
exec(open(ROOT + "tools/general/cycles_gpu.py").read())
exec(open(ROOT + "tools/04-uv-bake/bake_robust.py").read())
mat = bpy.data.objects["REFERENCE"].active_material
links = [(l.from_node.type, l.to_socket.name) for l in mat.node_tree.links]
low_mat = bpy.data.materials.get("cutlass") or bpy.data.materials.new("cutlass"); low_mat.use_nodes = True
for n in LOW:
    o = bpy.data.objects[n]; o.data.materials.clear(); o.data.materials.append(low_mat)
unwrap_atlas(LOW, margin=0.012, angle=66)
uv = qa_uv(LOW, size=1024, min_gap_px=4)
bpy.ops.wm.save_as_mainfile(filepath=P + "draft/cutlass_uv.blend")
os.makedirs(P + "output", exist_ok=True)
r = bake_robust(LOW, "REFERENCE", P + "output", "cutlass", size=1024, high_mat=mat.name)
bpy.ops.wm.save_as_mainfile(filepath=P + "draft/cutlass_baked.blend")
result = {"ref_links": links, "uv_pass": uv.get("pass"), "uv": {k: uv[k] for k in uv if k not in ("maps",) and not hasattr(uv[k], "shape")},
          "bake": {k: r[k] for k in r if k in ("device", "invalid_pct", "passes", "worst_unbaked_faces", "poor_fit_faces_mm", "files")}}
