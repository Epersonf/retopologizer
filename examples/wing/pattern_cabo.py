"""Engraving and enamel for the wing handle, as functions of the 3D position (no UV needed, so no seams between islands).
Each pattern returns (h, E): h = height 0..1 (1 raised, 0 engraved), E = enamel mask (the white stars of the Southern Cross on the collar).
Groove widths are in metres (1 mm = 0.001); `groove(d, w)` is 1 inside a groove of width w centred where d = 0."""
import numpy as np
sm = lambda x, a, b: (lambda t: t * t * (3 - 2 * t))(np.clip((x - a) / (b - a), 0, 1))
groove = lambda d, w: 1 - sm(np.abs(d), w * 0.5, w)          


def star(u, v, R):                                            # 4-point star (soft astroid)
    return 1 - sm((np.abs(u) ** 0.55 + np.abs(v) ** 0.55) ** (1 / 0.55) / R, 0.8, 1.05)


CRUX = [(-0.018, 0.0, 0.0062), (0.018, 0.001, 0.0062), (-0.002, -0.0115, 0.0048), (0.005, 0.0115, 0.0048), (0.006, -0.003, 0.0028)]


def collar(P, C):
    cy, cz, r, x0, x1 = C; xc = (x0 + x1) / 2; v = P[:, 0] - xc; ph = np.arctan2(P[:, 2] - cz, -(P[:, 1] - cy)); u = ph * r
    h = np.ones(len(P)); E = np.zeros(len(P)); hl = (x1 - x0) / 2
    for sgn in (-1, 1):   # borders with a wave line
        w = 0.0012 * np.sin(u / 0.0045)
        h -= 0.85 * groove(v - sgn * (hl - 0.006) - w, 0.0016) * (np.abs(v) > hl - 0.012)
    h -= 0.8 * groove(np.abs(v) - (hl - 0.0125), 0.0012)
    front = np.abs(ph) < 0.85
    for (su, sv, R) in CRUX:
        s = star(u - su, v - sv, R) * front; E = np.maximum(E, s); h -= 0.9 * s
    cell = np.mod(u + 0.0125, 0.025) - 0.0125; d = (np.abs(cell) + np.abs(v)) / 0.006     # diamonds on the rest of the circumference
    h -= 0.8 * (1 - sm(d, 0.7, 1.0)) * (~front)
    capm = np.abs(np.abs(P[:, 0] - xc) - hl) < 0.0006; rr = np.hypot(P[:, 1] - cy, P[:, 2] - cz) / r    # end caps: rings
    h -= 0.7 * capm * (groove(rr - 0.55, 0.07) + groove(rr - 0.82, 0.06)).clip(0, 1)
    return h.clip(0, 1), E


def neck(P, C):
    cy, cz, r, x0, x1 = C; s = (P[:, 0] - x0) / (x1 - x0); h = np.ones(len(P))
    for k in (0.2, 0.4, 0.6, 0.8):
        h -= 0.8 * groove(s - k, 0.07)
    return h.clip(0, 1), np.zeros(len(P))


def plate(P, C):
    cx, cz, R = C; dx, dz = P[:, 0] - cx, P[:, 2] - cz; r = np.hypot(dx, dz) / R; ph = np.arctan2(dz, dx); h = np.ones(len(P))
    h -= 0.8 * groove(r - 0.88, 0.07) + 0.7 * groove(r - 0.3, 0.06) + 0.75 * groove(r - 0.65 * (0.62 + 0.38 * np.abs(np.cos(4 * ph))), 0.07) * (r < 0.9)
    h += 0.3 * (r < 0.22); h -= 0.7 * groove(r - 0.45 * (0.5 + 0.5 * np.cos(8 * ph)), 0.05) * (r > 0.3) * (r < 0.6)
    return h.clip(0, 1), np.zeros(len(P))


def eye(P, C):
    cx, cz, R = C; dx, dz = P[:, 0] - cx, P[:, 2] - cz; r = np.hypot(dx, dz) / R; ph = np.arctan2(dz, dx); h = np.ones(len(P))
    f = np.mod(r * 2.4 + ph / (2 * np.pi), 1.0); h -= 0.85 * groove(f - 0.5, 0.3) * (r < 0.9)
    return h.clip(0, 1), np.zeros(len(P))


def bar(P, pts, half):                                       # pts: centre line (x, z), half: half width per point
    pts = np.array(pts); seg = pts[1:] - pts[:-1]; L = np.linalg.norm(seg, axis=1); cum = np.r_[0, np.cumsum(L)]; q = P[:, [0, 2]]
    best = np.full(len(P), 1e9); s = np.zeros(len(P)); w = np.zeros(len(P)); hw = np.zeros(len(P))
    for i in range(len(seg)):
        t = np.clip(((q - pts[i]) @ seg[i]) / (L[i] ** 2), 0, 1); pr = pts[i] + t[:, None] * seg[i]; d = np.linalg.norm(q - pr, axis=1); m = d < best
        cr = seg[i][0] * (q[:, 1] - pts[i][1]) - seg[i][1] * (q[:, 0] - pts[i][0])
        s[m] = cum[i] + t[m] * L[i]; w[m] = np.sign(cr[m]) * d[m]; hw[m] = half[i] * (1 - t[m]) + half[i + 1] * t[m]; best[m] = d[m]
    nu = w / np.maximum(hw, 1e-4); h = np.ones(len(P))
    h -= 0.8 * groove(np.abs(nu) - 0.66, 0.1); ph = np.mod(s / 0.02 + 0.4 * np.abs(nu), 1.0); h -= 0.7 * groove(ph - 0.5, 0.16) * (np.abs(nu) < 0.5)
    cs = np.mod(s + 0.013, 0.026) - 0.013; h -= 0.9 * (1 - sm(np.hypot(cs, w) / 0.0032, 0.7, 1.0)) * (np.abs(nu) < 0.5)
    return h.clip(0, 1), np.zeros(len(P))
