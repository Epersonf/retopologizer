"""Geodesic distance over the mesh edges and its persistent maxima: the tips of the body (head, hands, feet, a tail)
or of a hand (one per digit). A peak counts when it stands `min_pers` above the saddle where it joins a higher one."""
import heapq
import numpy as np


def dijkstra(M, sources, allowed=None):
    """Distance along edges from the source vertices; np.inf where unreachable (or outside `allowed`, a bool mask)."""
    D = np.full(len(M.V), np.inf); h = []
    for s in sources:
        D[s] = 0.0; h.append((0.0, int(s)))
    heapq.heapify(h)
    while h:
        d, v = heapq.heappop(h)
        if d > D[v]:
            continue
        for w in M.nbr[v]:
            if allowed is not None and not allowed[w]:
                continue
            nd = d + float(np.linalg.norm(M.V[v] - M.V[w]))
            if nd < D[w]:
                D[w] = nd; heapq.heappush(h, (nd, w))
    return D


def peaks(M, D, min_pers):
    """[(vertex, persistence)] of the local maxima of D, highest first (the global one has persistence inf)."""
    order = [int(i) for i in np.argsort(-D) if np.isfinite(D[i])]
    parent, top, done = {}, {}, set()

    def root(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]; v = parent[v]
        return v
    pers = {}
    for v in order:
        roots = {root(w) for w in M.nbr[v] if w in done}
        parent[v] = v; done.add(v)
        if not roots:
            top[v] = v; continue
        best = max(roots, key=lambda r: D[top[r]])
        for r in roots:
            if r != best:
                pers[top[r]] = D[top[r]] - D[v]
            parent[r] = best
        parent[v] = best
    for v in order:
        if parent.get(v) == v and top.get(v) is not None:
            pers.setdefault(top[v], np.inf)
    out = [(v, p) for v, p in pers.items() if p >= min_pers]
    return sorted(out, key=lambda t: -D[t[0]])
