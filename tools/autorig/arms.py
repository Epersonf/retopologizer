"""Arm joints from a walk along the arm tube, from the fingertips to where the tube flows into the torso: the wrist
where the sections past the palm and thumb get as slim as the forearm, the shoulder joint where vertical sections start to climb the
armpit's curve, the elbow between them. The arm is taken as straight from the wrist on (Mixamo's T-pose arms)."""
import numpy as np
from . import tube as T
from .sections import section, pick

ELBOW = 0.465       # elbow from shoulder to wrist (Mixamo male .458, female .471)
HAND = 0.25         # the palm and thumb are within this arc length (H) of the fingertip
SLIM = 1.2          # wrist: the first section past the palm within 1.2 x the slimmest forearm one ...
STAY = 1.35         # ... with the next 8 within 1.35 x (a dip inside the palm comes back up)
CURVE = 1.2         # shoulder joint: vertical section 1.2 x as tall as the arm's (start of the armpit curve)
STEP = 0.004        # walk step (H)
TORSO = 0.3         # the walk reached the torso: a section this wide (H); a hand with its thumb is narrower


def arm(B, hand, side):
    """{"Arm", "ForeArm", "Hand": np.array} for the arm whose fingertip is `hand`, side +1 left / -1 right."""
    M, H = B.M, B.H; tip = M.V[hand]
    d = np.array([B.x0, tip[1], B.z(0.75)]) - tip; d /= np.linalg.norm(d)
    path = T.walk(M, tip + d * 0.01 * H, d, STEP * H, 0.7 * H, stop=lambda L, h: L.size > TORSO * H, follow=0.25)
    C, S = np.array([p[0] for p in path]), np.array([p[3] for p in path])
    size, n = np.array([p[2].size for p in path]), len(path)
    kp = int(np.argmax(size[: max(2, int(np.searchsorted(S, HAND * H)))]))      # palm and thumb
    m = size[(S >= S[kp]) & (S <= S[kp] + 0.2 * H)].min()                         # the slimmest forearm section
    kw = next((k for k in range(kp, n - 9) if size[k] <= SLIM * m and size[k + 1: k + 9].max() <= STAY * m), kp)
    wrist = C[kw]
    ks = np.arange(kw + 1, n)
    ks = ks[side * (C[ks, 0] - C[-1, 0]) > 0.04 * H]
    fit = np.polyfit(C[ks, 0], C[ks, 1:], 1)           # y and z as lines of x, wrist to upper arm
    axis = lambda x: np.array([x, *(fit[0] * x + fit[1])])
    shoulder = axis(shoulder_x(B, side, axis, C[-1, 0]))
    s_w = S[kw] + np.linalg.norm(wrist - C[kw])
    s_sh = S[-1] + abs(shoulder[0] - C[-1, 0]) * np.sign(side * (C[-1, 0] - shoulder[0]))
    elbow = T.at_length(path, s_sh - ELBOW * (s_sh - s_w))
    return {"Arm": shoulder, "ForeArm": elbow, "Hand": wrist}, {"merge": C[-1], "palm": C[kp]}


def shoulder_x(B, side, axis, x_end):
    """x of the shoulder joint: vertical sections around the arm axis, moving in from the upper arm, grow taller over
    the armpit's curve and jump where they run down the flank; the joint is where the curve starts."""
    M, H = B.M, B.H
    hs, c = [], x_end + side * 0.1 * H
    while side * (c - B.x0) > 0:
        q = axis(c)
        L = pick(section(M, q, (1, 0, 0)), q, 0.05 * H)
        if L is None or (hs and L.extent((0, 0, 1)) > 2 * hs[-1][1]):
            break
        hs.append((c, L.extent((0, 0, 1)))); c -= side * 0.002 * H
    xj = hs[-1][0]
    ref = min(hs, key=lambda t: abs(t[0] - (xj + side * 0.05 * H)))[1]
    xa = xj
    for c, h in reversed(hs):                          # from the flank outward, while still on the curve
        if h < CURVE * ref:
            break
        xa = c
    return xa
