"""Numbered lock spines over the hair silhouette (front: x,z; side: y,z; top: x,y); line width = tube radius.
  python -I projects/hat-hair/hair_locks_plot.py [spines.npz] [out.png]"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

D = Path(__file__).resolve().parent / "draft"
S = np.load(D / (sys.argv[1] if len(sys.argv) > 1 else "hair_locks.npz")); out = D / "renders" / (sys.argv[2] if len(sys.argv) > 2 else "locks.png")
V = np.load(D / "hair_in.npz")["V"][::10]
fig, ax = plt.subplots(1, 3, figsize=(24, 9)); cm = plt.get_cmap("tab20")
for a, (i, j, t) in zip(ax, ((0, 2, "front x,z"), (1, 2, "side y,z"), (0, 1, "top x,y"))):
    a.scatter(V[:, i], V[:, j], s=0.3, c="#d0d0d0"); a.set_aspect("equal"); a.set_title(t); a.grid(alpha=.3)
    for k in range(int(S["n"])):
        p, r = S["p%d" % k], S["r%d" % k]
        a.plot(p[:, i], p[:, j], color=cm(k % 20), lw=max(1.0, float(np.median(r)) * 100 * 0.9))
        a.scatter(p[0, i], p[0, j], s=25, c="k"); a.text(p[-1, i], p[-1, j], str(k + 1), fontsize=11, weight="bold")
ax[0].invert_xaxis(); ax[2].invert_xaxis()
plt.tight_layout(); plt.savefig(out, dpi=60)
