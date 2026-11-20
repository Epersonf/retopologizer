"""Cross-section overlay (reference in colour, low-poly in white) as a PNG - the quickest way to
see where a hand-retopo ring misses the reference. Same local space for both objects.
  exec(open(...).read()); section_overlay("REF_LID", "LID_NEW", [0.0, 0.14, 0.28], path,
                                          axis=0, box=((-0.52, 0.06), (-0.03, 0.34)))
axis 0 = sections at x (plot y,z); axis 1 = at y (plot x,z); axis 2 = at z (plot x,y)."""
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

COLS = [(1, .35, .35), (.4, 1, .4), (.4, .6, 1), (1, 1, .3), (1, .5, 1)]


def _hits(bv, axis, val, box, step):
    (a0, a1), (b0, b1) = box; pts = []
    i, j = [k for k in range(3) if k != axis]
    for sweep in (0, 1):
        rng = np.arange(b0, b1, step) if sweep == 0 else np.arange(a0, a1, step)
        for t in rng:
            o = [0, 0, 0]; d = [0, 0, 0]; o[axis] = val
            if sweep == 0:
                o[i] = a0 - 0.3; o[j] = t; d[i] = 1
            else:
                o[j] = b0 - 0.3; o[i] = t; d[j] = 1
            o, d = Vector(o), Vector(d)
            while True:
                h = bv.ray_cast(o, d, 3.0)
                if h[0] is None:
                    break
                pts.append((h[0][i], h[0][j])); o = h[0] + d * 1e-4
    return pts


def section_overlay(ref, new, vals, path, axis=0, box=((-0.52, 0.06), (-0.03, 0.34)), scale=1500, step=0.002):
    (a0, a1), (b0, b1) = box
    W, H = int((a1 - a0) * scale) + 20, int((b1 - b0) * scale) + 20
    img = np.zeros((H, W, 3), np.float32) + 0.08
    bvs = []
    for n in (ref, new):
        o = bpy.data.objects[n]; me = o.data; me.calc_loop_triangles()
        bvs.append(BVHTree.FromPolygons([tuple(o.matrix_world @ v.co) for v in me.vertices],
                                        [tuple(t.vertices) for t in me.loop_triangles]))

    def put(p, col):
        u = int(10 + (p[0] - a0) * scale); v = H - 10 - int((p[1] - b0) * scale)
        for du in (0, 1):
            for dv in (0, 1):
                if 0 <= u + du < W and 0 <= v + dv < H:
                    img[v + dv, u + du] = col
    for k, val in enumerate(vals):
        for p in _hits(bvs[0], axis, val, box, step):
            put(p, COLS[k % 5])
        for p in _hits(bvs[1], axis, val, box, step / 2):
            put(p, (1, 1, 1))
    a = np.ones((H, W, 4), np.float32); a[..., :3] = img[::-1]
    im = bpy.data.images.new("_sec", W, H); im.pixels.foreach_set(a.ravel())
    im.filepath_raw = path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
    return path
