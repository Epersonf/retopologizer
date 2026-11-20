"""Topology QA of a retopo object (the checks the artist does by eye), as a dict.
  topo_qa("Cuca_retopo", ref=Ref("HiPoly"))
faces/tris/quads/ngons, triangle count after triangulation, holes (boundary edges), non-manifold edges, loose
verts, doubles (< 0.5 mm), winding conflicts (an edge walked the same way by its two faces), faces facing
inward (normal against the reference normal), poles (valence 3 / 5 / 6+), degenerate faces, distance to ref."""
import bpy, bmesh, numpy as np
from collections import Counter
from mathutils.kdtree import KDTree


def topo_qa(name, ref=None, seam_x=None, doubles=0.0005):
    bm = bmesh.new(); bm.from_mesh(bpy.data.objects[name].data); M = bpy.data.objects[name].matrix_world
    bm.transform(M); bm.normal_update()
    fc = Counter(min(len(f.verts), 5) for f in bm.faces)
    bnd = [e for e in bm.edges if e.is_boundary]
    if seam_x is not None:                       # half model: the mirror plane border is not a hole
        bnd = [e for e in bnd if not all(abs(v.co.x - seam_x) < 0.002 for v in e.verts)]
    kd = KDTree(len(bm.verts))
    for v in bm.verts:
        kd.insert(v.co, v.index)
    kd.balance()
    dbl = sum(1 for v in bm.verts if len(kd.find_range(v.co, doubles)) > 1) // 2
    wind = 0
    for e in bm.edges:
        if len(e.link_faces) == 2:
            l0 = [l for l in e.link_faces[0].loops if l.edge is e][0]
            l1 = [l for l in e.link_faces[1].loops if l.edge is e][0]
            wind += l0.vert is l1.vert
    val = Counter(len(v.link_edges) for v in bm.verts if not v.is_boundary)
    rep = {"faces": len(bm.faces), "verts": len(bm.verts), "tris": fc[3], "quads": fc[4], "ngons": fc[5],
           "triangles_total": sum(len(f.verts) - 2 for f in bm.faces), "holes_edges": len(bnd),
           "nonmanifold_edges": sum(1 for e in bm.edges if len(e.link_faces) > 2),
           "wire_edges": sum(1 for e in bm.edges if not e.link_faces), "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
           "doubles": dbl, "winding_conflicts": wind, "poles": {k: val[k] for k in sorted(val) if k != 4},
           "degenerate_faces": sum(1 for f in bm.faces if f.calc_area() < 1e-8)}
    rep["quad_only"] = fc[3] == 0 and fc[5] == 0          # the repo's rule: delivered retopo is quads only
    if ref is not None:
        inward, area, d = 0.0, 0.0, []
        for f in bm.faces:
            h = ref.nearest(f.calc_center_median(), 0.1); a = f.calc_area(); area += a
            if h and f.normal.dot(h[1]) < 0:
                inward += a
        for v in bm.verts:
            h = ref.nearest(v.co, 0.2); d.append(h[2] if h else 0.2)
        d = np.array(d) * 1000
        rep["inward_area_pct"] = round(100 * inward / (area or 1), 2)
        rep["vert_to_ref_mm"] = {"mean": round(float(d.mean()), 2), "p95": round(float(np.percentile(d, 95)), 2),
                                 "max": round(float(d.max()), 2)}
    bm.free()
    return rep
