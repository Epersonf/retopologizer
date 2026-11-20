"""STRICT gate for visible reversed faces (what Face Orientation shows red). ZERO tolerance: rays come from `n_dirs` directions all
around the model (default 400 x 200x200 rays, near edge-on hits below 0.02 ignored); if the FIRST thing any ray hits is the back
of a face (confirmed by 4 neighbouring rays, see _strict_back_hits), the model is rejected. A closed, outward-wound surface can never fail this, so a failure is a fold, an open border or
a reversed face. `heal_flipped` repairs folds by relaxing the vertices of the failing faces; the gate runs after it and raises.
Inside Blender: exec(open(ROOT+r"\tools\03-qa\qa_faces.py").read()); exec(open(ROOT+r"\tools\03-qa\qa_strict.py").read())
  r = qa_strict(["LowPoly"])                      # r["pass"], r["faces"] {object: [polygon indices]}
  heal_flipped(["LowPoly"])                       # relax + retest (fast 100 dirs), then the full strict test; raises if rejected"""
import bpy, bmesh


def _strict_back_hits(names, n_dirs, res, graze):
    """{object: {polygon: rays}} of CONFIRMED back hits. A back hit counts only if the 4 rays a third of a pixel to each side
    also hit the back of a face: a lone ray that slips through a silhouette edge (float noise) does not."""
    bpy.context.view_layer.update()
    trees = [(o,) + _tree(bpy.data.objects[o]) for o in names]
    pts = [bpy.data.objects[o].matrix_world @ Vector(c) for o in names for c in bpy.data.objects[o].bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    ctr, rad = (lo + hi) / 2, (hi - lo).length / 2; px = 2 * rad / (res - 1); out = {n: {} for n in names}

    def first(org, d):
        best = None
        for name, t, tri2poly, _ in trees:
            loc, nor, idx, dist = t.ray_cast(org, d)
            if loc is not None and (best is None or dist < best[0]):
                best = (dist, name, tri2poly[idx], nor.dot(d))
        return best
    for d in _sphere_dirs(n_dirs):
        a = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized(); b = d.cross(a)
        for i in range(res):
            for j in range(res):
                org = ctr + a * ((i / (res - 1) * 2 - 1) * rad) + b * ((j / (res - 1) * 2 - 1) * rad) - d * rad * 1.2
                h = first(org, d)
                if not h or h[3] <= graze:
                    continue
                if all((lambda g: g and g[3] > 0)(first(org + a * du + b * dv, d)) for du, dv in ((px / 3, 0), (-px / 3, 0), (0, px / 3), (0, -px / 3))):
                    out[h[1]][h[2]] = out[h[1]].get(h[2], 0) + 1
    return out


def qa_strict(names, n_dirs=400, res=200, graze=0.02):
    bad = _strict_back_hits(names, n_dirs, res, graze)
    return {"pass": not any(bad.values()), "reversed_faces": sum(len(v) for v in bad.values()),
            "faces": {n: sorted(v)[:60] for n, v in bad.items()}, "_all": {n: sorted(v) for n, v in bad.items()}}


def _relax(name, faces, k=0.5, rings=1):
    """Move the vertices of the given faces (and `rings` rings around them) a fraction k toward the average of their neighbours."""
    me = bpy.data.objects[name].data; bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    vs = {v for i in faces for v in bm.faces[i].verts}
    for _ in range(rings):
        vs |= {e.other_vert(v) for v in list(vs) for e in v.link_edges}
    new = {v: v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges), v.co * 0) / len(v.link_edges), k) for v in vs}
    for v, c in new.items():
        v.co = c
    bm.to_mesh(me); bm.free(); me.update()


def heal_flipped(names, rounds=80, n_dirs=100, res=100):
    """Relax the failing faces (stronger and wider every round) until none is seen from the back, then require the strict test.
    Run it on the shells BEFORE the tubes are attached: it moves vertices."""
    for r in range(rounds):
        q = qa_strict(names, n_dirs, res)
        if q["pass"]:
            break
        for n in names:
            if q["_all"][n]:
                _relax(n, q["_all"][n], k=min(0.9, 0.4 + 0.03 * r), rings=1 + r // 10)
    final = qa_strict(names)
    if not final["pass"]:
        raise RuntimeError("REJECTED: %d faces still seen from the back: %s" % (final["reversed_faces"], final["faces"]))
    return {"rounds": r, "reversed_faces": 0}
