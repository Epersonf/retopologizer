"""Wing handle ("cabo"): simple separate shapes made only of quads (collar, neck, plate, eye, arm, spine). Coordinates in metres on the wing's front view.
`uv_mm(u, v)` converts the hillshade pixel grid used while measuring (2 px per mm unit: x = -0.46 + u/1000, z = 0.6 - v/1000) to metres.
Why these shapes: they are the silhouette + volume the game needs; the engraved detail comes later from texel_paint (examples/wing/pattern_cabo.py).
The arm and the spine START INSIDE the plate and the plate is taller than the bars, so no flat bar end pokes out of it (a visible defect we fixed once)."""
import numpy as np


def cylinder(c, axis, r, length, sides=8, rings=2, cap_a=True, cap_b=True):
    a = np.array(axis, float); a /= np.linalg.norm(a); h = np.array([0, -1., 0]) if abs(a[1]) < .9 else np.array([1., 0, 0])
    u = np.cross(a, h); u /= np.linalg.norm(u); w = np.cross(a, u); V = []; F = []
    for k in range(rings):
        t = (k / (rings - 1) - .5) * length
        for s in range(sides):
            ang = 2 * np.pi * s / sides; V.append(np.array(c) + a * t + r * (np.cos(ang) * u + np.sin(ang) * w))
    for k in range(rings - 1):
        for s in range(sides):
            F.append([k * sides + s, k * sides + (s + 1) % sides, (k + 1) * sides + (s + 1) % sides, (k + 1) * sides + s])

    def cap(k):      # cap = centre vertex + quads (no n-gon, no triangles)
        t = (k / (rings - 1) - .5) * length; o = len(V); V.append(np.array(c) + a * t)
        for q in range(sides // 2):
            i = 2 * q; F.append([o, k * sides + i, k * sides + (i + 1) % sides, k * sides + (i + 2) % sides])
    if cap_a:
        cap(0)
    if cap_b:
        cap(rings - 1)
    return V, F


def bar(pts, widths, thick):
    V = []; F = []; pts = [np.array(p, float) for p in pts]; yh = np.array([0, -1., 0])
    for i, p in enumerate(pts):
        t = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]; t /= np.linalg.norm(t); wd = np.cross(t, yh); wd /= np.linalg.norm(wd)
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            V.append(p + sx * widths[i] / 2 * wd + sy * thick / 2 * yh)
    for i in range(len(pts) - 1):
        for s in range(4):
            F.append([i * 4 + s, i * 4 + (s + 1) % 4, (i + 1) * 4 + (s + 1) % 4, (i + 1) * 4 + s])
    n = (len(pts) - 1) * 4; F.append([0, 1, 2, 3]); F.append([n, n + 1, n + 2, n + 3])
    return V, F


uv_mm = lambda u, v: (-0.46 + u / 1000, 0.6 - v / 1000)
ARM_PX = [(135, 235), (185, 200), (225, 165), (252, 130), (280, 100), (320, 65), (370, 47), (440, 30), (505, 17)]; ARM_W = [40, 46, 48, 46, 40, 34, 28, 22, 14]   # width in mm
SPINE_PX = [(115, 262), (105, 300), (80, 380), (60, 455)]; SPINE_W = [36, 40, 30, 20]


def support_parts(front_y):
    """front_y(x, z) -> Y of the reference front surface (depth_map.sampler). Returns [(name, V, F)]."""
    cx, cz = uv_mm(30, 235); yc = min(front_y(-0.43, cz), front_y(-0.41, cz)) + 0.048; px, pz = uv_mm(117, 255); yp = front_y(px, pz) + 0.012
    nx, nz = uv_mm(78, 245); ex, ez = uv_mm(160, 278)
    P = [("SUP_collar",) + cylinder((cx, yc, cz), (1, 0, 0), 0.048, 0.05, 8, 3), ("SUP_neck",) + cylinder((nx, 0.5 * (yc + yp), nz), (1, 0, 0), 0.032, 0.06, 8, 2),
         ("SUP_plate",) + cylinder((px, yp, pz), (0, 1, 0), 0.05, 0.07, 8, 2), ("SUP_eye",) + cylinder((ex, yp, ez), (0, 1, 0), 0.018, 0.03, 8, 2)]
    ap = [(uv_mm(*p)[0], yp if i == 0 else front_y(*uv_mm(*p)) + 0.009, uv_mm(*p)[1]) for i, p in enumerate(ARM_PX)]
    sp = [(uv_mm(*p)[0], yp if i == 0 else front_y(*uv_mm(*p)) + 0.008, uv_mm(*p)[1]) for i, p in enumerate(SPINE_PX)]
    return P + [("SUP_arm",) + bar(ap, [w / 1000 for w in ARM_W], 0.03), ("SUP_spine",) + bar(sp, [w / 1000 for w in SPINE_W], 0.03)]
