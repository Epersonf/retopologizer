"""Face-orientation views, the way Blender's overlay shows them: blue = a front face, RED = the back of a face (a reversed normal seen from outside),
shaded by how much the face looks at the camera so the shape stays readable. Orthographic views framed by the bbox of `fit_to`; Cycles on the CPU, 1 sample.
This is what the user sees with Overlays > Face Orientation, so a model that shows no red here from any view is clean in that sense (qa_strict and
qa_local do the same with rays, from 400 far and many near cameras). Inside Blender:
  exec(open(ROOT+r"\tools\03-qa\qa_orient.py").read())
  orient_views(["LowPoly"], outdir, "o", views=["front", "back", (60, 0, 35)], res=420, fit_to=["HairFull"])   # -> [(view, path, red_pixels)]"""
import bpy, math
import numpy as np
from mathutils import Vector

_VIEWS = {"front": (90, 0, 0), "back": (90, 0, 180), "right": (90, 0, 90), "left": (90, 0, -90), "top": (0, 0, 0), "bottom": (180, 0, 0), "q1": (75, 0, 35), "q2": (75, 0, -35), "q3": (75, 0, 215), "q4": (75, 0, 145), "low1": (110, 0, 30), "low2": (110, 0, 210)}


def orient_material():
    m = bpy.data.materials.get("_orient") or bpy.data.materials.new("_orient"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new
    geo, lw, mul, mix, eb, er, out = N("ShaderNodeNewGeometry"), N("ShaderNodeLayerWeight"), N("ShaderNodeMath"), N("ShaderNodeMix"), N("ShaderNodeEmission"), N("ShaderNodeEmission"), N("ShaderNodeOutputMaterial")
    mul.operation = 'MULTIPLY_ADD'; mul.inputs[1].default_value = 0.65; mul.inputs[2].default_value = 0.35; lw.inputs["Blend"].default_value = 0.5
    mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0; mix.inputs[6].default_value = (0.25, 0.5, 1.0, 1)
    er.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1); sh = N("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], mul.inputs[0]); nt.links.new(mul.outputs[0], mix.inputs[7]); nt.links.new(mix.outputs[2], eb.inputs["Color"])
    nt.links.new(geo.outputs["Backfacing"], sh.inputs[0]); nt.links.new(eb.outputs[0], sh.inputs[1]); nt.links.new(er.outputs[0], sh.inputs[2]); nt.links.new(sh.outputs[0], out.inputs[0])
    return m


def orient_views(names, outdir, prefix, views=("front", "back", "left", "q1", "top"), res=420, fit_to=None):
    sc = bpy.context.scene; vl = bpy.context.view_layer; objs = [bpy.data.objects[n] for n in (fit_to or names)]
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            v = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
    ctr = (lo + hi) / 2; size = max(hi - lo)
    cd = bpy.data.cameras.new("_ocam"); cd.type = 'ORTHO'; cd.ortho_scale = size * 1.25; cd.clip_end = 100; cam = bpy.data.objects.new("_ocam", cd); sc.collection.objects.link(cam)
    old = (sc.camera, sc.render.engine, vl.material_override, sc.cycles.samples, sc.view_settings.view_transform)
    sc.camera = cam; sc.render.engine = 'CYCLES'; sc.cycles.samples = 1; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = False; sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = res; sc.render.resolution_percentage = 100; vl.material_override = orient_material()
    w = sc.world or bpy.data.worlds.new("_w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.3, 0.3, 1)
    vis = {o: o.hide_render for o in bpy.data.objects}
    for o in bpy.data.objects:
        o.hide_render = o.name not in names
    res_ = []
    for v in views:
        rx, ry, rz = _VIEWS[v] if isinstance(v, str) else v
        cam.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz)); cam.location = ctr + cam.rotation_euler.to_matrix() @ Vector((0, 0, 1)) * size * 3
        path = "%s/%s_%s.png" % (outdir, prefix, v if isinstance(v, str) else "%d_%d_%d" % v); sc.render.filepath = path; bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(path, check_existing=False); px = np.array(img.pixels[:]).reshape(-1, 4); bpy.data.images.remove(img)
        res_.append((v, path, int(((px[:, 0] > 0.6) & (px[:, 1] < 0.2) & (px[:, 2] < 0.2)).sum())))
    for o, h in vis.items():
        if o.name in bpy.data.objects:
            o.hide_render = h
    sc.camera, sc.render.engine, vl.material_override, sc.cycles.samples, sc.view_settings.view_transform = old
    bpy.data.objects.remove(cam); bpy.data.cameras.remove(cd)
    return res_
