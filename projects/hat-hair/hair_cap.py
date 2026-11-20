"""Closes the open rim of the hair shells (Hair_hood by default; worker) with a fan: one vertex inside the head and n/2 quads from
the rim to it, wound to match the shell. The vertex is searched on a grid around the rim centroid for the position where no lid quad
is inverted (a fan from a badly placed point folds, and a folded lid face is seen from behind = red). Seen from below the shell then
shows its outer side; the lid lies inside the head. Cheaper than a solidify (no second shell). Prints the inverted quads left.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_cap.py"""
import bpy, bmesh, itertools
from mathutils import Vector
SHELLS = globals().get("SHELLS", ["Hair_hood"])
info = {}
for name in SHELLS:
    ob = bpy.data.objects[name]; bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    nxt = {}
    for e in bm.edges:
        if len(e.link_faces) == 1:
            l = [l for l in e.link_faces[0].loops if l.edge == e][0]; nxt.setdefault(l.vert, []).append(l.link_loop_next.vert)
    loop = [next(iter(nxt))]
    while nxt[loop[-1]][0] != loop[0]:
        loop.append(nxt[loop[-1]][0])
    n = len(loop); assert n % 2 == 0 and n == len(nxt), (name, n, len(nxt))
    cen = sum((v.co for v in loop), Vector()) / n; inside = sum((f.calc_center_median() for f in bm.faces), Vector()) / len(bm.faces)

    def lid(c):                                          # quads (as vertex coordinates) of the fan from c; existing faces run loop[k] -> loop[k+1]
        return [(loop[2 * j + 2 - n].co, loop[2 * j + 1].co, loop[2 * j].co, c) for j in range(n // 2)]

    def inverted(c):                                     # lid quads whose normal points toward the inside of the shell
        bad = 0
        for q in lid(c):
            nrm = (q[1] - q[0]).cross(q[3] - q[0]); bad += nrm.dot(sum(q, Vector()) / 4 - inside) < 0
        return bad
    best = min((cen + Vector(d) for d in itertools.product(*[[k * .02 for k in range(-8, 9)]] * 2, [k * .025 for k in range(-12, 13)])),
               key=lambda c: (inverted(c), (c - cen).length))
    left = inverted(best); c = bm.verts.new(best)
    for j in range(n // 2):
        bm.faces.new((loop[2 * j + 2 - n], loop[2 * j + 1], loop[2 * j], c))
    bm.normal_update(); bm.to_mesh(ob.data); ob.data.update(); bm.free()
    info[name] = {"rim": n, "quads": len(ob.data.polygons), "inverted_lid_quads": left}
result = info
