"""Marketplace thumbnail (Fab: 1920x1080, jpg/png/webp, <= 3 MB) rendered in Cycles with a studio rig:
warm key softbox, cool fill, two strip rim lights, a spot that makes a light pool on a glossy dark floor,
85 mm lens with a touch of depth of field, AgX. Temp objects and render settings are restored afterwards.
  exec(open(...).read()); render_thumbnail(["chest_base","chest_lid"], path, samples=96)    # quick look
  render_thumbnail([...], path, samples=768)                                                # final
Scale `look_at` / `cam` to the model (defaults fit a ~0.7 m prop with the lid open). Wire the final
material first (wire_and_export). Painted-only albedo gets a temporary roughness/specular so it is not
flat; the material is put back. ALWAYS open the jpg and check framing / exposure before uploading."""
import bpy, os
from mathutils import Vector

RIG = (  # name, kind, location, energy(W), colour, size_x, size_y
    ("key", 'AREA', (-2.6, -2.4, 2.9), 620, (1.0, 0.88, 0.74), 3.2, 3.2),
    ("fill", 'AREA', (3.0, -2.2, 1.1), 130, (0.72, 0.82, 1.0), 3.5, 2.5),
    ("rim_l", 'AREA', (-2.2, 2.4, 1.6), 520, (0.78, 0.88, 1.0), 0.5, 2.8),
    ("rim_r", 'AREA', (2.4, 2.1, 1.4), 520, (1.0, 0.92, 0.82), 0.5, 2.8),
    ("pool", 'SPOT', (0.0, -0.3, 4.2), 330, (1.0, 0.95, 0.9), 0, 0),
)
SAVE = ("engine", "resolution_x", "resolution_y", "resolution_percentage", "filepath")


def _settings(sc):
    return {k: getattr(sc.render, k) for k in SAVE}, (sc.camera, sc.world, sc.view_settings.view_transform,
            sc.view_settings.look, sc.view_settings.exposure, sc.cycles.samples, sc.cycles.use_denoising)


def render_thumbnail(names, path, look_at=(0, 0.02, 0.40), cam=(-2.5, -3.35, 1.45), lens=85, samples=768,
                     exposure=0.0, fstop=9.0):
    sc = bpy.context.scene; made = []; r0, o0 = _settings(sc)
    sc.render.engine = 'CYCLES'; cy = sc.cycles
    try:
        sc.cycles.device = 'GPU'
    except Exception:
        pass
    cy.samples = samples; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.005
    cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'; cy.max_bounces = 10
    cy.sample_clamp_indirect = 8; cy.caustics_reflective = False; cy.caustics_refractive = False
    sc.render.film_transparent = False; sc.render.filter_size = 1.3
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 94
    vs = sc.view_settings; vs.view_transform = 'AgX'; vs.exposure = exposure
    try:
        vs.look = 'Punchy'
    except TypeError:
        pass
    w = bpy.data.worlds.new("_thw"); w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.03, 0.04, 0.06, 1); bg.inputs[1].default_value = 0.3
    sc.world = w; tgt = Vector(look_at)

    def aim(o):
        o.rotation_euler = (tgt - o.location).to_track_quat('-Z', 'Y').to_euler()
    for nm, kind, loc, en, col, sx, sy in RIG:
        d = bpy.data.lights.new("_th_" + nm, kind); d.energy = en; d.color = col
        if kind == 'AREA':
            d.shape = 'RECTANGLE'; d.size = sx; d.size_y = sy
        else:
            d.spot_size = 0.85; d.spot_blend = 1.0; d.shadow_soft_size = 1.2
        o = bpy.data.objects.new("_th_" + nm, d); sc.collection.objects.link(o); o.location = loc; aim(o); made.append(o)
    cd = bpy.data.cameras.new("_thcam"); cd.lens = lens; cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop; cd.sensor_width = 36
    c = bpy.data.objects.new("_thcam", cd); sc.collection.objects.link(c); c.location = cam; aim(c); made.append(c)
    cd.dof.focus_distance = (Vector(cam) - Vector((0, -0.4, 0.3))).length; sc.camera = c
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.001)); fl = bpy.context.active_object; made.append(fl)
    m = bpy.data.materials.new("_thfloor"); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.02, 0.022, 0.03, 1); b.inputs["Roughness"].default_value = 0.65; b.inputs["Specular IOR Level"].default_value = 0.05
    fl.data.materials.append(m)
    tweaks = []                                   # temp look-dev on the painted material, restored below
    for n in names:
        ob = bpy.data.objects[n]; ob.hide_set(False); ob.hide_render = False
        for s in ob.material_slots:
            for nd in s.material.node_tree.nodes:
                if nd.type == 'BSDF_PRINCIPLED' and nd not in [t[0] for t in tweaks]:
                    tweaks.append((nd, nd.inputs["Roughness"].default_value, nd.inputs["Specular IOR Level"].default_value))
                    nd.inputs["Roughness"].default_value = 0.6; nd.inputs["Specular IOR Level"].default_value = 0.35
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    for nd, r, s in tweaks:
        nd.inputs["Roughness"].default_value = r; nd.inputs["Specular IOR Level"].default_value = s
    for o in made:
        bpy.data.objects.remove(o)
    for k, v in r0.items():
        setattr(sc.render, k, v)
    sc.camera, sc.world, vs.view_transform, vs.look, vs.exposure, cy.samples, cy.use_denoising = o0
    return {"path": path, "mb": round(os.path.getsize(path) / 1e6, 2)}
