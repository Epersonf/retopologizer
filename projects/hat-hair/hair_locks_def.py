"""The locks of the hair, hand-drawn on the unrolled map (view them with hair_unwrap.py): the manual half of the hybrid. Each lock is a polyline
of (azimuth deg, height m) from its root (top) to its tip, read off the map; hair_curves.py snaps it to the crest of the surface, takes the
radius of the surface from the reference and makes the Bezier control points. OPT[name] may set rho (the lock's radius in m, else RHO) and
sides (6 or 8, else 6). Azimuth from +y toward +x: front 180, the character's left (+x) 90, right (-x) 270, back 0/360.
Names: f = front, s = side, b = back; l / r = the character's left / right."""
RHO = 0.022
LOCKS = {
    "fr1": [(207.5, 0.495), (214.2, 0.445), (214.7, 0.395), (220.0, 0.345), (219.9, 0.295), (213.4, 0.245), (218.6, 0.195), (215.5, 0.145), (214.5, 0.11)],
    "fr2": [(226.4, 0.25), (231.9, 0.2), (235.2, 0.15), (231.0, 0.105)],
    "fr3": [(240.5, 0.32), (238.7, 0.27), (243.4, 0.22), (250.9, 0.2)],
    "sl1": [(59.8, 0.395), (53.3, 0.345), (60.7, 0.295), (69.1, 0.245), (63.6, 0.2)],
    "sl2": [(41.9, 0.465), (38.9, 0.415), (37.4, 0.365), (35.1, 0.315), (30.3, 0.265), (26.9, 0.215), (31.3, 0.165), (36.2, 0.115), (34.7, 0.07)],
    "br1": [(327.8, 0.495), (319.2, 0.445), (314.7, 0.395), (313.1, 0.345), (314.7, 0.295), (320.1, 0.245), (321.5, 0.195), (317.4, 0.145), (319.0, 0.095), (320.8, 0.07)],
    "sl3": [(79.9, 0.415), (84.3, 0.365), (91.3, 0.315), (98.5, 0.265), (105.0, 0.215), (113.4, 0.175)],
}
OPT = {}
