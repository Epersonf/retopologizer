"""Automatic quad retopo of a dense reference, snapped back to it (statue as-is, no symmetry needed).
  exec(open(...).read()); auto_quad("REFERENCE", "cow", faces=2000)
1. weld the reference copy (glTF splits vertices; QuadriFlow needs a closed manifold) 2. collapse-decimate to ~60k tris
3. QuadriFlow to `faces` quads (preserve sharp) 4. Shrinkwrap NEAREST_SURFACEPOINT onto the reference (restores form).
Thin parts (tails, whiskers) disappear or detach: delete the loose islands and rebuild those by hand (see build_cow.py).
Result is a new object; the reference is untouched. Run in steps if the MCP times out (~20 s total for 1.5M tris)."""
import bpy, bmesh


def _eval_mesh(ob):
    return bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))


def auto_quad(ref_name, out_name, faces=2000, mid_ratio=0.04, seed=3, sharp=True):
    ref = bpy.data.objects[ref_name]
    for n in ("_aq_tmp", out_name):
        if n in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[n])
    me = ref.data.copy(); bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("_aq_tmp", me); bpy.context.scene.collection.objects.link(o)
    m = o.modifiers.new("c", 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = mid_ratio; m.use_collapse_triangulate = True
    nm = _eval_mesh(o); o.modifiers.remove(m); o.data = nm
    bpy.context.view_layer.objects.active = o
    for x in bpy.data.objects:
        x.select_set(x is o)
    bpy.ops.object.shade_flat()
    r = bpy.ops.object.quadriflow_remesh(target_faces=faces, use_mesh_symmetry=False, use_preserve_sharp=sharp,
                                         smooth_normals=False, seed=seed)
    q = bpy.context.active_object; q.name = out_name
    sw = q.modifiers.new("sw", 'SHRINKWRAP'); sw.target = ref; sw.wrap_method = 'NEAREST_SURFACEPOINT'
    nm = _eval_mesh(q); q.modifiers.remove(sw); q.data = nm
    return {"ret": list(r), "faces": len(q.data.polygons), "tris": sum(len(p.vertices) - 2 for p in q.data.polygons)}


def drop_small_islands(ob, min_verts=60):
    """Delete loose parts with fewer than `min_verts` verts (QuadriFlow leaves the tips of thin parts floating)."""
    bm = bmesh.new(); bm.from_mesh(ob.data); seen = set(); kill = []
    for v in bm.verts:
        if v.index in seen:
            continue
        st, comp = [v], []; seen.add(v.index)
        while st:
            u = st.pop(); comp.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index); st.append(w)
        if len(comp) < min_verts:
            kill += comp
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(ob.data); bm.free()
    return {"removed_verts": len(kill)}
