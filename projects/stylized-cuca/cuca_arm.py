"""Arm (half model: the +x arm), 8-sided contour rings from the arm root (torso arm hole) to the wrist.
Stations (x, m): deltoid, upper arm, 3 rings around the elbow (x ~ 0.21), forearm, wrist. Each ring is centred on
its own cross-section and aligned to the previous one (no twist). Exports L["wrist"] (8 verts, P[0] on top)."""
STATIONS = [0.13, 0.16, 0.19, 0.21, 0.23, 0.265, 0.30, 0.335]

prev = L["arm_root"]; c = co(prev[0]) * 0 + Vector((0.13, 0.008, 0.769))
for x in STATIONS:
    c = centred(R, Vector((x, c.y, c.z)), (1, 0, 0))
    ring = T.vs(align(cring(R, c, (1, 0, 0), (0, 0, 1), 8), prev), snap=False)
    T.strip(prev, ring, closed=True)
    prev = ring
L["wrist"] = prev
