"""profile: where along a limb do rings have to go. The cross-section area A(t) is sampled densely, smoothed and differentiated;
rings go where the shape changes direction (local maxima and minima of A, the sign changes of dA/dt), at the joints, and wherever a
straight line between neighbouring rings would miss the profile by more than a tolerance (piecewise-linear error control).
  P = sample_profile(ref, a, b, m=80)                     -> dict t, c (centres), A, r (equivalent radius sqrt(A/pi)), axis
  ex = extrema(P["t"], P["r"], prominence=0.05)           -> [(index, "max"|"min")], zigzag smaller than 5% of the mean radius dropped
  ts = auto_stations(P, joints=(), per_joint=3, tol=0.06) -> station fractions 0..1 (extrema + joints + error refinement)
Exactness: every local extremum with prominence >= `prominence` is a station, and between stations |r(t) - line| <= tol x mean(r) and no gap is longer than `max_aspect` quad widths (2 pi r / n)."""
import math
import numpy as np
from mathutils import Vector
from .contour import centred, frame
from .curves import arc


def sample_profile(ref, a, b, m=80, up=(0, 0, 1), dense=48):
    a, b = Vector(a), Vector(b); d = (b - a).normalized()
    ts, cs, As, pc = np.linspace(0, 1, m), [], [], None
    for t in ts:
        c = a + (b - a) * float(t)
        ax = d if pc is None or (c - pc).length < 1e-6 else (c - pc).normalized()
        c = centred(ref, c, ax, up); ax_, u = frame(ax, up); w = ax_.cross(u)
        P = arc(ref, c, ax_, u, 0.0, 360.0, dense, "exit")[:-1]
        x = np.array([(p - c).dot(u) for p in P]); y = np.array([(p - c).dot(w) for p in P])
        As.append(abs(float((x * np.roll(y, -1) - np.roll(x, -1) * y).sum()) / 2))     # shoelace area of the section
        cs.append(c.copy()); pc = c
    A = np.array(As); raw = np.sqrt(A / math.pi)
    return {"t": ts, "c": cs, "A": A, "raw": raw, "r": despike(raw), "length": (b - a).length}


def despike(y, w=5):
    """Median of w samples: a section that jumps for one or two samples (a ray leaving through the crease of the elbow, a thumb)
    is a measuring artefact, not a shape; a real bulge is wider than w/2 samples (w/2 x 1/m of the limb) and survives."""
    p = np.pad(y, w // 2, mode="edge"); return np.median(np.lib.stride_tricks.sliding_window_view(p, w), axis=1)


def smooth(y, k=1):
    if k <= 0 or len(y) < 3:
        return np.asarray(y, float)
    p = np.pad(y, k, mode="edge"); return np.convolve(p, np.ones(2 * k + 1) / (2 * k + 1), "valid")


def extrema(t, r, prominence=0.05, k=2):
    """Local maxima/minima of r(t): sign changes of the derivative of the smoothed profile; a zigzag smaller than
    `prominence x mean(r)` is noise and is dropped (extrema must alternate)."""
    s = smooth(r, k); d = np.gradient(s, t); sg = np.sign(np.where(np.abs(d) < 1e-9, 0, d)); cand = []
    last = 0
    for i in range(len(sg)):
        if sg[i] == 0:
            continue
        if last and sg[i] != last:
            cand.append((i, "max" if last > 0 else "min"))
        last = sg[i]
    thr, out = prominence * float(np.mean(r)), []
    for i, kind in cand:
        if out and abs(s[i] - s[out[-1][0]]) < thr:
            out.pop(); continue                                     # too small a wiggle: drop both ends of it
        out.append((i, kind))
    return out


def _refine(t, r, lo, hi, tol, keep):
    if hi - lo < 2:
        return
    line = r[lo] + (r[hi] - r[lo]) * (t[lo:hi + 1] - t[lo]) / (t[hi] - t[lo]); err = np.abs(r[lo:hi + 1] - line)
    k = int(np.argmax(err))
    if err[k] > tol:
        keep.add(lo + k); _refine(t, r, lo, lo + k, tol, keep); _refine(t, r, lo + k, hi, tol, keep)


def dissolve(t, r, ts, target, protect=()):
    """Remove stations one by one until `target` are left. The cost of removing a station is the largest deviation of the profile
    from the straight line between its two neighbours, so a small bump goes before a big one (a level of detail that is exact and
    monotone: the more you dissolve, the larger the guaranteed error). Both ends and `protect` (the joint centres) stay."""
    ts = list(ts)
    def cost(k):
        i0, i1, i2 = (int(np.argmin(np.abs(t - ts[q]))) for q in (k - 1, k, k + 1))
        line = r[i0] + (r[i2] - r[i0]) * (t[i0:i2 + 1] - t[i0]) / max(t[i2] - t[i0], 1e-9)
        return float(np.max(np.abs(r[i0:i2 + 1] - line)))
    while len(ts) > max(target, 2):
        c = [(cost(k), k) for k in range(1, len(ts) - 1) if ts[k] not in protect]
        if not c:
            break
        ts.pop(min(c)[1])
    return ts


def auto_stations(P, joints=(), per_joint=3, tol=0.06, prominence=0.05, return_info=False, n=12, max_aspect=3.0, max_rings=None):
    t, r = P["t"], smooth(P["r"], 2); m = len(t); keep = {0, m - 1}
    ex = extrema(t, P["r"], prominence); keep |= {i for i, _ in ex}
    h = 0.5 * float(np.mean(r)) / P["length"]                        # joint spacing: half a radius
    for j in joints:
        for q in range(per_joint):
            keep.add(int(np.clip(round((j + (q - (per_joint - 1) / 2) * h) * (m - 1)), 0, m - 1)))
    idx = sorted(keep); tolerance = tol * float(np.mean(r))
    for lo, hi in zip(idx, idx[1:]):
        _refine(t, r, lo, hi, tolerance, keep)
    out = [float(t[i]) for i in sorted(keep)]
    gap_max = max_aspect * 2 * math.pi * float(np.mean(r)) / n / P["length"]          # quads no longer than max_aspect x their width
    fill = []
    for lo, hi in zip(out, out[1:]):
        k = int(math.ceil((hi - lo) / gap_max)) - 1; fill += [lo + (hi - lo) * (q + 1) / (k + 1) for q in range(k)]
    out = sorted(out + fill)
    if max_rings and len(out) > max_rings:                                    # polygon budget: dissolve the least significant stations
        out = dissolve(t, r, out, max_rings, protect={float(t[i]) for j_ in joints for i in [int(round(j_ * (m - 1)))]})
    return (out, {"extrema": [(float(t[i]), kind, float(r[i])) for i, kind in ex], "tolerance": tolerance}) if return_info else out
