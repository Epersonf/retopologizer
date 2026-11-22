r"""Local hill-climbing repair of faces that are wrong by themselves (twisted quad, face looking into the ref, stamped pair, crossing).
The Laplacian `untangle` relaxes whole neighbourhoods and often trades one bad face for another; this one moves ONE vertex at a time, tries random
steps projected back on the ref, and keeps a step only when the penalty of the faces around the vertex (and the crossings) goes down.
Topology never changes, `fixed` never moves, nobody leaves a `radius` ball around the starting position.
Inside Blender (face_intersect.py and face_shape.py exec'd first):
  V2, rep = polish(V, F, ref, fixed=range(120), radius=0.01)       # rep: {"before": penalty, "after": penalty, "bad_faces": [...]}"""
import random
from mathutils import Vector


def _quad_pen(P, f, ref, thr_t=0.2, thr_n=0.2):
    p = [P[i] for i in f]; pen = 0.0
    if len(f) == 4:
        n1 = (p[1] - p[0]).cross(p[2] - p[0]).normalized(); n2 = (p[2] - p[0]).cross(p[3] - p[0]).normalized()
        n3 = (p[2] - p[1]).cross(p[3] - p[1]).normalized(); n4 = (p[3] - p[1]).cross(p[0] - p[1]).normalized()
        pen += max(0.0, thr_t - min(n1.dot(n2), n3.dot(n4)))
    n = sum((p[i].cross(p[(i + 1) % len(p)]) for i in range(len(p))), Vector())
    if n.length > 1e-15 and ref is not None:
        c = sum(p, Vector()) / len(p); h = ref.nearest(c, 0.03)
        if h: pen += max(0.0, thr_n - n.normalized().dot(h[1]))
    return pen


def polish(V, F, ref, fixed=(), radius=0.01, sweeps=40, seed=1, min_edge=0.0012):
    rnd = random.Random(seed); P = [Vector(v) for v in V]; P0 = list(P); fx = set(fixed)
    inc = [[] for _ in P]; nb = [set() for _ in P]
    for fi, f in enumerate(F):
        for i, a in enumerate(f): inc[a].append(fi); nb[a].add(f[(i + 1) % len(f)]); nb[f[(i + 1) % len(f)]].add(a)
    pen = lambda fs: sum(_quad_pen(P, F[fi], ref) for fi in fs)
    inter, shape = globals().get("face_intersections"), globals().get("stamped_pairs")

    def hot():  # faces ruins: pela propria forma, cruzando ou estampadas
        hs = {fi for fi in range(len(F)) if not all(v in fx for v in F[fi]) and _quad_pen(P, F[fi], ref) > 0}
        if inter: hs |= {x for p in inter(P, F) for x in p[:2]}
        if shape: hs |= {x for p in shape(P, F) for x in p[:2]}
        return hs
    total0 = pen(range(len(F))) + len(hot()); H = hot(); k = 0
    while H and k < sweeps:
        k += 1; sigma = 0.004 * (1 - k / (sweeps + 1)) + 0.0008
        vs = {v for fi in H for v in F[fi]}; vs |= {w for v in list(vs) for w in nb[v]}
        for v in sorted(vs):
            if v in fx: continue
            cur = pen(inc[v]); best = (cur, None)
            for _ in range(14):
                q = P[v] + Vector((rnd.gauss(0, sigma), rnd.gauss(0, sigma), rnd.gauss(0, sigma)))
                q = Vector(ref.snap(q, None, 0.02)) if ref else q
                if (q - P0[v]).length > radius or any((q - P[w]).length < min_edge for w in nb[v]): continue
                old = P[v]; P[v] = q; c = pen(inc[v]); P[v] = old
                if c < best[0] - 1e-9: best = (c, q)
            if best[1] is not None: P[v] = best[1]
        H = hot()
    return [tuple(p) for p in P], {"before": round(total0, 3), "after": len(H), "sweeps": k, "bad_faces": sorted(H)}
