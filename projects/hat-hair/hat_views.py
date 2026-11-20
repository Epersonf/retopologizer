"""Check renders of Hat_retopo over the reference (hair clipped away). TAG / VIEWS may be set before running."""
exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\wire_overlay.py", encoding="utf-8").read())
OUT = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft\renders"
TAG = globals().get("TAG", "o1")
VIEWS = globals().get("VIEWS") or ["front", (75, 0, -135), (75, 0, 135), "top"]
paths = []
for i, view in enumerate(VIEWS):
    p = OUT + "\%s_%d.png" % (TAG, i)
    wire_overlay(["Hat_retopo"], p, view=view, shade=["HiPoly"], center=(0.447, 0.02, 0.25), size=0.68, res=800)
    paths.append(p)
result = paths
