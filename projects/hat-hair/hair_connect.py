"""Makes every hair tube touch something (normal python; the worker is up with Hair_dome and Hair_front built and capped).
Loop: hair_tubes.py -> load the tubes in Blender -> qa_floating over the shell + tubes -> for each floating tube, make the end nearest
to the rest reach the point it floated next to, plus half a radius further in (draft/hair_ext.json, read by hair_tubes.py) -> again,
until nothing floats.
  python -I projects/hat-hair/hair_connect.py [min_len=0.06] [budget=450]"""
import json, subprocess, sys
import numpy as np
from pathlib import Path
H = Path(__file__).resolve().parent; ROOT = H.parent.parent; ARGS = sys.argv[1:] or ["0.06", "450"]
EXT = H / "draft" / "hair_ext.json"; EXT.unlink(missing_ok=True)
QA = r"""
exec(open(r'%s').read())
import numpy as np
r = qa_floating(["Hair_hood"] + [o.name for o in bpy.data.objects if o.name.startswith("Hair_tube_")])
for f in r["floating"]:
    me = bpy.data.objects[f["object"]].data; V = [v.co for v in me.vertices]; ends = V[-2:]       # tip cap vertex, root cap vertex
    f["near"] = "tip" if (ends[0] - __import__("mathutils").Vector(f["end"])).length < (ends[1] - __import__("mathutils").Vector(f["end"])).length else "root"
    f["radius"] = (V[0] - V[1]).length
result = r
""" % (ROOT / "tools" / "03-qa" / "qa_floating.py")


def rpc(*a):
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools/general/blender_rpc.py"), "--port", "9877", *a], capture_output=True, text=True)
    return r.stdout


ext = {}
for it in range(6):
    subprocess.run([sys.executable, "-I", str(H / "hair_tubes.py"), *ARGS], capture_output=True)
    rpc(str(H / "hair_tubes_load.py"))
    tmp = H / "draft" / "_qa.py"; tmp.write_text(QA, encoding="utf-8")
    out = rpc(str(tmp)); r = json.loads(out[out.index("{"):out.rindex("}") + 1])
    print("pass", it, "floating", [(f["object"], f["gap_mm"], f["near"]) for f in r["floating"]])
    if r["pass"]:
        break
    for f in r["floating"]:
        i = str(int(f["object"].split("_")[-1]) - 1); e = ext.setdefault(i, [1.2 * f["radius"], 0.0, None, None])
        d = np.array(f["to"]) - np.array(f["end"]); d /= max(np.linalg.norm(d), 1e-9)
        e[2 if f["near"] == "root" else 3] = list(np.array(f["to"]) + d * 0.5 * f["radius"])
    EXT.write_text(json.dumps(ext))
