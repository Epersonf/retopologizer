"""Step 5: lean assets for the Godot client: mesh + rig + flap as a GLB WITHOUT textures, and 1024 px maps (basecolor, normal, ORM).
One-shot: ... blender_once.py -- examples/wing/s5_game_assets.py     Env: FINAL_BLEND (step 4 output), GAME_WINGS (destination folder, e.g. <game repo>/frontend/godot-client/assets/wings), SIZE (1024).
Why not the FBX/GLB of step 4: those carry 2048 px textures (11 MB) and the Godot client builds its own materials anyway (tint per style, ORM from one texture:
roughness in G, metallic in B, AO in R). Godot 4.7 does not read Blender 5's JPEG, so the maps are PNG. Names: Wing.glb, WingBaseColor.png, WingNormal.png, WingORM.png."""
import bpy, os, sys, numpy as np
sys.path.insert(0, os.environ.get("WING_EX", "")); from _cfg import *
DST = os.environ["GAME_WINGS"]; os.makedirs(DST, exist_ok=True); size = int(os.environ.get("SIZE", 1024))
bpy.ops.wm.open_mainfile(filepath=os.environ.get("FINAL_BLEND") or os.path.join(DRAFT, "wing_15_final.blend"))


def load(name):
    i = bpy.data.images.load(os.path.join(OUT, f"wing_{name}.png"), check_existing=False); i.colorspace_settings.name = "Non-Color"; i.scale(size, size); return i


def pixels(i):
    b = np.empty(size * size * 4, np.float32); i.pixels.foreach_get(b); return b.reshape(size, size, 4)


def save(arr, name):
    img = bpy.data.images.new(name, size, size, alpha=False); img.colorspace_settings.name = "Non-Color"; img.pixels.foreach_set(arr.ravel()); img.filepath_raw = os.path.join(DST, name + ".png")
    img.file_format = 'PNG'; img.save()


bc, nm, ro, me, ao = (pixels(load(n)) for n in ("basecolor", "normal", "roughness", "metallic", "ao"))
orm = np.ones_like(bc); orm[..., 0] = ao[..., 0]; orm[..., 1] = ro[..., 0]; orm[..., 2] = me[..., 0]
save(bc, "WingBaseColor"); save(nm, "WingNormal"); save(orm, "WingORM")
for o in bpy.data.objects:
    o.select_set(o.name in ("WING", "Wing_Rig"))
bpy.context.view_layer.objects.active = bpy.data.objects["Wing_Rig"]; bpy.context.scene.frame_set(1)
bpy.ops.export_scene.gltf(filepath=os.path.join(DST, "Wing.glb"), use_selection=True, export_format='GLB', export_image_format='NONE', export_animations=True, export_skins=True)
result = sorted(os.listdir(DST))
