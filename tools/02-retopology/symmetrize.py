"""Make a hand-built mesh symmetric in X: straighten it, cut on the axis, keep one half, mirror it with IDENTICAL UVs.
For a prop the artist built a bit crooked (the sword case: `docs/08-cases/sword.md`). The result is one welded mesh whose
two halves share the same texture (mirrored UV on purpose: islands overlap, so `qa_uv` overlap is expected, say so in the listing).
  exec(open(r"<repo>\\tools\\02-retopology\\symmetrize.py", encoding="utf-8").read())
  knots = axis_knots(ob, [0.0, 0.3, 0.6, 0.9])            # measures where the axis sits (x of the mid-point of the silhouette) per z
  r = symmetrize(ob, knots, x0=0.0, keep="right", tol=0.0015)   # edits ob.data in place; r = counts and checks
`knots` = [(z, x_axis), ...]: every vertex is moved by -x_axis(z) (linear interpolation), so the axis becomes x = x0.
Vertices within `tol` of the plane are snapped onto it. Triangles that the cut leaves on the plane are merged or collapsed;
`r["quads"]`, `r["tris"]`, `r["open_or_nonmanifold_edges"]` and `r["volume"]` tell what is left: REPORT the triangles."""
import bpy, bmesh, math
import numpy as np

_JOIN = dict(cmp_seam=False, cmp_sharp=False, cmp_uvs=False, cmp_vcols=False, cmp_materials=False,
             angle_face_threshold=math.pi, angle_shape_threshold=math.pi)


def axis_knots(ob, zs, band=0.06):
    """x of the middle of the object at each z (mean of min and max x of the vertices within `band` of z; a z with no vertex in
    the band is left out: widen `band` or use more z values)."""
    co = np.array([v.co[:] for v in ob.data.vertices])
    out = []
    for z in zs:
        m = np.abs(co[:, 2] - z) < band
        if m.any():
            out.append((z, float((co[m, 0].min() + co[m, 0].max()) / 2)))
    return out


def _cut_half(bm, x0, tol, keep):
    if keep == "left":  # reflect first so "keep" is always the +x side
        for v in bm.verts: v.co.x = 2 * x0 - v.co.x
        for f in bm.faces: f.normal_flip()
    snapped = 0
    for v in bm.verts:
        if abs(v.co.x - x0) < tol and v.co.x != x0:
            v.co.x = x0; snapped += 1
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=1e-6,
                           plane_co=(x0, 0, 0), plane_no=(1, 0, 0), clear_inner=True, clear_outer=False)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
    for f in [f for f in bm.faces if any(v.co.x < x0 - 1e-7 for v in f.verts)]: bm.faces.remove(f)
    for v in [v for v in bm.verts if not v.link_faces]: bm.verts.remove(v)
    bm.faces.ensure_lookup_table()
    return snapped


def _tidy_plane(bm, x0):
    """Pentagons -> tris -> quads where possible; collapse tris that still sit on the cut plane."""
    pent = [f for f in bm.faces if len(f.verts) > 4]
    if pent: bmesh.ops.triangulate(bm, faces=pent)
    bmesh.ops.join_triangles(bm, faces=[f for f in bm.faces if len(f.verts) == 3], **_JOIN)
    bm.faces.ensure_lookup_table()
    on_plane = lambda e: all(abs(v.co.x - x0) < 1e-7 for v in e.verts)
    for _ in range(40):
        cand = [e for f in bm.faces if len(f.verts) == 3 for e in f.edges if on_plane(e) and len(e.link_faces) == 1]
        if not cand: break
        bmesh.ops.collapse(bm, edges=[cand[0]], uvs=True)
        bm.faces.ensure_lookup_table()
    tris = [f for f in bm.faces if len(f.verts) == 3]
    if tris: bmesh.ops.join_triangles(bm, faces=tris, **_JOIN)
    bm.faces.ensure_lookup_table()


def _mirror(bm, x0):
    """New mesh = the half + its reflection, same UVs, welded on the plane by rounded position."""
    uvl = bm.loops.layers.uv.active
    data = [([v.co.copy() for v in f.verts], [l[uvl].uv.copy() for l in f.loops]) for f in bm.faces]
    nb = bmesh.new(); uv2 = nb.loops.layers.uv.verify(); cache = {}; skipped = 0

    def V(p, flip):
        q = (round(2 * x0 - p.x if flip else p.x, 7), round(p.y, 7), round(p.z, 7))
        if q not in cache: cache[q] = nb.verts.new(q)
        return cache[q]
    for co, uvs in data:
        k = len(co)
        try:
            f = nb.faces.new([V(p, False) for p in co])
            for l, u in zip(f.loops, uvs): l[uv2].uv = u
            g = nb.faces.new([V(co[i], True) for i in reversed(range(k))])
            for j, l in enumerate(g.loops): l[uv2].uv = uvs[k - 1 - j]
        except ValueError:  # degenerate face (e.g. blade tip): skipped, counted
            skipped += 1
    nb.verts.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(nb, faces=nb.faces)
    return nb, skipped


def symmetrize(ob, knots, x0=0.0, keep="right", tol=0.0015):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    kz, kx = zip(*knots)
    for v in bm.verts: v.co.x -= float(np.interp(v.co.z, kz, kx))
    snapped = _cut_half(bm, x0, tol, keep)
    _tidy_plane(bm, x0)
    nb, skipped = _mirror(bm, x0); bm.free()
    bad = [e for e in nb.edges if len(e.link_faces) != 2]
    res = {"snapped": snapped, "skipped_faces": skipped, "verts": len(nb.verts), "faces": len(nb.faces),
           "quads": sum(len(f.verts) == 4 for f in nb.faces), "tris": sum(len(f.verts) == 3 for f in nb.faces),
           "open_or_nonmanifold_edges": len(bad), "volume": round(nb.calc_volume(signed=True), 6)}
    nb.to_mesh(ob.data); nb.free(); ob.data.update()
    return res
