# UV, PBR maps and bake (high → low)

Prerequisite: mesh approved in QA (`docs/03-qa/qa.md`). After the UV, do not run builders again (they recreate the mesh and the UV is lost):
only move vertices.

## New model with no high-poly (nothing to bake from)
When the asset is designed here and there is no reference to bake, the texture is **painted in TextureCraft** (MCP
`texturecraft`: `project_new`/`mesh_import` → `paint_stroke`, `resource_import`, `viewport_render` → `textures_export`),
never a flat colour or a procedural noise left as the final. Order:
1. **Ask the user the style before painting** (hand-painted cartoon, stylized PBR, palette, materials, wear, mood,
   references). Do not guess; show 1-2 viewport renders and adjust before exporting.
2. UV first (rules below, `qa_uv` passing), then import the low into TextureCraft with that UV.
3. Export basecolor + normal (roughness/metallic/AO if the asset needs them) at the project size; the game keeps only
   albedo and normal for metal (`docs/05-delivery/delivery.md`).
4. Report which maps came from TextureCraft and which were not painted.

## UV
- **One 0–1 atlas for all the asset's pieces**: one material, one texture per map, one draw call.
- **Zero overlap**: the bake writes one texel per place; mirrored or stacked UVs don't pass `qa_uv`.
- **Hidden seams** (underneath, behind, inside, in corners) and **every hard corner with a seam**, otherwise the normal
  map marks the corner.
- **Equal texel density** across the pieces; straight islands when possible (less waste and aliasing).
- **Gap ≥ 8 px at 2048** between islands, so mip-maps and the bake margin don't bleed into the neighbor.
- `unwrap_atlas(names, margin=0.012, angle=66)` (`qa_uv.py`: smart project + equal density + pack) is good for
  unblocking and measuring; 89° folded the arc islands. In general the user does the UV by hand: respect theirs.
- Check: `qa_uv(names, size=2048, min_gap_px=8)["pass"]`.

## PBR maps
| map | color space | stores |
|---|---|---|
| basecolor | sRGB | color, no light or shadow |
| normal (tangent) | Non-Color | fine relief of the high; Blender and Godot use OpenGL (Y+), Unreal uses DirectX (invert green) |
| roughness | Non-Color | 0 smooth and glossy, 1 matte |
| metallic | Non-Color | 0 dielectric, 1 metal (almost always one or the other) |
| AO | Non-Color | cavity occlusion |

In glTF, roughness and metallic come in a single map (G = roughness, B = metallic; R = AO in the ORM). The high's material
must be wired this way (albedo, metal-rough, normal) for the bake to read the channels.

## Robust bake — Cycles GPU (`bake_robust.py`)
> **Always on the GPU.** Before any Cycles bake or render: `use_gpu()` (`tools/general/cycles_gpu.py`; `bake_robust`,
> `bake_all` and `render_thumbnail` already call it and the report carries `device`). `scene.cycles.device = 'GPU'` alone is not enough,
> especially in the worker/background: the type (OPTIX/CUDA/HIP...) is needed in the preferences and the devices
> enabled. On the CPU a 2048 bake takes many times longer. If `CPU (no GPU found)` comes back, tell the user.

`r = bake_robust(["chest_base", "chest_lid"], "REFERENCE", outdir, "chest")`
1. **One bake for all pieces, in one image**: the script joins copies of the pieces (world space, UV intact) into a temporary
   active object and does selected-to-active. Baking piece by piece into the same image erased the first one.
2. **Extrusion and max ray**: inverted normal (blue ≈ 0) = the ray starts inside the reference (extrusion smaller than the
   low↔high deviation). Rule: extrusion ≈ 3–4× the p95 of `compare_mesh`. Chest: 0.03 → 31% inverted; 0.10/0.20 → 6%.
3. **Per-texel validation**: it also bakes where the ray hit and whether it was a backface. Valid = found a hit + front face + hit
   within < `max_dist` (default 0.05 m) of the low. Invalid ones are re-baked with the next extrusion/ray pair of the `schedule`
   (0.10/0.20 → 0.05/0.10 → 0.03/0.06 → 0.20/0.40 → 0.02/0.04) and the rest becomes inpaint inside the same UV island
   (`bake_inpaint.py`, an automatic clone); islands dilated at the margin.
4. **Report**: `worst_unbaked_faces` and `poor_fit_faces_mm` (low faces far from the ref: move vertices), plus an optional
   mask map (green ok, yellow recovered, red inpaint). Chest: 1.27% invalid on the 1st pass → 0.43%.
5. Maps: basecolor, normal, roughness, metallic (via emission of the B channel), AO. 2048 px, margin 8 px (EXTEND, scales
   with size). `high_mat=` is the name of the high's material (default `"Material.001"`).
6. **Check**: % of black faces in the basecolor per piece (< 3%) and a workbench TEXTURE render.

Simple bake: `bake_all(lows, high, outdir, prefix, size=2048, extrusion=0.03, max_ray=0.06, cage_dist=None)`
(`bake_maps.py`). **Cage** only if the default fails on hard corners: duplicate the low and `Alt+S` (push along normals)
until it covers the whole reference; `cage_dist=<m>` does this by script. A thin cage (0.02) doesn't fix it: it must cover the
largest deviation.

## Artifacts: what to look at
| symptom | cause | fix |
|---|---|---|
| black faces, inverted normal | extrusion smaller than the deviation | extrusion 3–4× p95, or cage |
| black squares in Cycles | coplanar faces (z-fight) | `qa_zfight`, space 2–4 mm apart |
| blur on plates and clasps | piece 2–3 cm beyond the ref (far ray) | move the vertices to the surface |
| "No valid selected objects" | reference hidden (`hide_set`) or locked (`hide_select`) | visible and selectable during the bake (`bake_robust` already does this and restores) |
| slow bake (minutes for 2048) | Cycles on the CPU | `use_gpu()` first; check `device` in the report |
| seam marked in the normal map | hard corner without a UV seam | seam on the corner |

## Adjusting after the UV or the bake (without breaking the UV)
- Start from a backup in `draft/backups/`; change only vertex positions (same topology).
- Snapping all vertices to the nearest point crushed small plates: measure the ref's profiles per region and
  offset per region.
- High distance at corners = box corner against the ref's rounded bevel: expected.
- Afterwards: `qa_all`, rebake, check again.

## Procedural detail on top of the bake (`texel_paint.py`)
When part of the low-poly is a simple stand-in for sculpted detail (the wing's handle: cylinders and bars 2-5 cm from the original), the high-to-low bake gives wrong
colours (rays hit neighbours). Paint those texels from functions of the 3D position instead: `texels(ob, material, size)` gives world position and tangent frame per texel,
`height_to_normal(T, fn)` turns a height function into a tangent-space normal map, `write_map(...)` writes values with a margin. Gold = value noise + engraving (darker, rougher),
enamel masks for inlays. No UV dependence = no seams between islands. Worked example: `docs/08-cases/wing.md`, `examples/wing/pattern_cabo.py`.
Check with a PBR render (Cycles, sky light): workbench does not show metal.
