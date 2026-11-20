"""Retopo artist's view as a PNG: workbench render + the low-poly wireframe drawn on top (hidden lines removed).
  exec(open(...).read())
  wire_overlay(["LowPoly"], path, view="front", shade=["HiPoly"], center=(0, 0, 0.8), size=0.4)
Edges come from the evaluated mesh (Mirror etc. applied). An edge sample is drawn when no low-poly face hides it
(raycast toward the camera), so the back half of a closed mesh is not drawn. `size` = ortho width in metres.
Views: front (-Y), back, left (-X), right (+X), top, bottom, persp, persp2, or a (rx, ry, rz) tuple in degrees."""
import bpy, math, numpy as np
from mathutils import Vector, Euler
from mathutils.bvhtree import BVHTree

import os
_TOOLS = os.path.join(os.environ.get("RETOPOLOGIZER_ROOT") or (os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) if "__file__" in globals() else os.getcwd()), "tools", "02-retopology")
WVIEWS = {"front": (90, 0, 0), "back": (90, 0, 180), "right": (90, 0, 90), "left": (90, 0, -90),
          "top": (0, 0, 0), "bottom": (180, 0, 0), "persp": (65, 0, -35), "persp2": (65, 0, 215)}


def _eval_mesh(o, dg):
    oe = o.evaluated_get(dg); me = oe.to_mesh(); M = o.matrix_world
    V = [M @ v.co for v in me.vertices]; me.calc_loop_triangles()
    T = [tuple(t.vertices) for t in me.loop_triangles]; E = [tuple(e.vertices) for e in me.edges]
    oe.to_mesh_clear()
    return V, T, E


def _render(shade, path, rot, center, size, res, clip=None):
    sc = bpy.context.scene
    cd = bpy.data.cameras.new("_wcam"); cd.type = 'ORTHO'; cd.ortho_scale = size; cd.clip_end = 100
    cd.clip_start = 10 - clip if clip else 0.1
    cam = bpy.data.objects.new("_wcam", cd); sc.collection.objects.link(cam)
    cam.rotation_euler = rot; back = rot.to_matrix() @ Vector((0, 0, 1)); cam.location = Vector(center) + back * 10
    old_cam, old_eng = sc.camera, sc.render.engine
    sc.camera = cam; sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x = sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.62, 0.64, 0.68)
    sh.show_cavity = False; sh.show_object_outline = False
    hid = {o: o.hide_render for o in bpy.data.objects}
    for o in bpy.data.objects:
        o.hide_render = o.name not in shade
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    for o, h in hid.items():
        o.hide_render = h
    sc.camera, sc.render.engine = old_cam, old_eng
    bpy.data.objects.remove(cam); bpy.data.cameras.remove(cd)
    return back


def wire_overlay(low, path, view="front", shade=None, center=None, size=None, res=900, color=(1.0, 0.5, 0.05),
                 seam_color=(0.1, 0.9, 1.0), labels=False, clip=None):
    """Boundary (open) edges are drawn in `seam_color` so holes / unfinished borders stand out.
    labels=True writes <path>_labels.json (index + pixel of each visible vertex of low[0]) for label_png.py.
    clip=d cuts away everything more than d metres in front of `center` (look at a shoulder under the head)."""
    dg = bpy.context.evaluated_depsgraph_get()
    data = [_eval_mesh(bpy.data.objects[n], dg) for n in low]
    allv = [v for V, _, _ in data for v in V]
    if center is None:
        lo = Vector(map(min, *zip(*allv))) if allv else Vector(); hi = Vector(map(max, *zip(*allv))) if allv else Vector()
        center, size = (lo + hi) / 2, size or max(hi - lo) * 1.2
    rot = Euler([math.radians(a) for a in (WVIEWS[view] if isinstance(view, str) else view)])
    back = _render(shade or list(low), path, rot, center, size, res, clip)
    R = rot.to_matrix(); right, up = R @ Vector((1, 0, 0)), R @ Vector((0, 1, 0)); c = Vector(center)
    img = bpy.data.images.load(path, check_existing=False)
    px = np.array(img.pixels[:], np.float32).reshape(res, res, 4)
    import sys                                         # shaded reference objects also hide the wire (6 mm slack)
    if _TOOLS not in sys.path:
        sys.path.insert(0, _TOOLS)
    from retopo.ref import Ref
    occ = [Ref(n) for n in (shade or []) if n not in low]

    def visible(p, bv):
        d = 5.0 if clip is None else clip - (p - c).dot(back)
        if d < 0:
            return False
        h = bv.ray_cast(p + back * d, -back, d + 1)
        if h[0] is not None and h[3] < d - 2e-3:
            return False
        for r in occ:
            hh = r.ray(p + back * d, -back, d + 1)
            if hh is not None and hh[2] < d - 0.006:
                return False
        return True
    for V, T, E in data:
        bv = BVHTree.FromPolygons(V, T)
        cnt = {}
        for t in T:
            for k in range(3):
                e = tuple(sorted((t[k], t[(k + 1) % 3]))); cnt[e] = cnt.get(e, 0) + 1
        for a, b in E:
            pa, pb = V[a], V[b]
            L = (pa - pb).length / size * res; n = max(2, int(L * 1.5))
            col = seam_color if cnt.get(tuple(sorted((a, b))), 2) < 2 else color
            for t in np.linspace(0, 1, n):
                p = pa.lerp(pb, t)
                if not visible(p, bv):
                    continue
                u = int((((p - c).dot(right)) / size + 0.5) * res); v = int((((p - c).dot(up)) / size + 0.5) * res)
                if 0 <= u < res - 1 and 0 <= v < res - 1:
                    px[v:v + 2, u:u + 2, :3] = col
    if labels:
        import json
        V, T, E = data[0]; bv = BVHTree.FromPolygons(V, T); out = []
        me = bpy.data.objects[low[0]].data; orig = me.attributes.get("orig")    # artist's index (retopo.Topo)
        for i in range(len(me.vertices)):
            p = V[i]; k = orig.data[i].value - 1 if orig else i
            if visible(p, bv):
                out.append([k if k >= 0 else "n%d" % i, (((p - c).dot(right)) / size + 0.5) * res,
                            (0.5 - ((p - c).dot(up)) / size) * res])
        json.dump(out, open(path[:-4] + "_labels.json", "w"))
    img.pixels.foreach_set(px.ravel()); img.filepath_raw = path; img.file_format = 'PNG'; img.save()
    bpy.data.images.remove(img)
    return path
