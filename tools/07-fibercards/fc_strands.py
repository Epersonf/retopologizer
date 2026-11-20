"""The strands of one card: a port of src/hair/* of fiber-card-gen (mulberry32, spawn disk, spread/clump, curl, frizz, centripetal Catmull-Rom).
Card space: x across (0 = the middle of the cell), y up from the bottom edge of the cell, z toward the camera. The noise is a value-noise fbm (the app uses
open-simplex-noise), so frizz differs in detail, not in kind. strands(seed, n, cellW, cellH, s, step=2.5) -> [(P [m,3] points every `step` px along the strand, radius [m] px)]."""
import math
import numpy as np
M32 = 0xFFFFFFFF


def mulberry32(seed):
    a = [seed & M32]

    def rnd():
        a[0] = (a[0] + 0x6D2B79F5) & M32; x = a[0]
        t = ((x ^ (x >> 15)) * (1 | x)) & M32
        t = (t ^ (t + (((t ^ (t >> 7)) * (61 | t)) & M32))) & M32
        return ((t ^ (t >> 14)) & M32) / 4294967296
    return rnd


def _hash(ix, iy, seed=0):
    h = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & M32; h = ((h ^ (h >> 13)) * 1274126177) & M32
    return ((h ^ (h >> 16)) & M32) / 4294967296 * 2 - 1


def noise2(x, y):
    ix, iy = math.floor(x), math.floor(y); fx, fy = x - ix, y - iy; u, v = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = _hash(ix, iy), _hash(ix + 1, iy), _hash(ix, iy + 1), _hash(ix + 1, iy + 1)
    return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v


def fbm2(x, y, octaves=4):
    v = amp = s = 0.0; amp = 0.5
    for _ in range(octaves):
        v += amp * noise2(x, y); s += amp; x *= 2; y *= 2; amp *= 0.5
    return v / s * 0.5 + 0.5


def radius_px(thickness, cellW):
    return max(0.25, thickness * cellW * 0.20)


def padding(cellW, cellH, s):
    r = max(radius_px(s["root_thickness"], cellW), radius_px(s["tip_thickness"], cellW)); pad = cellH * 0.09 + r
    return pad, max(1.0, cellH - 2 * pad)


def curve_points(pts, alpha=0.5):                                         # centripetal Catmull-Rom through pts (ends extrapolated as three.js does), dense
    P = np.vstack([2 * pts[0] - pts[1], pts, 2 * pts[-1] - pts[-2]]); out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t0 = 0.0; t1 = t0 + max(np.linalg.norm(p1 - p0), 1e-6) ** alpha; t2 = t1 + max(np.linalg.norm(p2 - p1), 1e-6) ** alpha; t3 = t2 + max(np.linalg.norm(p3 - p2), 1e-6) ** alpha
        t = np.linspace(t1, t2, 24, endpoint=False)[:, None]
        a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1; a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2; a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
        b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2; b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
        out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    out.append(pts[-1][None]); return np.vstack(out)


def strand(rnd, cellW, cellH, s, step=2.5):
    n = max(2, int(s["strand_points_count"])); t = np.arange(n) / (n - 1); pad, usableH = padding(cellW, cellH, s)
    L = s["combined_length"] if s["fixed_length_size"] else s["minimum_length"] + (s["maximum_length"] - s["minimum_length"]) * rnd()
    local = (0.1 + 0.9 * min(max(L / 20.0, 0), 1)) * usableH; yTop = pad + usableH
    tilt = math.radians(s["spawn_tilt_deg"]); rx, rz = s["spawn_radius_ratio_x"] * cellW, s["spawn_radius_ratio_y"] * cellW
    u, v = rnd(), rnd(); r = math.sqrt(u); ang = 2 * math.pi * v; px, pz = math.cos(ang) * r * rx, math.sin(ang) * r * rz
    base = np.array([px, yTop + pz * math.sin(tilt), pz * math.cos(tilt)]) if s["spawn_enabled"] else np.array([0.0, yTop, 0.0])
    rk = np.array([(rnd() - 0.5) * 2 for _ in range(3)])
    phase, az, fj, aj = 2 * math.pi * rnd(), 2 * math.pi * rnd(), 1 + 0.15 * (rnd() - 0.5), 1 + 0.25 * (rnd() - 0.5); ox, oy = rnd() * 1000, rnd() * 1000
    pts = []
    for i, tt in enumerate(t):
        y = min(max(base[1] - tt * local, pad), yTop)
        c = (s["clump_root"] + (s["clump_tip"] - s["clump_root"]) * tt) / 1000; sc = (tt ** s["hairline_shape"] if tt > 0 or s["hairline_shape"] == 0 else 0.0) * c * s["spread_amount_offset"]
        off = np.array([rk[0] * sc * 1.5, 0.0, rk[2] * sc * 1.5])
        if s["enable_hair_curl"]:
            th = ((s["curl_shape"] + s["curl_count"]) * 2 * math.pi) * fj * tt + phase; amp = s["curl_amount"] * s["curl_scale"] * aj
            cx, cz = math.sin(th) * amp * tt, math.sin(th + math.pi / 2) * amp * tt; off += np.array([cx * math.cos(az) + cz * math.sin(az), 0.0, -cx * math.sin(az) + cz * math.cos(az)])
        if s["enable_frizz_hair"]:
            k = s["frizz_scale"] * (np.interp(tt, [p["x"] for p in s["frizz_curve_points"]], [p["y"] for p in s["frizz_curve_points"]]) if s["frizz_curve_enabled"] else 1)
            c2 = 2 * fbm2(i + ox, s["messiness_scale"] * tt * L + oy) - 1; off += np.array([c2 * k, 0.0, c2 * k])
        pts.append([base[0] + off[0], y, base[2] + off[2]])
    P = curve_points(np.array(pts)); seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    m = max(2, int(seg[-1] / step)); q = np.linspace(0, seg[-1], m); P = np.column_stack([np.interp(q, seg, P[:, j]) for j in range(3)])
    f = np.linspace(0, 1, m); return P, radius_px(s["root_thickness"], cellW) * (1 - f) + radius_px(max(0, s["tip_thickness"]), cellW) * f


def strands(seed, count, cellW, cellH, s, step=2.5):
    rnd = mulberry32(seed); return [strand(rnd, cellW, cellH, s, step) for _ in range(count)]
