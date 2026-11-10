"""QA: no backface may be visible from outside. Multi-view ray test (orthographic grids
from N directions on a sphere, interior of open cavities included). A face whose BACK side is
the first thing a ray hits is an exposed backface (what Blender's Face Orientation shows red).
Inside Blender: exec(open(...).read())
  r = qa_faces(["chest_base","chest_lid"])            # report, r["pass"] is True/False
  fix_flipped(["chest_base","chest_lid"])             # flips faces seen only from the back
"""
import bpy, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _sphere_dirs(n):
    g = math.pi * (3 - math.sqrt(5))
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        out.append(Vector((math.cos(g * i) * r, math.sin(g * i) * r, z)))
    return out


def _tree(o):
    """World-space BVH from our own triangulation; returns (tree, tri->polygon index)."""
    me = o.data; me.calc_loop_triangles()
    M = o.matrix_world
    verts = [M @ v.co for v in me.vertices]
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    return BVHTree.FromPolygons(verts, tris, epsilon=0.0), [t.polygon_index for t in me.loop_triangles], M.to_3x3()


def _votes(names, n_dirs=64, res=80, graze=0.1):
    bpy.context.view_layer.update()
    objs = [bpy.data.objects[n] for n in names]
    trees = [(o.name,) + _tree(o) for o in objs]
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    ctr, rad = (lo + hi) / 2, (hi - lo).length / 2
    front = {n: {} for n in names}; back = {n: {} for n in names}
    for d in _sphere_dirs(n_dirs):
        a = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized()
        b = d.cross(a)
        for i in range(res):
            for j in range(res):
                u = (i / (res - 1) * 2 - 1) * rad; v = (j / (res - 1) * 2 - 1) * rad
                org = ctr + a * u + b * v - d * rad * 1.2
                best = None
                for name, t, tri2poly, _ in trees:
                    loc, nor, idx, dist = t.ray_cast(org, d)
                    if loc is not None and (best is None or dist < best[0]):
                        best = (dist, name, tri2poly[idx], nor.dot(d))
                if best and abs(best[3]) > graze:   # ignore near edge-on hits
                    tgt = front if best[3] < 0 else back
                    tgt[best[1]][best[2]] = tgt[best[1]].get(best[2], 0) + 1
    return front, back


def qa_faces(names, n_dirs=64, res=80, tol=0, graze=0.1):
    front, back = _votes(names, n_dirs, res, graze)
    bad = {n: sorted(i for i, c in back[n].items() if c > tol) for n in names}
    nbad = sum(len(v) for v in bad.values())
    return {"pass": nbad == 0, "exposed_backface_faces": nbad,
            "per_object": {n: len(v) for n, v in bad.items()},
            "faces": {n: v[:40] for n, v in bad.items()},
            "back_votes": {n: sum(back[n].values()) for n in names},
            "front_votes": {n: sum(front[n].values()) for n in names}}


def fix_flipped(names, n_dirs=64, res=80, graze=0.1):
    """Flip faces whose back side is seen more than their front side."""
    front, back = _votes(names, n_dirs, res, graze)
    flipped = {}
    for n in names:
        me = bpy.data.objects[n].data
        bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        fl = [bm.faces[i] for i, c in back[n].items() if c > front[n].get(i, 0)]
        for f in fl:
            f.normal_flip()
        bm.to_mesh(me); bm.free(); me.update()
        flipped[n] = len(fl)
    return flipped
