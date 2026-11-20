"""Mixamo-named humanoid armature from joint positions, skinned to one mesh with bone-heat weights.
  J = {"Hips": (x, y, z), ..., "LeftHandIndex1": ...}: world metres, the character faces -Y and its LEFT is +X
  (give the left side and call mirror_left). B = bones(fingers) + chain([...], "Hips") for extra chains (a tail).
  rig = build("Body", "Name_Rig", J, B, sideways=tail_names); qa = skin("Body", rig)
Bone names get the "mixamorig:" prefix (Godot's FBX import turns it into "mixamorig_"). Weights: max 4 per vertex,
normalized, tiny ones dropped (game engines). Exported like the Saci: export_fbx (default axes, no leaf bones)."""
import bpy
from mathutils import Vector

P = "mixamorig:"


def bones(fingers=("Thumb", "Index", "Middle", "Ring", "Pinky")):
    """(bone, parent, tail joint or None) in Mixamo's hierarchy; None = short leaf along the parent direction."""
    B = [("Hips", None, "Spine"), ("Spine", "Hips", "Spine1"), ("Spine1", "Spine", "Spine2"), ("Spine2", "Spine1", "Neck"),
         ("Neck", "Spine2", "Head"), ("Head", "Neck", "HeadTop_End"), ("HeadTop_End", "Head", None)]
    for s in ("Left", "Right"):
        B += [(s + "Shoulder", "Spine2", s + "Arm"), (s + "Arm", s + "Shoulder", s + "ForeArm"),
              (s + "ForeArm", s + "Arm", s + "Hand"), (s + "Hand", s + "ForeArm", s + "HandMiddle1"),
              (s + "UpLeg", "Hips", s + "Leg"), (s + "Leg", s + "UpLeg", s + "Foot"), (s + "Foot", s + "Leg", s + "ToeBase"),
              (s + "ToeBase", s + "Foot", s + "Toe_End"), (s + "Toe_End", s + "ToeBase", None)]
        for f in fingers:
            for i in range(1, 5):
                n = "%sHand%s%d" % (s, f, i)
                B.append((n, s + "Hand" if i == 1 else n[:-1] + str(i - 1), n[:-1] + str(i + 1) if i < 4 else None))
    return B


def chain(names, parent):
    """Extra chain hanging from `parent`: each joint to the next, the last one a leaf."""
    return [(n, names[i - 1] if i else parent, names[i + 1] if i + 1 < len(names) else None) for i, n in enumerate(names)]


def mirror_left(J):
    for k in [k for k in J if k.startswith("Left")]:
        v = Vector(J[k]); J["Right" + k[4:]] = Vector((-v.x, v.y, v.z))
    return {k: Vector(v) for k, v in J.items()}


def is_end(name):
    return name.endswith("_End") or ("Hand" in name and name[-1] == "4")


def _roll_up(ax, sideways):
    """Bone Z axis: chains in the mirror plane keep X to the side (bend = rotation about X); limbs along X or Y
    keep Z up; the rest (spine, legs) faces forward (-Y)."""
    if sideways:
        return Vector((1, 0, 0)).cross(ax)
    return Vector((0, 0, 1)) if abs(ax.x) > 0.7 or abs(ax.y) > 0.7 else Vector((0, -1, 0))


def _activate(o):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o


def build(mesh_name, rig_name, J, B, sideways=(), leaf=(0.012, 0.03)):
    """Armature `rig_name` (replaces a previous one); the mesh loses its old armature and groups. Leaf bones (no
    tail joint) go on along their parent, 0.6 x its length within `leaf` (min, max)."""
    low = bpy.data.objects[mesh_name]
    for o in [o for o in bpy.data.objects if o.name == rig_name]:
        bpy.data.objects.remove(o)
    low.parent = None
    for m in [m for m in low.modifiers if m.type == 'ARMATURE']:
        low.modifiers.remove(m)
    low.vertex_groups.clear()
    arm = bpy.data.armatures.new(rig_name); rig = bpy.data.objects.new(rig_name, arm)
    bpy.context.scene.collection.objects.link(rig); arm.display_type = 'STICK'; rig.show_in_front = True
    _activate(rig); bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones
    for name, par, tail in B:
        b = eb.new(P + name); b.head = J[name]
        if tail:
            b.tail = J[tail]
        else:
            d = J[name] - J[par]; b.tail = J[name] + d.normalized() * max(leaf[0], min(leaf[1], d.length * 0.6))
        if par:
            b.parent = eb[P + par]; b.use_connect = (eb[P + par].tail - b.head).length < 1e-5
    for b in eb:
        b.align_roll(_roll_up((b.tail - b.head).normalized(), b.name[len(P):] in sideways))
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in arm.bones:
        b.use_deform = not is_end(b.name)
    return rig


def skin(mesh_name, rig, limit=4, clean=0.01):
    """Bone-heat weights, then per vertex: the `limit` largest weights >= clean, normalized."""
    low = bpy.data.objects[mesh_name]
    _activate(low); rig.select_set(True); bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    vg = low.vertex_groups; empty = []
    for v in low.data.vertices:
        gs = sorted(((g.group, g.weight) for g in v.groups), key=lambda t: -t[1])
        keep = [(i, w) for i, w in gs[:limit] if w >= clean] or gs[:1]
        if not keep:
            empty.append(v.index); continue
        s = sum(w for i, w in keep)
        for i, w in gs:
            vg[i].remove([v.index])
        for i, w in keep:
            vg[i].add([v.index], w / s, 'REPLACE')
    for b in rig.data.bones:          # Mixamo-style: every bone is a deform bone in the file, end bones just stay empty
        b.use_deform = True
    used = {g.group for v in low.data.vertices for g in v.groups}
    return {"bones": len(rig.data.bones), "unweighted": empty,
            "max_influences": max(len(v.groups) for v in low.data.vertices),
            "bones_without_weights": sorted(g.name[len(P):] for g in vg if g.index not in used)}


def export_fbx(path, rig, mesh_name, textures=False):
    """FBX like the Saci's: Blender's default axes (faces +Z, left +X in the file), no leaf bones. Units in metres
    and the axis change baked into the data: otherwise Godot puts x100 and -90 deg X into the skin binds and the mesh
    comes out 1 cm tall in its own space (skinned right, but the AABB and any code reading vertices see the wrong size)."""
    _activate(rig)
    for n in [mesh_name] if isinstance(mesh_name, str) else mesh_name:
        bpy.data.objects[n].select_set(True)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             apply_scale_options='FBX_SCALE_UNITS', bake_space_transform=True,
                             bake_anim=bool(bpy.data.actions), bake_anim_use_all_actions=True,
                             bake_anim_use_nla_strips=False, path_mode='COPY' if textures else 'STRIP',
                             embed_textures=textures)
    return path
