"""QA: ugly shapes. Normals and contacts can be perfect and a low poly still looks wrong. Per loose part it measures:
  spike    a vertex far from the centre of its neighbours compared with its edge length (a stretched rim point, a pin)
  pointed  a closed tube whose end ring is < 40 % of its middle radius (a needle-pointed end; hair ends are blunt on a low poly)
  thin     a tube whose middle radius is < `thin` (2.2 cm): too thin to read next to its neighbours
  sliver   a face with an angle < 20 or > 165 degrees, or its longest edge > 5x its shortest (reported; judge by share)
Inside Blender (after qa_faces.py and qa_strict.py, which provide the relax step):
  exec(open(ROOT+r"\tools\03-qa\qa_shape.py").read())
  r = qa_shape("LowPoly")     # r["pass"] (no spike / pointed / thin); r["spikes"], r["pointed"], r["thin"], r["slivers"] (polygons)
  heal_spikes("LowPoly")      # relaxes spike vertices until none is left; the caller re-runs the reversed-face gate afterwards"""
import bpy, bmesh, math
import numpy as np


def _parts(bm):
    seen = set(); out = []
    for v0 in bm.verts:
        if v0.index in seen:
            continue
        st, comp = [v0], []; seen.add(v0.index)
        while st:
            v = st.pop(); comp.append(v)
            for e in v.link_edges:
                u = e.other_vert(v)
                if u.index not in seen:
                    seen.add(u.index); st.append(u)
        out.append(comp)
    return out


def _layers(comp, src):
    """Graph layers (BFS) of a part from a vertex."""
    dist = {src.index: 0}; order = [[src]]; frontier = [src]
    while frontier:
        nxt = []
        for v in frontier:
            for e in v.link_edges:
                u = e.other_vert(v)
                if u.index not in dist:
                    dist[u.index] = dist[v.index] + 1; nxt.append(u)
        if nxt:
            order.append(nxt)
        frontier = nxt
    return order


def _axis_dist(v, a, b):
    """Distance from vertex v to the segment a-b (the tube axis between two layer centres)."""
    ab = b - a; s = max(0.0, min(1.0, (v.co - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (v.co - (a + ab * s)).length


def _tube_ends(comp):
    """[(end vertex, radius near that end, median radius, its 2 end layers: cap + first ring)]. The tube is walked as graph layers from one end to the other (BFS from a
    far vertex); a layer's radius is the median distance of its vertices to the axis through the neighbouring layer centres. The end
    radius is the smallest of the first two layers from that end, the middle one the median over the middle half."""
    far = _layers(comp, comp[0])[-1][0]; la = _layers(comp, far)
    if len(la) < 7:
        return []
    C = [sum((v.co for v in l), l[0].co * 0) / len(l) for l in la]
    rad = [None] + [sorted(_axis_dist(v, C[i - 1], C[i + 1]) for v in la[i])[len(la[i]) // 2] for i in range(1, len(la) - 1)]
    med = lambda xs: sorted(xs)[len(xs) // 2]
    r_mid = med(rad[len(la) // 4: 3 * len(la) // 4])
    return [(la[0][0], min(rad[1:3]), r_mid, la[:2]), (la[-1][0], min(rad[-3:-1]), r_mid, la[-1:-3:-1])]


def _is_tube(P):
    """P = world positions (n,3) of a loose part: True when it is long and narrow (width < 15 cm), the hood is wide."""
    w, vec = np.linalg.eigh(np.cov(P.T)); return float(np.ptp(P @ vec[:, 1])) < 0.15


def _spike(v):
    nb = [e.other_vert(v) for e in v.link_edges]
    if len(nb) < 3 or len(v.link_faces) >= 6:
        return 0.0
    c = sum((u.co for u in nb), v.co * 0) / len(nb); el = sum((u.co - v.co).length for u in nb) / len(nb)
    return (v.co - c).length / max(el, 1e-9)


def qa_shape(name, spike=0.8, ang=(20, 165), aspect=5.0, thin=0.022, pointed=0.4):
    ob = bpy.data.objects[name]; bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    M = ob.matrix_world; spikes, slivers, pts, thins, info = [], [], [], [], []
    for k, comp in enumerate(_parts(bm)):
        P = np.array([(M @ v.co)[:] for v in comp]); w, vec = np.linalg.eigh(np.cov(P.T)); ext = [float(np.ptp(P @ vec[:, i])) for i in (2, 1, 0)]
        info.append({"part": k, "verts": len(comp), "length": round(ext[0], 3), "width": round(ext[1], 3)})
        if ext[1] < 0.15:                                                    # a tube (the shell is wide)
            ends = _tube_ends(comp)
            if ends and ends[0][2] < thin:
                thins.append({"part": k, "mid_radius_cm": round(ends[0][2] * 100, 1), "at": [round(x, 3) for x in P.mean(0)]})
            for end, r_end, r_mid, _ in ends:
                if r_end < pointed * r_mid:
                    pts.append({"part": k, "end_radius_cm": round(r_end * 100, 1), "mid_radius_cm": round(r_mid * 100, 1),
                                "at": [round(x, 3) for x in (M @ end.co)]})
        for v in comp:
            s = _spike(v)
            if s > spike:
                spikes.append({"vert": v.index, "ratio": round(s, 2), "at": [round(x, 3) for x in (M @ v.co)]})
    for f in bm.faces:
        vs = [l.vert.co for l in f.loops]; n = len(vs)
        a = [math.degrees((vs[i - 1] - vs[i]).angle(vs[(i + 1) % n] - vs[i])) if (vs[i - 1] - vs[i]).length and (vs[(i + 1) % n] - vs[i]).length else 0 for i in range(n)]
        el = [(vs[i] - vs[(i + 1) % n]).length for i in range(n)]
        if min(a) < ang[0] or max(a) > ang[1] or max(el) > aspect * max(min(el), 1e-9):
            slivers.append(f.index)
    n_faces = len(bm.faces); bm.free()
    return {"pass": not (spikes or pts or thins), "spikes": spikes, "pointed": pts, "thin": thins, "slivers": slivers,
            "sliver_share": round(len(slivers) / max(n_faces, 1), 3), "parts": info}


def heal_spikes(name, rounds=30, spike=0.8):
    """Relax every spike vertex (and its ring) toward its neighbours until none is left."""
    for r in range(rounds):
        ob = bpy.data.objects[name]; bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
        bad = [v for v in bm.verts if _spike(v) > spike]
        if not bad:
            bm.free(); return {"rounds": r, "spikes": 0}
        for v in bad:
            nb = [e.other_vert(v) for e in v.link_edges]; v.co = v.co.lerp(sum((u.co for u in nb), v.co * 0) / len(nb), 0.6)
        bm.to_mesh(ob.data); ob.data.update(); bm.free()
    return {"rounds": rounds, "spikes": "left"}
