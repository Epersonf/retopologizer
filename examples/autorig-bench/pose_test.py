"""Deformation check of the auto-rigged bench models (output/rigged/<case>.blend): a hard test pose (arms down and
forward, elbows, a hip and a knee bent, the other leg out, spine twisted and bent, head turned, fingers curled, tail
swung) rendered next to the rest pose: output/pose/<case>_<rest|pose>_<view>.png, then pose_sheet.py.
  "<blender.exe>" -b --factory-startup --python tools/general/blender_once.py -- examples/autorig-bench/pose_test.py"""
import math, os, sys
import bpy
from mathutils import Matrix
ROOT = os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd())             # the repo root (run from it, or set RETOPOLOGIZER_ROOT)
sys.path.insert(0, ROOT + r"\tools\general")
from render_views import render_views

OUT = ROOT + r"\projects\autorig-bench\output"
P = "mixamorig:"
CURL = [(f"{s}Hand{f}{i}", "Y", 35 * (1 if s == "Left" else -1))
        for s in ("Left", "Right") for f in ("Index", "Middle", "Ring", "Pinky") for i in (3, 2, 1)]
POSE = CURL + [("LeftForeArm", "Z", -70), ("RightForeArm", "Z", 70), ("LeftArm", "Y", 50), ("RightArm", "Y", -50),
               ("LeftShoulder", "Y", -12), ("LeftLeg", "X", 70), ("LeftUpLeg", "X", -50), ("RightUpLeg", "Y", 25),
               ("Head", "Z", 35), ("Spine2", "X", 15), ("Spine1", "Z", 25)] + \
       [("Tail%d" % i, "Z", 12) for i in (5, 4, 3, 2, 1)]


def turn(rig, name, axis, deg):
    """Rotate a pose bone about its head by `deg` around a world axis (children follow)."""
    pb = rig.pose.bones.get(P + name)
    if pb is None:
        return
    m = pb.matrix.copy(); t = m.translation.copy()
    m = Matrix.Rotation(math.radians(deg), 4, axis) @ m; m.translation = t
    pb.matrix = m; bpy.context.view_layer.update()


done = []
for case in globals().get("CASES") or ["male", "female", "saci", "cuca"]:
    bpy.ops.wm.open_mainfile(filepath=OUT + r"\rigged\%s.blend" % case)
    rig = bpy.data.objects["Auto_Rig"]; body = [o.name for o in bpy.data.objects if o.type == 'MESH']
    os.makedirs(OUT + r"\pose", exist_ok=True)
    render_views(body, (OUT + r"\pose").replace("\\", "/"), case + "_rest", views=["front"], res=520)
    for name, axis, deg in POSE:
        turn(rig, name, axis, deg)
    render_views(body, (OUT + r"\pose").replace("\\", "/"), case + "_pose", views=["front", "persp"], res=520)
    done.append(case)
result = done
