"""Step 1 (after the artist's front retopo): from the artist's one-sided skin ("Plane") to a closed wing shell + separate handle parts, ready for the UV.
One-shot: blender -b --factory-startup --python tools/general/blender_once.py -- examples/wing/s1_prepare_for_uv.py
Env: SKIN_BLEND (blend with REFERENCE and the skin object "Plane"; default draft/wing_manual_00_user_front.blend), PREP_BLEND (output, default draft/wing_11_mirror.blend).
What it does, in order (the order matters):
  1. depth map of the reference (front F and back B), cached in draft/depth.npz
  2. handle parts (support.py) on the reference front surface
  3. the skin is stretched where its border is <6 cm from a part, so it touches the handle (touch_parts, only for x < 0.02 to keep the far tip untouched)
  4. close_skin: border extruded to the mirror plane P, then mirrored (same mesh inverted, 760 quads for the 284-quad skin)
  5. the parts are pulled onto the shell where they are <2.5 cm from it (closes the slits); the artist's skin object is kept, hidden."""
import bpy, os, sys, numpy as np
sys.path.insert(0, os.environ.get("WING_EX", "")); from _cfg import *
load_tool("02-retopology", "skin_close.py"); load_tool("01-input-and-measurement", "depth_map.py")
from support import support_parts
SKIN = os.environ.get("SKIN_BLEND") or os.path.join(DRAFT, "wing_manual_00_user_front.blend"); PREP = os.environ.get("PREP_BLEND") or os.path.join(DRAFT, "wing_11_mirror.blend")
bpy.ops.wm.open_mainfile(filepath=SKIN)
NPZ = os.path.join(DRAFT, "depth.npz")
if not os.path.exists(NPZ):
    depth_map("REFERENCE", NPZ, x=(-0.46, 0.64), z=(0.0, 0.60))
front = sampler(NPZ, "F", 3, np.nanmin); back = sampler(NPZ, "B", 3, np.nanmedian)


def mat(name, col, tint=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.6; b.inputs["Base Color"].default_value = col; return m


MF, MG = mat("WING_FEATHER", (1, 1, 1, 1)), mat("WING_GOLD", (0.85, 0.62, 0.2, 1))
parts = []
for n, V, F in support_parts(front):
    parts.append(make_object(n, V, F, MG))
skin = bpy.data.objects["Plane"]; bm = skin_bmesh(skin)
moved = touch_parts(bm, parts, max_dist=0.06, inside=0.004, where=lambda v: v.co.x < 0.02)
V, F, info = close_skin(bm, back_depth=back); bm.free()
wing = make_object("WING_FEATHERS", V, F, MF); pulled = pull_parts_to_shell(parts, wing)
skin.hide_viewport = skin.hide_render = True; skin.name = "USER_SKIN_SOURCE"
bpy.ops.wm.save_as_mainfile(filepath=PREP)
result = {"skin_verts_moved": moved, "shell": info, "faces": len(wing.data.polygons), "parts_pulled": pulled, "saved": PREP}
