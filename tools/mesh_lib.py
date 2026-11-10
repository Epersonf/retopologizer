"""Low-poly construction helpers (bmesh). Use via exec(open(...).read()) inside Blender.
All builders return bmesh data appended to a shared bm; finish with to_object().
Conventions: Z up, front = -Y, units = meters.
"""
import bpy, bmesh, math
from mathutils import Vector


def new_bm():
    return bmesh.new()


def to_object(bm, name, collection=None, smooth=False):
    """Write bm to a new mesh/object named `name` (replaces existing)."""
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old)
    old_me = bpy.data.meshes.get(name)
    if old_me:
        bpy.data.meshes.remove(old_me)
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def quad(bm, a, b, c, d):
    return bm.faces.new((a, b, c, d))


def box(bm, lo, hi, skip=()):
    """Axis aligned box lo..hi. skip: face names among -x,+x,-y,+y,-z,+z."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    v = [bm.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    f = {"-z": (0, 3, 2, 1), "+z": (4, 5, 6, 7), "-y": (0, 1, 5, 4),
         "+y": (2, 3, 7, 6), "-x": (0, 4, 7, 3), "+x": (1, 2, 6, 5)}
    for k, idx in f.items():
        if k not in skip:
            bm.faces.new([v[i] for i in idx])
    return v


def loft(bm, rings, closed_ring=True, cap_start=True, cap_end=True):
    """Bridge a list of vertex-position rings (each a list of (x,y,z), same length)."""
    vr = [[bm.verts.new(p) for p in r] for r in rings]
    n = len(vr[0])
    for a, b in zip(vr, vr[1:]):
        for i in range(n if closed_ring else n - 1):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_start:
        bm.faces.new(vr[0][::-1])
    if cap_end:
        bm.faces.new(vr[-1])
    return vr


def rect_sweep(bm, x0, x1, y0, y1, profile, cap_bottom=True, cap_top=True):
    """Sweep a (offset, z) profile around the rectangle [x0,x1]x[y0,y1].
    Each profile point -> a 4 vertex ring expanded by `offset` (negative = inward)."""
    rings = []
    for d, z in profile:
        rings.append([(x0 - d, y0 - d, z), (x1 + d, y0 - d, z),
                      (x1 + d, y1 + d, z), (x0 - d, y1 + d, z)])
    return loft(bm, rings, cap_start=cap_bottom, cap_end=cap_top)


def prism(bm, pts2d, z0, z1, plane="xy"):
    """Extrude a convex 2D polygon (list of (a,b)) between z0,z1 along the missing axis.
    plane 'xy' extrudes along z; 'xz' along y; 'yz' along x."""
    def p(a, b, c):
        return {"xy": (a, b, c), "xz": (a, c, b), "yz": (c, a, b)}[plane]
    lo = [bm.verts.new(p(a, b, z0)) for a, b in pts2d]
    hi = [bm.verts.new(p(a, b, z1)) for a, b in pts2d]
    n = len(lo)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    return lo, hi


def pentagon(r, rot=90):
    return [(r * math.cos(math.radians(rot + 72 * i)),
             r * math.sin(math.radians(rot + 72 * i))) for i in range(5)]
