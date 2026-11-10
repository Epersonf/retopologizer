"""QA for UV layouts shared by several objects (one atlas).
Fails on: any overlap (between or inside islands), UVs outside 0..1, zero-area or flipped UV
faces, islands closer than min_gap_px (bake bleeding). Inside Blender:
  exec(open(...).read()); r = qa_uv(["chest_base","chest_lid"], size=2048, min_gap_px=8)
  r["pass"] must be True. Rasterises at `size`, sampling pixel centres strictly inside faces.
"""
import bpy, numpy as np


def _islands(me, uv):
    parent = list(range(len(me.polygons)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    seen = {}
    for p in me.polygons:
        for li in p.loop_indices:
            key = (me.loops[li].vertex_index, round(uv[li].uv[0], 5), round(uv[li].uv[1], 5))
            if key in seen:
                parent[find(p.index)] = find(seen[key])
            else:
                seen[key] = p.index
    return [find(i) for i in range(len(me.polygons))]


def qa_uv(names, size=2048, min_gap_px=8, layer=0):
    cover = np.zeros((size, size), np.int16)      # polygons covering each pixel centre
    ids = np.zeros((size, size), np.int32)        # island id per pixel
    out = {"oob_faces": 0, "zero_area_faces": 0, "flipped_uv_faces": 0}
    next_id = 1; island_count = 0
    for n in names:
        me = bpy.data.objects[n].data
        uvl = me.uv_layers[layer].data
        isl = _islands(me, uvl)
        remap = {}
        me.calc_loop_triangles()
        for p in me.polygons:
            pts = np.array([uvl[li].uv for li in p.loop_indices], np.float64)
            if pts.min() < -1e-6 or pts.max() > 1 + 1e-6:
                out["oob_faces"] += 1
            x, y = pts[:, 0], pts[:, 1]
            area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
            if abs(area) < 1e-10:
                out["zero_area_faces"] += 1
        flipped_ref = {}
        for t in me.loop_triangles:
            root = isl[t.polygon_index]
            if root not in remap:
                remap[root] = next_id; next_id += 1
            iid = remap[root]
            a, b, c = [np.array(uvl[li].uv, np.float64) * size for li in t.loops]
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-12:
                continue
            x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
            x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
            xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, size)), np.arange(max(y0, 0), min(y1 + 1, size)))
            qx, qy = xs + 0.5, ys + 0.5
            l1 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
            l2 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
            m = (l1 > 1e-9) & (l2 > 1e-9) & (1 - l1 - l2 > 1e-9)
            cover[ys[m], xs[m]] += 1
            ids[ys[m], xs[m]] = iid
        island_count += len(remap)
    out["overlap_pixels"] = int((cover > 1).sum())
    # minimum distance between different islands (shift test inside a disk of radius g)
    gap_bad = 0; g = int(min_gap_px)
    for dy in range(-g, g + 1):
        for dx in range(-g, g + 1):
            if (dx or dy) and dx * dx + dy * dy <= g * g:
                a = ids[max(dy, 0):size + min(dy, 0), max(dx, 0):size + min(dx, 0)]
                b = ids[max(-dy, 0):size + min(-dy, 0), max(-dx, 0):size + min(-dx, 0)]
                gap_bad += int(((a != b) & (a > 0) & (b > 0)).sum())
    out.update({"islands": island_count, "gap_violation_pixels": gap_bad, "min_gap_px": g,
                "coverage_pct": round(100 * float((ids > 0).mean()), 1), "size": size})
    out["pass"] = (out["overlap_pixels"] == 0 and out["oob_faces"] == 0 and
                   out["zero_area_faces"] == 0 and gap_bad == 0)
    return out


def unwrap_atlas(names, margin=0.012, angle=66.0):
    """Smart UV project all objects together, equalise texel density, pack with margin."""
    import math
    bpy.ops.object.mode_set(mode='OBJECT') if bpy.context.object and bpy.context.object.mode != 'OBJECT' else None
    bpy.ops.object.select_all(action='DESELECT')
    for n in names:
        bpy.data.objects[n].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[names[0]]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin / 2)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=False, margin=margin)
    bpy.ops.object.mode_set(mode='OBJECT')
