"""Snap helpers da árvore: raio do centro para fora, pega o hit MAIS EXTERNO dentro de um
elipsoide limite (a referência tem cascas internas, então o primeiro hit engana).
Uso no Blender (MCP): exec(open(...).read())"""
import bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_o = bpy.data.objects["REF_tree_highpoly"]
BV = BVHTree.FromObject(_o, bpy.context.evaluated_depsgraph_get())


def all_hits(c, d, rmax=3.0):
    c, d = Vector(c), Vector(d).normalized(); out = []; o = c.copy(); tot = 0.0
    while tot < rmax:
        h = BV.ray_cast(o, d, rmax - tot)
        if h[0] is None:
            break
        tot += h[3] + 1e-4; o = h[0] + d * 1e-4; out.append((tot - 1e-4, Vector(h[0])))
    return out


def outer(c, d, bound=None):
    """Hit mais externo; `bound` = raios (rx,ry,rz) do elipsoide limite em torno de c."""
    best = None
    for t, p in all_hits(c, d):
        q = p - Vector(c)
        if bound and (q.x / bound[0]) ** 2 + (q.y / bound[1]) ** 2 + (q.z / bound[2]) ** 2 > 1:
            continue
        best = p
    return best


def sph(az, lat):
    a, l = math.radians(az), math.radians(lat)
    return Vector((math.cos(a) * math.cos(l), math.sin(a) * math.cos(l), math.sin(l)))
