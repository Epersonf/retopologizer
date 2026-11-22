"""plane_cards: replace each leaf/feather/scale/cloth strip of a ref by ONE low-poly plane that wears a shared texture.
Only measures (components, frame, curvature); the quads are built by the project script. Guide: docs/04-uv-bake/leaf-cards.md.
Inside Blender: exec the file, then `components(obj)` -> `leaf_frame(P, center_xy)` -> `cell_offset(...)`."""
import bpy
import numpy as np


def components(o, min_pts=200):
    """Loose pieces of the EVALUATED mesh (a mirror modifier makes the other side a separate piece): list of Nx3 world points."""
    dg = bpy.context.evaluated_depsgraph_get()
    oe = o.evaluated_get(dg)
    me = oe.to_mesh()
    V = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])
    par = list(range(len(V)))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for e in me.edges:
        par[find(e.vertices[0])] = find(e.vertices[1])
    root = np.array([find(i) for i in range(len(V))])
    oe.to_mesh_clear()
    return [V[root == r] for r in np.unique(root) if (root == r).sum() > min_pts]


def leaf_frame(P, center_xy=(0.0, 0.0)):
    """PCA frame of one piece: c, u (width), v (length, pointing from the tip to the base), n (outward), (su, sv) extents.
    The base is the end that is higher, or closer to the body axis when the piece lies flat; CHECK it on a render
    (a wrong guess flips the texture gradient). n looks away from the body axis."""
    c0 = np.asarray(center_xy, float)
    c = P.mean(0)
    vec = np.linalg.eigh(np.cov((P - c).T))[1]
    e1, e3 = vec[:, 2], vec[:, 0]
    s = (P - c) @ e1
    hi, lo = s > np.percentile(s, 85), s < np.percentile(s, 15)
    dz = P[hi, 2].mean() - P[lo, 2].mean()
    rad = lambda Q: np.linalg.norm(Q[:, :2] - c0, axis=1).mean()
    up = dz > 0 if abs(dz) > 0.03 else rad(P[hi]) < rad(P[lo])
    v = e1 if up else -e1
    r = np.r_[c[:2] - c0, 0.0]
    r /= np.linalg.norm(r) or 1
    n = e3 if (e3 @ r) > 0 else -e3
    if abs(e3 @ r) < 0.3:
        n = e3 if e3[2] > 0 else -e3
    n = n - v * (n @ v)
    n /= np.linalg.norm(n)
    u = np.cross(v, n)
    su, sv = (P - c) @ u, (P - c) @ v
    return c, u, v, n, (np.percentile(su, 1), np.percentile(su, 99)), (np.percentile(sv, 1), np.percentile(sv, 99))


def cell_offset(P, c, u, v, n, su, sv, cols, rows):
    """Mean offset along n at each node of a (cols+1) x (rows+1) grid over the piece: gives a flat plane its curvature."""
    a, b, h = (P - c) @ u, (P - c) @ v, (P - c) @ n
    out = np.zeros((rows + 1, cols + 1))
    for j in range(rows + 1):
        for i in range(cols + 1):
            pu, pv = su[0] + (su[1] - su[0]) * i / cols, sv[0] + (sv[1] - sv[0]) * j / rows
            d = np.hypot(a - pu, b - pv)
            k = d < max(0.03, 0.6 * (sv[1] - sv[0]) / rows)
            out[j, i] = h[k].mean() if k.any() else h[np.argmin(d)]
    return out
