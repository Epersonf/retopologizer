"""Finalize low-poly objects: collections, UVs, material, budget check, blend save, FBX export.
Inside Blender: exec(open(...).read()); finalize(["chest_base","chest_lid"], "REF_...", fbx, blend, budget=2000)
"""
import bpy, math


def _uv(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003)
    bpy.ops.object.mode_set(mode='OBJECT')


def finalize(names, ref_name, fbx_path, blend_path, budget=2000, mat_name="chest_mat"):
    sc = bpy.context.scene
    col_lp = bpy.data.collections.get("LOWPOLY") or bpy.data.collections.new("LOWPOLY")
    col_ref = bpy.data.collections.get("REFERENCE") or bpy.data.collections.new("REFERENCE")
    for c in (col_lp, col_ref):
        if c.name not in sc.collection.children:
            sc.collection.children.link(c)
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    mat.diffuse_color = (0.55, 0.42, 0.30, 1)
    total = 0
    for n in names:
        ob = bpy.data.objects[n]
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col_lp.objects.link(ob)
        ob.data.materials.clear(); ob.data.materials.append(mat)
        _uv(ob)
        ob.data.calc_loop_triangles(); total += len(ob.data.loop_triangles)
    ref = bpy.data.objects[ref_name]
    for c in list(ref.users_collection):
        c.objects.unlink(ref)
    col_ref.objects.link(ref)
    assert total <= budget, f"over budget: {total} > {budget}"
    bpy.ops.object.select_all(action='DESELECT')
    for n in names:
        bpy.data.objects[n].select_set(True)
    bpy.ops.export_scene.fbx(filepath=fbx_path, use_selection=True, apply_scale_options='FBX_SCALE_ALL',
                             axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE',
                             add_leaf_bones=False, bake_space_transform=False)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    return {"tris_total": total, "budget": budget, "fbx": fbx_path, "blend": blend_path}
