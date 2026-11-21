"""Export ONE mesh (no armature) for the Mixamo auto-rigger: scale applied, Y-up FBX, albedo embedded.
  "<blender.exe>" -b --factory-startup --python tools/06-rig/export_for_mixamo.py -- model.blend MeshName albedo.png out.fbx
Check the character faces the way YOU want it to move (Mixamo follows the feet/markers you place, not the face):
a character with backwards feet must be rigged looking toward its toes. Upload the FBX at mixamo.com (T-pose,
markers on chin, wrists, elbows, knees, groin), download "With Skin" FBX and validate it (docs/08-cases/curupira.md)."""
import sys, bpy

blend, name, albedo, out = sys.argv[sys.argv.index("--") + 1:][:4]
bpy.ops.wm.open_mainfile(filepath=blend)
for o in list(bpy.data.objects):
    if o.name != name:
        bpy.data.objects.remove(o)
ob = bpy.data.objects[name]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
mat = bpy.data.materials.new(name)
mat.use_nodes = True
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(albedo)
mat.node_tree.links.new(tex.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
ob.data.materials.clear()
ob.data.materials.append(mat)
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={'MESH'}, apply_scale_options='FBX_SCALE_UNITS',
                         path_mode='COPY', embed_textures=True)
print("MIXAMO_EXPORT", out, [round(x, 3) for x in ob.dimensions])
