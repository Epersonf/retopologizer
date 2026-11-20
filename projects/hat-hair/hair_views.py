"""Renders of the hair reference (hat framed out) and optionally a low-poly over it. TAG / LOW / VIEWS may be set
before running (worker on draft/hair_work.blend):
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_views.py"""
exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\02-retopologia\wire_overlay.py", encoding="utf-8").read())
OUT = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft\renders"
TAG = globals().get("TAG", "hr")
LOW = globals().get("LOW") or ["Hat_retopo"]
VIEWS = globals().get("VIEWS") or ["front", "back", "left", "right", "top", (65, 0, 35)]
CENTER = globals().get("CENTER") or (-0.17, 0.0, 0.30)
SIZE = globals().get("SIZE") or 0.62
paths = []
for i, view in enumerate(VIEWS):
    p = OUT + "/%s_%d.png" % (TAG, i)
    wire_overlay(LOW, p, view=view, shade=["HiPoly"], center=CENTER, size=SIZE, res=700)
    paths.append(p)
result = paths
