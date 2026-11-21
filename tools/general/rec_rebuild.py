"""Rebuild the artist's mesh from a session recording (`record_session.py`), without opening their Blender.
Why: a recording survives when the .blend was never saved, was saved over, or Blender froze (sword case: the artist's work
lived in `session/rec_NN`, not in a .blend). The last `snap_*.json` is the base; the `actions.jsonl` lines after it are replayed
(add_vertex / move_vertex / add_face). Deletions are NOT recorded as actions: compare with the next `checkpoint_*.json` (Ctrl+S)
if the artist deleted geometry, and prefer the checkpoint when it is newer than the snapshot.
  exec(open(r"<repo>\\tools\\general\\rec_rebuild.py", encoding="utf-8").read())
  V, E, F = replay(r"projects\\x\\session\\rec_04")                     # lists, no Blender needed (also works with plain python)
  r = rebuild(r"projects\\x\\session\\rec_04", bpy.data.objects["LowPoly"])   # replaces the object's geometry; r = counts
Reference transform: the REFERENCE object's matrix is NOT in the snapshots if the artist moved it after saving; recover it
from the recorded operators (`events.jsonl`) or ask for the matrix, then set `ref.matrix_world` (sword case: sign brute force
against the low-poly distance). Always work on a COPY of the .blend."""
import json, glob, os


def replay(rec_dir):
    snaps = sorted(glob.glob(os.path.join(rec_dir, "snap_*.json")))
    s = json.load(open(snaps[-1], encoding="utf-8"))
    V = [list(v) for v in s["verts"]]; E = {tuple(sorted(e)) for e in s["edges"]}; F = [list(f) for f in s["faces"]]
    for line in open(os.path.join(rec_dir, "actions.jsonl"), encoding="utf-8"):
        o = json.loads(line)
        if o["n"] <= s["n"]: continue
        for a in o["actions"]:
            t = a["type"]
            if t == "add_vertex":
                if a["id"] != len(V): raise ValueError("vertex ids out of sync at action %s: a deletion happened, use a checkpoint" % o["n"])
                V.append(list(a["local"]))
                for k in a.get("linked_to", []): E.add(tuple(sorted((k, a["id"]))))
            elif t == "move_vertex": V[a["id"]] = list(a["to"])
            elif t == "add_face": F.append(list(a["verts"]))
    return V, sorted(E), F


def rebuild(rec_dir, ob):
    V, E, F = replay(rec_dir)
    me = ob.data
    me.clear_geometry(); me.from_pydata(V, [list(e) for e in E], F); me.update()
    sizes = [len(f) for f in F]
    return {"verts": len(V), "faces": len(F), "quads": sizes.count(4), "others": [n for n in sizes if n != 4]}
