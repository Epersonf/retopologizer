r"""Merge by distance on plain lists (the step the artist forgot in rec_02: 5 stacked clusters, 22 border edges instead of 14).
  V2, F2, rep = merge_doubles(V, F, dist=0.0006)      # rep: {"merged": n_vertices_removed, "faces_dropped": n, "tris_made": n}
Vertices closer than `dist` collapse onto the first one; faces that lose a vertex become triangles (a collapsed claw tip is a pole of triangles),
faces left with < 3 distinct vertices are dropped. Winding and order of the survivors are kept."""


def merge_doubles(V, F, dist=0.0006):
    n = len(V); rep = list(range(n)); cell = {}
    key = lambda p: tuple(int(c // dist) for c in p)
    for i, p in enumerate(V):
        k = key(p); hit = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in cell.get((k[0] + dx, k[1] + dy, k[2] + dz), ()):
                        if sum((a - b) ** 2 for a, b in zip(V[i], V[j])) < dist * dist: hit = rep[j] if hit is None else min(hit, rep[j])
        if hit is not None: rep[i] = hit
        else: cell.setdefault(k, []).append(i)
    keep = [i for i in range(n) if rep[i] == i]; new = {v: k for k, v in enumerate(keep)}
    F2 = []; dropped = 0; tris = 0
    for f in F:
        g = []
        for i in f:
            r = new[rep[i]]
            if not g or g[-1] != r: g.append(r)
        if len(g) > 1 and g[0] == g[-1]: g.pop()
        if len(set(g)) < 3: dropped += 1; continue
        tris += len(f) == 4 and len(g) == 3; F2.append(g)
    return [V[i] for i in keep], F2, {"merged": n - len(keep), "faces_dropped": dropped, "tris_made": tris}
