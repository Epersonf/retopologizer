"""The hat as the Cuca's hat in the Braziletto Godot client: CucaChapeu.fbx with the vertices in the space of her
mixamorig:Head bone (so a BoneAttachment3D on Head holds it with no offset), plus AlbedoCucaChapeu.jpg and
NormalCucaChapeu.png at 1024. Same FBX settings as Cuca.fbx (rig_mixamo.export_fbx: metres, axes baked). The fine fit
is done by hand in the game's prop editor (data/cuca_props.json); here it only starts close: scaled to her head and
the inner ceiling just above the top of her head. The bone axes did not match: the user turned it ~80/-139/-136 deg
in the editor (docs/entrega.md, "Adereço preso à cabeça").
  blender -b projects/hat-hair/draft/hat_baked.blend --python tools/blender_once.py -- projects/hat-hair/hat_to_cuca.py"""
import os, subprocess
import bpy
from mathutils import Matrix, Vector

ROOT = r"C:\Users\epers\Desktop\retopologizer"
GAME = r"C:\Users\epers\Documents\Repositories\Personal\Braziletto\frontend\godot-client\assets\characters"
MAPS = ROOT + r"\projects\hat-hair\output"
RIG = ROOT + r"\projects\stylized-cuca\draft\cuca_rig.blend"
TEX = 1024
SCALE = 0.66                                    # hat cavity ~33 cm wide -> her head is 20 cm wide
HAT_IN = Vector((0.485, 0.03, 0.48))            # hat: centre of the cavity under the inner ceiling (hat-hair space)
HEAD_TOP = Vector((0.0, -0.02, 1.055))          # Cuca: above the top of her head (z 1.048), centre of the skull
TO_IMG = ("import sys; from PIL import Image; s, d, n = sys.argv[1:]; "   # plain JFIF/PNG: Godot 4.7 chokes on Blender's
          "Image.open(s).convert('RGB').resize((int(n),) * 2, Image.LANCZOS).save(d, quality=90, optimize=True)")

with bpy.data.libraries.load(RIG) as (src, dst):
    dst.objects = ["Cuca_Rig"]
rig = dst.objects[0]
head = rig.matrix_world @ rig.data.bones["mixamorig:Head"].matrix_local
place = Matrix.Translation(HEAD_TOP) @ Matrix.Scale(SCALE, 4) @ Matrix.Translation(-HAT_IN)

low = bpy.data.objects["Hat_retopo"]
hat = bpy.data.objects.new("CucaChapeu", low.data.copy()); bpy.context.scene.collection.objects.link(hat)
hat.data.transform(head.inverted() @ place @ low.matrix_world)       # vertices in Head bone space
hat.data.update()

albedo, normal = os.path.join(GAME, "AlbedoCucaChapeu.jpg"), os.path.join(GAME, "NormalCucaChapeu.png")
subprocess.run(["python", "-c", TO_IMG, MAPS + r"\hat_basecolor.png", albedo, str(TEX)], check=True)
subprocess.run(["python", "-c", TO_IMG, MAPS + r"\hat_normal.png", normal, str(TEX)], check=True)
mat = bpy.data.materials.new("CucaChapeu"); mat.use_nodes = True; nt = mat.node_tree    # albedo the FBX points at
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(albedo)
nt.links.new(tex.outputs[0], nt.nodes["Principled BSDF"].inputs["Base Color"])
hat.data.materials.clear(); hat.data.materials.append(mat)

bpy.ops.object.select_all(action='DESELECT'); hat.select_set(True); bpy.context.view_layer.objects.active = hat
fbx = os.path.join(GAME, "CucaChapeu.fbx")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'MESH'}, apply_scale_options='FBX_SCALE_UNITS',
                         bake_space_transform=True, path_mode='STRIP', mesh_smooth_type='FACE')
result = {os.path.basename(f): os.path.getsize(f) for f in (fbx, albedo, normal)}
result["hat_dims_in_bone_space"] = [round(x, 3) for x in hat.dimensions]
