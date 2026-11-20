"""Export the rigged Cuca (cuca_rig.py) like the Saci: Cuca.fbx + AlbedoCuca.jpg (her baked albedo at 1024) in the
Braziletto Godot client (assets/characters), plus a copy in output/. The FBX material points at the JPG next to it.
  python tools/general/blender_rpc.py --port 9877 examples/cuca-rig/cuca_rig_export.py"""
import os, shutil, subprocess, sys, bpy
from mathutils import Matrix
ROOT = os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd())             # the repo root (run from it, or set RETOPOLOGIZER_ROOT)
sys.path.insert(0, ROOT + r"\tools\06-rig")
import importlib, rig_mixamo
importlib.reload(rig_mixamo)

GAME = os.environ.get("GAME_ASSETS", os.path.join(ROOT, "game-assets"))      # where your game keeps its characters (set GAME_ASSETS)
OUT = ROOT + r"\projects\stylized-cuca\output"
BLEND = ROOT + r"\projects\stylized-cuca\draft\cuca_rig.blend"
TEX = 1024
# Godot 4.7 did not load the JPEG Blender 5 writes (ICC + OIIO metadata): plain JFIF from PIL, in the system Python
TO_JPG = ("import sys; from PIL import Image; s, d, n = sys.argv[1:]; "
          "Image.open(s).convert('RGB').resize((int(n),) * 2, Image.LANCZOS).save(d, quality=90, optimize=True)")

if bpy.data.filepath != BLEND:
    bpy.ops.wm.open_mainfile(filepath=BLEND)
rig, body = bpy.data.objects["Cuca_Rig"], bpy.data.objects["Cuca_Body"]
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix()
os.makedirs(OUT, exist_ok=True)
jpg, src = os.path.join(GAME, "AlbedoCuca.jpg"), bpy.data.images["Albedo"]
png = os.path.join(OUT, "albedo_cuca_%d.png" % src.size[0])          # the bake as it is packed in the .blend
open(png, "wb").write(bytes(src.packed_file.data))
subprocess.run(["python", "-c", TO_JPG, png, jpg, str(TEX)], check=True)
node = next(n for n in body.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE')
node.image = bpy.data.images.load(jpg)
files = [rig_mixamo.export_fbx(os.path.join(GAME, "Cuca.fbx"), rig, body.name),
         rig_mixamo.export_fbx(os.path.join(OUT, "cuca_rigged.fbx"), rig, body.name), jpg,
         shutil.copy(jpg, os.path.join(OUT, "AlbedoCuca.jpg"))]
loaded = node.image; node.image = src; bpy.data.images.remove(loaded)
bpy.ops.wm.save_mainfile()
result = {os.path.basename(f) + (" (output)" if OUT in f else ""): os.path.getsize(f) for f in files}
