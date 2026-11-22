# Grip and pommel: one 8-sided tube that starts buried in the crossguard and closes at the pommel tip.
import bpy, numpy as np
import os
ROOT = os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd()).replace("\\", "/").rstrip("/") + "/"
P = ROOT + "projects/cutlass/"
bpy.ops.wm.open_mainfile(filepath=P + "draft/cutlass_guard.blend")
exec(open(ROOT + "tools/02-retopology/snap_retopo.py").read())
exec(open(ROOT + "tools/02-retopology/tube_path.py").read())
if "Grip" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Grip"])
PATH = [(0.13, 0.219), (0.16, 0.205), (0.21, 0.181), (0.26, 0.153), (0.30, 0.126), (0.33, 0.110), (0.36, 0.100), (0.377, 0.095)]
FLOOR = 0.6                                                       # on the pommel a long diagonal ray reaches the knuckle bow
S = Surface("REFERENCE")
o = build_tube(S, "Grip", PATH, 17, bury=(0.035, 0.0), r=0.08, wide=0.019)
exec(open(ROOT + "tools/02-retopology/wire_overlay.py").read())
for v in ("front", "persp", "top"):
    wire_overlay(["Grip"], P + f"draft/grip_{v}.png", view=v, shade=["REFERENCE"], center=(0.25, 0, 0.16), size=0.36, res=900)
exec(open(ROOT + "tools/02-retopology/fit_report.py").read())
result = {"quads": len(o.data.polygons), "fit": fit_report("Grip", "REFERENCE", ref_max=1000)["new_to_ref_mm"]}
bpy.ops.wm.save_as_mainfile(filepath=P + "draft/cutlass_grip.blend")
