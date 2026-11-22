"""Step 2 (after the artist's UV and shape adjustments): bake the reference into the artist's atlas.
One-shot: ... blender_once.py -- examples/wing/s2_bake.py        Env: UV_BLEND (artist's file; default draft/wing_12_para_uv.blend), OBJ (object name; default: the visible mesh with UV that is not REFERENCE),
BAKED_BLEND (output, default draft/wing_13_baked.blend), SIZE (2048).
Uses tools/04-uv-bake/bake_robust.py: one bake for all pieces, per-texel validation, extrusion/ray schedule, inpaint inside the island.
Results we got: 5.4% invalid texels on the first pass, 1.1% after the schedule; the faces that stay far from the reference (up to ~48 mm) are the
handle (simple shapes) and a few thin feather tips. The UV report may say `pass: false` for the 8 px gap rule: that is the artist's layout, do not edit it.
Writes output/wing_{basecolor,normal,roughness,metallic,ao}.png and renames the artist's single object to WING."""
import bpy, os, sys, json
sys.path.insert(0, os.environ.get("WING_EX", "")); from _cfg import *
SRC = os.environ.get("UV_BLEND") or os.path.join(DRAFT, "wing_12_para_uv.blend"); DST = os.environ.get("BAKED_BLEND") or os.path.join(DRAFT, "wing_13_baked.blend")
bpy.ops.wm.open_mainfile(filepath=SRC); size = int(os.environ.get("SIZE", 2048)); os.makedirs(OUT, exist_ok=True)
load_tool("04-uv-bake", "bake_robust.py")
ob = bpy.data.objects.get(os.environ.get("OBJ", "")) or next(o for o in bpy.data.objects if o.type == "MESH" and o.name != "REFERENCE" and o.data.uv_layers and not o.hide_viewport)
ob.name = "WING"   # the artist joined everything into one object (it was called SUP_arm); any name works
uv = qa_uv(["WING"], size=size, min_gap_px=8)
rep = bake_robust(["WING"], "REFERENCE", OUT, "wing", size=size)
bpy.ops.wm.save_as_mainfile(filepath=DST)
result = {"uv": {k: v for k, v in uv.items() if not k.startswith("_")},
          "bake": {k: rep[k] for k in ("device", "passes", "invalid_first_pass_pct", "inpainted_texels", "poor_fit_faces_mm") if k in rep}, "saved": DST}
