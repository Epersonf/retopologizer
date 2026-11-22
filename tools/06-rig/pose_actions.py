"""Actions (clips) by script for a rigged creature: keyframe poses, rotate in the right axis, check the pose by number.
Inside Blender (worker): exec(open(r"<repo>\tools\06-rig\pose_actions.py", encoding="utf-8").read())
  pa = PoseAnim(rig, base={"Jaw": (-42, 0, 0)})        # base pose (degrees XYZ) every frame starts from
  pa.new("Walk"); pa.pose(1, {"UpLeg_FL": (28, 0, 0)}); pa.pose(13, {...}); pa.done()
  axis, sign = local_axis(rig, "Root", "Y")             # which LOCAL axis of the bone is the armature's Y (forward)?
  pa.pose(16, {"Root": rot_about(rig, "Root", "Y", 180)}, loc={"Root": lift_up(rig, "Root", 0.277)})
  report = check_pose(rig, mesh, frame=16, bones=("Head", "Foot_FL"))   # bbox z and bone positions: belly up and on the floor?
WHY (alligator, death clip): pose-bone rotation_euler/location are in the bone's LOCAL axes, which follow the bone's rest
roll. On a Root bone that points up, local Z was the animal's forward axis and local Y was up; rotating "Y by 180" turned it
sideways (a yaw) and the test I made (bbox z) could not tell. Never guess the axis: call local_axis / rot_about, then check_pose.
Frames: evaluate with scene.frame_set(frame); setting pose then view_layer.update() is overridden by the action at the current frame."""
import bpy, math
R = math.radians
AXES = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}


def local_axis(rig, bone, arm_axis):
    """(index 0-2, sign) of the bone-local axis that points along the armature axis 'X'|'Y'|'Z' at rest."""
    m = rig.data.bones[bone].matrix_local.to_3x3(); t = AXES[arm_axis]
    best = max(range(3), key=lambda i: abs(sum(m.col[i][k] * t[k] for k in range(3))))
    return best, (1 if sum(m.col[best][k] * t[k] for k in range(3)) > 0 else -1)


def rot_about(rig, bone, arm_axis, deg):
    """rotation_euler (radians) of `bone` that turns `deg` around the armature axis (e.g. 'Y' = the animal's length)."""
    i, s = local_axis(rig, bone, arm_axis); e = [0.0, 0.0, 0.0]; e[i] = R(deg) * s; return tuple(e)


def lift_up(rig, bone, meters):
    """location (bone-local) that moves `bone` up (armature +Z) by `meters`."""
    i, s = local_axis(rig, bone, "Z"); v = [0.0, 0.0, 0.0]; v[i] = meters * s; return tuple(v)


class PoseAnim:
    def __init__(self, rig, base=None):
        self.rig, self.base = rig, base or {}
        bpy.context.view_layer.objects.active = rig
        if rig.mode != 'POSE': bpy.ops.object.mode_set(mode='POSE')
        for b in rig.pose.bones: b.rotation_mode = 'XYZ'

    def new(self, name):
        old = bpy.data.actions.get(name)
        if old: bpy.data.actions.remove(old)
        a = bpy.data.actions.new(name); a.use_fake_user = True    # no fake user = the clip is lost on save/export
        self.rig.animation_data_create(); self.rig.animation_data.action = a; return a

    def pose(self, frame, rot=None, loc=None, deg=True):
        """rot: {bone: (x, y, z)} degrees (or radians when deg=False); loc: {bone: (x, y, z)}. Others return to the base pose."""
        for b in self.rig.pose.bones:
            b.rotation_euler = tuple(R(v) if deg else v for v in self.base.get(b.name, (0, 0, 0))); b.location = (0, 0, 0)
        for n, v in (rot or {}).items(): self.rig.pose.bones[n].rotation_euler = tuple(R(c) if deg else c for c in v)
        for n, v in (loc or {}).items(): self.rig.pose.bones[n].location = v
        for b in self.rig.pose.bones:
            b.keyframe_insert("rotation_euler", frame=frame); b.keyframe_insert("location", frame=frame)

    def done(self):
        for a in bpy.data.actions: a.use_fake_user = True
        if self.rig.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
        return [a.name for a in bpy.data.actions]


def check_pose(rig, mesh, frame, bones=("Head",)):
    """Mesh z range and the world position of some bones at `frame` (evaluates the action): lies flat and belly-up?"""
    sc = bpy.context.scene; sc.frame_set(frame); bpy.context.view_layer.update()
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    zs = [(mesh.matrix_world @ v.co).z for v in m.vertices]; ev.to_mesh_clear()
    return {"z": (round(min(zs), 3), round(max(zs), 3)), **{b: [round(c, 3) for c in rig.matrix_world @ rig.pose.bones[b].head] for b in bones}}
