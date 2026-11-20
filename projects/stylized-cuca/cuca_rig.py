"""Cuca rig: Mixamo-named humanoid like the Saci's (thumb + 3 fingers: Index, Middle, Ring) plus a tail chain
(mixamorig:Tail1..Tail5, Tail_End) hanging from the Hips, skinned to her LowPoly (renamed Cuca_Body) in a COPY of
cuca.blend. Joints in world metres, measured on the LowPoly sections (she faces -Y, her LEFT is +X): limb centres
(contour.centred / track), elbow and knee on their middle loops, wrist on the narrowest ring, hip joint on the thigh
axis inside the skirt. The tail bends on every other gap between the scutes, so each scute stays on one bone.
  python tools/general/blender_rpc.py --port 9877 projects/stylized-cuca/cuca_rig.py"""
import sys, bpy
from mathutils import Vector
ROOT = r"C:\Users\epers\Desktop\retopologizer"
sys.path.insert(0, ROOT + r"\tools\02-retopologia"); sys.path.insert(0, ROOT + r"\tools\06-rig")
import importlib, rig_mixamo
importlib.reload(rig_mixamo)
from retopo import Ref, centred
from rig_mixamo import bones, chain, mirror_left, build, skin

BLEND = ROOT + r"\projects\stylized-cuca\draft\cuca_rig.blend"
BODY, RIG = "Cuca_Body", "Cuca_Rig"
TAIL = ["Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail_End"]
J = {"Hips": (0, -0.02, 0.48), "Spine": (0, -0.018, 0.555), "Spine1": (0, -0.027, 0.635), "Spine2": (0, -0.023, 0.715),
     "Neck": (0, -0.004, 0.80), "Head": (0, -0.006, 0.866), "HeadTop_End": (0, -0.006, 1.047),
     "LeftShoulder": (0.025, -0.01, 0.785), "LeftArm": (0.10, 0.003, 0.772), "LeftForeArm": (0.232, 0.011, 0.768),
     "LeftHand": (0.35, -0.003, 0.767),
     "LeftUpLeg": (0.075, -0.035, 0.45), "LeftLeg": (0.111, 0.0, 0.257), "LeftFoot": (0.127, 0.008, 0.08),
     "LeftToeBase": (0.126, -0.08, 0.027), "LeftToe_End": (0.126, -0.154, 0.019),
     "Tail1": (0, 0.05, 0.43), "Tail2": (0, 0.0886, 0.308), "Tail3": (0, 0.1633, 0.179), "Tail4": (0, 0.2383, 0.108),
     "Tail5": (0, 0.317, 0.065), "Tail_End": (0, 0.4255, 0.038)}
# left hand digits: base (knuckle; the thumb root sits over the palm, near the wrist) -> claw tip
DIGITS = {"Thumb": ((0.372, -0.035, 0.752), (0.429, -0.071, 0.709)),
          "Index": ((0.452, -0.034, 0.766), (0.507, -0.032, 0.752)),
          "Middle": ((0.452, -0.001, 0.771), (0.523, 0.003, 0.752)),
          "Ring": ((0.452, 0.031, 0.764), (0.508, 0.035, 0.751))}
FRACS = (0.0, 0.4, 0.72, 1.0)                    # joints 1..4 along the digit (4 = the tip, an end bone)

if bpy.data.filepath != BLEND:
    bpy.ops.wm.open_mainfile(filepath=BLEND)
for o in bpy.data.objects:
    if o.mode != 'OBJECT':
        with bpy.context.temp_override(active_object=o, object=o):
            bpy.ops.object.mode_set(mode='OBJECT')
if "LowPoly" in bpy.data.objects:
    bpy.data.objects["LowPoly"].name = BODY
R = Ref(BODY)
for f, (a, b) in DIGITS.items():
    a, b = Vector(a), Vector(b)
    for i, t in enumerate(FRACS):
        p = a.lerp(b, t)
        J["LeftHand%s%d" % (f, i + 1)] = centred(R, p, b - a) if f != "Thumb" and 0 < t < 1 else p
J = mirror_left(J)
rig = build(BODY, RIG, J, bones(("Thumb", "Index", "Middle", "Ring")) + chain(TAIL, "Hips"), sideways=TAIL)
qa = skin(BODY, rig)
bpy.ops.wm.save_mainfile()
result = dict(qa, fingers={k: tuple(round(x, 3) for x in v) for k, v in J.items() if k.startswith("LeftHand")})
