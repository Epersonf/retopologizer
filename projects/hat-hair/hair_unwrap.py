"""The unrolled shaded map of the hair, cropped and gridded: what a hair artist traces the locks on. Azimuth t in degrees from +y toward +x
(front = 180, the character's left +x = 90, right = 270, back = 0/360), z in metres. Over the map: the ridge chains of hair_ridges.py
(thin, numbered) and the hand-drawn locks of hair_locks_def.py (thick, named) when they exist. A crop may wrap (-40..40).
  python -I projects/hat-hair/hair_unwrap.py <t0> <t1> [tag]  ->  draft/renders/unwrap_<tag>.png (default tag t0_t1)
  python -I projects/hat-hair/hair_unwrap.py all                the whole 360 deg"""
import sys
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
H = Path(__file__).resolve().parent / "draft"


def shade(d):
    nt, nz = d["NT_"], d["NZ_"]; nr = np.sqrt(np.clip(1 - nt ** 2 - nz ** 2, 0, 1)); L = np.array([-0.5, 0.6, 0.6]); L /= np.linalg.norm(L)
    return np.clip(nt * L[0] + nz * L[1] + nr * L[2], 0, 1)


def unwrap(t0, t1, path, locks=None):
    d = np.load(H / "hair_radial.npz"); zs = d["zs"]; sh = shade(d); k = sh.shape[0] / 360.0
    cols = np.arange(int(round(t0 * k)), int(round(t1 * k))) % sh.shape[0]
    fig, ax = plt.subplots(figsize=(max(6, (t1 - t0) * 0.115), 6.2)); half = 0.5 * (zs[1] - zs[0])
    ax.imshow(np.ma.masked_invalid(sh[cols].T), origin="lower", aspect="auto", extent=[t0, t1, zs[0] - half, zs[-1] + half], cmap="gray", vmin=0.1, vmax=1.0)
    ax.set_facecolor("black")
    if (H / "hair_ridges.npz").exists():
        S = np.load(H / "hair_ridges.npz")
        for i in range(int(S["n"])):
            a = S["c%d" % i]; x = np.degrees(np.unwrap(np.radians(a[:, 0]))); x = x + 360 * np.round(((t0 + t1) / 2 - x.mean()) / 360)
            ax.plot(x, a[:, 1], "-", color="cyan", lw=0.8); ax.text(x[0], a[0, 1], "r%d" % i, color="cyan", fontsize=7)
    for name, pts in (locks or {}).items():
        a = np.array(pts, float); x = np.degrees(np.unwrap(np.radians(a[:, 0]))); x = x + 360 * np.round(((t0 + t1) / 2 - x.mean()) / 360)
        ax.plot(x, a[:, 1], "-o", color="orange", lw=1.6, ms=3); ax.text(x[0], a[0, 1] + 0.01, name, color="yellow", fontsize=8, weight="bold")
    ax.set_xlim(t0, t1); ax.set_xticks(np.arange(np.ceil(t0 / 5) * 5, t1 + 1, 5)); ax.set_yticks(np.arange(0.05, 0.6, 0.05))
    ax.tick_params(labelsize=6); ax.grid(alpha=0.3, lw=0.4); plt.tight_layout(); plt.savefig(path, dpi=100); plt.close(fig)


if __name__ == "__main__":
    a = sys.argv[1:]
    t0, t1 = (0, 360) if a[0] == "all" else (float(a[0]), float(a[1])); tag = a[2] if len(a) > 2 else ("all" if a[0] == "all" else "%d_%d" % (t0, t1))
    try:
        from hair_locks_def import LOCKS
    except ImportError:
        LOCKS = {}
    p = H / "renders" / ("unwrap_%s.png" % tag); unwrap(t0, t1, p, LOCKS); print(p)
