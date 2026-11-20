"""Spine, neck and head joints on the mirror plane: hips just above the hip joints, the neck base just above the
shoulder joints, the spine evenly between them on a straight line (as Mixamo does), the head joint at the chin
(where the sections grow again above the slimmest neck one). The clavicles (Left/RightShoulder) run from the neck
toward the shoulder joints."""
import numpy as np

HIPS = 0.028                    # hips above the hip joints (H); Mixamo .029 / .028
NECK = 0.027                    # neck base above the shoulder joints (Mixamo .029 / .025)
SPINE = (0.20, 0.435, 0.70)     # Spine, Spine1, Spine2 from hips to neck
CHIN = 1.5                      # the chin: the first section above the slimmest neck one that is 1.5 x bigger
HEAD_BACK = 0.006               # head joint behind the neck base (Mixamo male and female)
HEAD_LEAN = 0.176               # the head bone leans 10 degrees forward (tan; Mixamo male .175, female .177)
CLAVICLE = (0.33, 0.68)         # Shoulder: x as a fraction of the shoulder joint's, z from it toward the neck


def spine(B, up_l, up_r, arm_l, arm_r):
    H, x = B.H, B.x0
    hz = (up_l[2] + up_r[2]) / 2 + HIPS * H
    hips = np.array([x, B.centre(B.index(hz)).c[1], hz])
    neck = np.array([x, (arm_l[1] + arm_r[1]) / 2, (arm_l[2] + arm_r[2]) / 2 + NECK * H])
    J = {"Hips": hips, "Neck": neck}
    for name, f in zip(("Spine", "Spine1", "Spine2"), SPINE):
        J[name] = hips + f * (neck - hips)
    top = B.z(1.0)
    lv = np.arange(B.index(neck[2]), B.index((neck[2] + top) / 2))
    a = smooth(np.array([B.centre(i).area for i in range(lv[0] - 2, lv[-1] + 3)]))[2:-2]
    k = int(np.argmin(a)); k = next((j for j in range(k, len(a)) if a[j] >= CHIN * a[k]), k)
    head = J["Head"] = np.array([x, neck[1] - HEAD_BACK * H, B.zi(lv[k])])
    J["HeadTop_End"] = np.array([x, head[1] - HEAD_LEAN * (top - head[2]), top])
    for s, a in (("Left", arm_l), ("Right", arm_r)):
        J[s + "Shoulder"] = np.array([x + CLAVICLE[0] * (a[0] - x), a[1], a[2] + CLAVICLE[1] * (neck[2] - a[2])])
    return J


def smooth(a, r=2):
    """Running median over 2r+1 levels: a level or two cut badly (a non-manifold edge breaks the loop) are no neck.
    The caller passes r extra levels on each side, so the ends are medians of real levels too."""
    p = np.pad(a, r, mode="edge")
    return np.median(np.stack([p[i:i + len(a)] for i in range(2 * r + 1)]), axis=0)
