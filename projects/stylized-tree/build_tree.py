"""Retopo manual da árvore: anéis em torno de eixos, cada vértice colado na referência (snap).
Roda no Blender (MCP). Depois do UV do usuário NÃO rodar de novo (recria a malha)."""
import bpy, statistics
from mathutils import Vector
_P = r"C:\Users\epers\Desktop\retopologizer\projects\stylized-tree"
exec(open(_P + r"\snap_tree.py").read())
exec(open(_P + r"\build_branch.py").read())
exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\snap_mesh.py").read())


def snap_pt(c, d, bound, ref_r):
    """Hit mais externo; se faltar ou for outlier, cai no ponto mais próximo da ref no raio mediano."""
    p = outer(c, d, bound); c = Vector(c)
    if p is not None and (p - c).length < 1.35 * ref_r:
        return tuple(p)
    q = c + Vector(d).normalized() * ref_r
    r = BV.find_nearest(q, 0.3)
    return tuple(r[0]) if r[0] is not None else tuple(q)


def ring_pts(c, bound, az_list, lat):
    raw = [outer(c, sph(a, lat), bound) for a in az_list]
    rs = [(p - Vector(c)).length for p in raw if p is not None]
    med = statistics.median(rs) if rs else 0.3
    return [snap_pt(c, sph(a, lat), bound, med) for a in az_list]


def canopy(name, c, bound, n=10, lats=(-25, 15, 55), rot=0.0):
    m = Mesh(); azs = [rot + 360.0 * i / n for i in range(n)]
    R = [[m.v(p) for p in ring_pts(c, bound, azs, la)] for la in lats]
    for lo, hi in zip(R, R[1:]):
        m.strip_closed(lo, hi)
    def pole(ring, dz):  # polo colado na ref perto do centro do anel (o raio vertical pegava calombos)
        k = sum((Vector(v.co) for v in ring), Vector()) / len(ring) + Vector((0, 0, dz))
        d = Vector((0, 0, -1 if dz > 0 else 1)); h = BV.ray_cast(k - d * 0.2, d, 0.4)
        if h[0] is None or abs(h[0].z - k.z) > abs(dz) + 0.03:  # calombo/casca interna: fica achatado
            return tuple(k)
        return tuple(h[0])  # só sobe/desce na vertical: o polo não anda de lado
    top = pole(R[-1], 0.06); bot = pole(R[0], -0.05)
    m.cap(R[-1], top); m.cap(R[0], bot, flip=True)
    return m.to_object(name)


def ring_h(c, z, az_list, b):
    """Anel horizontal do tronco na altura z, centrado em c=(x,y)."""
    o = (c[0], c[1], z); bd = (b, b, 0.03)
    med = statistics.median([(outer(o, sph(a, 0), bd) - Vector(o)).length
                             for a in az_list if outer(o, sph(a, 0), bd)] or [0.15])
    return [snap_pt(o, sph(a, 0), bd, med * 1.6) for a in az_list]


def trunk(name="tree_trunk"):
    m = Mesh(); a12 = [30.0 * i for i in range(12)]; a6 = [60.0 * i for i in range(6)]
    A0 = [m.v(p) for p in ring_h((-0.02, -0.10), 0.02, a12, 0.7)]
    A1 = [m.v(p) for p in ring_h((-0.015, -0.11), 0.12, a12, 0.6)]
    B = [m.v(p) for p in ring_h((-0.02, -0.15), 0.27, a6, 0.35)]
    C = [m.v(p) for p in ring_h((-0.05, -0.18), 0.5, a6, 0.25)]
    D = [m.v(p) for p in ring_h((-0.03, -0.15), 0.75, a6, 0.25)]
    m.f(*A0[::-1]); m.strip_closed(A0, A1)
    for i in range(6):  # 12 -> 6: quad + triângulo por setor
        j = (i + 1) % 6
        m.f(A1[2 * i], A1[2 * i + 1], A1[(2 * i + 2) % 12], B[i])
        m.f(A1[(2 * i + 2) % 12], B[j], B[i])
    m.strip_closed(B, C); m.strip_closed(C, D)
    # tronco superior: continua o anel D inclinando para +y até a copa grande
    R = tube_rings(m, [(-0.03, -0.15, 0.75), (0.0, -0.10, 1.0), (0.05, 0.05, 1.25), (0.1, 0.28, 1.5)],
                   [0.13, 0.11, 0.09, 0.08], 6, tol=0.05)[1:]
    prev = D
    for r in R:
        m.strip_closed(prev, r); prev = r
    m.f(*prev)
    return m.to_object(name)
