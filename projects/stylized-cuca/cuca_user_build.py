"""Continue the artist's own LowPoly (draft copy): the parts in PARTS are added to their mesh and written back to
LowPoly. Their untouched mesh is kept as the mesh datablock LowPoly_user, so every run starts from it again.
  python tools/blender_rpc.py --port 9877 projects/stylized-cuca/cuca_user_build.py"""
import sys, bpy
from mathutils import Vector
ROOT = r"C:\Users\epers\Desktop\retopologizer"
sys.path.insert(0, ROOT + r"\tools")
import importlib, retopo
importlib.reload(retopo)
from retopo import *

PARTS = globals().get("PARTS") or ["cuca_hand"]
low = bpy.data.objects["LowPoly"]
if "LowPoly_user" not in bpy.data.meshes:
    keep = low.data.copy(); keep.name = "LowPoly_user"; keep.use_fake_user = True
R = Ref("HiPoly"); T = Topo(R, start="LowPoly_user"); L = {}
for _p in PARTS:
    exec(open(ROOT + r"\projects\stylized-cuca\%s.py" % _p, encoding="utf-8").read())
flipped = T.orient()
T.bm.verts.layers.int.remove(T._orig)
T.write("LowPoly")
result = {"parts": PARTS, "pieces_flipped": flipped, "qa": topo_qa("LowPoly", R, seam_x=0.0),
          "info": {k: v for k, v in L.items() if isinstance(v, list) and v and isinstance(v[0], tuple)}}
