"""Bake high->low maps (Cycles, selected-to-active). Run inside Blender (MCP).
bake_all(lows, high, outdir, prefix, size=2048, extrusion=0.03, max_ray=0.06, cage_dist=None)
- Standard method: extrusion + max ray distance. If rays miss at hard edges use a cage:
  cage_dist=0.02 -> duplicate each low, push verts along normals (same as Alt+S in edit
  mode), use as cage object, delete afterwards.
- Maps: basecolor, normal(tangent), roughness, metallic(emission trick), ao.
The high object's material must have albedo / metal-rough (G=rough,B=metal) / normal wired
like glTF; pass it as high_mat (name). Low objects share one material and one UV atlas.
"""
import bpy, bmesh
exec(open(os.path.join(os.environ.get("RETOPOLOGIZER_ROOT") or (os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) if "__file__" in globals() else os.getcwd()), "tools", "general", "cycles_gpu.py"), encoding="utf-8").read())

MAPS = {  # name: (bake_type, pass_filter, colorspace, clear_color, samples)
    "basecolor": ("DIFFUSE", {"COLOR"}, "sRGB", (0, 0, 0, 1), 16),
    "normal": ("NORMAL", set(), "Non-Color", (0.5, 0.5, 1, 1), 16),
    "roughness": ("ROUGHNESS", set(), "Non-Color", (1, 1, 1, 1), 16),
    "metallic": ("EMIT", set(), "Non-Color", (0, 0, 0, 1), 16),
    "ao": ("AO", set(), "Non-Color", (1, 1, 1, 1), 128),
}


def make_cage(low, dist):
    cg = low.copy(); cg.data = low.data.copy(); cg.name = low.name + "_cage"
    bpy.context.scene.collection.objects.link(cg)
    bm = bmesh.new(); bm.from_mesh(cg.data); bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * dist
    bm.to_mesh(cg.data); bm.free()
    cg.hide_render = True
    return cg


def join_copy(lows):
    """Temp object = world-space copy of all low parts joined (shared UV atlas).
    A single bake pass over it avoids the 2nd object wiping the 1st in the same image."""
    bpy.ops.object.select_all(action='DESELECT')
    copies = []
    for n in lows:
        o = bpy.data.objects[n]; c = o.copy(); c.data = o.data.copy(); c.name = n + "_bakecopy"
        bpy.context.scene.collection.objects.link(c); c.select_set(True); copies.append(c)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active; j.name = "_bake_joined"
    return j


def _metal_material(src):
    m = src.copy(); m.name = "_tmp_metal"
    nt = m.node_tree
    sep = next(n for n in nt.nodes if n.type == 'SEPARATE_COLOR')
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(sep.outputs["Blue"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def bake_all(lows, high, outdir, prefix, size=2048, extrusion=0.03, max_ray=0.06,
             cage_dist=None, high_mat="Material.001", maps=None, margin_px=8):
    sc = bpy.context.scene; b = sc.render.bake
    old = (sc.cycles.samples, sc.cycles.use_denoising, b.use_selected_to_active, b.margin)
    print("bake on", use_gpu(sc)); sc.cycles.use_denoising = False   # GPU always: CPU bakes take ages
    b.use_selected_to_active = True; b.target = 'IMAGE_TEXTURES'
    b.margin = max(1, margin_px * size // 2048); b.margin_type = 'EXTEND'  # must be < half the UV gap
    b.cage_extrusion = extrusion; b.max_ray_distance = max_ray
    H = bpy.data.objects[high]; slot0 = H.material_slots[0].material
    mat_low = bpy.data.objects[lows[0]].material_slots[0].material
    nt = mat_low.node_tree
    paths = {}
    J = join_copy(lows)
    for name in (maps or MAPS):
        typ, flt, cs, col, smp = MAPS[name]
        img = bpy.data.images.get("bake_" + name)
        if img: bpy.data.images.remove(img)
        img = bpy.data.images.new("bake_" + name, size, size, alpha=False)
        img.colorspace_settings.name = cs; img.generated_color = col
        node = nt.nodes.get("BAKE_TARGET") or nt.nodes.new("ShaderNodeTexImage")
        node.name = "BAKE_TARGET"; node.image = img
        for n in nt.nodes: n.select = False
        node.select = True; nt.nodes.active = node
        hm = bpy.data.materials[high_mat]
        tmp = _metal_material(hm) if name == "metallic" else None
        H.material_slots[0].material = tmp or hm
        sc.cycles.samples = smp
        cg = make_cage(J, cage_dist) if cage_dist else None
        bpy.ops.object.select_all(action='DESELECT')
        H.select_set(True); J.select_set(True); bpy.context.view_layer.objects.active = J
        b.use_cage = bool(cg)
        if cg: b.cage_object = cg
        bpy.ops.object.bake(type=typ, pass_filter=flt, save_mode='INTERNAL')
        if cg:
            bpy.data.objects.remove(cg)
        if tmp: bpy.data.materials.remove(tmp)
        img.filepath_raw = f"{outdir}/{prefix}_{name}.png"; img.file_format = 'PNG'
        img.save(); paths[name] = img.filepath_raw
    H.material_slots[0].material = slot0
    bpy.data.objects.remove(J)
    sc.cycles.samples, sc.cycles.use_denoising, b.use_selected_to_active, b.margin = old
    return paths
