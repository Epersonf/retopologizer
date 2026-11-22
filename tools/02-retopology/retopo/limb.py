"""limb: rings, tubes and bridges wrapped on the reference ("draw a circle around the arm, shrink it until it touches, bridge").
  wrap(ref, c, axis, n, mode="in")   -> (start, end): the circle of n points and where each point lands on the ref
        mode "in": circle bigger than the limb, every point shrinks toward the axis until it touches the first surface (shrinkwrap);
        mode "out": rays from the centre, the surface where each leaves the volume (same on convex sections)
  limb_ring(ref, c, axis, n, name)   one wrapped ring as an object
  ring_stations(length, radius, joints)  fractions 0..1 along a limb: denser around the joints (deformation), sparse on straight bone
  limb_tube(ref, a, b, stations, n, name, cap)  rings at the stations, centres following the limb, bridged, optional caps
  bridge(T, A, B)                    quads between two rings; different counts get triangles where one side has to wait
Every function returns Topo objects/vertex lists; run topo_qa after. `ref` is a Ref (retopo.ref)."""
import math
from mathutils import Vector
from .contour import align, centred, frame
from .curves import arc
from .topo import Topo
import numpy as np
from .profile import sample_profile, auto_stations, smooth
from .axes import station_axes, check_rings, flipped_faces


def circle(c, axis, up, n, r):
    a, u = frame(axis, up); w = a.cross(u)
    return [Vector(c) + (u * math.cos(2 * math.pi * k / n) + w * math.sin(2 * math.pi * k / n)) * r for k in range(n)]


def wrap(ref, c, axis, n=12, up=(0, 0, 1), mode="in", margin=1.6):
    c = centred(ref, c, axis, up); a, u = frame(axis, up)
    inner = arc(ref, c, a, u, 0.0, 360.0, n, "exit")[:-1]
    r = max((p - c).length for p in inner) * margin
    start = circle(c, a, up, n, r if mode == "in" else sum((p - c).length for p in inner) / n)
    if mode == "out":
        return start, inner
    end = []
    for s, f in zip(start, inner):
        h = ref.ray(s, c - s, 2 * r)
        # no hit from outside, or one that lands on a neighbour (torso next to the arm): keep the inside ray
        end.append(h[0] if h and (h[0] - c).length <= 1.25 * (f - c).length + 0.002 else f)
    return start, end


def limb_ring(ref, c, axis, n=12, name="Ring", mode="in"):
    T = Topo(ref); T.vs(wrap(ref, c, axis, n, mode=mode)[1], snap=False); T.write(name)
    return T


def ring_stations(length, radius, joints=(), per_joint=3, straight=1):
    """Fractions along the limb: both ends, `per_joint` rings around every joint fraction (spaced radius/2 apart) and `straight`
    rings between neighbours that are far apart."""
    h = 0.5 * radius / length; ts = {0.0, 1.0}
    for j in joints:
        ts |= {min(1.0, max(0.0, j + (k - (per_joint - 1) / 2) * h)) for k in range(per_joint)}
    ts = sorted(ts); out = []
    for a, b in zip(ts, ts[1:]):
        out.append(a); gap = b - a
        out += [a + gap * (k + 1) / (straight + 1) for k in range(straight)] if gap > 4 * h else []
    return out + [ts[-1]]


def _stations_data(P, ts):
    """Centres (smoothed centreline of the profile, jitter removed) and radii at the station fractions."""
    C = np.array([list(c) for c in P["c"]]); C = np.stack([smooth(C[:, q], 2) for q in range(3)], 1)
    return [Vector([float(np.interp(t, P["t"], C[:, q])) for q in range(3)]) for t in ts], [float(np.interp(t, P["t"], P["r"])) for t in ts]


def _rings(ref, c, r, d, theta, n, up, mode, k):
    ns = station_axes(c, r, d, theta, k); cs, loops, prev = [], [], None
    for ci, ni in zip(c, ns):
        ci = centred(ref, ci, ni, up); P = wrap(ref, ci, ni, n, up, mode)[1]
        P = align(P, prev) if prev else P
        prev = P; cs.append(ci); loops.append(P)
    return ns, cs, loops


def limb_tube(ref, a, b, stations=6, n=12, name="Tube", up=(0, 0, 1), cap=False, mode="in", joints=(), tol=0.06,
              max_rings=None, theta_max=10.0, k=1.5):
    """stations: a count, a list of fractions, or "auto" (extrema of the area profile + joints + error tolerance `tol`, see profile.py;
    `max_rings` = polygon budget: the least significant stations are dissolved first). Ring planes lean at most `theta_max` degrees
    from the limb axis and never cross (axes.py); if the check fails theta_max is halved until it passes (0 = parallel rings).
    The numbers of the check are in T.check; T.profile, T.centers are kept."""
    a, b = Vector(a), Vector(b); d = (b - a).normalized(); T = Topo(ref)
    T.profile = P = sample_profile(ref, a, b, up=up)
    if stations == "auto":
        stations = auto_stations(P, joints, tol=tol, n=n, max_rings=max_rings)
    ts = [i / (stations - 1) for i in range(stations)] if isinstance(stations, int) else list(stations)
    c0, r0 = _stations_data(P, ts); theta = theta_max
    while True:
        ns, cs, loops = _rings(ref, c0, r0, d, theta, n, up, mode, k)
        chk = check_rings(loops, cs, ns, r0, d); chk["theta_max_used"] = theta
        if chk["ok"] or theta < 0.5:
            break
        theta = theta / 2 if theta > 1 else 0.0
    rings = [T.vs(P_, snap=False) for P_ in loops]
    for r_a, r_b in zip(rings, rings[1:]):
        bridge(T, r_a, r_b)
    if cap:
        for ring, c in ((rings[0], cs[0]), (rings[-1], cs[-1])):
            T.fan(ring, c) if len(ring) % 2 == 0 else None
    T.orient(); T.write(name); T.centers = cs; T.check = chk; T.check["flipped_faces"] = flipped_faces(T, cs, ns)
    return T


def bridge(T, A, B):
    """Closed rings A and B joined by faces. Same count: quads (B is turned to the nearest start and direction first).
    Different counts: walk both rings by arc fraction; a quad when both advance, a triangle when one waits."""
    pa, pb = [Vector(v.co) for v in A], [Vector(v.co) for v in B]
    if len(A) == len(B):
        T.strip(A, B, closed=True); return
    k = min(range(len(B)), key=lambda i: (pb[i] - pa[0]).length); B = B[k:] + B[:k]
    i = j = 0; na, nb = len(A), len(B)
    while i < na or j < nb:
        ai, bj = (i + 1) / na, (j + 1) / nb
        if i < na and (j >= nb or ai <= bj + 1e-9):
            if j < nb and abs(ai - bj) < 1e-9:
                T.f(A[i % na], A[(i + 1) % na], B[(j + 1) % nb], B[j % nb]); i += 1; j += 1
            else:
                T.f(A[i % na], A[(i + 1) % na], B[j % nb]); i += 1
        else:
            T.f(A[i % na], B[(j + 1) % nb], B[j % nb]); j += 1
