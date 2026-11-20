"""The whole low poly, from the worker on a copy of draft/hair_work.blend (HairFull loaded; needs draft/hair_locks.npz from
hair_locks.py 0.03 and hair_locks_z.npz from hair_locks.py 0.04 z): hood shell -> lid -> heal folds (strict reversed-face gate) ->
tubes that all touch something -> join -> strict gates (reversed faces, floating parts). Any gate that fails raises: nothing is saved.
  python -I projects/hat-hair/hair_build.py [hood=32,16,8] [tube_budget=900]"""
import subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent; ROOT = H.parent.parent
hood, budget = (sys.argv[1:] + [None] * 2)[:2]; hood = hood or "32,16,8"; budget = budget or "900"
rpc = lambda *a: subprocess.run([sys.executable, "-I", str(ROOT / "tools/general/blender_rpc.py"), "--port", "9877", *a], capture_output=True, text=True)
run = lambda *a: subprocess.run([sys.executable, "-I", *map(str, a)], capture_output=True, text=True).stdout
rpc("-c", "import bpy\nfor o in list(bpy.data.objects):\n    if o.name == 'LowPoly' or o.name.startswith('Hair_tube_') or o.name in ('Hair_hood', 'Hair_dome', 'Hair_front'):\n        bpy.data.objects.remove(o)")
run(H / "hair_part.py", "hood", hood)
for step in ("hair_cap.py", "hair_heal.py"):
    r = rpc(str(H / step)); print(step, (r.stdout + r.stderr).replace("\n", " ")[-300:])
print(run(H / "hair_connect.py", "0.06", budget))
r = rpc(str(H / "hair_join.py")); print("join", (r.stdout + r.stderr).replace("\n", " ")[-500:])
