"""Front and back depth maps of a relief-like reference (wing, shield, plaque): the Y of the first surface hit from the front (F) and from the back (B).
Inside Blender (one-shot is fine):  exec(open(...).read());  depth_map("REFERENCE", "depth.npz", x=(-0.46, 0.64), z=(0.0, 0.60), step=0.002)
Saved: xs, zs (metres, grid `step`), F, B (rows = z, columns = x, NaN where the ray missed). Use it to:
  - sample the front surface under a hand-made skin (`F`) and the reference back (`B`) to choose the mirror plane of skin_close.close_skin,
  - place separate parts (handle, frame) on the surface, - measure where the retopo is off the reference.
The reference is only read (BVH from a copy of its triangles); it is never edited."""
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def depth_map(ref_name, path, x=(-0.5, 0.5), z=(0.0, 1.0), step=0.002, y_out=0.2):
    o = bpy.data.objects[ref_name]; me = o.data; n = len(me.vertices); co = np.empty(n * 3, np.float32); me.vertices.foreach_get("co", co)
    mw = np.array(o.matrix_world); co = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    me.calc_loop_triangles(); t = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", t)
    bvh = BVHTree.FromPolygons([tuple(v) for v in co.tolist()], t.reshape(-1, 3).tolist())
    xs = np.arange(x[0], x[1], step); zs = np.arange(z[0], z[1], step); F = np.full((len(zs), len(xs)), np.nan, np.float32); B = F.copy()
    for j, zz in enumerate(zs):
        for i, xx in enumerate(xs):
            h = bvh.ray_cast(Vector((xx, -y_out, zz)), Vector((0, 1, 0)))
            if h[0] is None:
                continue
            F[j, i] = h[0].y; h2 = bvh.ray_cast(Vector((xx, y_out, zz)), Vector((0, -1, 0)))
            B[j, i] = h2[0].y if h2[0] is not None else np.nan
    np.savez(path, xs=xs, zs=zs, F=F, B=B); return {"shape": F.shape, "hit": int((~np.isnan(F)).sum())}


def sampler(npz, which="F", window=3, reduce=np.nanmin):
    """Returns f(x, z) -> depth Y from the saved map (min of a (2*window+1) px window by default; falls back to -0.02 outside the map)."""
    d = np.load(npz); xs, zs, A = d["xs"], d["zs"], d[which]; step = xs[1] - xs[0]

    def f(x, z):
        i = int(round((x - xs[0]) / step)); j = int(round((z - zs[0]) / step)); w = A[max(j - window, 0):j + window + 1, max(i - window, 0):i + window + 1]
        return float(reduce(w)) if np.isfinite(w).any() else -0.02
    return f
