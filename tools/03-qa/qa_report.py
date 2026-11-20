"""QA report of an object as ONE file to read or hand over (the report idea of the TopoToolkit add-on, with this repo's battery): counts, polygon types, edge types
(orphan / boundary / multi), valence histogram (poles 3..8 and N = more than 8), doubles, the battery's lines when `ref`/`battery` are given, and workbench views as inline images.
fmt: "html" (tables + images), "txt", "csv". Inside Blender:
  exec(open(ROOT+r"\tools\03-qa\qa_report.py").read())
  qa_report("LowPoly", r"C:/out/lowpoly_report.html", ref="HairFull", battery=True, fast=True, views=("front", "back", "right", "persp"))     # -> {"path", "stats", "pass"}"""
import bpy, bmesh, base64, csv, datetime, io, os, tempfile
from collections import Counter
ROOT_QA = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.join(os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd()), "tools", "03-qa")
exec(open(ROOT_QA + "/qa_mark.py", encoding="utf-8").read()); exec(open(ROOT_QA + "/../general/render_views.py", encoding="utf-8").read())


def topo_stats(name):
    ob = bpy.data.objects[name]; bm = bmesh.new(); bm.from_mesh(ob.data); fc = Counter(min(len(f.verts), 5) for f in bm.faces); ec = Counter(min(len(e.link_faces), 3) for e in bm.edges)
    val = Counter(min(len(v.link_edges), 9) for v in bm.verts if v.link_edges); m = qa_mark(name, select="none"); remove_marks(name)
    s = {"vertices": len(bm.verts), "edges": len(bm.edges), "faces": len(bm.faces), "triangles_equiv": sum(len(f.verts) - 2 for f in bm.faces), "tris": fc[3], "quads": fc[4], "ngons": fc[5],
         "orphan_edges": ec[0], "boundary_edges": ec[1], "multi_edges": ec[3], "doubles": m["counts"]["doubles"], "valence": {("N" if k == 9 else str(k)): v for k, v in sorted(val.items())}}
    bm.free(); return s


def qa_report(name, path, ref=None, battery=False, fast=True, views=("front", "back", "right", "persp"), fmt=None, res=420):
    fmt = fmt or os.path.splitext(path)[1].lstrip(".").lower() or "html"; s = topo_stats(name); lines, ok = [], None
    if battery:
        exec(open(ROOT_QA + "/qa_suite.py", encoding="utf-8").read(), globals()); q = qa_suite(name, ref=ref, fast=fast); lines, ok = q["lines"], q["pass"]
    when = datetime.datetime.now().strftime("%Y-%m-%d %H:%M"); body = ""
    if fmt == "csv":
        o = io.StringIO(); w = csv.writer(o); w.writerow(["object", name]); w.writerow(["date", when])
        for k, v in s.items():
            w.writerows([[k + "." + a, b] for a, b in v.items()] if isinstance(v, dict) else [[k, v]])
        body = o.getvalue()
    elif fmt == "txt":
        body = "QA report %s (%s)\n" % (name, when) + "\n".join("%s: %s" % kv for kv in s.items()) + ("\n\nBattery:\n" + "\n".join(lines) if lines else "") + "\n"
    else:
        imgs = ""; d = tempfile.mkdtemp()
        for p in render_views([name], d, "v", views=list(views), res=res, fit_to=[name]):
            imgs += '<img src="data:image/png;base64,%s" alt="%s">' % (base64.b64encode(open(p, "rb").read()).decode(), os.path.basename(p))
        rows = lambda dct: "".join("<tr><th>%s</th><td>%s</td></tr>" % kv for kv in dct.items())
        flat = {k: v for k, v in s.items() if not isinstance(v, dict)}; bt = "<pre>%s</pre>" % "\n".join(lines) if lines else ""
        body = ('<!DOCTYPE html><html><head><meta charset="utf-8"><title>QA %s</title><style>body{font-family:sans-serif;margin:24px;color:#222}table{border-collapse:collapse;margin:8px 0}th,td{border:1px solid #ccc;padding:4px 10px;text-align:left}'
                'img{width:23%%;margin:1%%;border:1px solid #ccc}pre{background:#f4f4f4;padding:8px}.ok{color:#1a7f37}.no{color:#c62828}</style></head><body><h1>QA %s</h1><p>%s%s</p>%s%s'
                '<h2>Counts</h2><table>%s</table><h2>Valence (poles)</h2><table>%s</table></body></html>') % (
            name, name, when, "" if ok is None else ' <b class="%s">%s</b>' % ("ok" if ok else "no", "ALL PASS" if ok else "REJECTED"), imgs, bt, rows(flat), rows(s["valence"]))
    open(path, "w", encoding="utf-8").write(body); return {"path": path, "stats": s, "pass": ok}


def qa_report_parts(names, path, ref=None, battery=True, fast=True, **kw):
    """The same report for several objects as one model: joins temporary COPIES (the originals stay), reports, deletes the copy."""
    if len(names) == 1:
        return qa_report(names[0], path, ref=ref, battery=battery, fast=fast, **kw)
    copies = []
    for n in names:
        o = bpy.data.objects[n]; c = o.copy(); c.data = o.data.copy(); c.name = "_rep_" + n; bpy.context.scene.collection.objects.link(c); copies.append(c)
    bpy.ops.object.select_all(action='DESELECT')
    for c in copies:
        c.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]; bpy.ops.object.join(); j = bpy.context.view_layer.objects.active; j.name = j.data.name = "_rep_model"
    try:
        return qa_report("_rep_model", path, ref=ref, battery=battery, fast=fast, **kw)
    finally:
        me = j.data; bpy.data.objects.remove(j); bpy.data.meshes.remove(me)
