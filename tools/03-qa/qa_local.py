"""QA: reversed faces seen from INSIDE crevices. qa_strict.py shoots from far away; a face in a pit between a tube and the shell
can be hidden from every far ray and still look wrong (dark/red in Blender) when the eye is near. Here the rays start on the
front side of every face, on the outer side of its normal, in `n_dirs` directions of the hemisphere. A ray whose first hit is the
BACK of another face (|cos| > `graze`) is a sighting of that face. A start point inside a solid (buried tube root, > `buried` of its rays
hit a back face) is skipped, it sees the inside of the solid by definition. A face with `min_votes` sightings fails.
Inside Blender (after qa_faces.py): exec(open(ROOT+r"\tools\03-qa\qa_local.py").read())
  r = qa_local("LowPoly")    # r["pass"], r["faces"] = [{"face", "votes", "at"}] worst first"""
import bpy, math
from mathutils import Vector, Matrix


def _hemisphere(n):
    g = math.pi * (3 - math.sqrt(5))
    return [Vector((math.sqrt(1 - ((i + 0.5) / n) ** 2) * math.cos(g * i), math.sqrt(1 - ((i + 0.5) / n) ** 2) * math.sin(g * i), (i + 0.5) / n)) for i in range(n)]


def qa_local(name, n_dirs=48, graze=0.1, buried=0.85, min_votes=3, eps=1e-3):
    ob = bpy.data.objects[name]; tree, tri_poly, R = _tree(ob); me = ob.data; M = ob.matrix_world
    base = _hemisphere(n_dirs); votes = {}; skipped = 0
    for p in me.polygons:
        n = R @ p.normal; n.normalize(); c = M @ p.center + n * eps
        t = n.cross(Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))); t.normalize(); Rm = Matrix((t, n.cross(t), n)).transposed()
        hits = []
        for d in base:
            w = Rm @ d; h = tree.ray_cast(c, w, 1e3)
            if h[0] is not None and h[1].dot(w) > 0 and abs(h[1].dot(w)) > graze:
                hits.append(tri_poly[h[2]])
        if len(hits) >= buried * n_dirs:
            skipped += 1; continue
        for q in hits:
            votes[q] = votes.get(q, 0) + 1
    bad = sorted(((v, q) for q, v in votes.items() if v >= min_votes), reverse=True)
    return {"pass": not bad, "skipped_buried": skipped,
            "faces": [{"face": q, "votes": v, "at": [round(x, 3) for x in (M @ me.polygons[q].center)]} for v, q in bad[:30]]}
