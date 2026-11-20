"""Pure numpy helpers for texture clean-up (no Blender needed).
inpaint(): fill invalid texels from valid neighbours of the SAME UV island (like a clone/heal
brush, but automatic and never bleeding across islands). dilate(): grow islands into their
padding so mip-maps/bleeding do not show seams."""
import numpy as np

_SHIFTS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def _sh(a, dy, dx, fill=0):
    out = np.full_like(a, fill)
    H, W = a.shape[:2]
    ys, yd = (slice(dy, H), slice(0, H - dy)) if dy >= 0 else (slice(0, H + dy), slice(-dy, H))
    xs, xd = (slice(dx, W), slice(0, W - dx)) if dx >= 0 else (slice(0, W + dx), slice(-dx, W))
    out[yd, xd] = a[ys, xs]
    return out


def _grow(arr, valid, target, ids=None, iters=64):
    """Fill `target` texels from valid 8-neighbours (same island if ids is given)."""
    arr = arr.copy(); valid = valid.copy()
    for _ in range(iters):
        need = target & ~valid
        if not need.any():
            break
        ys, xs = np.where(need)
        y0, y1, x0, x1 = max(ys.min() - 2, 0), ys.max() + 3, max(xs.min() - 2, 0), xs.max() + 3
        A, V, N = arr[y0:y1, x0:x1], valid[y0:y1, x0:x1], need[y0:y1, x0:x1]
        I = ids[y0:y1, x0:x1] if ids is not None else None
        acc = np.zeros_like(A); cnt = np.zeros(N.shape, np.float32)
        for dy, dx in _SHIFTS:
            ok = N & _sh(V, dy, dx)
            if I is not None:
                ok &= _sh(I, dy, dx) == I
            acc[ok] += _sh(A, dy, dx)[ok]; cnt[ok] += 1
        fill = cnt > 0
        if not fill.any():
            break
        A[fill] = acc[fill] / cnt[fill][:, None]
        V[fill] = True
    return arr, valid


def inpaint(arr, valid, ids, iters=64):
    """arr (H,W,C) float, valid (H,W) bool, ids (H,W) island ids (0 = outside)."""
    return _grow(arr, valid, ids > 0, ids, iters)


def dilate(arr, ids, iters=8):
    """Extend island pixels outwards into empty (ids == 0) texels."""
    return _grow(arr, ids > 0, ids == 0, None, iters)[0]
