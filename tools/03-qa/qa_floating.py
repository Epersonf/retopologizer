"""QA: nothing floats. Splits the given objects into loose parts, joins parts that touch (triangles intersect, or the closest
points are within `tol` metres) and reports the connected groups. A group that is not the biggest one is FLOATING, unless the
original model really has that many separate pieces (`expected` = number of groups it should have; default 1).
Run it every time one object is split into several meshes, or when parts are built separately and put together.
Inside Blender: exec(open(ROOT+r"\tools\03-qa\qa_floating.py").read())
  r = qa_floating(["LowPoly"])               # or several names; r["pass"], r["groups"], r["floating"]
r["floating"] = [{"part": i, "object": name, "verts": n, "gap_mm": distance to the nearest other group, "end": vertex of this
group nearest to it, "to": the point of the other group it should reach}]."""
import bpy, bmesh
from mathutils.bvhtree import BVHTree


def _loose_parts(o):
    """[(object name, world verts, tris)] per loose part of the object."""
    bm = bmesh.new(); bm.from_mesh(o.data); M = o.matrix_world; seen = set(); out = []
    for v0 in bm.verts:
        if v0.index in seen:
            continue
        stack, comp = [v0], []; seen.add(v0.index)
        while stack:
            v = stack.pop(); comp.append(v)
            for e in v.link_edges:
                u = e.other_vert(v)
                if u.index not in seen:
                    seen.add(u.index); stack.append(u)
        idx = {v.index: k for k, v in enumerate(comp)}
        faces = {f for v in comp for f in v.link_faces}
        tris = [(idx[f.loops[0].vert.index], idx[f.loops[i].vert.index], idx[f.loops[i + 1].vert.index])
                for f in faces for i in range(1, len(f.loops) - 1)]
        out.append((o.name, [M @ v.co for v in comp], tris))
    bm.free()
    return out


def qa_floating(names, tol=0.003, expected=1):
    parts = [p for n in names for p in _loose_parts(bpy.data.objects[n])]
    trees = [BVHTree.FromPolygons(V, T, epsilon=0.0) for _, V, T in parts]
    n = len(parts); par = list(range(n)); gap = {}

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for i in range(n):
        for j in range(i + 1, n):
            if trees[i].overlap(trees[j]):
                par[find(i)] = find(j); continue
            for a_, b_ in ((i, j), (j, i)):
                best = (1e9, None, None)
                for v in parts[a_][1]:
                    h = trees[b_].find_nearest(v)
                    if h[0] is not None and h[3] < best[0]:
                        best = (h[3], v, h[0])
                gap[(a_, b_)] = best
            if min(gap[(i, j)][0], gap[(j, i)][0]) <= tol:
                par[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    order = sorted(groups.values(), key=lambda g: -sum(len(parts[i][1]) for i in g))
    floating = []
    for g in order[expected:]:
        others = [i for i in range(n) if i not in g]
        d, end, to = min((gap.get((i, j), (1e9, None, None)) for i in g for j in others), key=lambda x: x[0])
        floating.append({"part": g[0], "object": parts[g[0]][0], "parts": g, "verts": sum(len(parts[i][1]) for i in g), "gap_mm": round(d * 1000, 1),
                         "end": tuple(round(c, 4) for c in end) if end else None,
                         "to": tuple(round(c, 4) for c in to) if to else None})
    return {"pass": not floating, "parts": n, "groups": len(order), "floating": floating}
