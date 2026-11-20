"""Tail, horns, ears, udder, teats: small shells made of snapped rings (same method as torso/legs)."""
import bpy, numpy as np
from mathutils import Vector


def loft(S, M, stations, n, up, maxr=0.1, cap_end=True, cap_start=True, start_k=0.0):
    """stations = [(centre, axis)] ; closed rings snapped by raycast, re-centred once."""
    R = []
    for c, ax in stations:
        pts = ring(S, c, ax, up, n, maxr=maxr); cc = sum((Vector(p) for p in pts), Vector()) / n
        R.append([M.v(p) for p in ring(S, cc, ax, up, n, maxr=maxr)])
    for a, b in zip(R, R[1:]):
        M.strip_closed(a, b)
    if cap_start:
        M.cap(R[0], flip=True)
    if cap_end:
        M.cap(R[-1])
    return R


def tail(S, M):
    """Thin tube (5-gon rings) from the rump to the tuft, tuft = 6-gon rings + tip fan. Path measured by x-rays per z."""
    path = [(-0.470, 0.47), (-0.485, 0.44), (-0.499, 0.42), (-0.511, 0.40), (-0.523, 0.38), (-0.535, 0.355),
            (-0.553, 0.335), (-0.560, 0.305), (-0.562, 0.275), (-0.571, 0.245)]
    k = [5] * 6 + [6] * 4
    R = [[M.v(p) for p in ring(S, (x, 0.017, z), (0, 0, 1), (1, 0, 0), k[i], maxr=0.08)] for i, (x, z) in enumerate(path)]
    for i in range(5):
        M.strip_closed(R[i], R[i + 1], flip=True)
    for i in range(6, 9):
        M.strip_closed(R[i], R[i + 1], flip=True)
    # 5-gon -> 6-gon neck of the tuft: fan ring 5 into ring 6 (one triangle extra) via a tri-strip
    A, B = R[5], R[6]
    for i in range(5):
        M.f(A[i], A[(i + 1) % 5], B[(i + 1) % 6], B[i])
    M.f(A[0], B[5], B[0])
    M.cap(R[0])
    M.cap(R[-1], centre=S.ray((-0.571, 0.017, 0.30), (0, 0, -1), both=False, dist=0.2), flip=True)
    return R


def horns(S, M):
    for base, tip in (((0.346, 0.066, 0.772), (0.353, 0.080, 0.841)), ((0.300, -0.080, 0.772), (0.250, -0.114, 0.840))):
        b, t = Vector(base), Vector(tip); ax = (t - b).normalized()
        loft(S, M, [(b + (t - b) * f, ax) for f in (0.0, 0.4, 0.75)], 6, (1, 0, 0), maxr=0.05)


def teats(S, M):
    for x in (-0.24, -0.18):
        for y in (-0.01, 0.045):
            R = [[M.v((x + r * np.cos(2 * np.pi * i / 4), y + r * np.sin(2 * np.pi * i / 4), z)) for i in range(4)]
                 for z, r in ((0.185, 0.012), (0.165, 0.009), (0.148, 0.006))]
            for a, b in zip(R, R[1:]):
                M.strip_closed(a, b, flip=True)
            M.cap(R[0]); M.cap(R[-1], flip=True)


EARS = (dict(x=(0.10, 0.28), y=(-1, -0.14), z=(0.58, 1)),       # ear flap on -y (points back along the neck)
        dict(x=(0.30, 0.42), y=(0.14, 1), z=(0.60, 1)))         # ear flap on +y (points sideways)


def ears(S, M, ref_name="REFERENCE", n=6, stations=5):
    ref = bpy.data.objects[ref_name]; k = len(ref.data.vertices)
    a = np.empty(k * 3, np.float32); ref.data.vertices.foreach_get("co", a); a = a.reshape(-1, 3)
    for r in EARS:
        s = a[(a[:, 0] >= r["x"][0]) & (a[:, 0] <= r["x"][1]) & (a[:, 1] >= r["y"][0]) & (a[:, 1] <= r["y"][1])
              & (a[:, 2] >= r["z"][0]) & (a[:, 2] <= r["z"][1])].astype(np.float64)
        c0 = s.mean(0); _, _, vt = np.linalg.svd(s[::20] - c0, full_matrices=False)
        ax, up = Vector(vt[0]), Vector(vt[1]); t = (s - c0) @ vt[0]; lo, hi = t.min(), t.max()
        ts = [lo + (hi - lo) * (0.06 + 0.88 * i / (stations - 1)) for i in range(stations)]
        loft(S, M, [(Vector(c0) + ax * q, ax) for q in ts], n, up, maxr=0.12)
