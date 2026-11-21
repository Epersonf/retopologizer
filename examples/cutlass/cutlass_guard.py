# Cutlass guard: crossguard and knuckle bow as two 8-sided tubes along a path in the XZ plane, rings snapped by rays.
import bpy, numpy as np
import os
ROOT = os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd()).replace("\\", "/").rstrip("/") + "/"
P = ROOT + "projects/cutlass/"
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=P + "draft/cutlass_blade.blend")
exec(open(ROOT + "tools/02-retopology/snap_retopo.py").read())
exec(open(P + "tube_lib.py").read())
for n in ("Crossguard", "KnuckleBow"):
    if n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[n])
PATHS = {
    "Crossguard": ([(-0.008, 0.163), (0.04, 0.19), (0.085, 0.231), (0.12, 0.29), (0.135, 0.34), (0.13, 0.368)], 9),
    "KnuckleBow": ([(0.079, 0.15), (0.0775, 0.131), (0.0825, 0.091), (0.105, 0.046), (0.15, 0.021), (0.2, 0.021),
                    (0.24, 0.036), (0.265, 0.062)], 12),
}
BURY = {"KnuckleBow": (0.025, 0.025)}                             # bow ends go into the crossguard and the pommel

S = Surface("REFERENCE"); out = {}
for name, (pts, n) in PATHS.items():
    out[name] = len(build_tube(S, name, pts, n, BURY.get(name, (0.0, 0.0))).data.polygons)
exec(open(ROOT + "tools/02-retopology/wire_overlay.py").read())
for v in ("front", "persp", "back"):
    wire_overlay(["Crossguard", "KnuckleBow"], P + f"draft/guard_{v}.png", view=v, shade=["REFERENCE"], center=(0.13, 0, 0.19), size=0.42, res=900)
exec(open(ROOT + "tools/02-retopology/fit_report.py").read())
out["fit"] = {n: fit_report(n, "REFERENCE", ref_max=1000)["new_to_ref_mm"] for n in ("Crossguard", "KnuckleBow")}
bpy.ops.wm.save_as_mainfile(filepath=P + "draft/cutlass_guard.blend")
result = out
