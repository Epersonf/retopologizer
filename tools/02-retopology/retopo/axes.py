"""axes: ring planes that never cross and never lean away from the limb, plus the checks that prove it.
A ring is the section of the reference by a plane with normal n_i through the centre c_i. Two neighbouring planes (angle delta between
their normals, centres Delta apart) meet along a line about Delta/delta away from the centres; if that line is inside the limb
(Delta/delta < r) the rings overlap and the quads between them fold back (flipped normals). So, for every station:
  1. the angle between n_i and the limb axis d (a to b) stays <= theta_max        (a forearm points one way: no leaning rings)
  2. delta_i <= Delta_i / (k r_i)  with r_i = the larger radius of the pair, k = 1.5   (planes meet outside the limb, with margin)
  station_axes(c, r, d)  -> unit normals;  check_rings(T-free) -> numbers that must be positive / above 1 / within limits."""
import math
from mathutils import Vector


def angle(u, v):
    return math.acos(max(-1.0, min(1.0, u.dot(v))))


def toward(n, target, max_angle):
    """n rotated toward target until their angle is max_angle (unchanged when already closer)."""
    a = angle(n, target)
    return n.copy() if a <= max_angle else target.slerp(n, max_angle / a)


def tangents(c):
    """Unit tangents of the polyline of centres (central differences)."""
    out = []
    for i in range(len(c)):
        v = c[min(i + 1, len(c) - 1)] - c[max(i - 1, 0)]
        out.append(v.normalized() if v.length > 1e-9 else None)
    return [t if t is not None else (out[i - 1] if i else Vector((0, 0, 1))) for i, t in enumerate(out)]


def station_axes(c, r, d, theta_max=10.0, k=1.5):
    d = Vector(d).normalized(); th = math.radians(theta_max)
    n = [toward(t, d, th) for t in tangents(c)]
    for step in (1, -1):                                                      # forward, then backward pass
        for i in (range(1, len(n)) if step == 1 else range(len(n) - 2, -1, -1)):
            j = i - step
            delta_max = (c[i] - c[j]).length / (k * max(r[i], r[j]))
            n[i] = toward(n[i], n[j], delta_max)
    return n


def check_rings(rings, c, n, r, d):
    """rings: list of lists of Vectors. Returns the numbers that decide whether the tube is clean:
    axis_dev_deg (<= theta_max), step_deg, min_rung (rungs B_k - A_k along the mean axis: must be > 0 everywhere = no face goes back),
    min_cross_ratio ((Delta/delta)/r: must be >= 1 = planes do not meet inside the limb)."""
    d = Vector(d).normalized(); rung, ratio, step = 1e9, 1e9, 0.0
    for i in range(len(rings) - 1):
        m = (n[i] + n[i + 1]).normalized(); dl = angle(n[i], n[i + 1]); step = max(step, dl)
        rung = min(rung, min((q - p).dot(m) for p, q in zip(rings[i], rings[i + 1])))
        if dl > 1e-6:
            ratio = min(ratio, (c[i + 1] - c[i]).length / dl / max(r[i], r[i + 1]))
    return {"axis_dev_deg": round(max(math.degrees(angle(x, d)) for x in n), 2), "step_deg": round(math.degrees(step), 2),
            "min_rung_mm": round(rung * 1000, 2), "min_cross_ratio": round(ratio, 2), "ok": rung > 0 and ratio >= 1.0}


def flipped_faces(T, c, n):
    """Faces whose normal points toward the limb axis instead of away from it (after T.orient())."""
    bad = 0
    for f in T.bm.faces:
        fc = f.calc_center_median(); i = min(range(len(c)), key=lambda k: (fc - c[k]).length)
        o = (fc - c[i]) - n[i] * (fc - c[i]).dot(n[i])
        bad += f.normal.dot(o) < 0
    return bad
