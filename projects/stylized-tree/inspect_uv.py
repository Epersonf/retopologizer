import bpy, json
col = bpy.data.collections["tree_low"]
ref = bpy.data.objects["REF_tree_highpoly"]
m = ref.data.materials[0]
info = {
    "objs": [(o.name, [u.name for u in o.data.uv_layers], len(o.data.polygons),
              [s.material.name if s.material else None for s in o.material_slots]) for o in col.objects],
    "nodes": [(n.type, n.name, (n.image.name, list(n.image.size)) if n.type == 'TEX_IMAGE' and n.image else None)
              for n in m.node_tree.nodes],
}
print("INFO" + json.dumps(info))
