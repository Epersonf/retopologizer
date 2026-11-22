"""Blender side of the limb demo video: wraps a tube around the left arm of a reference and writes the geometry to json.
  python tools/general/blender_rpc.py --port 9877 tools/02-retopology/limb_demo_data.py     (env-less: edit OBJ/OUT below)
Writes OUT: ref (arm-side vertices + triangles), per ring centre/start radius/final points, tube faces, joint fraction."""
import json, sys, bpy
sys.path.insert(0, "C:/Users/epers/Desktop/retopologizer/tools"); sys.path.insert(0, "C:/Users/epers/Desktop/retopologizer/tools/06-rig")
BLEND = "C:/Users/epers/Desktop/retopologizer/projects/autorig-bench/input/female_apose.blend"
OUT = "C:/Users/epers/Desktop/retopologizer/projects/limb-demo/data.json"
import os; os.makedirs(os.path.dirname(OUT), exist_ok=True)
from mathutils import Vector
import importlib, retopo; importlib.reload(retopo)
from retopo import Ref, limb_tube, auto_stations
from autorig.load import mesh_of
from autorig.detect import detect
ob = bpy.data.objects["Body"]
J, B, _ = detect(mesh_of([ob])); ref = Ref("Body")
a, e, h = [Vector(J[k]) for k in ("LeftArm", "LeftForeArm", "LeftHand")]
a = a + (h - a) * 0.22                                   # start past the shoulder: rings there would catch the torso
L = (h - a).length; ef = (e - a).length / L; N = 12
for o in [o for o in bpy.data.objects if o.name.startswith("Arm_")]: bpy.data.objects.remove(o)
T = limb_tube(ref, a, h, "auto", N, "Arm_demo", joints=[ef])
st, info = auto_stations(T.profile, [ef], return_info=True, n=N)
t = bpy.data.objects["Arm_demo"]; P = [list(v.co) for v in t.data.vertices]
rings = []
for i, c in enumerate(T.centers):
    pts = P[i * N:(i + 1) * N]; R = 1.6 * max((Vector(p) - c).length for p in pts)
    rings.append({"c": list(c), "R": R, "end": pts})
M = ob.data; V = [list(v.co) for v in M.vertices]
def near(v):                                                 # only the arm: close to the shoulder-hand segment
    p = Vector(v); t = max(-0.05, min(1.1, (p - a).dot(h - a) / L ** 2)); return (p - (a + (h - a) * t)).length < 0.075 and 0 <= t
keep = {i for i, v in enumerate(V) if near(v)}
tri = [[p for p in f.vertices] for f in M.polygons if all(p in keep for p in f.vertices)]
json.dump({"ref_v": V, "ref_f": tri, "rings": rings, "faces": [list(p.vertices) for p in t.data.polygons], "stations": st,
           "elbow": ef, "check": T.check, "profile": {"t": [float(x) for x in T.profile["t"]], "r": [float(x) for x in T.profile["r"]], "raw": [float(x) for x in T.profile["raw"]]}, "extrema": info["extrema"], "joints": {"shoulder": list(a), "elbow": list(e), "wrist": list(h)}}, open(OUT, "w"))
result = {"rings": len(rings), "faces": len(t.data.polygons), "ref_tris": len(tri), "out": OUT}
