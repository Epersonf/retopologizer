"""The whole low poly, from the worker on a copy of draft/hair_work.blend (HairFull loaded; needs draft/hair_locks.npz from
hair_locks.py 0.03 and hair_locks_z.npz from hair_locks.py 0.04 z): hood shell -> lid -> heal (spikes, far and near reversed faces) ->
tubes buried in what they grow from -> join -> the whole QA battery (tools/03-qa/qa.py). Any gate that fails: nothing is delivered
(the file is kept as draft/hair_lowpoly_rejected.blend) and the failing lines are printed.
  python -I projects/hat-hair/hair_build.py [tubes] [hood=32,16,8] [tube_budget=900]
  `tubes` keeps the Hair_hood already in the worker (skips the ~40 s of shell building while tuning the tubes)."""
import subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent; ROOT = H.parent.parent
only_tubes = "tubes" in sys.argv[1:]
hood, budget = ([a for a in sys.argv[1:] if a != "tubes"] + [None] * 2)[:2]; hood = hood or "32,16,8"; budget = budget or "900"
rpc = lambda *a: subprocess.run([sys.executable, "-I", str(ROOT / "tools/general/blender_rpc.py"), "--port", "9877", *a], capture_output=True, text=True)
run = lambda *a: subprocess.run([sys.executable, "-I", *map(str, a)], capture_output=True, text=True).stdout
keep = "('Hair_hood', 'Hair_dome', 'Hair_front')" if not only_tubes else "()"
rpc("-c", "import bpy\nfor o in list(bpy.data.objects):\n    if o.name == 'LowPoly' or o.name.startswith('Hair_tube_') or o.name in %s:\n        bpy.data.objects.remove(o)" % keep)
if not only_tubes:
    run(H / "hair_part.py", "hood", hood)
    for step in ("hair_cap.py", "hair_heal.py"):
        r = rpc(str(H / step)); out = r.stdout + r.stderr; print(step, out.replace("\n", " ")[-200:])
        if "REJECTED" in out:
            sys.exit("hood rejected at " + step)
print(run(H / "hair_connect.py", "0.06", budget))
r = rpc(str(H / "hair_join.py")); out = r.stdout + r.stderr                  # the report is the battery's lines: one per check
print("join:", "ALL PASS, saved draft/hair_lowpoly_v3.blend" if "REJECTED" not in out else out[out.index("REJECTED"):].replace("\\n", "\n"))
