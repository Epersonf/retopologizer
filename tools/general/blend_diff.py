"""Understand what the artist changed between two saves of the same asset (counts, bbox, moved vertices, thickness, UV, materials).
Run (one-shot, result in RESULT_JSON):
  blender -b --factory-startup --python tools/general/blender_once.py -- script.py     with script.py = exec(open(this file).read()); result = compare_blends(a, "OBJ_A", b, "OBJ_B")
Vertices are matched by nearest position (the artist may join/rename objects, so indices cannot be trusted); `per_material` splits the moved
vertices by the material of a face that uses them. Thickness = distance between the first and last hit of rays along the depth axis (Y)."""
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


def mesh_report(ob, grid=0.02, box=(-0.4, 0.62, 0.02, 0.58)):
    me = ob.data; M = ob.matrix_world; co = np.array([(M @ v.co)[:] for v in me.vertices]); mats = [m.name if m else None for m in me.materials]
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(M); t = BVHTree.FromBMesh(bm); th = []
    for x in np.arange(box[0], box[1], grid):
        for z in np.arange(box[2], box[3], grid):
            o = Vector((x, -1, z)); hits = []
            while True:
                l, n, i, d = t.ray_cast(o, Vector((0, 1, 0)))
                if l is None:
                    break
                hits.append(l.y); o = l + Vector((0, 1e-5, 0))
            if len(hits) >= 2:
                th.append((hits[-1] - hits[0]) * 1000)
    border = sum(1 for e in bm.edges if len(e.link_faces) == 1); nonman = sum(1 for e in bm.edges if len(e.link_faces) > 2); bm.free()
    r = {"verts": len(co), "faces": len(me.polygons), "quads": sum(len(p.vertices) == 4 for p in me.polygons), "tris": sum(len(p.vertices) == 3 for p in me.polygons),
         "border_edges": border, "nonmanifold_edges": nonman, "bbox": [np.round(co.min(0), 3).tolist(), np.round(co.max(0), 3).tolist()], "materials": mats,
         "faces_per_material": {m: sum(1 for p in me.polygons if me.materials[p.material_index] and me.materials[p.material_index].name == m) for m in mats if m},
         "seams": sum(e.use_seam for e in me.edges), "modifiers": [m.type for m in ob.modifiers],
         "thickness_mm": {"mean": round(float(np.mean(th)), 1), "p10": round(float(np.percentile(th, 10)), 1), "p90": round(float(np.percentile(th, 90)), 1), "max": round(float(np.max(th)), 1)} if th else None}
    if me.uv_layers.active:
        uv = np.array([d.uv[:] for d in me.uv_layers.active.data]); r["uv"] = {"layers": [l.name for l in me.uv_layers], "min": np.round(uv.min(0), 3).tolist(), "max": np.round(uv.max(0), 3).tolist()}
    return r, co


def _a_side(obj_a):
    """obj_a: an object name, or a list of names (e.g. the pieces the artist later joined into one). Returns (report of the first, coords of all)."""
    names = [obj_a] if isinstance(obj_a, str) else list(obj_a); r, c = mesh_report(bpy.data.objects[names[0]])
    return r, np.concatenate([c] + [mesh_report(bpy.data.objects[n])[1] for n in names[1:]]) if len(names) > 1 else c


def compare_blends(path_a, obj_a, path_b, obj_b):
    bpy.ops.wm.open_mainfile(filepath=path_a); ra, ca = _a_side(obj_a)
    bpy.ops.wm.open_mainfile(filepath=path_b); ob = bpy.data.objects[obj_b]; rb, cb = mesh_report(ob)
    kd = KDTree(len(ca))
    for i, c in enumerate(ca):
        kd.insert(c, i)
    kd.balance(); d = np.array([kd.find(c)[2] for c in cb]) * 1000; mats = {}
    for p in ob.data.polygons:
        m = ob.data.materials[p.material_index].name if ob.data.materials[p.material_index] else None
        for v in p.vertices:
            mats.setdefault(m, set()).add(v)
    per = {m: {"verts": len(vs), "moved_gt_0.1mm": int((d[list(vs)] > 0.1).sum()), "mean_mm": round(float(d[list(vs)].mean()), 2), "max_mm": round(float(d[list(vs)].max()), 2)} for m, vs in mats.items()}
    return {"a": ra, "b": rb, "moved_mm": {"mean": round(float(d.mean()), 2), "max": round(float(d.max()), 2)}, "per_material": per,
            "same_vertex_count": len(ca) == len(cb)}


def edit_record(path_a, obj_a, path_b, obj_b, min_mm=0.1):
    """What the artist did between save A and save B, as data for the dataset: the vertices that moved (position before/after, in metres, matched by nearest
    position), the face list of B with the UV of every corner (the artist's UV layout), seams and the summary of compare_blends."""
    summ = compare_blends(path_a, obj_a, path_b, obj_b); ob = bpy.data.objects[obj_b]; me = ob.data; M = ob.matrix_world
    cb = np.array([(M @ v.co)[:] for v in me.vertices])
    bpy.ops.wm.open_mainfile(filepath=path_a); ca = _a_side(obj_a)[1]
    bpy.ops.wm.open_mainfile(filepath=path_b); me = bpy.data.objects[obj_b].data
    kd = KDTree(len(ca))
    for i, c in enumerate(ca):
        kd.insert(c, i)
    kd.balance(); moved = []
    for j, c in enumerate(cb):
        loc, i, d = kd.find(c)
        if d * 1000 > min_mm:
            moved.append({"b_index": j, "before": np.round(ca[i], 5).tolist(), "after": np.round(c, 5).tolist(), "mm": round(d * 1000, 2)})
    uvl = me.uv_layers.active.data if me.uv_layers.active else None
    faces = [{"verts": list(p.vertices), "material": me.materials[p.material_index].name if me.materials[p.material_index] else None,
              "uv": [list(np.round(uvl[l].uv[:], 5)) for l in p.loop_indices] if uvl else None} for p in me.polygons]
    return {"summary": summ, "moved_vertices": moved, "faces_uv": faces, "seams": [list(e.vertices) for e in me.edges if e.use_seam]}
