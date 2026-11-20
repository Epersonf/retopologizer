import bpy, json
exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\qa_uv.py").read())
for g in (1,2,3,4,6):
    r = qa_uv(["tree_twig"], size=2048, min_gap_px=g)
    print("GAP", g, r["gap_violation_pixels"], r["pass"])
