"""Deformation check of a rigged .blend: forced pose (elbows, hip, knee, spine, head), front and perspective renders.
  "<blender.exe>" -b --factory-startup --python tools/06-rig/pose_check.py -- rigged.blend outdir [prefix]
Look at volume at elbow/knee, armpit, fingers. Do NOT scale the armature object (or apply its scale) to resize a
character: the skin comes out as spikes. Resize the mesh before rigging, or scale in the game."""
import math, os, sys
import bpy
from mathutils import Matrix
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "general"))
from render_views import render_views

args = sys.argv[sys.argv.index("--") + 1:]
blend, outdir, prefix = args[0], args[1], (args + ["pose"])[2]
P = "mixamorig:"
POSE = [("LeftForeArm", "Z", -70), ("RightForeArm", "Z", 70), ("LeftArm", "Y", 50), ("RightArm", "Y", -50),
        ("LeftLeg", "X", 70), ("LeftUpLeg", "X", -50), ("RightUpLeg", "Y", 25), ("Head", "Z", 35), ("Spine2", "X", 15)]
bpy.ops.wm.open_mainfile(filepath=blend)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o.name for o in bpy.data.objects if o.type == 'MESH']
for name, axis, deg in POSE:
    pb = rig.pose.bones.get(P + name)
    if pb is None:
        continue
    m = pb.matrix.copy()
    t = m.translation.copy()
    m = Matrix.Rotation(math.radians(deg), 4, axis) @ m
    m.translation = t
    pb.matrix = m
    bpy.context.view_layer.update()
bpy.context.scene.render.image_settings.media_type = "IMAGE"      # Blender 5: a movie format is the default
bpy.context.scene.render.image_settings.file_format = "PNG"
os.makedirs(outdir, exist_ok=True)
render_views(meshes, outdir.replace("\\", "/"), prefix, views=["front", "persp"], res=520)
