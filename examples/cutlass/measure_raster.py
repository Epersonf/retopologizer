# Import the GLB, apply its transform (BVHTree.FromObject is local: the glTF import adds a rotation) and raster the
# silhouette and thickness: a ray along -Y and +Y every 2 mm on the XZ plane -> draft/raster.npz.
import bpy, numpy as np
import os
ROOT = os.environ.get("RETOPOLOGIZER_ROOT", os.getcwd()).replace("\\", "/").rstrip("/") + "/"
P = ROOT + "projects/cutlass/"

from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=P + "input/cutlass_ref.glb")
ref = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
ref.name = "REFERENCE"
bpy.context.view_layer.objects.active = ref; ref.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
ref.hide_select = True
bpy.ops.wm.save_as_mainfile(filepath=P + "draft/cutlass.blend")
bv = BVHTree.FromObject(ref, bpy.context.evaluated_depsgraph_get())
step = 0.002
xs = np.arange(-0.485, 0.39, step); zs = np.arange(-0.005, 0.895, step)
yf = np.full((len(zs), len(xs)), np.nan); yb = yf.copy()
for i, z in enumerate(zs):
    for j, x in enumerate(xs):
        h = bv.ray_cast(Vector((x, 0.5, z)), Vector((0, -1, 0)), 1.0)
        if h[0] is None:
            continue
        yf[i, j] = h[0].y
        yb[i, j] = bv.ray_cast(Vector((x, -0.5, z)), Vector((0, 1, 0)), 1.0)[0].y
np.savez(P + "draft/raster.npz", xs=xs, zs=zs, yf=yf, yb=yb)
result = {"hits": int(np.isfinite(yf).sum())}
