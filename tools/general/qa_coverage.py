r"""Does the retopo mesh COVER the reference? (the test that sees a toe that is missing or collapsed: every face can be perfect and a whole toe absent)
  exec(open(r"<repo>\tools\general\qa_coverage.py", encoding="utf-8").read())
  r = qa_coverage("Mesh", "HiPoly", tol=0.006, band=0.03)     # r["pass"], r["uncovered_pct"], r["worst_mm"], r["clusters"]
Takes the ref vertices inside the mesh bounding box (+ pad) whose nearest point on the mesh is between `tol` and `band`: too far to be covered,
too near to belong to another part of the body. Clusters = groups of such points (centroid in mm, size). Zero tolerance above `max_pct` (default 1%).
Measured: the artist's rear toes 0.0-0.3%; the agent's rear paw with the collapsed left toe, see docs/03-qa/qa.md."""
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _ref_pts(name):
    o = bpy.data.objects[name]; a = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", a)
    M = np.array(o.matrix_world); return a.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]


def qa_coverage(name, ref_name, tol=0.006, band=0.03, pad=0.01, max_pct=1.0, border_skip=True):
    o = bpy.data.objects[name]; bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bm.faces.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm); P = np.array([tuple(v.co) for v in bm.verts]); lo, hi = P.min(0) - pad, P.max(0) + pad
    H = _ref_pts(ref_name); H = H[((H > lo) & (H < hi)).all(1)]
    bv = {v.index for e in bm.edges if e.is_boundary for v in e.verts} if border_skip else set()
    def near(h):  # distancia ao mais proximo; pontos cujo mais proximo e uma face da borda aberta (fim da perna) nao contam: o pedaco de la e de outra peca
        r = tree.find_nearest(Vector(tuple(h)))
        if r[0] is None: return 9.9
        return 9.9 if bv and r[3] > tol and any(v.index in bv for v in bm.faces[r[2]].verts) else r[3]
    d = np.array([near(h) for h in H])
    bad = H[(d > tol) & (d < band)]; pct = round(100.0 * len(bad) / max(len(H), 1), 2); clusters = []
    if len(bad):
        cell = np.floor(bad / 0.008).astype(int); keys = {}
        for i, c in enumerate(map(tuple, cell)): keys.setdefault(c, []).append(i)
        seen = set()
        for c in keys:
            if c in seen: continue
            st = [c]; seen.add(c); idx = []
            while st:
                x = st.pop(); idx += keys[x]
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            n = (x[0] + dx, x[1] + dy, x[2] + dz)
                            if n in keys and n not in seen: seen.add(n); st.append(n)
            if len(idx) >= 8: clusters.append({"centroid_mm": [round(float(v) * 1000, 1) for v in bad[idx].mean(0)], "points": len(idx)})
    clusters.sort(key=lambda c: -c["points"]); bm.free()
    return {"pass": pct <= max_pct, "uncovered_pct": pct, "worst_mm": round(float(d[(d < band)].max()) * 1000, 1) if len(H) else 0, "clusters": clusters[:6], "ref_points": len(H)}
