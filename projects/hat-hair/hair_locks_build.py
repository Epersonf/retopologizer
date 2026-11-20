"""Builds the lock tubes (retopo.lock) along the spines of hair_locks.py into the object "Hair_locks" (worker on
draft/hair_work.blend with "HairFull" loaded). Set LOCKS (1-based ids as printed/plotted; default all) and NAME before running.
Intersecting tubes are fine: they are clumps laid over the dome and over each other.
  LOCKS = [1, 2, 5]; exec(open(".../hair_locks_build.py").read())"""
import sys
import numpy as np
sys.path.insert(0, r"C:\Users\epers\Desktop\retopologizer\tools\02-retopologia")
import importlib, retopo
importlib.reload(retopo)
from retopo import *

S = np.load(r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft\hair_locks.npz")
NAME = globals().get("NAME", "Hair_locks"); IDS = globals().get("LOCKS") or list(range(1, int(S["n"]) + 1))
R = Ref("HairFull")
T = Topo(R)
info = []
for i in IDS:
    rings, tip = lock(T, R, S["p%d" % (i - 1)], S["r%d" % (i - 1)])
    info.append((i, len(rings), len(rings[0])))
T.orient()
T.write(NAME)
qa = topo_qa(NAME, R)
result = {"locks (id, rings, n)": info, "quads": qa["quads"], "quad_only": qa["quad_only"], "holes_edges": qa["holes_edges"],
          "vert_to_ref_mm": qa["vert_to_ref_mm"], "inward_area_pct": qa["inward_area_pct"], "poles": qa["poles"]}
