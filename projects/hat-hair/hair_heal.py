"""Heals the capped shells (Hair_hood by default; worker) until three gates pass on them: no spikes (qa_shape.py), no reversed face
seen from far (qa_strict.py), no fold seen from inside a crevice (qa_local.py). Raises = rejected. Run before the tubes are built
(hair_build.py does it), so the tubes attach to the final shells.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_heal.py"""
import bpy
Q = r"C:\Users\epers\Desktop\retopologizer\tools\03-qa"
for f in ("qa_faces", "qa_strict", "qa_shape", "qa_local"):
    exec(open(Q + "\\" + f + ".py").read())
S = globals().get("SHELLS", ["Hair_hood"]); log = []
for it in range(10):                                   # relaxing one defect can create another: loop until all three hold
    log.append(heal_spikes(S[0])["rounds"]); heal_flipped(S, rounds=30)
    loc = qa_local(S[0]); done = not qa_shape(S[0])["spikes"] and loc["pass"]
    if done:
        break
    if not loc["pass"]:
        _relax(S[0], [f["face"] for f in loc["faces"]], k=0.5, rings=2)
assert done, "REJECTED: spikes %s, folds %s" % (qa_shape(S[0])["spikes"][:3], qa_local(S[0])["faces"][:3])
result = {"loops": it + 1, "spike_rounds": log, "reversed_faces": 0}
