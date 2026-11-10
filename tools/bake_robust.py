"""Bake with validation + automatic repair (Blender, MCP).
For every texel we also bake WHERE the ray hit the reference (world position) and whether it hit a
BACKFACE. A texel is valid if: the ray hit something, it was a front face, and the hit is within
`max_dist` of the low-poly surface. Invalid texels are re-baked with other extrusion/ray settings
(schedule); whatever is still invalid is inpainted from the same UV island. Returns a report with
the worst faces so geometry can be fixed where the fit is bad.
  r = bake_robust(["chest_base","chest_lid"], "REFERENCE", outdir, "chest")
"""
import bpy, numpy as np
T_ = r"C:\Users\epers\Desktop\retopologizer\tools"
for _f in ("bake_maps.py", "qa_uv.py", "bake_inpaint.py"):
    exec(open(T_ + "\\" + _f).read())
SENTINEL = 1000.0


def _emission_mat(name, socket):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    g = nt.nodes.new("ShaderNodeNewGeometry")
    nt.links.new(g.outputs[socket], em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs[0])
    return m


def _img(name, size, fill, float_=True):
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    img = bpy.data.images.new(name, size, size, alpha=False, float_buffer=float_)
    img.colorspace_settings.name = 'Non-Color'
    a = np.full((size, size, 4), fill, np.float32); a[..., 3] = 1
    img.pixels.foreach_set(a.ravel())
    return img


def _read(img):
    a = np.empty(len(img.pixels), np.float32); img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def _bake(J, H, typ, flt, img, node_mat, high_mat=None, selected=True):
    nt = node_mat.node_tree
    node = nt.nodes.get("BAKE_TARGET") or nt.nodes.new("ShaderNodeTexImage")
    node.name = "BAKE_TARGET"; node.image = img
    for n in nt.nodes:
        n.select = False
    node.select = True; nt.nodes.active = node
    if high_mat is not None:
        H.material_slots[0].material = high_mat
    bpy.context.scene.render.bake.use_selected_to_active = selected
    bpy.ops.object.select_all(action='DESELECT')
    if selected:
        H.select_set(True)
    J.select_set(True); bpy.context.view_layer.objects.active = J
    bpy.ops.object.bake(type=typ, pass_filter=flt, save_mode='INTERNAL')


def save_png(arr, path, colorspace, name):
    h, w = arr.shape[:2]
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    img = bpy.data.images.new(name, w, h, alpha=False)
    img.colorspace_settings.name = colorspace
    a = arr.copy(); a[..., 3] = 1
    img.pixels.foreach_set(a.ravel())
    img.filepath_raw = path; img.file_format = 'PNG'; img.save()
    return img


def bake_robust(lows, high, outdir, prefix, size=2048, schedule=((0.10, 0.20), (0.05, 0.10), (0.03, 0.06),
                (0.20, 0.40), (0.02, 0.04)), max_dist=0.05, stop_frac=2e-4, margin_px=8, high_mat="Material.001"):
    sc = bpy.context.scene; b = sc.render.bake
    old = (sc.cycles.samples, sc.cycles.use_denoising)
    sc.render.engine = 'CYCLES'; sc.cycles.use_denoising = False
    b.target = 'IMAGE_TEXTURES'; b.margin = margin_px * size // 2048; b.margin_type = 'EXTEND'
    uv = qa_uv(lows, size=size, maps=True)
    ids, pid, poly_of = uv["_ids"], uv["_pid"], uv["_poly_of"]; mask = ids > 0
    Hh = bpy.data.objects[high]; Hh.hide_set(False)   # hidden ref => "No valid selected objects"
    for o in [o for o in bpy.data.objects if o.name.startswith("_bake_joined")]:
        bpy.data.objects.remove(o)
    slot0 = Hh.material_slots[0].material
    mat_low = bpy.data.objects[lows[0]].material_slots[0].material
    J = join_copy(lows)
    m_pos, m_back = _emission_mat("_v_pos", "Position"), _emission_mat("_v_back", "Backfacing")
    hm = bpy.data.materials[high_mat]
    # low-poly surface position per texel (self bake)
    for s in J.material_slots:
        s.material = m_pos
    img = _img("_v_lowpos", size, 0.0)
    sc.cycles.samples = 1
    _bake(J, Hh, 'EMIT', set(), img, m_pos, selected=False)
    lowpos = _read(img)[..., :3]
    for s in J.material_slots:
        s.material = mat_low
    final = {}; valid = np.zeros(mask.shape, bool); dist_map = np.full(mask.shape, np.nan, np.float32)
    log = []
    for k, (ex, mr) in enumerate(schedule):
        b.cage_extrusion = ex; b.max_ray_distance = mr; b.use_cage = False
        got = {}
        for name, (typ, flt, cs, col, smp) in MAPS.items():
            im = _img("_b_" + name, size, 0.0); im.colorspace_settings.name = cs
            sc.cycles.samples = smp
            tmp = _metal_material(hm) if name == "metallic" else None
            _bake(J, Hh, typ, flt, im, mat_low, high_mat=tmp or hm)
            if tmp:
                bpy.data.materials.remove(tmp)
            got[name] = _read(im)
        sc.cycles.samples = 1
        hit_i = _img("_v_hit", size, SENTINEL); back_i = _img("_v_back", size, 0.0)
        _bake(J, Hh, 'EMIT', set(), hit_i, mat_low, high_mat=m_pos)
        _bake(J, Hh, 'EMIT', set(), back_i, mat_low, high_mat=m_back)
        hit, back = _read(hit_i)[..., :3], _read(back_i)[..., 0]
        dist = np.linalg.norm(hit - lowpos, axis=2)
        ok = mask & (hit[..., 0] < SENTINEL / 2) & (back < 0.5) & (dist < max_dist)
        new = ok & ~valid
        if k == 0:
            final = {n: a.copy() for n, a in got.items()}; first_bad = mask & ~ok
        for n in final:
            final[n][new] = got[n][new]
        dist_map[new] = dist[new]; valid |= new
        frac = float((mask & ~valid).sum() / mask.sum())
        log.append({"extrusion": ex, "max_ray": mr, "invalid_after_pct": round(100 * frac, 3)})
        if frac < stop_frac:
            break
    H_ = slot0; Hh.material_slots[0].material = slot0
    left = int((mask & ~valid).sum())
    for n in final:   # repair what no setting could bake, then pad the islands
        final[n], _ = inpaint(final[n], valid, ids)
        final[n] = dilate(final[n], ids, margin_px)
    for n, (typ, flt, cs, col, smp) in MAPS.items():
        save_png(final[n], f"{outdir}/{prefix}_{n}.png", cs, "bake_" + n)
    bpy.data.objects.remove(J)
    for m in (m_pos, m_back):
        bpy.data.materials.remove(m)
    sc.cycles.samples, sc.cycles.use_denoising = old
    worst = {}
    for p in np.unique(pid[mask & ~valid]):
        worst[poly_of[p]] = worst.get(poly_of[p], 0) + int(((pid == p) & ~valid & mask).sum())
    bad_fit = {}
    for p in np.unique(pid[mask]):
        d = dist_map[(pid == p) & valid]
        if d.size and np.nanmean(d) > 0.012:
            bad_fit[poly_of[p]] = round(float(np.nanmean(d)) * 1000, 1)
    return {"passes": log, "invalid_first_pass_pct": round(100 * float(first_bad.sum() / mask.sum()), 3),
            "inpainted_texels": left, "worst_unbaked_faces": sorted(worst.items(), key=lambda x: -x[1])[:12],
            "poor_fit_faces_mm": sorted(bad_fit.items(), key=lambda x: -x[1])[:15],
            "_first_bad": first_bad, "_valid": valid, "_ids": ids}
