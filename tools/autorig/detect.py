"""Joints of a humanoid mesh in Mixamo's names (no prefix), world metres: legs from the horizontal sections, arms
from walks along the arm tubes, spine and head on the mirror plane between them. Each side is found on its own, then
the two are averaged into a symmetric rig; a missing limb (the Saci's leg) is mirrored from the other side."""
import numpy as np
from .body import Body
from . import legs as LG, arms as AR, spine as SP, hands as HD, tail as TL

SIDE = {1: "Left", -1: "Right"}


def detect(M, symmetric=True):
    """(joints {name: np.array}, Body, landmarks) for the Mesh M."""
    B = Body(M); J, info = {}, {"tips": B.tips}
    for s, v in B.tips["feet"].items():
        jl, inf = LG.leg(B, v)
        J.update({SIDE[s] + k: p for k, p in jl.items()}); info[SIDE[s] + "Leg"] = inf
    for s, v in B.tips["hands"].items():
        ja, inf = AR.arm(B, v, s)
        J.update({SIDE[s] + k: p for k, p in ja.items()}); info[SIDE[s] + "Arm"] = inf
        axis = ja["Hand"] - ja["ForeArm"]
        jh, inf = HD.hand(B, ja["Hand"], axis / np.linalg.norm(axis))
        J.update({SIDE[s] + k: p for k, p in jh.items()}); info[SIDE[s] + "Hand"] = inf
    mirror_missing(J, B.x0)
    J.update(SP.spine(B, J["LeftUpLeg"], J["RightUpLeg"], J["LeftArm"], J["RightArm"]))
    if B.tips["tail"] is not None:
        J.update(TL.tail(B, B.tips["tail"], J["Hips"]))
    if symmetric:
        symmetrize(J, B.x0)
    return J, B, info


def mirror(p, x0):
    return np.array([2 * x0 - p[0], p[1], p[2]])


def mirror_missing(J, x0):
    for k in list(J):
        for a, b in (("Left", "Right"), ("Right", "Left")):
            if k.startswith(a) and b + k[len(a):] not in J:
                J[b + k[len(a):]] = mirror(J[k], x0)


def symmetrize(J, x0):
    for k in [k for k in J if k.startswith("Left")]:
        r = "Right" + k[4:]
        m = (J[k] + mirror(J[r], x0)) / 2
        J[k], J[r] = m, mirror(m, x0)
    for k in J:
        if not k.startswith(("Left", "Right")):
            J[k][0] = x0
