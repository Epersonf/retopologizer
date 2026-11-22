"""Store listing image set in one call: thumbnail + detail + full views of a prop, each with its own camera.
`render_thumbnail` renders ONE image; a listing needs 3-6 of the same prop, and a long prop (sword, staff) needs to be tilted
and centered on the look-at point first or it ends up cropped. This tilts the object (restored afterwards), centers it and renders every shot.
  exec(open(r"<repo>\\tools\\05-delivery\\listing_shots.py", encoding="utf-8").read())
  listing_shots(["Espada"], r"<project>\\listing", {
      "thumbnail.jpg":   dict(cam=(-0.5, -4.4, 1.0), look_at=(0, 0, 0.55), lens=85),            # whole prop, tilted
      "detail_hilt.jpg": dict(cam=(-0.3, -1.3, 0.75), look_at=(0, 0, 0.45), lens=85),           # close-up
  }, tilt_deg=-52, center=(0, 0, 0.55), samples=48)        # samples 48 for a test, 768 for the final
Test with low samples and OPEN every file: framing, nothing cropped, final texture (`docs/05-delivery/delivery.md`)."""
import bpy, math, os
from mathutils import Vector

exec(open(os.path.join(os.environ.get("RETOPOLOGIZER_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) if "__file__" in globals()
                       else os.getcwd(), "tools", "05-delivery", "render_thumbnail.py"), encoding="utf-8").read())


def listing_shots(names, out_dir, shots, tilt_deg=None, tilt_axis=1, center=None, samples=768):
    """`shots`: {filename: dict(cam, look_at, lens)}; tilt_deg rotates about euler axis `tilt_axis` (0 x, 1 y, 2 z) of the first object."""
    os.makedirs(out_dir, exist_ok=True)
    obs = [bpy.data.objects[n] for n in names]
    saved = [(o, o.location.copy(), o.rotation_euler.copy()) for o in obs]
    try:
        if tilt_deg is not None:
            for o in obs:
                e = list(o.rotation_euler); e[tilt_axis] = math.radians(tilt_deg); o.rotation_euler = e
        bpy.context.view_layer.update()
        if center is not None:
            cs = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
            shift = Vector(center) - sum(cs, Vector()) / len(cs)
            for o in obs: o.location += shift
            bpy.context.view_layer.update()
        done = []
        for fn, kw in shots.items():
            path = os.path.join(out_dir, fn)
            render_thumbnail(names, path, samples=samples, **kw); done.append((fn, round(os.path.getsize(path) / 1e6, 2)))
        return done
    finally:
        for o, loc, rot in saved: o.location = loc; o.rotation_euler = rot
        bpy.context.view_layer.update()
