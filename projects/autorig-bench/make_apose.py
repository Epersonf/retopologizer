"""A-pose bench case from the auto-rigged female (output/rigged/female.blend): arms 40 degrees down, written like
prep_cases.py does (input/female_apose.blend + _gt.json; the reference arm joints turned by the same angle).
  "<blender.exe>" -b --factory-startup --python tools/general/blender_once.py -- projects/autorig-bench/make_apose.py"""
import json, math
import bpy
from mathutils import Matrix, Vector
B = r"C:\Users\epers\Desktop\retopologizer\projects\autorig-bench"
DOWN = 40
bpy.ops.wm.open_mainfile(filepath=B + r"\output\rigged\female.blend")
rig = bpy.data.objects["Auto_Rig"]
for side, sign in (("Left", 1), ("Right", -1)):
    pb = rig.pose.bones["mixamorig:%sArm" % side]
    m = pb.matrix.copy(); t = m.translation.copy()
    m = Matrix.Rotation(math.radians(sign * DOWN), 4, "Y") @ m; m.translation = t
    pb.matrix = m; bpy.context.view_layer.update()
src = bpy.data.objects["Body"]
me = bpy.data.meshes.new_from_object(src.evaluated_get(bpy.context.evaluated_depsgraph_get()))
me.transform(src.matrix_world); me.name = "BodyAPose"
src.name = "Body_rigged"; o = bpy.data.objects.new("Body", me)
bpy.data.libraries.write(B + r"\input\female_apose.blend", {o, me}, fake_user=True)
gt = {k: Vector(v) for k, v in json.load(open(B + r"\input\female_gt.json")).items()}
for side, sign in (("Left", 1), ("Right", -1)):
    R, piv = Matrix.Rotation(math.radians(sign * DOWN), 3, "Y"), gt[side + "Arm"].copy()
    for k in [k for k in gt if k.startswith(side + "ForeArm") or k.startswith(side + "Hand")]:
        gt[k] = piv + R @ (gt[k] - piv)
json.dump({k: list(v) for k, v in gt.items()}, open(B + r"\input\female_apose_gt.json", "w"), indent=0)
result = {"verts": len(me.vertices), "LeftHand": [round(x, 3) for x in gt["LeftHand"]]}
