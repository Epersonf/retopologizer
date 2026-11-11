"""Wire baked PNGs into a Principled material and export the low-poly FBX only.
Inside Blender: exec(open(...).read()); wire_and_export(lows, mat_name, outdir, prefix, fbx_name)
FBX never contains the reference object (selection-only export)."""
import bpy


def wire_and_export(lows, mat_name, outdir, prefix, fbx_name, blend_path=None, maps=("basecolor", "roughness", "metallic", "normal")):
    """maps: which PNGs to wire (e.g. maps=("basecolor",) when only the albedo was kept)."""
    m = bpy.data.materials[mat_name]; nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (300, 0)
    nt.links.new(bsdf.outputs[0], out.inputs[0])

    def tex(name, cs, y):
        n = nt.nodes.new("ShaderNodeTexImage"); n.location = (-300, y)
        img = bpy.data.images.get(f"bake_{name}")   # reuse the baked image (no duplicates)
        # NEVER img.reload(): edits painted in Blender live only in the (packed) image, the PNG on disk is the old bake
        if img is None:
            img = bpy.data.images.load(f"{outdir}/{prefix}_{name}.png", check_existing=True)
        img.colorspace_settings.name = cs; n.image = img
        return n
    nt.links.new(tex("basecolor", "sRGB", 300).outputs["Color"], bsdf.inputs["Base Color"])
    if "roughness" in maps:
        nt.links.new(tex("roughness", "Non-Color", 0).outputs["Color"], bsdf.inputs["Roughness"])
    if "metallic" in maps:
        nt.links.new(tex("metallic", "Non-Color", -300).outputs["Color"], bsdf.inputs["Metallic"])
    if "normal" in maps:
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (0, -600)
        nt.links.new(tex("normal", "Non-Color", -600).outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bpy.ops.object.select_all(action='DESELECT')
    for n in lows:
        bpy.data.objects[n].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[lows[0]]
    fbx = f"{outdir}/{fbx_name}.fbx"
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, path_mode='RELATIVE',
                             apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
                             mesh_smooth_type='FACE', add_leaf_bones=False)
    if blend_path:
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    return fbx
