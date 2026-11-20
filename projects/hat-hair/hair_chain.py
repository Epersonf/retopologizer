"""Joins spines that continue each other into ONE spine (numpy; imported by hair_tubes.py). The detector cuts a long curl into pieces; built
as separate tubes they meet end to end with a kink and a thin / stuck-on look. Two ends are joined when they are closer than `gap` (5 cm)
and the curve really continues: the outward tangent of one points into the other (cosine > `cos`). Closest pair first, repeat. The root end
of the result is the higher one (hair hangs from the head), radii are blended over the joint.
  p, r = chain([(p0, r0), (p1, r1), ...])  ->  [(p, r), ...]"""
import numpy as np


def _out(p, s):
    """Unit tangent at end s (0 start, 1 end) pointing OUT of the spine."""
    t = p[0] - p[1] if s == 0 else p[-1] - p[-2]
    return t / max(np.linalg.norm(t), 1e-9)


def chain(spines, gap=0.05, cos=0.3):
    sp = [(np.asarray(p, float), np.asarray(r, float)) for p, r in spines]
    while True:
        best = None
        for i in range(len(sp)):
            for j in range(i + 1, len(sp)):
                for si in (0, 1):
                    for sj in (0, 1):
                        a = sp[i][0][0 if si == 0 else -1]; b = sp[j][0][0 if sj == 0 else -1]; d = np.linalg.norm(a - b)
                        if d < gap and (best is None or d < best[0]) and _out(sp[i][0], si).dot((b - a) / max(d, 1e-9) if d > 1e-4 else -_out(sp[j][0], sj)) > cos \
                                and _out(sp[i][0], si).dot(-_out(sp[j][0], sj)) > cos:
                            best = (d, i, si, j, sj)
        if best is None:
            break
        _, i, si, j, sj = best; (pi, ri), (pj, rj) = sp[i], sp[j]
        if si == 0:
            pi, ri = pi[::-1], ri[::-1]                                      # the joining end of i is its last point
        if sj == 1:
            pj, rj = pj[::-1], rj[::-1]                                      # and that of j its first
        p = np.vstack([pi, pj]); r = np.r_[ri, rj]; k = len(ri)
        r[max(0, k - 2):k + 2] = r[max(0, k - 2):k + 2].mean()               # one radius across the joint
        if p[0][2] < p[-1][2]:
            p, r = p[::-1], r[::-1]
        sp = [s for n, s in enumerate(sp) if n not in (i, j)] + [(p, r)]
    return sp
