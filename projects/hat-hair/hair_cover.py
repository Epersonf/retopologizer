"""Silhouette coverage of the low poly over the hair reference (worker, Blender). For each view: ref mask vs low mask; the pixels
of the ref not covered by the low poly are painted red over the ref in draft/renders/cov_<view>.png; prints the uncovered share.
LOW (object names) and VIEWS may be set before running; REF defaults to HiPoly.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_cover.py"""
import bpy, numpy as np
exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\02-retopologia\wire_overlay.py", encoding="utf-8").read())
LOW = globals().get("LOW") or ["LowPoly"]; REF = globals().get("REF") or ["HiPoly"]
VIEWS = globals().get("VIEWS") or ["front", "back", "left", "right", "top"]
RES = 500; OUT = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft\renders"
bpy.context.scene.render.film_transparent = True; res = {}
for v in VIEWS:
    rot = Euler([math.radians(a) for a in (WVIEWS[v] if isinstance(v, str) else v)]); m = []
    for names in (REF, LOW):
        p = OUT + "/_m.png"; _render(names, p, rot, (-0.17, 0, 0.30), 0.62, RES)
        img = bpy.data.images.load(p, check_existing=False); a = np.array(img.pixels[:], np.float32).reshape(RES, RES, 4)
        m.append(a[..., 3] > 0.5); bpy.data.images.remove(img)
    ref, low = m; un = ref & ~low; res[str(v)] = round(100 * un.sum() / max(ref.sum(), 1), 1)
    pic = np.where(ref[..., None], np.array([.6, .6, .65, 1]), np.array([.2, .2, .2, 1])); pic[un] = [1, .1, .1, 1]; pic[low & ref] = [.55, .8, .6, 1]
    out = bpy.data.images.new("c", RES, RES, alpha=True); out.pixels = pic.ravel().tolist()
    out.filepath_raw = OUT + "/cov_%s.png" % str(v).replace(" ", "").replace(",", "_"); out.file_format = "PNG"; out.save(); bpy.data.images.remove(out)
result = {"uncovered_pct": res}
