"""Benchmark cases for tools/autorig: one static mesh "Body" per case (input/<case>.blend) and the reference joints
(input/<case>_gt.json, world metres, Mixamo names without prefix). Mixamo bodies: the mesh as shown (posed by the
file's own T-pose take) and the posed bone heads, or (_bind) the bind pose and the rest skeleton; Saci and Cuca: their
hand-made rigs at rest.
  python tools/blender_rpc.py --port 9877 projects/autorig-bench/prep_cases.py"""
import bpy, json, os
IN = r"C:\Users\epers\Desktop\retopologizer\projects\autorig-bench\input"
CHARS = r"C:\Users\epers\Documents\Repositories\Personal\Braziletto\frontend\godot-client\assets\characters"
ALL = {"male": ("fbx", CHARS + r"\BaseMaleBody.fbx", None, "Armature"),
         "female": ("fbx", CHARS + r"\BaseFemaleBody.fbx", None, "Armature"),
         "male_bind": ("fbx_rest", CHARS + r"\BaseMaleBody.fbx", None, "Armature"),
         "female_bind": ("fbx_rest", CHARS + r"\BaseFemaleBody.fbx", None, "Armature"),
         "saci": ("blend", r"C:\Users\epers\Desktop\retopologizer\projects\stylized-saci\draft\saci_retopo.blend", "Saci_Body", "Saci_Rig"),
         "cuca": ("blend", r"C:\Users\epers\Desktop\retopologizer\projects\stylized-cuca\draft\cuca_rig.blend", "Cuca_Body", "Cuca_Rig")}
CASES = {k: ALL[k] for k in (globals().get("ONLY") or ALL)}
done = {}
for case, (kind, path, body, rig) in CASES.items():
    if kind.startswith("fbx"):
        bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.wm.open_mainfile(filepath=path)
    arm = bpy.data.objects[rig]
    if kind != "fbx":                         # rest pose: hand-made rigs (the file may sit on an animation frame) and
                                              # the Mixamo bodies' bind pose (what the mesh is without its rig)
        arm.data.pose_position = 'REST'; bpy.context.view_layer.update()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and (body is None or o.name == body)]
    dg = bpy.context.evaluated_depsgraph_get()
    gt = {b.name.replace("mixamorig:", ""): list(arm.matrix_world @ (b.head if kind == "fbx" else arm.data.bones[b.name].head_local))
          for b in arm.pose.bones}
    me = bpy.data.meshes.new_from_object(meshes[0].evaluated_get(dg)); me.transform(meshes[0].matrix_world)
    me.materials.clear(); me.name = "Body"
    o = bpy.data.objects.new("Body", me)
    bpy.data.libraries.write(os.path.join(IN, case + ".blend"), {o, me}, fake_user=True)   # only the mesh, no textures
    json.dump(gt, open(os.path.join(IN, case + "_gt.json"), "w"), indent=0)
    zs = [v.co.z for v in me.vertices]
    done[case] = {"verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons), "h": round(max(zs) - min(zs), 3),
                  "bones": len(gt), "meshes_in_file": [m.name for m in meshes]}
result = done
