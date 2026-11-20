"""Cut the piece of the reference that belongs to one low-poly part and put it in that part's LOCAL
space (so rotated/parented parts can be sculpted-snapped in their own frame, e.g. a lid in its closed pose).
  exec(open(...).read()); ref_part("REFERENCE", "chest_lid", "REF_LID", radius=0.06)
Keeps reference triangles whose centre is within `radius` of the part (rough old version of the part is
enough; raise radius if a detail is missing, lower it to drop neighbours). The result is a helper object:
keep it in draft/, never in output/ or the lean blend."""
import bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree


def ref_part(ref_name, part_name, out_name, radius=0.06):
    ref, part = bpy.data.objects[ref_name], bpy.data.objects[part_name]
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    me = ref.data; me.calc_loop_triangles()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(ref.matrix_world); cow = co @ M[:3, :3].T + M[:3, 3]        # reference may be rotated
    tri = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", tri)
    cen = cow[tri.reshape(-1, 3)].mean(1)
    pm = part.data; pm.calc_loop_triangles()
    bv = BVHTree.FromPolygons([tuple(part.matrix_world @ v.co) for v in pm.vertices],
                              [tuple(t.vertices) for t in pm.loop_triangles])      # WORLD space BVH
    keep = np.zeros(len(cen), bool)
    for i, c in enumerate(cen):
        keep[i] = bv.find_nearest(c.tolist(), radius)[0] is not None
    m2 = me.copy(); m2.name = out_name + "_mesh"; m2.transform(ref.matrix_world)
    bm = bmesh.new(); bm.from_mesh(m2); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep[f.index]], context='FACES')
    bm.to_mesh(m2); bm.free()
    m2.transform(part.matrix_world.inverted())
    o = bpy.data.objects.new(out_name, m2); bpy.context.scene.collection.objects.link(o)
    return {"tris_kept": int(keep.sum())}
