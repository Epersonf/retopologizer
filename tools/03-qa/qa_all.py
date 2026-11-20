"""Single QA gate: backfaces + UV + z-fighting. Inside Blender:
  exec(open(ROOT+r"\tools\03-qa\qa_all.py").read()); qa_all(["chest_base","chest_lid"])   # raises if it fails
Rules: no backface visible from any outside/cavity direction (400 dirs, 200x200 rays each,
near edge-on hits ignored below 0.1), no UV overlap/out-of-bounds/flipped, >= 8 px gap at 2048.
"""
import bpy
ROOT_TOOLS = r"C:\Users\epers\Desktop\retopologizer\tools"
exec(open(ROOT_TOOLS + r"\03-qa\qa_faces.py").read())
exec(open(ROOT_TOOLS + r"\general\qa_uv.py").read())
exec(open(ROOT_TOOLS + r"\03-qa\qa_zfight.py").read())


def qa_all(names, raise_on_fail=True):
    f = qa_faces(names, n_dirs=400, res=200)
    u = qa_uv(names, size=2048, min_gap_px=8)
    z = qa_zfight(names)
    u4 = qa_uv(names, size=4096, min_gap_px=8)
    rep = {"faces_pass": f["pass"], "exposed_backface_faces": f["exposed_backface_faces"],
           "uv_pass": u["pass"] and u4["pass"], "uv_overlap_px": u["overlap_pixels"] + u4["overlap_pixels"],
           "uv_gap_violation_px": u["gap_violation_pixels"], "uv_coverage_pct": u["coverage_pct"],
           "zfight_pairs": z["coplanar_overlapping_pairs"]}
    rep["pass"] = rep["faces_pass"] and rep["uv_pass"] and z["pass"]
    if raise_on_fail and not rep["pass"]:
        raise AssertionError(f"QA failed: {rep}")
    return rep
