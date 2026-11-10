"""Print bbox of an object's vertices per slice along an axis (numpy, no edit mode).
Run inside Blender: exec(open(...).read()); r = slice_profile(name, axis=2, step=0.04)
Optional filters: region=(axis, lo, hi) to restrict vertices first.
"""
import bpy, numpy as np

def verts_world(name):
    o = bpy.data.objects[name]
    n = len(o.data.vertices)
    a = np.empty(n * 3, dtype=np.float32)
    o.data.vertices.foreach_get("co", a)
    a = a.reshape(-1, 3)
    m = np.array(o.matrix_world, dtype=np.float32)
    return a @ m[:3, :3].T + m[:3, 3]

def slice_profile(name, axis=2, step=0.04, region=None, minpts=50):
    v = verts_world(name)
    if region:
        ax, lo, hi = region
        v = v[(v[:, ax] >= lo) & (v[:, ax] <= hi)]
    out = []
    z0 = v[:, axis].min(); z1 = v[:, axis].max()
    k = z0
    while k < z1:
        s = v[(v[:, axis] >= k) & (v[:, axis] < k + step)]
        if len(s) > minpts:
            out.append([round(float(k), 3), len(s)] +
                       [round(float(x), 3) for x in (*s.min(0), *s.max(0))])
        k += step
    return out  # [start, count, minx,miny,minz, maxx,maxy,maxz]
