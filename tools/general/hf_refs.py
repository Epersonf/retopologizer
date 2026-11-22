r"""For every recording with actions, extracts the reference surface of the .blend it started from (see hf_ref_worker.py) into <rec>/ref.npz + ref.json.
  python tools/general/hf_refs.py            # all recordings, skips the ones that already have ref.npz
Needs Blender (BLENDER_EXE or the Steam path). Several recordings of one blend share one extraction (copied)."""
import glob, json, os, shutil, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
EXE = os.environ.get("BLENDER_EXE", r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe")
done = {}
for r in sorted(glob.glob(os.path.join(ROOT, "projects", "*", "session", "rec_*"))):
    a = os.path.join(r, "actions.jsonl")
    if not os.path.exists(a) or os.path.getsize(a) == 0 or os.path.exists(os.path.join(r, "ref.npz")): continue
    proj = r.split(os.sep + "session")[0]; m = json.load(open(os.path.join(r, "meta.json")))
    blend = os.path.join(proj, "draft", os.path.basename(m["blend"].replace("\\", "/")))
    cps = sorted(glob.glob(os.path.join(r, "checkpoint_*.json"))); edited = set(json.load(open(cps[-1]))["objects"]) if cps else set()
    for l in open(a, encoding="utf-8"):
        if l.strip(): edited.add(json.loads(l)["obj"]); break
    key = (blend, tuple(sorted(edited)))
    if key in done and os.path.exists(os.path.join(done[key], "ref.npz")):
        for f in ("ref.npz", "ref.json"): shutil.copy(os.path.join(done[key], f), os.path.join(r, f))
        print("copied", r); continue
    subprocess.run([EXE, "-b", blend, "--python", os.path.join(ROOT, "tools", "general", "hf_ref_worker.py"), "--", r, ",".join(sorted(edited))], capture_output=True)
    print("extracted" if os.path.exists(os.path.join(r, "ref.npz")) else "FAILED", r); done[key] = r
