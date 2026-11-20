"""Leg joints above one foot, from the horizontal sections: the leg loop is followed up to the crotch (where it
merges with the other leg or the body) and down to the ankle (where the loop starts to stretch into the foot)."""
from collections import deque
import numpy as np

UPLEG = 0.045       # hip joint above the crotch (H); Mixamo male .038, female .051
KNEE = 0.525        # knee from hip to ankle (Mixamo .52-.53)
FLARE = 1.25        # the foot starts where the front-back extent passes 1.25 x the slimmest shin
TOE_BASE = 0.64     # ball of the foot from the ankle to the toe tip (plan view; Mixamo .655 / .63)
TOE_Z = 0.2         # toe joints' height, as a fraction of the ankle height (Mixamo keeps them on the floor)
FRONT = 0.03        # the toe tip: middle of the foot's front 0.03 H (not the big toe alone)


def leg(B, foot):
    """{"UpLeg", "Leg", "Foot", "ToeBase", "Toe_End": np.array} and the landmarks they come from."""
    M, H = B.M, B.H; tip = M.V[foot]
    i = B.index(B.z(0.15))
    seed = min(B.level(i), key=lambda L: np.linalg.norm(L.c[:2] - tip[:2])).c
    up, merge = B.track(i, seed, +1, lambda L, prev: L.area > 1.8 * prev.area)
    down, _ = B.track(i - 1, seed, -1, lambda L, prev: False)
    tube = sorted(down + up, key=lambda t: t[0])
    zc = B.zi(merge) - B.dz / 2
    ys = [L.extent((0, 1, 0)) for _, L in tube]
    lim = FLARE * min(y for (k, _), y in zip(tube, ys) if B.z(0.04) <= B.zi(k) <= B.z(0.3))
    k0 = int(np.argmax(ys[: max(1, len(ys) // 3)]))
    ka = next(k for k in range(k0, len(tube)) if ys[k] <= lim)
    ankle = tube[ka][1].c
    hip = np.array([*up[-1][1].c[:2], zc + UPLEG * H])
    zk = hip[2] + KNEE * (ankle[2] - hip[2])
    knee = min(tube, key=lambda t: abs(B.zi(t[0]) - zk))[1].c
    pts = M.V[below(M, foot, ankle[2])]
    front = pts[pts[:, 1] < pts[:, 1].min() + FRONT * H]
    toe, heel = np.array([front[:, 0].mean(), pts[:, 1].min(), 0]), pts[np.argmax(pts[:, 1])]
    ball = ankle[:2] + TOE_BASE * (toe[:2] - ankle[:2])
    J = {"UpLeg": hip, "Leg": np.array([knee[0], knee[1], zk]), "Foot": ankle,
         "ToeBase": np.array([*ball, B.z0 + TOE_Z * (ankle[2] - B.z0)]),
         "Toe_End": np.array([toe[0], toe[1], B.z0 + TOE_Z * (ankle[2] - B.z0)])}
    return J, {"crotch": zc, "toe": toe, "heel": heel}


def below(M, v, zmax):
    """Vertices reachable from v without climbing over zmax (the foot, not a tail lying on the ground)."""
    seen, q = {v}, deque([v])
    while q:
        a = q.popleft()
        for b in M.nbr[a]:
            if b not in seen and M.V[b, 2] < zmax:
                seen.add(b); q.append(b)
    return np.array(sorted(seen))
