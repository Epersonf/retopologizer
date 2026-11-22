"""Store images of a rigged creature in different clips/poses, rendered with the thumbnail studio (Cycles).
Inside Blender (worker), after render_thumbnail.py is loaded:
  exec(open(r"<repo>\tools\05-delivery\render_thumbnail.py", encoding="utf-8").read())
  exec(open(r"<repo>\tools\05-delivery\listing_renders.py", encoding="utf-8").read())
  shots = {"thumbnail": ("Idle", 1, look_at, cam), "bite": ("Attack", 6, ...), "death": ("Death", 40, ...)}   # name: (action, frame, look_at, cam)
  pose_shots(rig, mesh, "projects/x/listing/img", shots, samples=256, lens=70)
Fab: thumbnail 1920x1080 jpg <= 3 MB; a bite close-up, a walk side view and the death pose sell an animated model better than 3 idle views.
Do a first pass at samples=48 and LOOK at every image (framing was too far on the first alligator pass)."""
import bpy, os


def pose_shots(rig, mesh, out_dir, shots, samples=256, lens=70):
    os.makedirs(out_dir, exist_ok=True); out = []
    if bpy.context.object and bpy.context.object.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    for name, (action, frame, look_at, cam) in shots.items():
        rig.animation_data.action = bpy.data.actions[action]; bpy.context.scene.frame_set(frame)
        out.append(render_thumbnail([mesh.name], os.path.join(out_dir, name + ".jpg"), look_at=look_at, cam=cam, lens=lens, samples=samples))
    return out
