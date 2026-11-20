"""Hair shell part, step 1 (Blender worker): the faces of "HairFull" (hair_proxy.py with NPZ = hair_in.npz: every face,
grooves included) that are the outermost surface seen from the head centre C inside a window of directions: polar angle
TH = (lo, hi) from +z, azimuth PH = (lo, hi) from the back (+y) toward +x (the character's left), in degrees (-180..180].
Rays go from far outside inward, so the first hit is the outer envelope. Set PART, PH, TH before running; writes
draft/hair_<PART>_faces.npz (face indices into hair_in.npz); hair_shell.py makes the disk, hair_field.py the rings.
  PART = "dome"; PH = (-100, 100); TH = (0, 140)"""
import math
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PART = globals()["PART"]; PH = globals()["PH"]; TH = globals().get("TH", (0.0, 140.0))
C = Vector((-0.185, -0.03, 0.30)); STEP = 0.6; FAR = 0.7
bv = BVHTree.FromObject(bpy.data.objects["HairFull"], bpy.context.evaluated_depsgraph_get())
hit = set(); misses = 0
for t in np.arange(TH[0], TH[1] + 1e-6, STEP):
    a = math.radians(t); n = max(1, int(360 * math.sin(a) / STEP)) if t > 0 else 1
    for k in range(n):
        deg = 360.0 * k / n; deg = deg - 360 if deg > 180 else deg
        if t > 0 and not PH[0] <= deg <= PH[1]:
            continue
        b = math.radians(deg)
        d = Vector((math.sin(a) * math.sin(b), math.sin(a) * math.cos(b), math.cos(a)))
        h = bv.ray_cast(C + d * FAR, -d, FAR)
        if h[0] is None:
            misses += 1
        else:
            hit.add(h[2])
out = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft\hair_%s_faces.npz" % PART
np.savez(out, faces=np.array(sorted(hit), np.int32), C=np.array(C))
result = {"part": PART, "faces": len(hit), "misses": misses}
