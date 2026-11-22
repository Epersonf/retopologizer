"""Auto-rig a humanoid model the Mixamo way (mixamorig: bones, digits found on the hands, a tail if it has one),
headless:
  "<blender.exe>" -b --factory-startup --python tools/06-rig/autorig/cli.py -- model.fbx out.fbx [--blend out.blend]
      [--name Rig] [--asym] [--textures]
Input .fbx .obj .glb .gltf or .blend (every mesh in the scene; an old armature is dropped). The model stands on +Z
in T-pose or A-pose, facing -Y (one facing +Y is turned around). Prints "AUTORIG_QA: {...}"."""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # tools/
import bpy
import rig_mixamo as RM
from autorig.rig import autorig
from autorig.load import load_model as load

def main(argv):
    ap = argparse.ArgumentParser(prog="autorig")
    ap.add_argument("model"); ap.add_argument("out")
    ap.add_argument("--blend"); ap.add_argument("--name", default="Rig")
    ap.add_argument("--asym", action="store_true", help="keep each side as found (no mirror averaging)")
    ap.add_argument("--textures", action="store_true", help="copy and embed the textures in the FBX")
    ap.add_argument("--markers", help="json file of hand-placed joints (chin, wrists, elbows, knees, groin)")
    ap.add_argument("--front", default="auto", choices=["auto", "-Y", "+Y"], help="side the model faces (+Y is turned around)")
    ap.add_argument("--no-fingers", action="store_true"); ap.add_argument("--glb", help="also export a glTF for the browser")
    a = ap.parse_args(argv)
    meshes = load(os.path.abspath(a.model))
    if not meshes:
        raise SystemExit("autorig: no mesh in " + a.model)
    meshes.sort(key=lambda o: -len(o.data.vertices))                  # the body first
    rig, qa = autorig(meshes, a.name, symmetric=not a.asym, markers=a.markers and json.load(open(a.markers)),
                    front=a.front, fingers=not a.no_fingers)
    RM.export_fbx(os.path.abspath(a.out), rig, [o.name for o in meshes], textures=a.textures)
    if a.glb:
        bpy.ops.export_scene.gltf(filepath=os.path.abspath(a.glb), export_format='GLB', use_selection=False)
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
    print("AUTORIG_QA: " + json.dumps(qa), flush=True)


main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
