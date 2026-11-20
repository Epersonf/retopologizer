"""Neck (half), 12 around: half rings of 7 verts from the torso neck hole up toward the head.
The last ring is the neck top L["neck_top"]; the head part closes it onto the jaw / skull."""
NECK_Z = [0.84, 0.86]

prev = L["neck_base"]
for z in NECK_Z:
    c = centred(R, Vector((0, 0.0, z)), (0, 0, 1), (0, -1, 0)); c.x = 0.0
    ring = T.vs(chalf(R, c, (0, 0, 1), (0, -1, 0), 6), snap=False)
    T.strip(prev, ring)
    prev = ring
L["neck_top"] = prev
