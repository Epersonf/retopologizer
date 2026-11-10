"""Render workbench views of chosen objects (front/back/left/right/top/persp).
Run inside Blender (MCP execute_blender_code) via exec(open(...).read()) then call
render_views(names, outdir, prefix, wire=False, res=700).
Does not touch edit mode; safe for 500k-tri meshes (workbench).
"""
import bpy, math
from mathutils import Vector

VIEWS = {
    "front": (90, 0, 0), "back": (90, 0, 180), "right": (90, 0, 90),
    "left": (90, 0, -90), "top": (0, 0, 0), "persp": (65, 0, 35),
    "persp2": (65, 0, 215),
}

def render_views(names, outdir, prefix, wire=False, res=700, views=None, hide=(), fit_to=None):
    """fit_to: object names whose bbox defines framing (use the reference so
    reference and result renders overlay 1:1)."""
    sc = bpy.context.scene
    objs = [bpy.data.objects[n] for n in (fit_to or names)]
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            v = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
    ctr = (lo + hi) / 2; size = max(hi - lo)
    cam_d = bpy.data.cameras.new("_tmpcam"); cam_d.type = 'ORTHO'
    cam_d.ortho_scale = size * 1.25; cam_d.clip_end = 100
    cam = bpy.data.objects.new("_tmpcam", cam_d); sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x = sc.render.resolution_y = res
    sh = sc.display.shading
    sh.light = 'MATCAP'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.75, 0.78)
    sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.cavity_ridge_factor = 1.0; sh.cavity_valley_factor = 1.0
    sc.display.shading.show_object_outline = True
    vis = {o: o.hide_render for o in bpy.data.objects}
    for o in bpy.data.objects:
        o.hide_render = (o.name not in names) or (o.name in hide)
    paths = []
    for vn in (views or VIEWS):
        rx, ry, rz = VIEWS[vn]
        cam.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
        d = cam.rotation_euler.to_matrix() @ Vector((0, 0, 1))
        cam.location = ctr + d * size * 3
        p = f"{outdir}/{prefix}_{vn}.png"
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    for o, h in vis.items():
        if o.name in bpy.data.objects:
            o.hide_render = h
    bpy.data.objects.remove(cam); bpy.data.cameras.remove(cam_d)
    return paths
