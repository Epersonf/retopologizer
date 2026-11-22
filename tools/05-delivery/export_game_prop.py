"""export_game_prop: a prop that rides a skeleton bone in the game (headband, skirt, bracelet) as FBX + albedo + normal.
Vertices go to the SKELETON space of the body, so the game only needs a placement equal to the inverse of the bone rest
(rotation 0, scale 1 when the rest is a pure translation). Braziletto: docs/models-3d.md and docs/body-props.md there.
Inside Blender: exec the file, then `export_game_prop(low_obj, "CurupiraSaia", game_dir, albedo_png, normal_png)`."""
import math
import shutil
import bpy
from mathutils import Matrix

# Curupira: Blender (Y front, Z up) -> skeleton space is a half turn around Z plus this shift along Y
# (nose tip: Blender y 0.1541 = game z 0.1895). Another body: measure one landmark and pass its own shift.
CURUPIRA_SHIFT = 0.0354


def export_game_prop(low, name, game_dir, albedo=None, normal=None, shift=CURUPIRA_SHIFT):
    if albedo:
        shutil.copy(albedo, f"{game_dir}/Albedo{name}.png")
    if normal:
        shutil.copy(normal, f"{game_dir}/Normal{name}.png")
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name])
    ob = bpy.data.objects.new(name, low.data.copy())
    bpy.context.scene.collection.objects.link(ob)
    ob.data.transform(Matrix.Translation((0, -shift, 0)) @ Matrix.Rotation(math.pi, 4, "Z") @ low.matrix_world)
    ob.data.update()
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    if albedo:
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(f"{game_dir}/Albedo{name}.png")
        mat.node_tree.links.new(tex.outputs[0], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=f"{game_dir}/{name}.fbx", use_selection=True, object_types={"MESH"},
                             apply_scale_options="FBX_SCALE_UNITS", bake_space_transform=True, path_mode="STRIP",
                             mesh_smooth_type="FACE")
    return [round(x, 3) for x in ob.dimensions]
