"""Session metadata and checkpoints of session_recorder.py."""
import bpy, json, os, time, hashlib
from session_state import view, snap


def write_meta(out, version):
    ref = bpy.data.objects.get("REFERENCE")
    try:
        md5 = hashlib.md5(open(bpy.data.filepath, "rb").read()).hexdigest() if bpy.data.filepath else None
    except Exception:
        md5 = None
    m = {"recorder_version": version, "blender": bpy.app.version_string, "blend": os.path.basename(bpy.data.filepath), "blend_md5_at_start": md5,
         "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "snap": snap(), "view": view(),
         "reference": {"name": "REFERENCE", "tris": sum(len(p.vertices) - 2 for p in ref.data.polygons), "dims": list(ref.dimensions)} if ref else None,
         "conventions": "Z up, front = -Y, ortho front view, meters; world coords in actions.jsonl; screen = region pixels (origin bottom-left)"}
    json.dump(m, open(os.path.join(out, "meta.json"), "w", encoding="utf-8"), indent=1)


def write_checkpoint(out, n, t):
    objs = {o.name: {"verts": [list(v.co) for v in o.data.vertices], "faces": [list(p.vertices) for p in o.data.polygons],
                     "mw": [list(r) for r in o.matrix_world]}
            for o in bpy.data.objects if o.type == 'MESH' and o.name != "REFERENCE" and o.mode != 'EDIT'}
    json.dump({"t": t, "blend": os.path.basename(bpy.data.filepath), "objects": objs}, open(os.path.join(out, "checkpoint_%03d.json" % n), "w"))
