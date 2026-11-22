"""Paint maps straight into the UV atlas texels of one material (procedural detail the high-poly bake cannot give).
Inside Blender: exec(open(...).read()), then
  T = texels(ob, "WING_GOLD", 2048)                       # world position, texel, tangent T=dP/du and bitangent B=dP/dv of every texel
  nrm = height_to_normal(T, lambda P: height(P), depth=0.0004)   # tangent-space normal (OpenGL) from a height function of the 3D position
  write_map(path, T, colours, 2048, blocked=T["other"], margin=8)  # raw values (use Non-Color), margin extended into empty texels
A height function of the 3D position (not of the UV) has no seams between islands and works with any unwrap.
Texel (px, py): py counts from the BOTTOM of the image (Blender's convention)."""
import bpy, numpy as np


def texels(ob, material, size=2048):
    me = ob.data; M = ob.matrix_world; mats = [m.name for m in me.materials]; uvl = me.uv_layers.active.data; me.calc_loop_triangles()
    P, TX, TG, BG, FA = [], [], [], [], []; other = np.zeros((size, size), bool)
    for t in me.loop_triangles:
        uv = np.array([uvl[l].uv[:] for l in t.loops]) * size
        if mats[me.polygons[t.polygon_index].material_index] != material:
            other[int(uv[:, 1].min()):int(uv[:, 1].max()) + 1, int(uv[:, 0].min()):int(uv[:, 0].max()) + 1] = True; continue
        co = np.array([(M @ me.vertices[i].co)[:] for i in t.vertices]); a, b, c = uv
        A = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
        if abs(np.linalg.det(A)) < 1e-9:
            continue
        Ai = np.linalg.inv(A); E1, E2 = co[1] - co[0], co[2] - co[0]
        Tg = E1 * Ai[0, 0] + E2 * Ai[1, 0]; Bg = E1 * Ai[0, 1] + E2 * Ai[1, 1]; Tg /= np.linalg.norm(Tg) + 1e-12; Bg /= np.linalg.norm(Bg) + 1e-12
        x0, x1 = int(uv[:, 0].min()), int(uv[:, 0].max()) + 1; y0, y1 = int(uv[:, 1].min()), int(uv[:, 1].max()) + 1
        gx, gy = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1)); px = np.stack([gx.ravel() + .5, gy.ravel() + .5], 1)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        l1 = ((b[1] - c[1]) * (px[:, 0] - c[0]) + (c[0] - b[0]) * (px[:, 1] - c[1])) / d
        l2 = ((c[1] - a[1]) * (px[:, 0] - c[0]) + (a[0] - c[0]) * (px[:, 1] - c[1])) / d; l3 = 1 - l1 - l2
        k = (l1 >= -.02) & (l2 >= -.02) & (l3 >= -.02) & (px[:, 0] < size) & (px[:, 1] < size); n = int(k.sum())
        P.append(np.stack([l1[k], l2[k], l3[k]], 1) @ co); TX.append(np.floor(px[k]).astype(int)); FA += [t.polygon_index] * n
        TG.append(np.tile(Tg, (n, 1))); BG.append(np.tile(Bg, (n, 1)))
    return {"P": np.concatenate(P), "TX": np.concatenate(TX), "T": np.concatenate(TG), "B": np.concatenate(BG), "face": np.array(FA), "other": other}


def height_to_normal(T, fn, depth=0.0004, eps=0.0005):
    """fn(P) -> height in 0..1 (1 = raised). The relief is `depth` metres deep. Returns (n, 3) in 0..1, ready for a normal-map PNG."""
    P = T["P"]; dT = (fn(P + eps * T["T"]) - fn(P - eps * T["T"])) / (2 * eps); dB = (fn(P + eps * T["B"]) - fn(P - eps * T["B"])) / (2 * eps)
    nx, ny = -depth * dT, -depth * dB; ln = np.sqrt(nx ** 2 + ny ** 2 + 1)
    return np.stack([nx / ln, ny / ln, 1 / ln], 1) * 0.5 + 0.5


def write_map(path, T, values, size=2048, blocked=None, margin=8):
    """Write `values` ((n,) grey or (n,3) RGB, raw 0..1) into the texels of T inside the existing PNG `path`; grow the border `margin` px
    into texels that are empty (not in `blocked`, e.g. T['other'] = islands of the other materials) so mip-maps do not bleed."""
    img = bpy.data.images.load(path, check_existing=False); img.colorspace_settings.name = "Non-Color"
    buf = np.empty(size * size * 4, np.float32); img.pixels.foreach_get(buf); a = buf.reshape(size, size, 4)
    v = np.clip(values, 0, 1); v = np.repeat(v[:, None], 3, 1) if v.ndim == 1 else v[:, :3]
    a[T["TX"][:, 1], T["TX"][:, 0], :3] = v; a[T["TX"][:, 1], T["TX"][:, 0], 3] = 1
    cur = np.zeros((size, size), bool); cur[T["TX"][:, 1], T["TX"][:, 0]] = True; blocked = np.zeros_like(cur) if blocked is None else blocked
    for _ in range(margin):
        new = np.zeros_like(cur)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            m = np.roll(np.roll(cur, dy, 0), dx, 1) & ~cur & ~blocked & ~new; a[m] = np.roll(np.roll(a, dy, 0), dx, 1)[m]; new |= m
        cur |= new
    img.pixels.foreach_set(a.ravel()); img.filepath_raw = path; img.file_format = 'PNG'; img.save(); bpy.data.images.remove(img)
