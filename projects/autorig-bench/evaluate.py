"""Auto-rig joints of the benchmark cases against their reference joints (error in % of the height). Writes
output/eval.json (joints, reference, errors, bones) and output/<case>_mesh.npz for the overlay drawing.
  "<blender.exe>" -b --factory-startup --python tools/general/blender_once.py -- projects/autorig-bench/evaluate.py
  python projects/autorig-bench/draw.py"""
import sys, json
import numpy as np
ROOT = r"C:\Users\epers\Desktop\retopologizer"
sys.path.insert(0, ROOT + r"\tools\06-rig")
import autorig.load as LD, autorig.detect as DT
from rig_mixamo import bones, chain

BENCH = ROOT + r"\projects\autorig-bench"
CASES = globals().get("CASES") or ["male", "female", "male_bind", "female_bind", "saci", "cuca", "female_apose"]
TAIL = ["Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail_End"]
out, summary = {}, {}
for case in CASES:
    o, gt = LD.bench_case(BENCH + r"\input", case)
    M = LD.mesh_of([o])
    J, B, info = DT.detect(M)
    err = {k: round(float(np.linalg.norm(J[k] - gt[k]) / B.H * 100), 2) for k in J if k in gt}
    np.savez(BENCH + r"\output\%s_mesh.npz" % case, V=M.V, F=M.F)
    names = set(J) | set(gt)
    out[case] = {"H": B.H, "x0": B.x0, "z0": B.z0, "err": err,
                 "J": {k: v.tolist() for k, v in J.items()}, "gt": {k: v.tolist() for k, v in gt.items()},
                 "bones": [[n, p] for n, p, _ in bones() + chain(TAIL, "Hips") if p and n in names],
                 "info": json.loads(json.dumps(info, default=lambda a: np.asarray(a).tolist()))}
    part = lambda k: "fingers" if "Hand" in k and k[-1].isdigit() else "tail" if k.startswith("Tail") else "body"
    summary[case] = {g: round(float(np.mean([e for k, e in err.items() if part(k) == g] or [0])), 2)
                     for g in ("body", "fingers", "tail")}
    summary[case]["worst"] = sorted(err.items(), key=lambda t: -t[1])[:5]
    summary[case]["found"] = sorted({k[8:-1] for k in J if k.startswith("LeftHand") and k[-1].isdigit()})
json.dump(out, open(BENCH + r"\output\eval.json", "w"))
result = summary
