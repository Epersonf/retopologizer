"""Centreline and size of every lock piece of the reference (worker; needs hair_pieces.py, which writes draft/hair_vert_piece.npy and hair_pieces.npz). The
piece is a surface: geodesic (Dijkstra) distance from one end of it, the farthest vertex from an arbitrary one and then the farthest from that (the
two-sweep diameter), cut into rings of RING metres; the centroid of a ring is a point of the centreline and the spread of its vertices in the plane
across the lock is its half width a (major axis u) and half thickness b. Same idea as skeletor's by_wavefront, with no dependency.
Writes draft/hair_piece_axes.json: [{rank, vis, nv, length, pts [[x,y,z]..] from end A to end B, a [..], b [..], u [[x,y,z]..]}] for the N most visible pieces.
N and RING may be set before running.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_piece_axes.py"""
import bpy, heapq, json, time
import numpy as np
G = globals(); N = G.get("N", 150); RING = G.get("RING", 0.015); HD = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft"
t0 = time.time(); ob = bpy.data.objects["HairFull"]; me = ob.data; Wm = np.array(ob.matrix_world)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3).astype(np.float64) @ Wm[:3, :3].T + Wm[:3, 3]
e = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", e); e = e.reshape(-1, 2)
vp = np.load(HD + r"\hair_vert_piece.npy"); Z = np.load(HD + r"\hair_pieces.npz"); vis, nvs = Z["vis"], Z["nv"]
ek = vp[e[:, 0]]; o = np.argsort(ek, kind="stable"); e, ek = e[o], ek[o]; vs = np.argsort(vp, kind="stable"); vps = vp[vs]


def dijkstra(adj, s):
    d = [1e9] * len(adj); d[s] = 0.0; q = [(0.0, s)]
    while q:
        du, u = heapq.heappop(q)
        if du > d[u]:
            continue
        for v, w in adj[u]:
            nd = du + w
            if nd < d[v]:
                d[v] = nd; heapq.heappush(q, (nd, v))
    return np.array(d)


def spread(q, u):                                                                          # robust full extent of q along u (2.5 .. 97.5 percentile)
    p = q @ u; return float(np.percentile(p, 97.5) - np.percentile(p, 2.5))


def axis(k):
    idx = vs[np.searchsorted(vps, k, "left"):np.searchsorted(vps, k, "right")]; ed = e[np.searchsorted(ek, k, "left"):np.searchsorted(ek, k, "right")]
    loc = {int(g): i for i, g in enumerate(idx)}; P = co[idx]; adj = [[] for _ in idx]
    for a, b in ed.tolist():
        i, j = loc[a], loc[b]; w = float(np.linalg.norm(P[i] - P[j])); adj[i].append((j, w)); adj[j].append((i, w))
    d0 = dijkstra(adj, 0); A = int(np.argmax(np.where(d0 < 1e8, d0, -1))); dA = dijkstra(adj, A); ok = dA < 1e8; L = float(dA[ok].max())
    nr = max(2, int(round(L / RING))); ri = np.minimum((np.where(ok, dA, 0) / (L / nr)).astype(int), nr - 1)
    c = np.array([P[ok & (ri == i)].mean(0) if (ok & (ri == i)).any() else np.full(3, np.nan) for i in range(nr)])
    good = np.isfinite(c[:, 0]); c = np.column_stack([np.interp(np.arange(nr), np.nonzero(good)[0], c[good, j]) for j in range(3)])
    for _ in range(2):                                                                     # smooth the centreline, the ends stay
        c[1:-1] = (c[:-2] + 2 * c[1:-1] + c[2:]) / 4
    t = np.gradient(c, axis=0); t /= np.linalg.norm(t, axis=1)[:, None] + 1e-12
    a, b, uu = np.zeros(nr), np.zeros(nr), np.zeros((nr, 3))
    for i in range(nr):
        q = P[ok & (ri == i)] - c[i]; q = q - np.outer(q @ t[i], t[i])
        if len(q) < 6:
            a[i] = b[i] = 0.005; uu[i] = np.cross(t[i], [0, 0, 1.0]); continue
        w, v = np.linalg.eigh(np.cov(q.T)); u = v[:, 2] - (v[:, 2] @ t[i]) * t[i]; u /= np.linalg.norm(u) + 1e-12; n = np.cross(t[i], u)
        a[i], b[i] = spread(q, u) / 2, spread(q, n) / 2; uu[i] = u if i == 0 or u @ uu[i - 1] >= 0 else -u
    return {"rank": int(k), "vis": int(vis[k]), "nv": int(nvs[k]), "length": round(float(np.linalg.norm(np.diff(c, axis=0), axis=1).sum()), 4), "pts": c.round(5).tolist(),
            "a": a.round(4).tolist(), "b": b.round(4).tolist(), "u": uu.round(4).tolist()}


out = [axis(k) for k in range(min(N, len(vis)))]
open(HD + r"\hair_piece_axes.json", "w").write(json.dumps(out))
q = lambda v: np.percentile(v, [10, 50, 90]).round(3).tolist()
result = {"pieces": len(out), "seconds": round(time.time() - t0, 1), "length": q([p["length"] for p in out]), "half_width": q([np.median(p["a"]) for p in out]), "half_thick": q([np.median(p["b"]) for p in out])}
