"""The reference is not one skin: HairFull is ~700 separate lock pieces (connected components, ~11 cm long, 5 x 2 cm across) laid over each other. This
is the artist's lock list, for free. Worker script ("HairFull" loaded): labels every piece, and for the height field of hair_radial.py (same rays) keeps
WHICH piece is the first hit, so the unrolled map becomes a map of locks. Writes draft/hair_pieces.npz: L[NT, NZ] (piece rank, 0 = the biggest by
visible cells; -1 = nothing), vis[n] (visible cells per piece), nv[n] (vertices), and draft/hair_vert_piece.npy (the rank of every vertex of HairFull,
-1 for the pieces too small to count). hair_locks_auto.py makes the Bezier curves of the best ones.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_pieces.py"""
import bpy, math, os
import numpy as np
from mathutils import Vector
G = globals(); NT = G.get("NT", 360); DZ = G.get("DZ", 0.005); ZS = np.arange(0.01, 0.60, DZ); A = Vector((-0.185, -0.03, 0.0)); HD = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft"
exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\03-qa\qa_fit.py").read())                        # _world_tree
ob = bpy.data.objects["HairFull"]; me = ob.data; nv = len(me.vertices)
e = np.empty(len(me.edges) * 2, dtype=np.int32); me.edges.foreach_get("vertices", e); e = e.reshape(-1, 2)
par = list(range(nv))                                                                      # union-find over the edges: the connected pieces
def find(a):
    while par[a] != a:
        par[a] = par[par[a]]; a = par[a]
    return a
for a, b in e.tolist():
    ra, rb = find(a), find(b)
    if ra != rb:
        par[ra] = rb
root = np.array([find(i) for i in range(nv)]); u, inv, cnt = np.unique(root, return_inverse=True, return_counts=True)
pv = np.array([p.vertices[0] for p in me.polygons], dtype=np.int64)                        # a polygon belongs to the piece of its first vertex
tree, _, tri2poly = _world_tree(ob)
fill = {i for i, m in enumerate(me.materials) if m and m.name == "headfill"}; ign = {p.index for p in me.polygons if p.material_index in fill}
hit = np.full((NT, len(ZS)), -1, dtype=np.int64)                                           # the component id of the first hit, -1 = nothing
for i in range(NT):
    t = 2 * math.pi * i / NT; d = Vector((math.sin(t), math.cos(t), 0))
    for j, z in enumerate(ZS):
        h = tree.ray_cast(A + Vector((0, 0, z)) + d * 0.7, -d, 0.7)
        if h[0] is not None and tri2poly[h[2]] not in ign:
            hit[i, j] = inv[pv[tri2poly[h[2]]]]
vis = np.bincount(hit[hit >= 0], minlength=len(u)); rank = np.argsort(-vis, kind="stable"); n_vis = int((vis > 0).sum())
newid = np.full(len(u), -1, dtype=np.int64); newid[rank[:n_vis]] = np.arange(n_vis)                  # rank 0 = the most visible piece
L = np.where(hit >= 0, newid[np.maximum(hit, 0)], -1).astype(np.int32)
np.save(HD + r"\hair_vert_piece.npy", newid[inv].astype(np.int32))
np.savez(HD + r"\hair_pieces.npz", L=L, vis=vis[rank[:n_vis]], nv=cnt[rank[:n_vis]], zs=ZS)
cum = np.cumsum(vis[rank[:n_vis]]) / max(vis.sum(), 1)
result = {"pieces": int(len(u)), "visible": n_vis, "cells": int(vis.sum()), "cover": {k: int(np.searchsorted(cum, k / 100) + 1) for k in (50, 70, 80, 90, 95)}}
