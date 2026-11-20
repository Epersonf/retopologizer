"""Where the low poly differs from the reference, on the unrolled map (the artist's "what is still missing"): the same horizontal-ray height field
(hair_radial.py) of the reference and of the low poly (run in the worker, written to draft/hair_radial_low.npz), difference r_ref - r_low:
RED = the reference is farther out than the low poly by more than TOL (3 cm) or the low poly is absent there: MISSING, add a lock or fatten the base;
BLUE = the low poly is farther out (or present where the reference is absent): EXCESS; light gray = within TOL; dark = nothing in either.
The hand-drawn locks (hair_locks_def.py) are drawn on top. Prints the shares (of the reference's / the low poly's visible samples of this view only) and the RELIEF MATCH: the correlation of the two fields
after the large forms are removed (high-pass, 6 cm): 0 = the low poly is smooth where the reference has locks, 1 = every ridge is where it should be.
  python -I projects/hat-hair/hair_diff.py [object=LowPoly] [t0 t1]  ->  draft/renders/diff.png (whole map) or diff_<t0>_<t1>.png"""
import sys
import numpy as np
from pathlib import Path
from scipy import ndimage as ndi
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
H = Path(__file__).resolve().parent; ROOT = H.parent.parent; sys.path.insert(0, str(H)); sys.path.insert(0, str(ROOT / "tools" / "general"))
import blender_rpc
a = sys.argv[1:]; obj = a[0] if a and not a[0].replace(".", "").replace("-", "").isdigit() else "LowPoly"; nums = [float(x) for x in a if x.replace(".", "").replace("-", "").isdigit()]
TOL = 0.03
code = 'OBJ = %r; OUT = "hair_radial_low"\n' % obj + (H / "hair_radial.py").read_text(encoding="utf-8"); r = blender_rpc.run(code, port=9877)
if r.get("status") == "error":
    sys.exit(r["message"][-800:])
ref = np.load(H / "draft" / "hair_radial.npz"); low = np.load(H / "draft" / "hair_radial_low.npz"); R, L, zs = ref["R"], low["R"], ref["zs"]; nt = R.shape[0]
D = R - L; fr, fl = np.isfinite(R), np.isfinite(L); miss = fr & (~fl | (D > TOL)); exc = fl & (~fr | (-D > TOL))
rgb = np.full(R.shape + (3,), 0.1)
rgb[fr | fl] = 0.85
s = np.clip(np.where(fr & fl, D, 0.1) - TOL, 0, 0.07) / 0.07; rgb[miss] = np.stack([np.ones_like(s), 1 - 0.9 * s, 1 - 0.9 * s], -1)[miss]
s2 = np.clip(np.where(fr & fl, -D, 0.1) - TOL, 0, 0.07) / 0.07; rgb[exc] = np.stack([1 - 0.9 * s2, 1 - 0.9 * s2, np.ones_like(s2)], -1)[exc]
t0, t1 = (nums[0], nums[1]) if len(nums) >= 2 else (0.0, 360.0); k = nt / 360.0; cols = np.arange(int(round(t0 * k)), int(round(t1 * k))) % nt
print("view %.0f..%.0f deg: missing %.1f%% of the reference's samples, excess %.1f%% of the low poly's" % (t0, t1, 100 * miss[cols].sum() / max(fr[cols].sum(), 1), 100 * exc[cols].sum() / max(fl[cols].sum(), 1)))


def highpass(X, m, sig=(17, 12)):                                   # normalized convolution (NaN-aware blur) then X - blur
    num = ndi.gaussian_filter(np.where(m, X, 0.0), sig, mode=("wrap", "nearest")); den = ndi.gaussian_filter(m.astype(float), sig, mode=("wrap", "nearest"))
    return np.where(m, X - num / np.maximum(den, 1e-6), 0.0)


both = ndi.binary_erosion(fr & fl, iterations=3, border_value=1)
for name, sig in (("6 cm", (17, 12)), ("3 cm", (8, 6))):
    hr, hl = highpass(R, both, sig), highpass(L, both, sig)
    print("relief match above %s: %.2f (ref %.1f cm rms, low poly %.1f cm rms, %d%% of the map compared)" % (name, (hr * hl)[both].sum() / max(np.sqrt((hr[both] ** 2).sum() * (hl[both] ** 2).sum()), 1e-9), 100 * np.sqrt((hr[both] ** 2).mean()), 100 * np.sqrt((hl[both] ** 2).mean()), 100 * both.mean()))
fig, ax = plt.subplots(figsize=(max(6, (t1 - t0) * 0.115) if len(nums) >= 2 else 18, 6.2)); half = 0.5 * (zs[1] - zs[0])
ax.imshow(np.transpose(rgb[cols], (1, 0, 2)), origin="lower", aspect="auto", extent=[t0, t1, zs[0] - half, zs[-1] + half])
try:
    from hair_locks_def import LOCKS
    for name, pts in LOCKS.items():
        p = np.array(pts, float); x = np.degrees(np.unwrap(np.radians(p[:, 0]))); x = x + 360 * np.round(((t0 + t1) / 2 - x.mean()) / 360); ax.plot(x, p[:, 1], "-o", color="black", lw=1.4, ms=2.5); ax.text(x[0], p[0, 1] + 0.01, name, fontsize=8, weight="bold")
except ImportError:
    pass
ax.set_xlim(t0, t1); ax.set_xticks(np.arange(np.ceil(t0 / 15) * 15, t1 + 1, 15)); ax.set_yticks(np.arange(0.05, 0.6, 0.05)); ax.tick_params(labelsize=6); ax.grid(alpha=0.3, lw=0.4)
plt.tight_layout(); out = H / "draft" / "renders" / ("diff_%d_%d.png" % (t0, t1) if len(nums) >= 2 else "diff.png"); plt.savefig(out, dpi=70); print(out)
