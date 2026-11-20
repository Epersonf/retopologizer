"""QA battery: ONE call runs every gate and returns a short report (one line per check), so an agent spends a few hundred tokens
instead of reading six result dicts. Checks, cheapest first:
  mesh      qa_mesh.py     quads only, no open border / non-manifold / winding conflict / duplicate
  budget    triangles <= `budget`
  shape     qa_shape.py    spikes, needle-pointed tubes, thin tubes (+ sliver share, reported)
  floating  qa_floating.py parts that touch nothing
  attach    qa_attach.py   tubes that only touch (connected but stuck on, not buried in the parent)
  local     qa_local.py    reversed faces seen from inside crevices / folds (rays from every face, outward hemisphere)
  strict    qa_strict.py   reversed face visible from ANY of 400 directions (`fast=True`: 100 directions, ~4x quicker; final run is full)
  fit       qa_fit.py      silhouette IoU, uncovered reference, lumps that are not in the reference (needs `ref`)
Inside Blender: exec(open(ROOT+r"\tools\03-qa\qa_suite.py").read())
  r = qa_suite("LowPoly", ref="HairFull", only=None, skip=(), fast=False, budget=3000)   # r["pass"], r["lines"], r["raw"][check]
Command line (worker on 9877): python -I tools/03-qa/qa.py LowPoly --ref HairFull [--only shape,fit] [--skip strict] [--fast] [--json]"""
import bpy, time
ROOT_QA = r"C:\Users\epers\Desktop\retopologizer\tools\03-qa"
for _f in ("qa_faces", "qa_strict", "qa_shape", "qa_floating", "qa_attach", "qa_local", "qa_fit", "qa_mesh"):
    exec(open(ROOT_QA + "\\" + _f + ".py", encoding="utf-8").read())
ORDER = ["mesh", "budget", "shape", "floating", "attach", "local", "strict", "fit"]
HINT = {"mesh": "open border = hole: close it; winding: rebuild the part with outward winding; duplicates: merge",
        "budget": "drop the smallest tubes or coarsen the shell counts", "shape": "heal_spikes(); tube: raise min radius / blunt tip",
        "attach": "root deeper into the parent (EXT, hair_connect target + 1 r), never just touching", "floating": "hair_connect.py: extend the tube end to the target point", "local": "folds: heal_flipped after relaxing; move the rim / lid",
        "strict": "heal_flipped(); then change the geometry (rim, lid), never flip by hand", "fit": "cover the clusters: more shells/tubes where it says"}


def _line(k, r):
    if k == "mesh":
        return "%d quads-eq tris, tris=%d ngons=%d border=%d nonmanifold=%d winding=%d dup=%d" % (r["triangles_equiv"], r["tris"], r["ngons"], r["open_border_edges"], r["non_manifold_edges"], r["winding_conflicts"], r["duplicate_verts"])
    if k == "budget":
        return "%d / %d triangles" % (r["tris"], r["budget"])
    if k == "shape":
        return "spikes=%d pointed=%d thin=%d slivers=%.1f%%" % (len(r["spikes"]), len(r["pointed"]), len(r["thin"]), r["sliver_share"] * 100)
    if k == "attach":
        return "%d tubes, %d not buried in the parent (end cap pokes out or only touches): %s" % (r["tubes"], len(r["loose"]), [(l["end_at"], l["outside"], l["depth_r"]) for l in r["loose"]][:3])
    if k == "floating":
        return "groups=%d floating=%s" % (r["groups"], [(f["verts"], f["gap_mm"]) for f in r["floating"]][:4])
    if k in ("local", "strict"):
        return "%d reversed faces seen%s" % (r.get("reversed_faces", len(r["faces"])), ", worst at %s" % r["faces"][0]["at"] if k == "local" and r["faces"] else "")
    return "iou mean %.2f worst %.2f, missing %.1f%% %s, excess %.1f%% %s" % (r["iou_mean"], r["iou_worst"], r["missing_share"] * 100,
        [(c["where"], c["points"]) for c in r["missing_clusters"][:3]], r["excess_share"] * 100, [c["where"] for c in r["excess_clusters"][:2]])


def qa_suite(name, ref=None, only=None, skip=(), fast=False, budget=3000):
    raw = {}; lines = []; failed = []
    for k in [c for c in ORDER if (not only or c in only) and c not in skip and (c != "fit" or ref)]:
        t = time.time()
        r = {"mesh": lambda: qa_mesh(name), "budget": lambda: (lambda m: {"pass": m["triangles_equiv"] <= budget, "tris": m["triangles_equiv"], "budget": budget})(qa_mesh(name)),
             "shape": lambda: qa_shape(name), "floating": lambda: qa_floating([name]), "attach": lambda: qa_attach(name), "local": lambda: qa_local(name),
             "strict": lambda: qa_strict([name], n_dirs=100 if fast else 400, res=100 if fast else 200), "fit": lambda: qa_fit(name, ref)}[k]()
        r.pop("_all", None)
        raw[k] = r; ok = bool(r["pass"]); failed += [] if ok else [k]
        lines.append("%s %-8s %s  (%.0fs)%s" % ("PASS" if ok else "FAIL", k, _line(k, r), time.time() - t, "" if ok else "\n     fix: " + HINT[k]))
    return {"pass": not failed, "failed": failed, "lines": lines, "raw": raw}
