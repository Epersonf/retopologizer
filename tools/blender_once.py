"""Run a worker script (same contract as tools/blender_worker.py: it may set `result`) in a one-shot headless Blender,
for when no worker is listening. The result comes out as one stdout line "RESULT_JSON: {...}".
  "<blender.exe>" -b --factory-startup --python tools/blender_once.py -- script.py"""
import bpy, json, sys, traceback

path = sys.argv[sys.argv.index("--") + 1]
ns = {"bpy": bpy, "__name__": "__worker__"}
try:
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"), ns)
    print("RESULT_JSON: " + json.dumps(ns.get("result"), default=str), flush=True)
except Exception:
    traceback.print_exc()
    sys.stdout.flush()
    sys.exit(1)
