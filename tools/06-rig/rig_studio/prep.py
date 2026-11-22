"""Blender side of the rig studio: loads the uploaded model, turns it (yaw about the vertical, flip head over heels),
applies the transforms and writes norm.blend (for the auto-rig) and preview.glb (for the page).
  blender -b --factory-startup --python prep.py -- model.ext workdir yaw_deg flip(0|1)"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))        # tools/06-rig
import bpy
from mathutils import Matrix
from autorig.load import load_model

src, work, yaw, flip = sys.argv[sys.argv.index("--") + 1:][:4]
meshes = load_model(os.path.abspath(src))
R = Matrix.Rotation(math.radians(float(yaw)), 4, 'Z') @ (Matrix.Rotation(math.pi, 4, 'X') if flip == "1" else Matrix.Identity(4))
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.matrix_world = R @ o.matrix_world
    o.select_set(True); bpy.context.view_layer.objects.active = o
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, "norm.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(work, "preview.glb"), export_format='GLB', use_selection=False)
print("PREP_OK", flush=True)
