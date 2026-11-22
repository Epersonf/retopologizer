"""Rig for a limb-like prop (wing, tail, whip, cape): a bone chain along one axis, positional weights, a looping flap animation.
Inside Blender: exec(open(...).read()), then
  rig = build_rig("Wing_Rig", {"Root": ((x, y, z), (x, y, z), None), "W1": (head, tail, "Root"), "Fan": (head, tail, "Root")})   # name: (head, tail, parent)
  weight_chain(ob, rig, chain=["Root", "W1", "W2", "W3"], joints=[-0.30, 0.05, 0.35], half=0.10, axis=0,
               extra=("Fan", lambda co: weight_0_to_1), rigid=("Root", lambda v, co, gold: bool))
  flap(rig, amp={"Root": 12, "W1": 8}, lag={"Root": 0, "W1": 0.07}, frames=24, axis=(0, 1, 0))
Weights are numeric, not bone heat: heat gives holes and wrong parents on overlapping shells (feathers + frame in one mesh).
Smooth blend of width 2*half around each joint along `axis`; `extra` (a region bone, e.g. the lower feather fan) takes its share from the others;
`rigid` pins vertices to one bone (the handle/collar). At most 3 groups per vertex, so it fits the 4-bone game limit."""
import bpy, math
from mathutils import Vector, Quaternion

ss = lambda t: (lambda u: u * u * (3 - 2 * u))(min(max(t, 0.0), 1.0))


def build_rig(name, bones):
    arm = bpy.data.armatures.new(name); rig = bpy.data.objects.new(name, arm); bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig; rig.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    for n, (h, t, p) in bones.items():
        b = arm.edit_bones.new(n); b.head = h; b.tail = t
        if p:
            b.parent = arm.edit_bones[p]; b.use_connect = (tuple(arm.edit_bones[p].tail) == tuple(h))
    bpy.ops.object.mode_set(mode='OBJECT'); return rig


def weight_chain(ob, rig, chain, joints, half=0.1, axis=0, extra=None, rigid=None):
    me = ob.data; names = list(chain) + ([extra[0]] if extra else [])
    for n in names:
        ob.vertex_groups.new(name=n)
    gold = {v for p in me.polygons if me.materials[p.material_index].name.endswith("GOLD") for v in p.vertices}   # helper for rigid(): vertices of the frame material
    pinned = 0
    for v in me.vertices:
        co = ob.matrix_world @ v.co
        if rigid and rigid[1](v, co, v.index in gold):
            ob.vertex_groups[rigid[0]].add([v.index], 1.0, 'REPLACE'); pinned += 1; continue
        s = [ss((co[axis] - (j - half)) / (2 * half)) for j in joints]; w = [1 - s[0]] + [s[i] - s[i + 1] for i in range(len(s) - 1)] + [s[-1]]
        if extra:
            f = extra[1](co); w = [a * (1 - f) for a in w] + [f]
        for g, wt in zip(names, w):
            if wt > 1e-3:
                ob.vertex_groups[g].add([v.index], wt, 'REPLACE')
    m = ob.modifiers.new("Armature", 'ARMATURE'); m.object = rig; ob.parent = rig
    return {"pinned": pinned, "unweighted": sum(1 for v in me.vertices if not v.groups), "max_groups": max(len(v.groups) for v in me.vertices)}


def flap(rig, amp, lag, frames=24, axis=(0, 1, 0), name="Wing_Flap"):
    """Sine rotation in degrees about the world axis, each bone delayed by lag (fraction of a cycle) from its parent: a travelling wave.
    Frames 1..frames+1 (the last equals the first, so it loops). Keyed every 3 frames."""
    bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='POSE'); sc = bpy.context.scene
    sc.frame_start = 1; sc.frame_end = frames + 1
    for n, a in amp.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; ax = (pb.bone.matrix_local.to_3x3().inverted() @ Vector(axis)).normalized()
        for fr in range(1, frames + 2):
            if (fr - 1) % 3 and fr != frames + 1:
                continue
            pb.rotation_quaternion = Quaternion(ax, math.radians(a) * math.sin(2 * math.pi * ((fr - 1) / frames - lag[n]))); pb.keyframe_insert("rotation_quaternion", frame=fr)
    bpy.ops.object.mode_set(mode='OBJECT'); act = rig.animation_data.action; act.name = name; act.use_fake_user = True; return act
