"""Joint points placed by hand (Mixamo's markers: chin, wrists, elbows, knees, groin) override what detect() found.
Markers are {"Chin": [x,y,z], "LeftWrist": ..., "RightKnee": ...} in world metres (Z up, faces -Y, Left = +X)."""
import numpy as np

# marker -> joint name in the limb dict of its side / in the body
LIMB = {"Wrist": "Hand", "Elbow": "ForeArm", "Knee": "Leg"}


def of_side(markers, side, x0, symmetric):
    """{joint: point} for one side ("Left"/"Right"); with symmetry a missing side is the other one mirrored."""
    other = "Right" if side == "Left" else "Left"
    out = {}
    for m, joint in LIMB.items():
        own, far = markers.get(side + m), markers.get(other + m)
        if own is not None:
            out[joint] = np.array(own, float)
        elif far is not None and symmetric:
            out[joint] = np.array([2 * x0 - far[0], far[1], far[2]], float)
    return out


def apply_limb(limb, side, markers, x0, symmetric):
    """limb dict (Leg or Arm joints of one side) with the user's joints in place of the found ones."""
    if not markers:
        return limb
    mine = of_side(markers, side, x0, symmetric)
    return {**limb, **{k: v for k, v in mine.items() if k in limb}}


def apply_body(J, markers, x0):
    """Chin lifts the Head joint to the chin's height; the groin sets the Hips height (both on the mirror plane)."""
    if not markers:
        return J
    if "Chin" in markers and "Head" in J:
        J["Head"] = np.array([x0, markers["Chin"][1], markers["Chin"][2]], float)
    if "Groin" in markers and "Hips" in J:
        J["Hips"] = np.array([x0, J["Hips"][1], markers["Groin"][2]], float)
    return J
