"""Bake da árvore em background: blender -b draft/stylized-tree.blend -P bake_tree.py
Material original (Material.001 da ref) -> low 'tree_twig' (UV do usuário). Salva em draft/stylized-tree_baked.blend."""
import bpy, json, os
T = r"C:\Users\epers\Desktop\retopologizer\tools"
P = r"C:\Users\epers\Desktop\retopologizer\projects\stylized-tree"
OUT = P + r"\output"; os.makedirs(OUT, exist_ok=True)
exec(open(T + r"\04-uv-bake\bake_robust.py").read())
exec(open(T + r"\05-entrega\wire_material.py").read())

LOW = ["tree_twig"]
bpy.data.objects["REF_tree_highpoly"].hide_select = False  # hide_select impede o selected-to-active
o = bpy.data.objects[LOW[0]]
m = bpy.data.materials.get("tree_mat") or bpy.data.materials.new("tree_mat"); m.use_nodes = True
if not o.material_slots:
    o.data.materials.append(m)
else:
    o.material_slots[0].material = m
print("QA_UV", json.dumps({k: v for k, v in qa_uv(LOW, size=2048, min_gap_px=8).items() if not k.startswith("_")}, default=str))

# GPU se existir (Cycles em background usa as prefs do usuário)
try:
    cp = bpy.context.preferences.addons["cycles"].preferences
    for t in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            cp.compute_device_type = t; cp.get_devices()
            if any(d.type != "CPU" for d in cp.devices):
                for d in cp.devices: d.use = d.type != "CPU"
                bpy.context.scene.cycles.device = "GPU"; break
        except Exception:
            continue
except Exception as e:
    print("GPU?", e)

r = bake_robust(LOW, "REF_tree_highpoly", OUT, "tree", size=2048,
                schedule=((0.10, 0.25), (0.20, 0.50), (0.05, 0.12), (0.30, 0.70), (0.03, 0.06)), max_dist=0.15, margin_px=2)  # gap entre ilhas ~1 px: margem pequena
print("BAKE", json.dumps({k: v for k, v in r.items() if not k.startswith("_")}, default=str))
wire_and_export(LOW, "tree_mat", OUT, "tree", "tree", blend_path=P + r"\draft\stylized-tree_baked.blend")
print("DONE")
