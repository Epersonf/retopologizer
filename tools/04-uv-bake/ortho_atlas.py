"""ortho_atlas: render a source piece ONCE (orthographic raycast) into a tile of an atlas: color, alpha (silhouette) and a normal
map made from the depth. For leaves, feathers, scales and cloth strips that become cutout planes (guide: docs/04-uv-bake/leaf-cards.md).
Inside Blender (worker): exec the file. A tile is (x, y, w, h) px, top-left origin, MARGIN px of bleed kept inside it."""
import numpy as np
from mathutils.bvhtree import BVHTree

MARGIN = 6


def srgb(c):
    return np.clip(np.asarray(c, float), 0, 1) ** (1 / 2.2)


def ramp(t, stops):
    """Color from a ColorRamp copied as [(pos, (r, g, b) linear), ...] over t (UV.y of the hit): the source colors were a ramp."""
    xs = [p for p, _ in stops]
    return np.stack([np.interp(t, xs, [c[k] for _, c in stops]) for k in range(3)], -1)


def box_blur(a, r):
    k = 2 * r + 1
    p = np.pad(a, r, mode="edge")
    c = np.pad(np.cumsum(np.cumsum(p, 0), 1), ((1, 0), (1, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def fill_out(a, mask, iters=10):
    """Bleed the colors of `mask` outwards a few px (no black halo when the alpha is filtered or mipmapped)."""
    a = a.copy()
    ok = mask.copy()
    for _ in range(iters):
        s = np.zeros_like(a)
        n = np.zeros(a.shape[:2])
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            m, v = np.roll(ok, (dy, dx), (0, 1)), np.roll(a, (dy, dx), (0, 1))
            s += np.where(m[..., None] if a.ndim == 3 else m, v, 0)
            n += m
        new = (~ok) & (n > 0)
        a[new] = (s[new] / n[new][..., None]) if a.ndim == 3 else s[new] / n[new]
        ok = ok | new
    return a


def raster(obj, origin, u, v, n, we, he, w, h):
    """Rays from the +n side against `obj`, a w x h grid covering we x he metres from `origin` along u and v.
    Returns mask, height (towards the viewer) and the UV.y of the hit point (to rebuild a ramp color)."""
    me = obj.data
    me.calc_loop_triangles()
    uvl = me.uv_layers[0].data
    V = [obj.matrix_world @ p.co for p in me.vertices]
    tris = me.loop_triangles
    bvh = BVHTree.FromPolygons(V, [tuple(t.vertices) for t in tris])
    mask, hgt, uvy = np.zeros((h, w), bool), np.zeros((h, w)), np.zeros((h, w))
    for j in range(h):
        for i in range(w):
            p = origin + u * ((i + 0.5) / w * we) + v * ((h - j - 0.5) / h * he) + n * 0.5
            hit = bvh.ray_cast(p, -n)
            if hit[0] is None:
                continue
            t = tris[hit[2]]
            a, b, c = (V[k] for k in t.vertices)
            v0, v1, v2 = b - a, c - a, hit[0] - a
            d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
            den = d00 * d11 - d01 * d01 or 1e-12
            bv, bw = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
            ls = [uvl[k].uv for k in t.loops]
            uvy[j, i] = ls[0][1] * (1 - bv - bw) + ls[1][1] * bv + ls[2][1] * bw
            mask[j, i] = True
            hgt[j, i] = 0.5 - hit[3]
    return mask, hgt, uvy


def to_normal(hgt, mask, pitch, low):
    """OpenGL normal (Y+) from the height. The large shape (blur radius `low` px) is removed: it comes from the plane geometry.
    Outside the eroded core the normal is flat, or the cut border shows colored bands."""
    m = mask.astype(float)
    base = box_blur(hgt * m, low) / np.maximum(box_blur(m, low), 1e-3)
    hh = box_blur(box_blur(np.where(mask, hgt - base, 0.0), 1), 1)
    dx = (np.roll(hh, -1, 1) - np.roll(hh, 1, 1)) / (2 * pitch)
    dy = -(np.roll(hh, -1, 0) - np.roll(hh, 1, 0)) / (2 * pitch)
    nrm = np.stack([-dx, -dy, np.ones_like(dx)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    nrm = np.where((box_blur(m, 3) > 0.999)[..., None], nrm, np.array([0.0, 0.0, 1.0]))
    return nrm * 0.5 + 0.5


def paste(atlas_rgba, atlas_n, tile, rgb, alpha, nrm):
    x0, y0, w, h = tile
    m = MARGIN
    sl = (slice(y0 + m, y0 + h - m), slice(x0 + m, x0 + w - m))
    atlas_rgba[sl[0], sl[1], :3] = fill_out(rgb, alpha > 0.5, m)
    atlas_rgba[sl[0], sl[1], 3] = alpha
    atlas_n[sl] = fill_out(nrm, alpha > 0.5, m)
