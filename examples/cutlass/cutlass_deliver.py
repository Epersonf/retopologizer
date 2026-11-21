# Wire the baked maps, export the FBX of the 4 parts and render a textured preview.
import bpy
import os
ROOT = os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd()).replace("\\", "/").rstrip("/") + "/"
P = ROOT + "projects/cutlass/"
bpy.ops.wm.open_mainfile(filepath=P + "draft/cutlass_baked.blend")
LOW = ["Blade", "Crossguard", "KnuckleBow", "Grip"]
exec(open(ROOT + "tools/05-delivery/wire_material.py").read())
exec(open(ROOT + "tools/05-delivery/render_thumbnail.py").read())
r = wire_and_export(LOW, "cutlass", P + "output", "cutlass", "cutlass")
bpy.data.objects["REFERENCE"].hide_render = True
render_thumbnail(LOW, P + "draft/cutlass_preview.png", look_at=(-0.03, 0.0, 0.44), cam=(-3.6, -4.8, 2.1), samples=64)
bpy.ops.wm.save_as_mainfile(filepath=P + "draft/cutlass_final.blend")
result = str(r)[:300]
