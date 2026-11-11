"""Marketplace thumbnail (Fab: 1920x1080, jpg/png/webp, <= 3 MB). Eevee, 3 area lights, floor for the
contact shadow, 3/4 camera that looks at the model. Temp objects are removed afterwards.
  exec(open(...).read()); render_thumbnail(["chest_base","chest_lid"], path, look_at=(0,0.05,0.40), cam=(-1.9,-2.55,1.3))
Scale cam/look_at to the model (this default fits a ~0.7 x 0.7 x 0.8 m prop with the lid open).
Textured materials must already be wired (wire_and_export). Check the file with Read before uploading."""
import bpy, os
from mathutils import Vector


def render_thumbnail(names, path, look_at=(0, 0.05, 0.40), cam=(-1.9, -2.55, 1.3), lens=65, exposure=-0.2):
    sc = bpy.context.scene; made = []
    old = (sc.render.engine, sc.camera, sc.world, sc.view_settings.exposure, sc.view_settings.view_transform)
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = exposure
    w = bpy.data.worlds.new("_thw"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.09, 0.10, 0.13, 1); sc.world = w
    tgt = Vector(look_at)

    def aim(o):
        o.rotation_euler = (tgt - o.location).to_track_quat('-Z', 'Y').to_euler()

    for nm, loc, en, col, size in (("key", (-1.6, -1.8, 1.9), 260, (1, .93, .82), 2.5),
                                   ("rim", (1.8, 1.4, 1.5), 200, (.7, .8, 1), 2.0),
                                   ("fill", (1.6, -1.6, 0.6), 60, (1, 1, 1), 3.0)):
        d = bpy.data.lights.new("_th_" + nm, 'AREA'); d.energy = en; d.color = col; d.size = size
        o = bpy.data.objects.new("_th_" + nm, d); sc.collection.objects.link(o); o.location = loc; aim(o); made.append(o)
    cd = bpy.data.cameras.new("_thcam"); cd.lens = lens
    c = bpy.data.objects.new("_thcam", cd); sc.collection.objects.link(c); c.location = cam; aim(c); made.append(c)
    sc.camera = c
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.001)); fl = bpy.context.active_object; made.append(fl)
    m = bpy.data.materials.new("_thfloor"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.12, 0.13, 0.16, 1)
    b.inputs["Roughness"].default_value = 0.8; fl.data.materials.append(m)
    for n in names:
        bpy.data.objects[n].hide_set(False); bpy.data.objects[n].hide_render = False
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    for o in made:
        bpy.data.objects.remove(o)
    sc.render.engine, sc.camera, sc.world, sc.view_settings.exposure, sc.view_settings.view_transform = old
    return {"path": path, "mb": round(os.path.getsize(path) / 1e6, 2)}
