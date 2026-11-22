r"""Quad-only fill of a hole in a bmesh, snapped to the reference. Agent-driven (it does not decide WHERE a hole is; the caller picks the loop).
Inside Blender:
  exec(open(".../hole_fill.py").read())
  L = boundary_loops(bm)                      # ordered simple loops (a pinched loop raises: fix the pinch first)
  info = fill_loop(bm, L[0], ref, fixed=())   # even loop -> grid fill; odd loop -> one loop cut first (parity), then fill
  # loop_bridge (rings between two loops of the same count) lives in loop_bridge.py
  # info: {"faces": [...], "verts": [...], "cut": bool, "bad": n, "mean_mm": d}
Rules kept: quads only (never a triangle: an odd loop is fixed with a loop cut through the quads that touch the loop), no vertex of the old mesh moves
(`fixed`), new vertices are relaxed and snapped on the ref. Raises ValueError with the reason when it cannot (open ring, pinch, no quad strip to cut)."""
import bmesh
from mathutils import Vector


def boundary_loops(bm, strict=False):
    seen, out = set(), []
    for e in bm.edges:
        if not e.is_boundary or e.verts[0].index in seen: continue
        comp, st = [], [e.verts[0]]
        while st:
            v = st.pop()
            if v.index in seen: continue
            seen.add(v.index); comp.append(v)
            st += [x.other_vert(v) for x in v.link_edges if x.is_boundary]
        if any(sum(x.is_boundary for x in v.link_edges) != 2 for v in comp):
            if not strict: continue   # pinched loops are skipped (listed by `pinches`)
            raise ValueError("pinched boundary at vertex %d" % next(v.index for v in comp if sum(x.is_boundary for x in v.link_edges) != 2))
        order, prev, cur = [comp[0]], None, comp[0]
        while True:
            nx = [x.other_vert(cur) for x in cur.link_edges if x.is_boundary and x.other_vert(cur) is not prev]
            if not nx or nx[0] is comp[0]: break
            prev, cur = cur, nx[0]; order.append(cur)
        out.append(order)
    return out


def pinches(bm):
    """Vertices where a boundary touches itself (more than 2 boundary edges): fix these by hand before filling."""
    return [v.index for v in bm.verts if sum(x.is_boundary for x in v.link_edges) > 2]


def _ring(edge):
    """Edges opposite each other through quads, starting at `edge` (a loop-cut ring); stops at a non-quad or the border."""
    ring, seen = [edge], {edge.index}
    for d in (0, 1):
        e, f = edge, [x for x in edge.link_faces][d] if len(edge.link_faces) > d else None
        while f is not None and len(f.verts) == 4:
            vs = list(f.verts); i = next(k for k in range(4) if {vs[k], vs[(k + 1) % 4]} == set(e.verts))
            opp = next(x for x in f.edges if set(x.verts) == {vs[(i + 2) % 4], vs[(i + 3) % 4]})
            if opp.index in seen: break
            ring.append(opp); seen.add(opp.index); e = opp
            nf = [x for x in opp.link_faces if x is not f]; f = nf[0] if nf else None
    return ring


def loop_cut(bm, edge, ref=None):
    """Loop cut through the quad strip that contains `edge`: one new vertex per ring edge (midpoint, snapped). Returns the new vertices."""
    ring = _ring(edge); before = {v.index for v in bm.verts}
    bmesh.ops.subdivide_edges(bm, edges=ring, cuts=1, use_grid_fill=True)
    new = [v for v in bm.verts if v.index not in before]
    if ref is not None:
        for v in new: v.co = Vector(ref.snap(v.co, None, 0.02))
    return new


def _snap_relax(verts, ref, fixed, iters=12):
    mv = [v for v in verts if v.index not in fixed]
    for _ in range(iters):
        for v in mv:
            ns = [e.other_vert(v).co for e in v.link_edges]
            if ns: v.co = Vector(ref.snap(v.co.lerp(sum(ns, Vector()) / len(ns), 0.5), None, 0.03)) if ref else v.co.lerp(sum(ns, Vector()) / len(ns), 0.5)


def _after_cut(bm, idx):
    """Loop (as vertex objects) that still contains most of the old vertices (by index) after a loop cut."""
    keep = set(idx)
    for L in boundary_loops(bm):
        if len(keep & {v.index for v in L}) >= max(3, len(keep) - 2): return L
    raise ValueError("lost the loop after the cut")


def fill_loop(bm, loop, ref=None, fixed=(), cut_edge=None, relax=12):
    """Fill the boundary `loop` (ordered vertices) with quads. See the module docstring."""
    cut = False
    if len(loop) % 2:
        idx = [v.index for v in loop]; cands = []
        for a, b in zip(loop, loop[1:] + loop[:1]):
            e = bm.edges.get((a, b))
            if e is not None and len(e.link_faces) == 1 and len(e.link_faces[0].verts) == 4: cands.append((len(_ring(e)), e.index))
        if cut_edge is not None: cands = [(0, cut_edge.index)]
        for _, ei in sorted(cands):
            t = bm.copy(); t.edges.ensure_lookup_table()
            try:
                loop_cut(t, t.edges[ei]); ok = len(_after_cut(t, idx)) % 2 == 0
            except ValueError: ok = False
            t.free()
            if ok:
                bm.edges.ensure_lookup_table(); loop_cut(bm, bm.edges[ei], ref); bm.verts.ensure_lookup_table(); loop = _after_cut(bm, idx); cut = True; break
        if not cut: raise ValueError("odd loop (%d): no loop cut gives an even loop" % len(loop))
    best = None
    for k in range(len(loop)):                   # rotate the 4 corners round the loop and try every side split a + b = n / 2
        for na in range(1, len(loop) // 2):
            sc = _score(loop, k, na)
            if best is None or sc < best[0]: best = (sc, k, na)
    _, k, na = best; faces, new = _grid(bm, loop, k, na, ref, fixed, relax)
    return {"faces": [f.index for f in faces], "verts": [v.index for v in new], "cut": cut, "n": len(loop), "corner": k, "a": na, "b": len(loop) // 2 - na}


def _score(loop, k, na):
    """Lower is better: the 4 corners should be where the loop really turns (about 90 deg) and the grid cells should be close to square."""
    n = len(loop); nb = n // 2 - na; cs = [k, k + na, k + na + nb, k + 2 * na + nb]; pen = 0.0
    for c in cs:
        p, a, b = loop[c % n].co, loop[(c - 1) % n].co, loop[(c + 1) % n].co
        u, v = (a - p), (b - p)
        pen += abs(u.angle(v) - 1.5708) if u.length > 0 and v.length > 0 else 3
    sides = [sum((loop[(cs[i] + j) % n].co - loop[(cs[i] + j + 1) % n].co).length for j in range(((cs[(i + 1) % 4] - cs[i]) % n))) for i in range(4)]
    cell = [sides[0] / na, sides[1] / nb, sides[2] / na, sides[3] / nb]
    pen += 2.0 * (max(cell) / max(min(cell), 1e-9) - 1)
    return pen


def _side(loop, start, count, rev=False):
    n = len(loop); return [loop[(start + j) % n] for j in range(count + 1)]


def _grid(bm, loop, k, na, ref, fixed, relax):
    """Quad grid (na x nb) whose border is the loop: corners at k, k+na, k+na+nb, k+2na+nb; interior by a Coons patch, snapped and relaxed."""
    n = len(loop); nb = n // 2 - na
    S0 = _side(loop, k, na); S1 = _side(loop, k + na, nb); S2 = _side(loop, k + na + nb, na); S3 = _side(loop, k + 2 * na + nb, nb)
    S2 = S2[::-1]; S3 = S3[::-1]                       # S0 bottom (u: 0..na), S1 right (v), S2 top (u), S3 left (v)
    G = [[None] * (nb + 1) for _ in range(na + 1)]
    for i in range(na + 1): G[i][0] = S0[i]; G[i][nb] = S2[i]
    for j in range(nb + 1): G[0][j] = S3[j]; G[na][j] = S1[j]
    P00, P10, P01, P11 = S0[0].co, S0[na].co, S2[0].co, S2[na].co
    new = []
    for i in range(1, na):
        for j in range(1, nb):
            u, v = i / na, j / nb
            c = (1 - v) * S0[i].co + v * S2[i].co + (1 - u) * S3[j].co + u * S1[j].co - ((1 - u) * (1 - v) * P00 + u * (1 - v) * P10 + (1 - u) * v * P01 + u * v * P11)
            G[i][j] = bm.verts.new(Vector(ref.snap(c, None, 0.03)) if ref else c); new.append(G[i][j])
    faces = []
    for i in range(na):
        for j in range(nb):
            faces.append(bm.faces.new((G[i][j], G[i + 1][j], G[i + 1][j + 1], G[i][j + 1])))
    # winding: a boundary edge a->b used by an old face must be b->a in the new one
    e0 = bm.edges.get((S0[0], S0[1])); old = [f for f in e0.link_faces if f not in faces][0]; new_f = [f for f in e0.link_faces if f in faces][0]
    def fwd(f, a, b):
        vs = list(f.verts); return any(vs[i] is a and vs[(i + 1) % len(vs)] is b for i in range(len(vs)))
    if fwd(old, S0[0], S0[1]) == fwd(new_f, S0[0], S0[1]):
        for f in faces: f.normal_flip()
    bm.verts.index_update(); bm.edges.index_update(); bm.faces.index_update()
    _snap_relax(new, ref, set(fixed), relax)
    return faces, new

