"""QA: point at the defects in the mesh itself (the idea of the TopoToolkit add-on: select the offenders). Writes a boolean attribute per kind (Object Data >
Attributes: qa_border, qa_nonmanifold, qa_wire, qa_doubles, qa_tris, qa_ngons, qa_degenerate, qa_pole_<v>, qa_pole_n) and selects the offenders of one kind, so the saved
.blend opens in Edit Mode with them highlighted (the select mode of the scene is set to match: vertex, edge or face). Nothing else is touched.
  kinds: border (edge with 1 face) nonmanifold (3+ faces) wire (0 faces) doubles (vertices closer than `tol`) tris ngons degenerate poles (interior vertices of valence != 4)
Inside Blender: exec(open(ROOT+r"\tools\03-qa\qa_mark.py").read())
  r = qa_mark("LowPoly", select="border")      # r["counts"] = {kind: n}, r["selected"]; the attributes stay in the mesh (remove_marks("LowPoly") deletes them)"""
import bpy, bmesh
from mathutils.kdtree import KDTree

_DOMAIN = {"border": "EDGE", "nonmanifold": "EDGE", "wire": "EDGE", "doubles": "POINT", "tris": "FACE", "ngons": "FACE", "degenerate": "FACE"}


def _flags(bm, tol):
    ed = {"border": [len(e.link_faces) == 1 for e in bm.edges], "nonmanifold": [len(e.link_faces) > 2 for e in bm.edges], "wire": [not e.link_faces for e in bm.edges]}
    kd = KDTree(len(bm.verts))
    for v in bm.verts:
        kd.insert(v.co, v.index)
    kd.balance(); vt = {"doubles": [len(kd.find_range(v.co, tol)) > 1 for v in bm.verts]}
    for v in bm.verts:                                                           # poles: interior vertices of valence != 4 (3, 5, 6, 7, 8 and N = more than 8)
        if not v.is_boundary and v.link_edges:
            n = len(v.link_edges); k = "qa_pole_n" if n > 8 else "qa_pole_%d" % n
            if n != 4:
                vt.setdefault(k, [False] * len(bm.verts))[v.index] = True
    fc = {"tris": [len(f.verts) == 3 for f in bm.faces], "ngons": [len(f.verts) > 4 for f in bm.faces], "degenerate": [f.calc_area() < 1e-8 for f in bm.faces]}
    return ed, vt, fc


def remove_marks(name):
    me = bpy.data.objects[name].data
    for a in [a for a in me.attributes if a.name.startswith("qa_")]:
        me.attributes.remove(a)


def qa_mark(name, select="border", tol=5e-4):
    ob = bpy.data.objects[name]; me = ob.data; bm = bmesh.new(); bm.from_mesh(me); ed, vt, fc = _flags(bm, tol); remove_marks(name); counts = {}; sel = {}
    for kind, flags, dom in [(k, f, "EDGE") for k, f in ed.items()] + [(("qa_" + k) if not k.startswith("qa_") else k, f, "POINT") for k, f in vt.items()] + [(k, f, "FACE") for k, f in fc.items()]:
        key = kind[3:] if kind.startswith("qa_") else kind; counts[key] = sum(flags)
        if any(flags):
            a = me.attributes.new("qa_" + key, 'BOOLEAN', dom); a.data.foreach_set("value", flags); sel[key] = (dom, flags)
    for k in ("pole_3", "pole_5", "pole_6", "pole_7", "pole_8", "pole_n"):
        counts.setdefault(k, 0)
    want = [k for k in sel if k == select or (select == "poles" and k.startswith("pole_"))]; dom = sel[want[0]][0] if want else "EDGE"
    for coll, n in ((me.vertices, len(me.vertices)), (me.edges, len(me.edges)), (me.polygons, len(me.polygons))):
        coll.foreach_set("select", [False] * n)
    for k in want:
        d, flags = sel[k]; coll = {"POINT": me.vertices, "EDGE": me.edges, "FACE": me.polygons}[d]; cur = [False] * len(coll); coll.foreach_get("select", cur)
        coll.foreach_set("select", [a or b for a, b in zip(cur, flags)])
    bpy.context.scene.tool_settings.mesh_select_mode = (dom == "POINT", dom == "EDGE", dom == "FACE"); me.update(); bm.free()
    return {"counts": counts, "selected": sum(counts[k] for k in counts if k == select or (select == "poles" and k.startswith("pole_"))), "mode": dom}
