"""Regenerate output/ (PNGs + FBX) from the lean, committed .blend (images are packed in it).
  blender --background <project>/<name>.blend --python tools/05-delivery/export_from_blend.py -- <outdir> <prefix>
Writes <prefix>_{basecolor,normal,roughness,metallic,ao}.png and <prefix-less name>.fbx."""
import bpy, sys, os

argv = sys.argv[sys.argv.index("--") + 1:]
outdir, prefix = argv[0], argv[1]
os.makedirs(outdir, exist_ok=True)
saved = []
for img in bpy.data.images:
    if not img.name.startswith("bake_"):
        continue
    kind = img.name[len("bake_"):].split(".")[0]
    path = os.path.join(outdir, f"{prefix}_{kind}.png")
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    saved.append(path)

lows = [o for o in bpy.data.objects if o.type == 'MESH']
for o in lows:  # lean blends written with libraries.write are not linked to a scene
    if o.name not in bpy.context.scene.objects:
        bpy.context.scene.collection.objects.link(o)
bpy.ops.object.select_all(action='DESELECT')
for o in lows:
    o.select_set(True)
fbx = os.path.join(outdir, os.path.splitext(os.path.basename(bpy.data.filepath))[0] + ".fbx")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, path_mode='RELATIVE',
                         apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
                         mesh_smooth_type='FACE', add_leaf_bones=False)
print("EXPORTED", saved, fbx)
