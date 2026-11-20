"""Cross-sections of the reference as a PNG with a cm grid, to read coordinates (runs in normal python).
  python tools/general/slice_plot.py hi_world.npz out.png z 0.60 0.65 0.70 [--box xmin xmax ymin ymax] [--low low.npz]
Axis z: plot x,y   axis y: plot x,z   axis x: plot y,z. hi_world.npz holds V (world verts) and T (triangles),
exported once from Blender (see docs/02-retopology/retopo-llm.md). --low overlays a second mesh (e.g. the retopo) in black."""
import sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

AX = {"x": (0, (1, 2)), "y": (1, (0, 2)), "z": (2, (0, 1))}


def section(V, T, axis, val):
    """Segments where the plane coordinate[axis] == val cuts the triangles: (n, 2, 3) array."""
    d = V[:, axis] - val; dt = d[T]
    s = (dt > 0).sum(1); m = (s > 0) & (s < 3); tri, dt = T[m], dt[m]
    P = V[tri]; C, Q = [], []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        C.append((dt[:, i] > 0) != (dt[:, j] > 0))
        t = dt[:, i] / (dt[:, i] - dt[:, j] + 1e-30)
        Q.append(P[:, i] + (P[:, j] - P[:, i]) * t[:, None])
    C, Q = np.stack(C, 1), np.stack(Q, 1)
    idx = np.argsort(~C, axis=1, kind="stable")[:, :2]
    return np.take_along_axis(Q, idx[:, :, None], axis=1)


def plot(V, T, axis, vals, path, box=None, low=None):
    a, (i, j) = AX[axis]
    n = len(vals); cols = min(n, 3); rows = (n + cols - 1) // cols
    fig, axs = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows), squeeze=False)
    for k, v in enumerate(vals):
        ax = axs[k // cols][k % cols]; s = section(V, T, a, v)
        ax.add_collection(LineCollection(s[:, :, [i, j]] * 100, colors="tab:red", linewidths=0.8))
        if low is not None:
            sl = section(low[0], low[1], a, v)
            ax.add_collection(LineCollection(sl[:, :, [i, j]] * 100, colors="k", linewidths=1.2))
        if box:
            ax.set_xlim(box[0] * 100, box[1] * 100); ax.set_ylim(box[2] * 100, box[3] * 100)
        else:
            ax.autoscale()
        ax.set_aspect("equal"); ax.grid(True, lw=0.3); ax.minorticks_on(); ax.grid(True, which="minor", lw=0.1)
        ax.set_title(f"{axis} = {v:.3f} m  (cm: {'xyz'[i]} , {'xyz'[j]})", fontsize=9)
    for k in range(n, rows * cols):
        axs[k // cols][k % cols].axis("off")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


if __name__ == "__main__":
    args = sys.argv[1:]; box = low = None
    if "--box" in args:
        k = args.index("--box"); box = [float(x) for x in args[k + 1:k + 5]]; args = args[:k] + args[k + 5:]
    if "--low" in args:
        k = args.index("--low"); L = np.load(args[k + 1]); low = (L["V"], L["T"]); args = args[:k] + args[k + 2:]
    D = np.load(args[0]); plot(D["V"], D["T"], args[2], [float(x) for x in args[3:]], args[1], box, low)
