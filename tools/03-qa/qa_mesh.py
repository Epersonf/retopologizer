"""QA: mesh integrity, the cheap checks. Per object: quads only (no tris / n-gons), open borders (an edge with ONE face = a hole), non-manifold
edges (3+ faces), winding conflicts (two faces of an edge running the same way = one is reversed), loose vertices, duplicate vertices
(< 0.5 mm), degenerate faces (area < 1e-8). A closed low poly (hair tubes with caps, shell with lid) has 0 open borders.
Inside Blender: exec(open(ROOT+r"\tools\03-qa\qa_mesh.py").read())
  r = qa_mesh("LowPoly")       # r["pass"], counts, r["borders"] = world points of open edges (first 8)"""
import bpy, bmesh
from mathutils.kdtree import KDTree


def qa_mesh(name, quads_only=True):
    ob = bpy.data.objects[name]; bm = bmesh.new(); bm.from_mesh(ob.data); M = ob.matrix_world; bm.verts.ensure_lookup_table()
    tris = sum(len(f.verts) == 3 for f in bm.faces); ngons = sum(len(f.verts) > 4 for f in bm.faces)
    border = [e for e in bm.edges if len(e.link_faces) == 1]; nonman = sum(len(e.link_faces) > 2 for e in bm.edges); wind = 0
    for e in bm.edges:
        if len(e.link_faces) == 2:
            a, b = e.link_faces; wind += [l for l in a.loops if l.edge == e][0].vert == [l for l in b.loops if l.edge == e][0].vert
    loose = sum(not v.link_edges for v in bm.verts); degen = sum(f.calc_area() < 1e-8 for f in bm.faces)
    kd = KDTree(len(bm.verts))
    for v in bm.verts:
        kd.insert(v.co, v.index)
    kd.balance(); dup = sum(len([1 for _, i, _ in kd.find_range(v.co, 5e-4) if i != v.index]) > 0 for v in bm.verts)
    out = {"faces": len(bm.faces), "triangles_equiv": sum(len(f.verts) - 2 for f in bm.faces), "tris": tris, "ngons": ngons, "open_border_edges": len(border),
           "non_manifold_edges": nonman, "winding_conflicts": wind, "loose_verts": loose, "duplicate_verts": dup, "degenerate_faces": degen,
           "borders": [[round(x, 3) for x in (M @ (border[i].verts[0].co + border[i].verts[1].co) / 2)] for i in range(0, len(border), max(1, len(border) // 8))][:8]}
    bm.free()
    out["pass"] = not (out["open_border_edges"] or nonman or wind or loose or dup or degen or (quads_only and (tris or ngons)))
    return out
