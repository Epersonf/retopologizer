"""Contact sheet: the same views of the reference and of the candidates, tiled in ONE png (one Read shows it all; the agent flow
costs one image instead of one per view). Rows = groups (the first row is always HairFull), columns = views, framed by the reference.
A group is object names joined by +; a trailing * is a prefix (Hair_base+Hair_lock_*). Worker on 9877 (HairFull loaded).
  python -I projects/hat-hair/hair_sheet.py [group ...] [--views front,left,back,q1,top] [--res 420] [--tag sheet] [--orient]  ->  draft/renders/<tag>.png
--orient: the groups are drawn as Blender's face-orientation overlay (blue front, RED back = a reversed face seen from outside; qa_orient.py) and the
red pixels per view are printed. Views: front back left right top q1..q4 (3/4) low1 low2 (from below)."""
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
H = Path(__file__).resolve().parent; ROOT = H.parent.parent; OUT = H / "draft" / "renders"; OUT.mkdir(exist_ok=True)
a = sys.argv[1:]; opt = {"--views": "front,left,back,q1,top", "--res": "420", "--tag": "sheet"}; orient = "--orient" in a; a = [x for x in a if x != "--orient"]
for k in opt:
    if k in a:
        i = a.index(k); opt[k] = a[i + 1]; del a[i:i + 2]
views = opt["--views"].split(","); res = int(opt["--res"]); groups = [["HairFull"]] + [g.split("+") for g in a]
code = '''
import bpy, fnmatch
exec(open(r"%s", encoding="utf-8").read())
exec(open(r"%s", encoding="utf-8").read())
VIEWS.update({"q1": (75, 0, 35), "q2": (75, 0, -35), "q3": (75, 0, 215), "q4": (75, 0, 145), "low1": (110, 0, 30), "low2": (110, 0, 210)})
reds = []
for gi, g in enumerate(%r):
    names = [o.name for o in bpy.data.objects if any(fnmatch.fnmatch(o.name, pat) for pat in g)]
    if %r and gi > 0:
        reds.append([x[2] for x in orient_views(names, r"%s", "_s%%d" %% gi, views=%r, res=%d, fit_to=["HairFull"])])
    else:
        render_views(names, r"%s", "_s%%d" %% gi, res=%d, views=%r, fit_to=["HairFull"])
result = reds
''' % (ROOT / "tools/general/render_views.py", ROOT / "tools/03-qa/qa_orient.py", groups, orient, OUT, views, res, OUT, res, views)
r = subprocess.run([sys.executable, "-I", str(ROOT / "tools/general/blender_rpc.py"), "--port", "9877", "-c", code], capture_output=True, text=True)
if "Traceback" in r.stdout + r.stderr:
    sys.exit((r.stdout + r.stderr)[-1500:])
if orient:
    print("red pixels per view", views, r.stdout.replace("\n", "").replace(" ", "")[-300:])
sheet = Image.new("RGB", (res * len(views), res * len(groups)), (255, 255, 255)); d = ImageDraw.Draw(sheet)
for gi, g in enumerate(groups):
    for vi, v in enumerate(views):
        sheet.paste(Image.open(OUT / ("_s%d_%s.png" % (gi, v))).convert("RGB"), (vi * res, gi * res))
        d.text((vi * res + 6, gi * res + 4), "+".join(g) + " " + v, fill=(200, 0, 0))
path = OUT / (opt["--tag"] + ".png"); sheet.save(path); print(path)
