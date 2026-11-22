"""Wire baked PBR maps into the materials, render PBR previews and export a delivery folder (FBX + GLB + maps) in one call.
Inside Blender: exec(open(...).read()), then
  wire_pbr(["WING_FEATHER", "WING_GOLD"], maps_dir, prefix="wing", tint=["WING_FEATHER"])      # tint: materials that get a white Tint multiplier
  render_previews(["WING", "Wing_Rig"], out_dir, {"front": (loc, rot_deg, ortho_scale, w, h)})   # Cycles GPU, sky light
  export_package(["WING", "Wing_Rig"], out_dir, "Asa_Braziletto", maps_dir, prefix="wing")
FBX and glTF cannot carry the Tint multiplier, so export_package rewires the materials WITHOUT it (the .blend you saved before keeps the Tint);
in Godot recolor with the material's albedo_color, which multiplies the albedo texture.
Maps: basecolor (sRGB), roughness, metallic, normal (OpenGL) as `<prefix>_<map>.png`; the AO is copied but not wired (glTF has no AO slot here)."""
import bpy, math, os, shutil, sys
MAPS = (("basecolor", "sRGB", "Base Color"), ("roughness", "Non-Color", "Roughness"), ("metallic", "Non-Color", "Metallic"))


def wire_pbr(materials, maps_dir, prefix="wing", tint=()):
    imgs = {}
    for k, cs, _ in MAPS + (("normal", "Non-Color", ""),):
        i = bpy.data.images.load(os.path.join(maps_dir, f"{prefix}_{k}.png"), check_existing=True); i.colorspace_settings.name = cs; i.pack(); imgs[k] = i
    for name in materials:
        m = bpy.data.materials[name]; nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(b.outputs[0], out.inputs[0])
        for k, _, sock in MAPS:
            n = nt.nodes.new("ShaderNodeTexImage"); n.image = imgs[k]
            if k == "basecolor" and name in tint:
                t = nt.nodes.new("ShaderNodeRGB"); t.name = t.label = "Tint"; t.outputs[0].default_value = (1, 1, 1, 1)
                mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
                nt.links.new(n.outputs["Color"], mx.inputs[6]); nt.links.new(t.outputs[0], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs[sock])
            else:
                nt.links.new(n.outputs["Color"], b.inputs[sock])
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = imgs["normal"]; nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(n.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])


def render_previews(names, out_dir, views, samples=48):
    """views: {name: (camera_location, rotation_deg, ortho_scale, width, height)}. Writes <out_dir>/p_<name>.png."""
    T = os.path.join(os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd()), "tools", "general", "cycles_gpu.py"); exec(open(T, encoding="utf-8").read(), globals())
    for o in bpy.data.objects:
        if o.name not in names:
            o.hide_viewport = o.hide_render = True
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; use_gpu(sc); sc.cycles.samples = samples; sc.cycles.use_denoising = True
    w = bpy.data.worlds.new("w"); w.use_nodes = True; sc.world = w; sky = w.node_tree.nodes.new("ShaderNodeTexSky")
    w.node_tree.links.new(sky.outputs[0], w.node_tree.nodes["Background"].inputs[0]); w.node_tree.nodes["Background"].inputs[1].default_value = 1.4
    for loc, e in (((-1.5, -2, 1.2), 600), ((2, -2, 0.2), 300)):
        L = bpy.data.lights.new("a", 'AREA'); L.energy = e; L.size = 1.5; lo = bpy.data.objects.new("a", L); sc.collection.objects.link(lo)
        lo.location = loc; lo.rotation_euler = (math.radians(80), 0, math.radians(-30))
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; sc.frame_set(1)
    for n, (loc, rot, size, rw, rh) in views.items():
        cam.data.ortho_scale = size; cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
        sc.render.resolution_x, sc.render.resolution_y = rw, rh; sc.render.filepath = os.path.join(out_dir, f"p_{n}.png"); bpy.ops.render.render(write_still=True)


def export_package(names, out_dir, name, maps_dir, prefix="wing", frame=1):
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(maps_dir):
        if f.startswith(prefix + "_") and f.endswith(".png"):
            shutil.copy(os.path.join(maps_dir, f), out_dir)
    bpy.context.scene.frame_set(frame)
    for o in bpy.data.objects:
        o.select_set(o.name in names)
    bpy.context.view_layer.objects.active = bpy.data.objects[names[0]]
    bpy.ops.export_scene.fbx(filepath=os.path.join(out_dir, name + ".fbx"), use_selection=True, path_mode='COPY', embed_textures=False, add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0,
                             object_types={'ARMATURE', 'MESH'}, mesh_smooth_type='FACE')
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, name + ".glb"), use_selection=True, export_format='GLB', export_animations=True, export_skins=True)
    return sorted(os.listdir(out_dir))
