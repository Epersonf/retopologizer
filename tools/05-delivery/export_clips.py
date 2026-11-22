"""One call exports an animated creature for the game AND for a store: GLB (Godot, clips as AnimationPlayer animations),
FBX with every action baked, and the zip for Fab. Inside Blender (worker):
  exec(open(r"<repo>\tools\05-delivery\export_clips.py", encoding="utf-8").read())
  export_clips(rig, mesh, "projects/x/output", "Gator", tex={"basecolor": "a.png", "normal": "n.png"}, game_tex=...)
Returns {"glb": path, "fbx": path, "actions": [...]}; every action needs a fake user (pose_actions.PoseAnim.new does it).
Godot: the GLB goes to frontend/godot-client/creatures/<name>.glb and a shape in creatures/creatures.json (clips idle/walk/attack/death).
Fab: afterwards `python tools/05-delivery/fab_package.py <dir with Name.fbx> <textures dir> <out> Name --formats fbx`.
Textures: 1024 PNG for the game, 2048 for the store (swap the image nodes before each export; Godot 4.7 does not read Blender 5's JPEG)."""
import bpy, os


def _wire(mat_name, tex):
    for n in bpy.data.materials[mat_name].node_tree.nodes:
        if n.type != 'TEX_IMAGE' or not n.image: continue
        key = "normal" if "normal" in n.image.name.lower() else "basecolor"
        if key in tex:
            n.image = bpy.data.images.load(tex[key])
            if key == "normal": n.image.colorspace_settings.name = 'Non-Color'


def export_clips(rig, mesh, out_dir, name, mat_name=None, game_tex=None, store_tex=None, glb=True, fbx=True):
    os.makedirs(out_dir, exist_ok=True); res = {"actions": sorted(a.name for a in bpy.data.actions)}
    missing = [a.name for a in bpy.data.actions if not a.use_fake_user]
    if missing: raise RuntimeError("actions without fake user would be lost: %s" % missing)
    if bpy.context.object and bpy.context.object.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    for o in bpy.context.view_layer.objects: o.select_set(o in (rig, mesh))
    bpy.context.view_layer.objects.active = rig
    mat = mat_name or mesh.material_slots[0].material.name
    if glb:
        if game_tex: _wire(mat, game_tex)
        res["glb"] = os.path.join(out_dir, name + ".glb")
        bpy.ops.export_scene.gltf(filepath=res["glb"], use_selection=True, export_animations=True, export_animation_mode='ACTIONS', export_image_format='AUTO')
    if fbx:
        if store_tex: _wire(mat, store_tex)
        res["fbx"] = os.path.join(out_dir, name + ".fbx")
        bpy.ops.export_scene.fbx(filepath=res["fbx"], use_selection=True, path_mode='COPY', embed_textures=False, add_leaf_bones=False, bake_anim=True,
                                 bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0,
                                 object_types={'ARMATURE', 'MESH'}, mesh_smooth_type='FACE')
    return res
