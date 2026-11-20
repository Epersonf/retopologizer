"""Auto-rig a humanoid model the Mixamo way (mixamorig: bones, digits found on the hands, a tail if it has one),
headless:
  "<blender.exe>" -b --factory-startup --python tools/autorig/cli.py -- model.fbx out.fbx [--blend out.blend]
      [--name Rig] [--asym] [--textures]
Input .fbx .obj .glb .gltf or .blend (every mesh in the scene; an old armature is dropped). The model stands on +Z
in T-pose or A-pose, facing -Y (one facing +Y is turned around). Prints "AUTORIG_QA: {...}"."""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # tools/
import bpy
import rig_mixamo as RM
from autorig.rig import autorig

IMPORT = {".fbx": lambda p: bpy.ops.import_scene.fbx(filepath=p), ".obj": lambda p: bpy.ops.wm.obj_import(filepath=p),
          ".glb": lambda p: bpy.ops.import_scene.gltf(filepath=p), ".gltf": lambda p: bpy.ops.import_scene.gltf(filepath=p)}


def load(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".blend":
        bpy.ops.wm.open_mainfile(filepath=path)
    elif ext in IMPORT:
        bpy.ops.wm.read_factory_settings(use_empty=True); IMPORT[ext](path)
    else:
        raise SystemExit("autorig: unsupported input " + ext)
    for a in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        for c in a.children:                           # keep the meshes where they are without their old rig
            mw = c.matrix_world.copy(); c.parent = None; c.matrix_world = mw
        bpy.data.objects.remove(a)
    for act in list(bpy.data.actions):                 # its animations would be baked onto the new rig
        bpy.data.actions.remove(act)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes:                                     # a .blend of loose objects (in no scene): take them all
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
        for o in meshes:
            bpy.context.scene.collection.objects.link(o)
    return meshes


def main(argv):
    ap = argparse.ArgumentParser(prog="autorig")
    ap.add_argument("model"); ap.add_argument("out")
    ap.add_argument("--blend"); ap.add_argument("--name", default="Rig")
    ap.add_argument("--asym", action="store_true", help="keep each side as found (no mirror averaging)")
    ap.add_argument("--textures", action="store_true", help="copy and embed the textures in the FBX")
    a = ap.parse_args(argv)
    meshes = load(os.path.abspath(a.model))
    if not meshes:
        raise SystemExit("autorig: no mesh in " + a.model)
    meshes.sort(key=lambda o: -len(o.data.vertices))                  # the body first
    rig, qa = autorig(meshes, a.name, symmetric=not a.asym)
    RM.export_fbx(os.path.abspath(a.out), rig, [o.name for o in meshes], textures=a.textures)
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
    print("AUTORIG_QA: " + json.dumps(qa), flush=True)


main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
