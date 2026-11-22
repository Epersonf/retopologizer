"""Step 4: rig (bone chain + flap), wire the PBR maps, save the final .blend (with the Tint) and export FBX + GLB + maps + previews.
One-shot: ... blender_once.py -- examples/wing/s4_rig_export.py     Env: BAKED_BLEND (input), FINAL_BLEND (default draft/wing_15_final.blend), EXPORT_DIR (default <WING_DIR>/export), NAME (Asa_Braziletto).
Rig: Root at the collar, W1/W2/W3 along the wing, Fan_Low for the lower feathers; numeric weights by X (smooth blend of 0.2 m at each joint), Fan_Low by
region (below z = 0.28 and left of x = 0.05); the collar/neck/plate/eye (gold, x < -0.30, near the collar height) are pinned to Root.
Flap: Root 12 deg, W1 8, W2 8, W3 7, Fan_Low -5, each delayed by 0.07-0.21 of a 24-frame cycle (the loop is frames 1-25; frame 1 is NOT the rest pose)."""
import bpy, os, sys
sys.path.insert(0, os.environ.get("WING_EX", "")); from _cfg import *
load_tool("06-rig", "rig_chain.py"); load_tool("05-delivery", "export_package.py")
bpy.ops.wm.open_mainfile(filepath=os.environ.get("BAKED_BLEND") or os.path.join(DRAFT, "wing_13_baked.blend"))
ob = bpy.data.objects["WING"]; Y = -0.02
for o in bpy.data.objects:
    if o.name not in ("WING",):
        o.hide_viewport = o.hide_render = True
rig = build_rig("Wing_Rig", {"Root": ((-0.43, Y, 0.365), (-0.30, Y, 0.385), None), "W1": ((-0.30, Y, 0.385), (0.05, Y, 0.40), "Root"), "W2": ((0.05, Y, 0.40), (0.35, Y, 0.42), "W1"),
                             "W3": ((0.35, Y, 0.42), (0.64, Y, 0.52), "W2"), "Fan_Low": ((-0.33, Y, 0.33), (-0.30, Y, 0.04), "Root")})
fan = lambda co: ss((0.28 - co[2]) / 0.10) * ss((0.05 - co[0]) / 0.12)
rep = weight_chain(ob, rig, ["Root", "W1", "W2", "W3"], [-0.30, 0.05, 0.35], half=0.10, axis=0, extra=("Fan_Low", fan),
                   rigid=("Root", lambda v, co, is_gold: is_gold and co[0] < -0.30 and abs(co[2] - 0.365) < 0.07))
flap(rig, {"Root": 12, "W1": 8, "W2": 8, "W3": 7, "Fan_Low": -5}, {"Root": 0.0, "W1": 0.07, "W2": 0.14, "W3": 0.21, "Fan_Low": 0.18})
out = os.environ.get("EXPORT_DIR") or os.path.join(WING, "export"); name = os.environ.get("NAME", "Asa_Braziletto"); os.makedirs(out, exist_ok=True)
wire_pbr(["WING_FEATHER", "WING_GOLD"], OUT, "wing", tint=["WING_FEATHER"])
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("FINAL_BLEND") or os.path.join(DRAFT, "wing_15_final.blend"))
views = {"front": ((0.09, -4, 0.32), (90, 0, 0), 1.35, 1100, 760), "handle": ((-0.33, -3, 0.36), (90, 0, 0), 0.34, 1000, 800)}
render_previews(["WING", "Wing_Rig"], out, views); wire_pbr(["WING_FEATHER", "WING_GOLD"], OUT, "wing", tint=[])
files = export_package(["Wing_Rig", "WING"], out, name, OUT, "wing")
result = {"rig": rep, "files": files}
