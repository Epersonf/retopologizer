"""Cuca retopo, built from a topology plan (PLAN.md): half model (x >= 0) part by part, then mirrored.
Inside Blender (MCP):  exec(open(r"<repo>/projects/stylized-cuca/cuca_build.py").read())
Each part file runs in this namespace (T = Topo, R = Ref of HiPoly, L = named loops shared between parts).
The result is Cuca_retopo + a Mirror modifier while the half is in progress."""
import sys, bpy
from mathutils import Vector
ROOT = r"C:\Users\epers\Desktop\retopologizer"
if ROOT + r"\tools" not in sys.path:
    sys.path.insert(0, ROOT + r"\tools")
import importlib, retopo
importlib.reload(retopo)
from retopo import *

PARTS = globals().get("PARTS") or ["cuca_torso", "cuca_arm", "cuca_neck"]
R = Ref("HiPoly"); T = Topo(R); L = {}
for _p in PARTS:
    exec(open(ROOT + r"\projects\stylized-cuca\%s.py" % _p, encoding="utf-8").read())
flipped = T.orient()
o = T.write("Cuca_retopo")
if "Mirror" not in o.modifiers:
    m = o.modifiers.new("Mirror", 'MIRROR'); m.use_clip = True; m.use_mirror_merge = True; m.merge_threshold = 0.001
result = {"parts": PARTS, "pieces_flipped": flipped, "qa": topo_qa("Cuca_retopo", R, seam_x=0.0)}
