"""Lid v5: hand-retopo style. Half of the lid (x >= 0) is built from rings whose vertices are
SNAPPED on the reference (REF_LID, lid-local space), then mirrored in X (Mirror + apply).
Needs a REF_LID object (reference faces near the lid, in lid-local space, identity transform).
  exec(open(ROOT+r"\tools\snap_retopo.py").read()); exec(open(this file).read()); build_lid_v5()
Section layout was measured on the reference (x along the hinge, y front=-, z up):
  centre strap |x|<0.055 (+14 mm), body, end block 0.225..0.31 (+22 mm), chamfer, end face x~0.326,
  cavity x<0.26 with a constant arch profile, rim plane z=0.06."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
C =(-0.23, 0.15)                                  # section centre (y, z), inside the cavity
A_OUT = [-18, 4, 21, 39, 65, 125, 153, 183, 198]   # corner angles of the outer arch (DP, eps 6 mm)
A_IN = [-18, 2, 22, 51, 129, 160, 175, 198]        # cavity corners
RIM = 0.06
XS = dict(strap=0.055, frame=0.225, end_in=0.31, end=0.326, cav=0.26)


def wall_y(S, x, back, z=0.09):
    """y of the front/back wall at height z (horizontal ray) - stable, unlike the 18-deg corner ray."""
    from mathutils import Vector
    o, d = ((0.6, -1) if back else (-0.7, 1))
    h = S.bv.ray_cast(Vector((x, o, z)), Vector((0, d, 0)), 1.5)
    return h[0].y if h[0] is not None else None


def ring_out(S, xs, xp):
    pts = [S.outer(xs, C, a) for a in A_OUT]
    pts = [(xp, p[0], p[1]) for p in pts]
    pts[0] = (xp, wall_y(S, xs, True), RIM); pts[-1] = (xp, wall_y(S, xs, False), RIM)
    return pts


def end_face_ring(S):
    """Outline of the flat end face: along each corner ray, outermost point whose x-ray hits x>0.318."""
    from mathutils import Vector
    out = []
    for a in A_OUT:
        d = Vector((0, math.cos(math.radians(a)), math.sin(math.radians(a)))); got = None
        for r in np.arange(0.62, 0.05, -0.002):
            y, z = C[0] + d.y * r, C[1] + d.z * r
            h = S.bv.ray_cast(Vector((0.6, y, z)), Vector((-1, 0, 0)), 1.0)
            if h[0] is not None and h[0].x > 0.318:
                got = (y, z); break
        out.append(got)
    pts = [(XS["end"], p[0], p[1]) for p in out]
    pts[0] = (XS["end"], pts[0][1], RIM); pts[-1] = (XS["end"], pts[-1][1], RIM)
    return pts


def ring_in(S, xp):
    pts = [S.inner(0.14, C, a) for a in A_IN]
    pts = [(xp, p[0], p[1]) for p in pts]
    pts[0] = (xp, pts[0][1], RIM); pts[-1] = (xp, pts[-1][1], RIM)
    return pts


def build_lid_v5(S=None):
    S = S or Surface("REF_LID"); M = Mesh()
    L = lambda pts: [M.v(p) for p in pts]
    s, f, e, ei, ee = XS["strap"], XS["frame"], XS["end"], XS["end_in"], XS["end"]
    band = ring_out(S, 0.14, 0)[-2:]                  # front band below the clasp (clasp is a separate slab)
    def strap(x, xp):
        p = ring_out(S, x, xp); p[-2:] = [(xp, b[1], b[2]) for b in band]; return p
    R0 = L(strap(0.0, 0.0)); R1 = L(strap(s - 0.005, s)); R2 = L(ring_out(S, s + 0.005, s))
    R3 = L(ring_out(S, f - 0.005, f)); R4 = L(ring_out(S, f + 0.005, f)); R5 = L(ring_out(S, ei, ei))
    R6 = L(end_face_ring(S))
    for a, b in ((R0, R1), (R1, R2), (R2, R3), (R3, R4), (R4, R5), (R5, R6)):
        M.strip(a, b)
    M.f(*R6[::-1])                                   # end face (n-gon)
    K0 = L(ring_in(S, 0.0)); K1 = L(ring_in(S, XS["cav"]))
    M.strip(K0, K1, flip=True); M.f(*K1)             # cavity wall + cavity end
    bmesh.ops.remove_doubles(M.bm, verts=M.bm.verts, dist=0.002); M.map = {}   # 2 mm sliver quads -> triangles
    M.mirror_x()
    bm = M.bm
    M.fill_flat_ring()                               # rim between outer and cavity loops
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)   # shell only: add-ons below are oriented by construction
    addons(S, M)
    return M


def addons(S, M):
    """Clasp (front, centre) and 4 corner rivets, as slabs standing on the shell."""
    from mathutils.bvhtree import BVHTree
    bm = M.bm; bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    sh = BVHTree.FromBMesh(bm)
    def snap(p, n):                                  # project a footprint point onto OUR shell along -n
        h = sh.ray_cast(Vector(p) + Vector(n) * 0.05, -Vector(n), 0.2)
        return h[0] if h[0] is not None else p
    yf = S.ray((0.15, -0.7, 0.10), (0, 1, 0), both=False, dist=1.0)[1]      # front band plane y
    ring = [(-0.062, yf, 0.065), (0.062, yf, 0.065), (0.05, yf, 0.14), (-0.05, yf, 0.14)]
    top = M.prism(ring, (0, -1, 0), 0.023, top_scale=0.92, closed_top=False, snap=snap)
    ctr = sum((v.co for v in top), Vector()) / 4
    frame = [M.v(tuple(ctr + (v.co - ctr) * 0.62)) for v in top]
    for i in range(4):
        j = (i + 1) % 4; M.f(top[i], top[j], frame[j], frame[i])
    M.dimple(frame, 0.01, 0.8)
    for sx in (-1, 1):
        for (y0, d, z) in ((-0.7, (0, 1, 0), 0.108), (0.6, (0, -1, 0), 0.139)):
            x = 0.285 * sx
            hit = S.ray((x, y0, z), d, both=False, dist=1.0)
            n = (0, -d[1], 0)
            ring = Mesh.ngon(hit, n, (0, 0, 1), 0.021)
            M.prism(ring, n, 0.009, top_scale=0.65, snap=snap)
