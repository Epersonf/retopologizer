"""Auto-rig in Blender: joints from autorig.detect, a Mixamo armature (tools/rig_mixamo.py) holding the digits found
on the hands and a tail chain when there is one, bone-heat skin with a nearest-bone fallback, and a QA summary.
  rig, qa = autorig([body, clothes, ...], "Name_Rig")"""
import math
import numpy as np
from mathutils import Matrix, Vector
import rig_mixamo as RM
from .body import Body, faces_back
from .detect import detect
from .load import mesh_of

FINGERS = ("Thumb", "Index", "Middle", "Ring", "Pinky")


def skeleton(J):
    """((bone, parent, tail joint) list, tail chain names) for the joints J: Mixamo's body, the digits found, a tail."""
    B = RM.bones([f for f in FINGERS if "LeftHand%s1" % f in J])
    tail = sorted((k for k in J if k[:4] == "Tail" and k[4:].isdigit()), key=lambda k: int(k[4:]))
    if tail:
        tail.append("Tail_End"); B += RM.chain(tail, "Hips")
    knuckle = next((f + "1" for f in ("Middle", "Ring", "Index", "Pinky") if "LeftHand%s1" % f in J), None)
    # the hand points at the middle knuckle (or the nearest one there is), or goes on along the forearm
    return [(n, p, n + knuckle if knuckle else None) if n.endswith("Hand") else (n, p, t) for n, p, t in B], tail


def autorig(objects, name="Rig", symmetric=True):
    """Armature `name` fitted to the mesh objects (detected on all of them together) and skinned to each one. The
    meshes get their transforms applied (world = local), and are turned to face -Y if they faced +Y."""
    facing = "-Y"
    for o in objects:
        clear(o); bake_transform(o)
    M = mesh_of(objects)
    if faces_back(Body(M)):
        facing = "+Y (turned)"
        for o in objects:
            bake_transform(o, Matrix.Rotation(math.pi, 4, 'Z'))
        M = mesh_of(objects)
    J, body, info = detect(M, symmetric)
    bones, tail = skeleton(J)
    rig = RM.build(objects[0].name, name, {k: Vector(v) for k, v in J.items()}, bones, sideways=tail,
                   leaf=(0.011 * body.H, 0.028 * body.H))
    qa, empty = {}, None
    for o in objects:
        for b in rig.data.bones:                         # end bones stay out of the heat solve
            b.use_deform = not RM.is_end(b.name)
        q = RM.skin(o.name, rig)
        if q["unweighted"]:
            nearest_bone(o, rig, q["unweighted"])
        qa[o.name] = {"verts": len(o.data.vertices), "fallback_verts": len(q["unweighted"]),
                      "max_influences": q["max_influences"]}
        lost = {b for b in q["bones_without_weights"] if not RM.is_end(b)}
        empty = lost if empty is None else empty & lost
    for o in objects:
        share(o, rig, empty, 0.02 * body.H)
        empty -= {g.name[len(RM.P):] for g in o.vertex_groups if g.name[len(RM.P):] in empty and has_weights(o, g)}
    return rig, {"height": round(body.H, 4), "bones": len(rig.data.bones), "meshes": qa,
                 "deform_bones_without_weights": sorted(empty or ()), "tail": len(tail) - 1 if tail else 0,
                 "digits": [f for f in FINGERS if "LeftHand%s1" % f in J], "facing": facing}


def bake_transform(o, extra=Matrix.Identity(4)):
    """Mesh data in world space (optionally moved by `extra`), object transform identity."""
    mw = o.matrix_world.copy(); o.parent = None
    o.data.transform(extra @ mw); o.matrix_world = Matrix.Identity(4)


def clear(o):
    """No armature left on the mesh (an old rig's pose would fool the detection and the skin)."""
    for m in [m for m in o.modifiers if m.type == 'ARMATURE']:
        o.modifiers.remove(m)
    o.vertex_groups.clear()


def nearest_bone(o, rig, verts):
    """Weight 1 on the nearest deform bone (distance to its segment) for vertices the heat solver left empty."""
    segs = [(b.name, np.array(rig.matrix_world @ b.head_local), np.array(rig.matrix_world @ b.tail_local))
            for b in rig.data.bones if not RM.is_end(b.name)]
    A, Bt = np.array([s[1] for s in segs]), np.array([s[2] for s in segs])
    W = np.array(o.matrix_world)
    for i in verts:
        p = W[:3, :3] @ np.array(o.data.vertices[i].co) + W[:3, 3]
        d = Bt - A; t = np.clip(((p - A) * d).sum(1) / np.maximum((d * d).sum(1), 1e-12), 0, 1)
        name = segs[int(np.argmin(np.linalg.norm(A + d * t[:, None] - p, axis=1)))][0]
        (o.vertex_groups.get(name) or o.vertex_groups.new(name=name)).add([i], 1.0, 'REPLACE')


def has_weights(o, g):
    return any(g.index == e.group for v in o.data.vertices for e in v.groups)


def share(o, rig, names, reach):
    """A deform bone the heat skin left empty (a short bone between two vertex rings) takes half the weight of the
    ring of vertices closest to it, within `reach` (a bone far from the mesh, like the Saci's missing leg, stays)."""
    V = np.array([np.array(v.co) for v in o.data.vertices])
    for name in sorted(names or ()):
        b = rig.data.bones[RM.P + name]; h, t = np.array(b.head_local), np.array(b.tail_local)
        d = t - h; u = np.clip(((V - h) @ d) / max(float(d @ d), 1e-12), 0, 1)
        dist = np.linalg.norm(V - (h + u[:, None] * d), axis=1)
        if dist.min() > reach:
            continue
        ring = np.nonzero(dist < dist.min() * 1.25 + 1e-6)[0]
        g = o.vertex_groups.get(RM.P + name) or o.vertex_groups.new(name=RM.P + name)
        for i in ring:
            for e in o.data.vertices[i].groups:
                e.weight *= 0.5
            g.add([int(i)], 0.5, 'REPLACE')
            gs = sorted(o.data.vertices[i].groups, key=lambda e: e.weight)
            for e in gs[:-4]:                              # still at most 4 bones per vertex
                o.vertex_groups[e.group].remove([int(i)])
            total = sum(e.weight for e in o.data.vertices[i].groups)
            for e in o.data.vertices[i].groups:
                e.weight /= total
