# Case study: the wing (Braziletto) - from an AI-generated GLB to a rigged, textured, flapping game asset

Single wing (white feathers + gold handle), 1.5 M triangles in, 760 + 120 quads out, one atlas, one rig. Everything below is reproducible with
`examples/wing/` (scripts) and `tools/` (the reusable parts). Conventions: Z up, front = -Y, metres. Project folder: `projects/wing/` (not in git);
the artist's choices and recordings are versioned in `dataset/` (see `docs/00-rules-and-tools/dataset-spec.md`).

## Who does what
| stage | actor | how |
|---|---|---|
| measure the reference, depth maps | agent | `tools/01-input-and-measurement/depth_map.py` |
| retopology of the white part (the front skin) | **artist, by hand** (recorded) | orthographic front view, extrude one point at a time + F, Face snap; `tools/general/session_recorder.py` |
| close the skin into a shell, handle parts | agent | `examples/wing/s1_prepare_for_uv.py` -> `tools/02-retopology/skin_close.py` |
| UV (one atlas, no overlap) and shape adjustments | **artist** | by hand; recovered afterwards with `tools/general/blend_diff.py` |
| bake, handle relief, rig, export | agent | `examples/wing/s2..s4`, run by `examples/wing/run_all.py` |

## Steps (with the numbers we got)
1. **Input and measurement.** The GLB (two wings glued together, 1.5 M tris) becomes `REFERENCE` in `draft/wing_01_ref.blend`; keep one wing. Front/back depth maps
   of the reference on a 2 mm grid (`depth_map`): front Y from -0.043 to 0.014 over the white part.
2. **Why the artist retopologizes.** Our automatic attempts (layered feathers + core + mirror, ring extrusion, chain sweep to continue the artist's mesh) gave
   loose feathers, crossing quads, or lost the depth ("a bunch of loose feathers"). The artist's method is what works, so the agent **records and continues it**
   (`docs/00-rules-and-tools/human-in-the-loop.md`). Rule kept: never replace or hide the artist's mesh; extend it.
3. **The artist's method** (read from 4 recordings, 87 -> 333 vertices; `dataset/retopology/wing`): vertices on the feather rims and tips with Face snap; one strip of
   2-4 rows x 5-9 columns per feather; the previous feather's border chain is reused as the first row; each strip sweeps across the feather to the opposite rim;
   the tip converges; shared vertices welded; progress from the leading edge downward. Result: one continuous skin, 333 vertices, 284 quads, no triangles.
4. **Closing the skin.** Solidify was tried and rejected: it offsets along normals and crumples the stepped feather skin. The artist asked for
   **extrude the border back and mirror**. `close_skin`: border extruded along +Y to the plane P (mean of the midpoints between skin and reference back,
   P = 0.0172 m), whole skin mirrored across P, ring welded: 760 quads, closed, same mesh inverted on both sides (good for UV and rig).
5. **Handle parts** (`examples/wing/support.py`): collar, neck, plate, eye (8-sided cylinders; caps = centre vertex + quads), arm and spine (4-sided bars along a polyline).
   Separate meshes, simple shapes, quads only, 120 quads in all. Arm and spine start INSIDE the plate and the plate is taller than the bars (otherwise the flat bar ends
   poked out of the plate).
6. **Touching, no slits.** The artist spotted gaps between handle and wing. `touch_parts` stretches the skin border (<6 cm from a part, x < 0.02) until it sinks 4 mm
   into the part (neighbours follow at 50 %); `pull_parts_to_shell` then pulls part vertices <2.5 cm from the shell onto it. The far tip of the skin is untouched.
   Measured afterwards: wing-arm 0.1 mm, wing-spine 0.5 mm, wing-eye 0.1 mm, all parts interpenetrating. Output: `draft/wing_11_mirror.blend`.
7. **Artist's UV and adjustments** (not automated). They joined everything into one object (`SUP_arm`, 894 vertices, 880 quads, two materials
   `WING_FEATHER` 760 / `WING_GOLD` 120), made an atlas of 91 islands without overlap, and **thinned the wing** from 85 mm to 47 mm mean thickness (front moved
   ~14 mm forward, back flattened; our 12 cm at the root was too thick). Recovered with `blend_diff.edit_record` into `dataset/adjust` and `dataset/uv`.
   From here on only the artist moves vertices; the pipeline never rebuilds the mesh.
8. **Bake** (`s2_bake.py`, `tools/04-uv-bake/bake_robust.py`, Cycles on the GPU, 2048): basecolor, normal, roughness, metallic, AO from `REFERENCE`.
   5.4 % invalid texels on the first pass, 1.1 % after the extrusion schedule (inpainted 26 k texels). The feathers came out well.
   The handle came out wrong: our simple shapes sit 2-5 cm from the sculpted original, so rays hit feathers or nothing (flat beige collar, dark plate).
9. **Handle texture, what did not work.** Sampling the original's colour by front projection and by normal rays gave pale "silver" with gold streaks (rays land on
   feathers). A flat procedural gold looked plain. TextureCraft (MCP) could not be used: its server had no `--read-root/--write-root`, so it could not read the mesh.
10. **Handle texture, what worked** (`s3_relief.py`, `tools/04-uv-bake/texel_paint.py`, `examples/wing/pattern_cabo.py`): paint the atlas texels of `WING_GOLD` from functions of the
    3D position (no UV dependence, so no seams): procedural gold (value noise, 5 octaves, dark-to-light ramp), engraving as a height field (darker, rougher, normal map from its
    gradient, AO), enamel for the white stars. Motifs: **Southern Cross** (5 stars) in white enamel on the collar front, wave line + diamonds around it, ring grooves on the caps,
    8-petal rosette on the plate, spiral on the eye, edge lines + chevrons + studs on the arm and spine, 4 rings on the neck. Each shell is found by connectivity and labelled
    (arm = longest in X, spine = lowest in Z, the rest sorted by X). Margin of 8 px so mip-maps do not bleed.
11. **Rig** (`s4_rig_export.py`, `tools/06-rig/rig_chain.py`): bones Root (collar) -> W1 -> W2 -> W3 along the wing and Fan_Low for the lower feathers. Numeric weights by X
    (0.2 m smooth blend per joint), Fan_Low by region, collar/neck/plate/eye pinned to Root; 0 unweighted vertices, at most 3 groups per vertex. Action `Wing_Flap`: 24-frame
    loop, Root 12 deg, W1 8, W2 8, W3 7, Fan_Low -5, each bone delayed by 0.07-0.21 of the cycle (a travelling wave). Bone heat was not used (overlapping shells).
12. **Export** (`tools/05-delivery/export_package.py`): `wing_15_final.blend` keeps the white `Tint` multiplier; FBX and GLB are exported with plain image materials (they cannot carry
    the Tint: recolor with the material's `albedo_color` in Godot), animation baked, maps copied next to the files, PBR previews rendered with Cycles.

## Reproduce
```
python examples/wing/run_all.py prepare --skin-blend <artist's skin .blend>       # step 1 (-> draft/wing_11_mirror.blend); then the artist does the UV
python examples/wing/run_all.py finish  --uv-blend <artist's UV .blend>           # bake -> relief -> rig -> export (-> projects/wing/export/)
```
Needs Blender 5.3 (`BLENDER_EXE`), a GPU for the bake, the reference as `REFERENCE` in the skin blend. Reproduced here: step 6 within 1.5 mm of the original; steps 8-12 re-run from the artist's UV file.

## Known limits
- The reference's gold detail is not baked (the handle is procedural, by design); the handle silhouette is simple shapes. More silhouette detail = new geometry = new UV.
- The baked basecolor of the feathers is not pure white (shading, warm tint); the Tint multiplies it, so the hue shifts.
- Frame 1 of the flap loop is not the rest pose; with no action the model is at rest.
- The UV passes overlap and bounds but not the 8 px gap rule (`qa_uv`); we left the artist's layout alone.
- The shape QA battery (`tools/03-qa`) is tube/hair oriented: `shape`, `floating`, `attach` fail on this asset by construction; mesh and budget pass (1552 tris-eq of 3000).
