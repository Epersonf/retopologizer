"""Bake of the hat: HiPoly (original GLB, 4096 PBR) -> Hat_retopo with the user's UV, 2048 px, validated per texel
(bake_robust). The retopo sits on the reference (mean 0.04 mm), so the extrusions are small: a big one makes the dome
rays near the drooping tail hit the tail first. The lid underneath spans air: its texels are inpainted.
Then a material with the maps goes on the low and a copy is saved as draft/hat_baked.blend (hat_uv.blend untouched).
  worker on draft/hat_uv.blend: python tools/blender_rpc.py --port 9877 projects/hat-hair/hat_bake.py"""
import os
import bpy
T_ = r"C:\Users\epers\Desktop\retopologizer\tools"
exec(open(T_ + r"\bake_robust.py", encoding="utf-8").read())
P = r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair"
OUT = P + r"\output"
LOW = "Hat_retopo"
os.makedirs(OUT, exist_ok=True)

low = bpy.data.objects[LOW]
mat = bpy.data.materials.get("Hat_mat") or bpy.data.materials.new("Hat_mat"); mat.use_nodes = True
if not low.material_slots:
    low.data.materials.append(mat)
low.material_slots[0].material = mat
r = bake_robust([LOW], "HiPoly", OUT, "hat", size=2048,
                schedule=((0.02, 0.04), (0.01, 0.02), (0.04, 0.08), (0.005, 0.01)))


def wire(mat):
    """Principled BSDF fed by the baked PNGs (normal map in tangent space, OpenGL)."""
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bs.outputs[0], out.inputs[0])
    tex = lambda n, cs: (lambda t: (setattr(t, "image", bpy.data.images.load(f"{OUT}\\hat_{n}.png", check_existing=True)),
                                    setattr(t.image.colorspace_settings, "name", cs), t)[-1])(nt.nodes.new("ShaderNodeTexImage"))
    nt.links.new(tex("basecolor", "sRGB").outputs[0], bs.inputs["Base Color"])
    nt.links.new(tex("roughness", "Non-Color").outputs[0], bs.inputs["Roughness"])
    nt.links.new(tex("metallic", "Non-Color").outputs[0], bs.inputs["Metallic"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(tex("normal", "Non-Color").outputs[0], nm.inputs["Color"])
    nt.links.new(nm.outputs[0], bs.inputs["Normal"])


wire(mat)
bpy.ops.wm.save_as_mainfile(filepath=P + r"\draft\hat_baked.blend", copy=True)
result = {k: v for k, v in r.items() if not k.startswith("_")}
result["maps"] = sorted(f for f in os.listdir(OUT) if f.startswith("hat_"))
