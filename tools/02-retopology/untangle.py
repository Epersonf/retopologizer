r"""Removes faces that cut through each other (and edges shorter than min_edge = collapsed tips) by moving ONLY the vertices of the offending faces (and their neighbours): relax toward
the neighbour average, project back on the ref, re-test; the radius grows if it does not clear. Topology never changes, `fixed` never moves.
Inside Blender, after transplant.py / conform, or whenever qa_intersect fails:
  exec(open(r"<repo>\tools\general\face_intersect.py", encoding="utf-8").read())
  V2, rep = untangle(V, F, ref, fixed=range(120))     # rep: {"before": n_pairs, "after": n_pairs, "rounds": k, "moved": n_vertices}
If `after` is not 0 the part must be rebuilt (or fixed by hand): it is never delivered with intersecting faces."""
from mathutils import Vector


def untangle(V, F, ref, fixed=(), rounds=60, lam=0.5, maxd=0.02, min_edge=0.0008, max_move=None):
    test = globals()["face_intersections"]
    P = [Vector(v) for v in V]; P0 = list(P); fx = set(fixed); nb = [set() for _ in P]
    for f in F:
        for i, a in enumerate(f): nb[a].add(f[(i + 1) % len(f)]); nb[f[(i + 1) % len(f)]].add(a)

    def bad(P):
        pr = test(P, F); return pr, {v for a, b in pr for f in (a, b) for v in F[f]}
    edges = {tuple(sorted((a, f[(i + 1) % len(f)]))) for f in F for i, a in enumerate(f)}

    def spread(P):  # aresta menor que min_edge (vertices quase coincidentes) vira degenerada: afasta os dois
        for a, b in edges:
            d = P[b] - P[a]
            if d.length >= min_edge: continue
            u = d.normalized() if d.length > 1e-9 else (sum((P[j] for j in nb[a]), Vector()) / len(nb[a]) - P[a]).normalized()
            push = (min_edge - d.length) / 2
            if a not in fx: P[a] = Vector(ref.snap(P[a] - u * push, None, maxd)) if ref else P[a] - u * push
            if b not in fx: P[b] = Vector(ref.snap(P[b] + u * push, None, maxd)) if ref else P[b] + u * push
        return P
    P = spread(P); pairs, vs = bad(P); before = len(pairs); moved = set(); k = 0
    while pairs and k < rounds:
        k += 1; ring = set(vs)
        for _ in range(1 + k // 8): ring |= {w for v in ring for w in nb[v]}   # o raio cresce se nao resolver
        Q = list(P)
        for i in ring:
            if i in fx: continue
            avg = sum((P[j] for j in nb[i]), Vector()) / len(nb[i]); t = P[i].lerp(avg, lam)
            Q[i] = Vector(ref.snap(t, None, maxd)) if ref else t; moved.add(i)
        if max_move: Q = [p0 + (q - p0).normalized() * max_move if (q - p0).length > max_move else q for p0, q in zip(P0, Q)]
        P = spread(Q); pairs, vs = bad(P)
    return [tuple(p) for p in P], {"before": before, "after": len(pairs), "rounds": k, "moved": len(moved)}
