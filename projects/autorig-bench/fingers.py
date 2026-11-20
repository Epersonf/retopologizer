"""Finger and tail joints of the last evaluation next to the reference (x y z as fractions of H; offsets in % H).
  python projects/autorig-bench/fingers.py"""
import json, os
import numpy as np
R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "eval.json")))
for case, r in R.items():
    H, x0, z0 = r["H"], r["x0"], r["z0"]
    rel = lambda p: np.array([(p[0] - x0) / H, p[1] / H, (p[2] - z0) / H])
    print("====", case, " left hand digits (tip, root, length) / H")
    for name, d in r["info"].get("LeftHand", []):
        print("  %-7s tip %s root %s len %.3f" % (name, np.round(rel(d["tip"]), 3), np.round(rel(d["root"]), 3), d["length"] / H))
    for k in sorted(k for k in r["gt"] if (k.startswith("LeftHand") and k[-1].isdigit()) or k.startswith("Tail")):
        g = rel(r["gt"][k]); a = rel(r["J"][k]) if k in r["J"] else None
        print("  %-17s gt %s" % (k, np.round(g, 3)), "auto %s  d %s" % (np.round(a, 3), np.round((a - g) * 100, 1)) if a is not None else "-")
