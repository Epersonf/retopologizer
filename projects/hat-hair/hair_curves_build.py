"""Blender side of the hair locks (worker; needs the base Hair_hood from hair_base.py and draft/hair_curves.json from hair_curves.py or hair_pick.py). For every
lock: a Bezier curve object Hair_curve_NN (kept in the file: select a point, Alt+S changes its radius, G moves it, Ctrl+T its tilt) and the mesh made from it,
Hair_tube_NN. The conversion is Blender's own: a lock with `ratio` (a flat ribbon, half thickness / half width) gets a bevel OBJECT, a cyclic polygon of `sides`
points (half width 1, half thickness ratio; a point's radius = the half width in metres), turned about the curve by the tilt of every point so that its wide axis
follows `u` (measured: one evaluation with tilt 0 gives Blender's own frame); without ratio, Bevel round with depth 1 m (a point's radius in metres). Quad rings
only at RES_U per span, no fill caps (n-gons); both ends are closed by quad fans (the tip 0.25 r beyond its ring). Every root is BURIED: the end of the lock
nearer to a parent (the base or a lock already built) is the root; its control point moves toward the head centre until its ring lies inside the parent,
a root farther than DMAX from every parent waits for the next pass and is dropped when nothing is left to hold it.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_curves_build.py"""
import bpy, bmesh, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
G = globals(); P = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft"; ROOTK = G.get("ROOTK", 1.0); RES_U = G.get("RES_U", 2); DMAX = G.get("DMAX", 0.06)
C = Vector((-0.185, -0.03, 0.30))
for o in list(bpy.data.objects) + list(bpy.data.curves):
    if o.name.startswith(("Hair_curve_", "Hair_tube_", "Hair_prof_")):
        (bpy.data.objects if isinstance(o, bpy.types.Object) else bpy.data.curves).remove(o)
trees = []; profs = {}
mat = bpy.data.materials.get("hair") or bpy.data.materials.new("hair")


DIRS = [Vector(d).normalized() for d in ((1, 0.37, 0.21), (-0.3, 1, 0.45), (0.2, -0.5, 1))]


def inside(tree, q):                                                     # majority of three ray parities (the face normal at the nearest point is no sign for thin ribbons: their edges are sharp)
    votes = 0
    for d in DIRS:
        n = 0; o = q + d * 1e-5
        for _ in range(40):
            h = tree.ray_cast(o, d)
            if h[0] is None:
                break
            n += 1; o = h[0] + d * 1e-5
        votes += n % 2
    return votes >= 2


def depth(q):                                                            # metres inside the best parent (negative: outside all of them, minus the distance to the nearest)
    best = -1e9
    for t, lo, hi in trees:
        if all(lo[i] <= q[i] <= hi[i] for i in range(3)) and inside(t, q):
            loc, n, i, d = t.find_nearest(q); best = max(best, d if loc is not None else 0.0)
        else:
            loc, n, i, d = t.find_nearest(q, 0.3)
            if loc is not None:
                best = max(best, -d)
    return best if best > -1e8 else -1.0


def add_tree(ob):                                                        # a parent: its BVH and its bounding box
    bpy.context.view_layer.update(); V = np.array([ob.matrix_world @ v.co for v in ob.data.vertices]); trees.append((BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get()), V.min(0), V.max(0)))


def ring(c, t, u, a, b, S):                                              # the ring of the profile polygon at a point (vertex 0 on the wide axis)
    u = (u - t * u.dot(t)).normalized(); n = t.cross(u)
    return [c + u * a * math.cos(2 * math.pi * j / S) + n * b * math.sin(2 * math.pi * j / S) for j in range(S)]


def bury(pts, rad, us, ratio, S):                                        # the root point goes toward the head centre until its ring lies inside a parent
    q = Vector(pts[0]); t = (q - Vector(pts[1])).normalized(); u = Vector(us[0]); a = rad[0]; b = a * (ratio or 1.0); n = 0
    good = lambda q: depth(q) >= ROOTK * b and sum(depth(x) < 0 for x in ring(q, t, u, a, b, S)) <= S // 4
    while not good(q) and n < 40:
        q = q + (C - q).normalized() * 0.005; n += 1
    return [list(q)] + pts[1:], n


def profile(S, ratio):                                                   # a cyclic polygon curve as the bevel object
    key = (S, round(ratio, 3))
    if key not in profs:
        pc = bpy.data.curves.new("Hair_prof_%d_%03d" % (S, round(ratio * 100)), 'CURVE'); pc.dimensions = '2D'; sp = pc.splines.new('POLY'); sp.points.add(S - 1); sp.use_cyclic_u = True
        for i, p in enumerate(sp.points):
            p.co = (math.cos(2 * math.pi * i / S), ratio * math.sin(2 * math.pi * i / S), 0, 1)
        po = bpy.data.objects.new(pc.name, pc); bpy.context.scene.collection.objects.link(po); po.hide_render = True; profs[key] = po
    return profs[key]


def evaluate(ob, S):                                                     # the rings of the converted curve: centres, wide axes (unit, sign free) and plane normals
    bpy.context.view_layer.update(); me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    V = np.array([v.co[:] for v in me.vertices]).reshape(-1, S, 3); bpy.data.meshes.remove(me); c = V.mean(1); E = [np.linalg.eigh((R - m).T @ (R - m))[1] for R, m in zip(V, c)]
    return c, np.array([e[:, 2] for e in E]), np.array([e[:, 0] for e in E])


def wanted(c, ax, nr, j, u):                                             # the ring plane normal along the travel, the baseline axis and the wanted one, both in the ring plane
    t = nr[j] * (1 if nr[j] @ (c[min(j + 1, len(c) - 1)] - c[max(j - 1, 0)]) >= 0 else -1); f = lambda v: (v - t * (v @ t)) / (np.linalg.norm(v - t * (v @ t)) + 1e-12)
    return t, f(ax[j]), f(np.array(u))


def make_curve(name, pts, rad, sides, ratio=None, us=None):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.resolution_u = RES_U; cu.use_fill_caps = False
    if ratio:
        cu.bevel_mode = 'OBJECT'; cu.bevel_object = profile(sides, ratio); cu.twist_mode = 'MINIMUM'
    else:
        cu.bevel_mode = 'ROUND'; cu.bevel_resolution = (sides - 4) // 2
    cu.bevel_depth = 1.0; sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for bp, p, r in zip(sp.bezier_points, pts, rad):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'; bp.radius = r
    ob = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(ob); ob.hide_render = True; err = 0.0
    if ratio:                                                            # tilt of every point: from Blender's own frame (tilt 0) to the wanted wide axis (the ellipse repeats every 180 deg)
        c, ax, nr = evaluate(ob, sides); prev = 0.0
        for i, bp in enumerate(sp.bezier_points):
            t, b0, d = wanted(c, ax, nr, i * RES_U, us[i]); phi = math.atan2(np.cross(b0, d) @ t, b0 @ d); tilt = (phi + math.pi / 2) % math.pi - math.pi / 2
            tilt += math.pi * round((prev - tilt) / math.pi); bp.tilt = prev = tilt
        c, ax, nr = evaluate(ob, sides)
        for i in range(len(pts)):
            t, b0, d = wanted(c, ax, nr, i * RES_U, us[i]); err = max(err, math.degrees(math.acos(min(1.0, abs(b0 @ d)))))
    return ob, err


def tube_mesh(curve_ob, name, sides):
    me = bpy.data.meshes.new_from_object(curve_ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me); vs = list(bm.verts); n = sides; m = len(vs) // n
    assert m * n == len(vs), "ring size mismatch in " + name
    ctr = lambda i: sum((v.co for v in vs[i * n:(i + 1) * n]), Vector()) / n
    for i, j, k in ((0, 1, -1), (m - 1, m - 2, 1)):                      # root cap, tip cap: a vertex 0.25 r beyond the ring, a fan of n/2 quads
        c = ctr(i); r = (vs[i * n].co - c).length; t = (c - ctr(j)).normalized(); tv = bm.verts.new(c + t * 0.25 * r); rv = vs[i * n:(i + 1) * n]
        for q in range(n // 2):
            bm.faces.new((tv, rv[2 * q], rv[2 * q + 1], rv[(2 * q + 2) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    out = bpy.data.meshes.new(name); bm.to_mesh(out); bm.free(); out.materials.append(mat)
    ob = bpy.data.objects.new(name, out); bpy.context.scene.collection.objects.link(ob)
    return ob


add_tree(bpy.data.objects["Hair_hood"]); todo = json.load(open(P + r"\hair_curves.json")); rows, dropped, k = [], [], 0
for _ in range(6):                                                       # passes: a lock waits until a parent is near its root
    wait = []
    for c in todo:
        pts, rad, us = c["pts"], c["rad"], c.get("u") or [[0, 0, 1]] * len(c["pts"]); ends = [-depth(Vector(pts[0])), -depth(Vector(pts[-1]))]
        if ends[1] < ends[0]:                                            # the root is the end nearer to a parent
            pts, rad, us = pts[::-1], rad[::-1], us[::-1]
        if min(ends) > DMAX:
            wait.append(c); continue
        k += 1; ratio = c.get("ratio"); pts, nb = bury(pts, rad, us, ratio, c["sides"]); cu, err = make_curve("Hair_curve_%02d" % k, pts, rad, c["sides"], ratio, us)
        t = tube_mesh(cu, "Hair_tube_%02d" % k, c["sides"]); add_tree(t)
        rows.append((c["name"], len(t.data.polygons), len(pts), round(min(ends) * 100, 1), round(err), nb, round(depth(Vector(pts[0])) * 100, 1)))
    todo = wait
    if not todo:
        break
result = {"locks": rows, "quads": sum(r[1] for r in rows), "waiting": [c["name"] for c in todo]}
