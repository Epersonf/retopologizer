"""One part of a retopo on its own: the faces a round added to (or changed in) the artist's mesh, as a separate object
for QA, close-up renders and delivery (an OBJ the artist imports into their own file). Guide: docs/02-retopology/retopo-by-parts.md.
  p = part_object("LowPoly", "LowPoly_user", "Cuca_mao")   # faces of LowPoly that are not in the untouched mesh
  topo_qa("Cuca_mao", Ref("HiPoly"))                        # open edges: only the joining ring(s) (+ the x=0 seam)
  export_obj("Cuca_mao", r"<folder>/cuca_mao.obj")
A face is new when its corner positions (rounded to 0.01 mm) are not a face of the base mesh: faces with new vertices,
new faces between old vertices, and old faces whose vertices moved. `also` adds the faces around some vertices of the
result (by index), e.g. faces the artist had started for this part."""
import bpy, bmesh


def _key(f):
    return tuple(sorted(tuple(round(c, 5) for c in v.co) for v in f.verts))


def part_object(obj, base, name, also=()):
    """New object `name` (same transform as `obj`) holding only the part's faces; an older `name` is replaced."""
    o = bpy.data.objects[obj]
    b = bmesh.new(); b.from_mesh(bpy.data.meshes[base] if base in bpy.data.meshes else bpy.data.objects[base].data)
    old = {_key(f) for f in b.faces}; b.free()
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    keep = {f for i in also for f in bm.verts[i].link_faces} | {f for f in bm.faces if _key(f) not in old}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in keep], context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    p = bpy.data.objects.new(name, me); p.matrix_world = o.matrix_world.copy()
    bpy.context.scene.collection.objects.link(p)
    return p


def export_obj(name, path):
    """OBJ of this one object (Blender's default axes, Y up and -Z forward: imported with the defaults it lands in
    place), no modifiers, no materials. Returns faces by number of sides and the open edges."""
    p = bpy.data.objects[name]
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    p.select_set(True); bpy.context.view_layer.objects.active = p
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=True, apply_modifiers=False, export_materials=False)
    sides, use = {}, {}
    for f in p.data.polygons:
        sides[f.loop_total] = sides.get(f.loop_total, 0) + 1
        for k in f.edge_keys:
            use[k] = use.get(k, 0) + 1
    return {"obj": path, "faces": len(p.data.polygons), "sides": sides, "open_edges": sum(n == 1 for n in use.values())}
