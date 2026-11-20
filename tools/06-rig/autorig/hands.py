"""Finger joints: the fingertips are the geodesic tips of the hand (distance from the wrist), each digit is walked
back from its tip to where it merges into the palm. The thumb is the digit that leaves the palm closest to the
wrist; the others are named Index to Pinky going away from the thumb. Joints 1..4 run from the knuckle (a little
inside the palm) to the tip, as in Mixamo."""
import numpy as np
from . import geodesic as G, tube as T
from .rings import snap_chain

TIP = 0.015                      # a fingertip stands this much (H) above the saddle to a longer digit
FRACS = (0.39, 0.74)             # joints 2 and 3 from the knuckle to the tip (Mixamo female index .39, .75)
KNUCKLE = 0.0                    # knuckle past the finger's root into the palm, x the finger's length (Mixamo: the web)
THUMB_IN = 0.65                  # the thumb's first joint sits deep in the palm, on the thumb's axis (Mixamo .66)
THUMB_ROOT = 0.75                # the thumb leaves the palm nearer the wrist than 0.75 x the fingers' median (.4-.6)
NAMES = {1: ("Index",), 2: ("Index", "Middle"), 3: ("Index", "Middle", "Ring"), 4: ("Index", "Middle", "Ring", "Pinky")}


def hand(B, wrist, axis):
    """{"HandThumb1": .., "HandIndex1": .., ...} for the hand past `wrist` (axis: unit vector toward the fingers)."""
    J, info = {}, []
    digits = sorted(walk_digits(B, wrist, axis), key=lambda d: d["root_along"])
    others = [d["root_along"] for d in digits[1:]]
    if others and digits[0]["root_along"] < THUMB_ROOT * float(np.median(others)):
        thumb = digits.pop(0)
        place(J, "Thumb", thumb, THUMB_IN); snap(B.M, J, "Thumb", thumb, 1); info.append(("Thumb", thumb))
        digits.sort(key=lambda d: np.linalg.norm(d["root"] - thumb["root"]))
    for name, d in zip(NAMES.get(len(digits), NAMES[4]), digits[:4]):
        place(J, name, d, KNUCKLE); snap(B.M, J, name, d, 0); info.append((name, d))
    return J, [(n, {k: d[k] for k in ("tip", "root", "length")}) for n, d in info]


def walk_digits(B, wrist, axis):
    M, H = B.M, B.H
    rel = M.V - wrist; along = rel @ axis
    region = (along > -0.005 * H) & (np.linalg.norm(rel, axis=1) < 0.25 * H)
    ring = np.nonzero(region & (along < 0.01 * H) & (np.linalg.norm(rel - np.outer(along, axis), axis=1) < 0.06 * H))[0]
    D = G.dijkstra(M, ring, allowed=region)
    out = []
    for v, p in G.peaks(M, D, TIP * H):
        t = M.V[v]; d = (wrist - t) / np.linalg.norm(wrist - t)
        path = T.walk(M, t + d * 0.004 * H, d, 0.002 * H, 0.15 * H, stop=T.jump(1.6))
        if len(path) < 4:
            continue
        root = path[-1][0]
        out.append({"tip": t, "tip_v": v, "root": root, "path": path, "length": path[-1][3] + 0.004 * H,
                    "root_along": float((root - wrist) @ axis),
                    "radius": float(np.median([np.sqrt(p[2].area / np.pi) for p in path[2:]]))})
    return out


def snap(M, J, name, d, first):
    """Joints first..3 of the digit onto its edge rings (low-poly digits bend only there)."""
    keys = ["Hand%s%d" % (name, i) for i in (1, 2, 3, 4)]
    P, _ = snap_chain(M, np.array([J[k] for k in keys]), d["tip_v"], 2.2 * d["radius"], first)
    J.update(zip(keys, P))


def place(J, name, d, knuckle):
    """Joints 1..4 of one digit: 1 `knuckle` x its length past the root (on the tip-to-root line), 4 on the tip."""
    path, l, root, tip = d["path"], d["length"], d["root"], d["tip"]
    end, s1 = path[-1][3], path[-1][3] + knuckle * l
    inward = (root - tip) / np.linalg.norm(root - tip)
    for i, s in enumerate((s1, s1 * (1 - FRACS[0]), s1 * (1 - FRACS[1]), 0.0)):
        J["Hand%s%d" % (name, i + 1)] = tip if s <= 0 else root + inward * (s - end) if s > end else T.at_length(path, s)
