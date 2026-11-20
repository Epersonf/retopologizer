"""Blender side of fibercards.py (one-shot: blender -b --factory-startup --python tools/general/blender_once.py -- tools/07-fibercards/fc_blender.py, the job
JSON path in the environment variable FC_JOB). Builds every strand as a tube (8 sides, a radius per ring, a colour per ring: the gradient) in card space of the
sheet (1 px = 0.001 m, x across, y up, z toward the camera), one mesh per card, and renders the sheet with an orthographic camera looking down -z, Cycles, transparent
film, no denoise: <tag>_color.png (lighting "soft": a sun from (0,10,5) + a grey world, Principled with the preset's glossiness/sheen; "flat": pure albedo) and
<tag>_normal.png (view-space normal * 0.5 + 0.5, raw). Optionally saves the cards in a .blend. The job: {size, tag, out, lighting, samples, cards: [{cell: [x0, y0, w, h], strands: [{p, r, c}]}], blend}."""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Vector
job = json.load(open(os.environ["FC_JOB"])); exec(open(job["tools"] + r"/general/cycles_gpu.py").read()); U = 0.001; W = H = job["size"]; S = 8; sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def tube_mesh(name, strands, origin):                                          # all the strands of a card as one mesh, vertex colours "Col" (linear)
    V, C, F, base = [], [], [], 0; ang = np.arange(S) * 2 * math.pi / S
    for st in strands:
        P = np.array(st["p"]) * U; r = np.array(st["r"]) * U; col = lin(np.array(st["c"])); m = len(P)
        T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None] + 1e-12; N1 = np.cross(T, [0, 0, 1.0]); N1 /= np.linalg.norm(N1, axis=1)[:, None] + 1e-12; N2 = np.cross(T, N1)
        ring = P[:, None, :] + r[:, None, None] * (np.cos(ang)[None, :, None] * N1[:, None, :] + np.sin(ang)[None, :, None] * N2[:, None, :])
        V.append(ring.reshape(-1, 3) + origin); C.append(np.repeat(col, S, axis=0)); i = base + np.arange(m - 1)[:, None] * S + np.arange(S)[None, :]; j = (np.arange(S) + 1) % S
        F.append(np.stack([i, base + np.arange(m - 1)[:, None] * S + j[None, :], base + (np.arange(m - 1)[:, None] + 1) * S + j[None, :], i + S], -1).reshape(-1, 4)); base += m * S
    V = np.concatenate(V); F = np.concatenate(F); C = np.concatenate(C); me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set("co", V.ravel())
    me.loops.add(len(F) * 4); me.polygons.add(len(F)); me.loops.foreach_set("vertex_index", F.ravel()); me.polygons.foreach_set("loop_start", np.arange(len(F)) * 4); me.polygons.foreach_set("loop_total", np.full(len(F), 4))
    me.polygons.foreach_set("use_smooth", np.ones(len(F), bool)); me.update(); a = me.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT'); a.data.foreach_set("color", np.column_stack([C, np.ones(len(C))]).ravel())
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); return ob


def material(kind):
    m = bpy.data.materials.new("fc_" + kind); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new("ShaderNodeOutputMaterial")
    if kind == "normal":
        g = nt.nodes.new("ShaderNodeNewGeometry"); v = nt.nodes.new("ShaderNodeVectorMath"); v.operation = 'MULTIPLY_ADD'; v.inputs[1].default_value = (0.5, 0.5, 0.5); v.inputs[2].default_value = (0.5, 0.5, 0.5)
        e = nt.nodes.new("ShaderNodeEmission"); nt.links.new(g.outputs["Normal"], v.inputs[0]); nt.links.new(v.outputs[0], e.inputs["Color"]); nt.links.new(e.outputs[0], out.inputs[0]); return m
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "Col"
    if kind == "flat":
        e = nt.nodes.new("ShaderNodeEmission"); nt.links.new(at.outputs["Color"], e.inputs["Color"]); nt.links.new(e.outputs[0], out.inputs[0]); return m
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.inputs["Metallic"].default_value = job["glossiness"]; b.inputs["Roughness"].default_value = job["sheen"]
    nt.links.new(at.outputs["Color"], b.inputs["Base Color"]); nt.links.new(b.outputs[0], out.inputs[0]); return m


def render(kind, path):
    for ob in cards:
        ob.data.materials.clear(); ob.data.materials.append(material(kind))
    vs = sc.view_settings; vs.view_transform = 'Raw' if kind == "normal" else 'Standard'; vs.look = 'None'; vs.exposure = 0; vs.gamma = 1
    w = bpy.data.worlds.new("fc"); w.use_nodes = True; bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (1, 1, 1, 1); bg.inputs["Strength"].default_value = 0.65 if kind == "soft" else 0.0; sc.world = w
    sun.hide_render = kind != "soft"; sc.render.filepath = path; bpy.ops.render.render(write_still=True)


sc.render.engine = 'CYCLES'; print("device:", use_gpu()); sc.cycles.samples = job["samples"]; sc.cycles.use_denoising = False; sc.cycles.film_exposure = 1.0; sc.cycles.filter_width = 1.5
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = W; sc.render.resolution_percentage = 100; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
cam = bpy.data.objects.new("fc_cam", bpy.data.cameras.new("fc_cam")); cam.data.type = 'ORTHO'; cam.data.ortho_scale = W * U; cam.location = (0, 0, 5); cam.data.clip_end = 100; sc.collection.objects.link(cam); sc.camera = cam
sun = bpy.data.objects.new("fc_sun", bpy.data.lights.new("fc_sun", 'SUN')); sun.data.energy = 1.8; sun.rotation_euler = Vector((0, 10, 5)).to_track_quat('Z', 'Y').to_euler(); sc.collection.objects.link(sun)
cards = []
for k, c in enumerate(job["cards"]):
    x0, y0, w, h = c["cell"]; cards.append(tube_mesh("card_%02d" % (k + 1), c["strands"], np.array([(x0 + w / 2 - W / 2) * U, (H / 2 - (y0 + h)) * U, 0.0])))
os.makedirs(job["out"], exist_ok=True); render(job["lighting"], os.path.join(job["out"], job["tag"] + "_color.png")); render("normal", os.path.join(job["out"], job["tag"] + "_normal.png"))
if job.get("blend"):
    bpy.ops.wm.save_as_mainfile(filepath=job["blend"])
result = {"cards": len(cards), "verts": sum(len(o.data.vertices) for o in cards)}
