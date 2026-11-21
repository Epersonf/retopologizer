# Case study: the sword (Braziletto) - from an AI-generated GLB to a game item and a Fab listing

"Espada de Braziletto": 1.5 M triangles in, 1464 triangles / 1 material / 2048 PBR set out; item 28 of the game, with a
fire effect, and a Fab listing. Project folder `projects/espada-braziletto/` (not in git; scripts `b1.py`, `d1.py`, `m4.py`...
are its history, the reusable parts are now in `tools/`). Conventions: Z up, front = -Y, metres, sword vertical, pommel z = 0, tip z ~ 1.19.
Same shape as `wing.md`, with a second lesson: **an AI that skipped the pipeline wasted a whole session** (step 0).

## Who does what
| stage | actor | how |
|---|---|---|
| front shell of pommel, grip, blade, diamond, right guard | **artist, by hand** (recorded) | Face snap on the ref, strips along the silhouette |
| left guard, UV, shape adjustments | **artist** | after the agent's mirrored left hook was rejected |
| continuing the artist's line (grip, blade), closing, QA, bake, delivery | agent | `s3`-`s5`, `q1`-`q5`, `b1`, `d1` |
| straightening + symmetry, red boost, texture retouch | agent (artist asks, looks at renders) | `symmetrize.py`, `texturecraft_cli.py` |
| game item + fire effect, Fab listing | agent | Braziletto `docs/models-3d.md`, `docs/05-delivery/fab-upload.md` |

## Steps (with what happened)
0. **The failed attempt.** Codex was asked to do the sword and built it with automatic builders (`build_sword_v2.py`,
   `construct_sword.py`, `build_surface_retopology.py`), a mesh that was not faithful. Cause: the docs let an AI read them and still
   skip the pipeline. Fix (commit 658d25b, then the "new model" notes): README rule 7 ("from scratch" does not turn rules off),
   a 6-item **Definition of done**, `AGENTS.md`/`CLAUDE.md` with the same list, "ornamented parts need snap", OBJ = checkpoint only,
   and for a model with no high-poly: paint in TextureCraft and ask the user the style first. Read those before starting.
1. **Input.** AI-generated GLB (~1.5 M tris, `input/*.glb`) imported as `REFERENCE`; reference views in `draft/reference/`.
   The artist rotated the ref upright **after** saving, so the matrix was not in the .blend: recovered from the recorded operators
   (`events.jsonl`; sign brute force against the low-poly distance) and set with `ref.matrix_world` (`apply_ref.py`).
2. **The artist starts again by hand, recorded** (`record_session.py` -> `session/rec_01..10`). Method read from the recordings:
   front-only shell (no mirror modifier), vertices on the ref with Face snap, quad strips along the silhouette, a diamond medallion
   with a tiny centre quad. Blender froze once when they entered Edit Mode on the 1.5 M ref: the ref is select-locked (`blender-automation.md`).
   If a recording is all that survives, `tools/general/rec_rebuild.py` rebuilds the mesh from it (`rebuild_rec04.py` was the first version).
3. **Continuing their line.** Pommel and grip, then the blade as strips, with Y-ray snapping on the ref (`fslib.Ref.front/sil`; the same
   job as `snap_surface.Surface.ray`). Then the left hook: our eye-placed rows and a plain mirror gave edges inside the ref -
   "o chifre esquerdo ficou ruim". **Rule learnt: show images early, check in perspective too, and when the artist offers
   ("deixe eu fazer a guarda") let them.** They built the right guard and the left one; we only mirrored a replacement (`g3_mirror.py`: cut
   at the diamond, mirror the right half with a fresh snap) and they corrected it (rec_08).
4. **Closing the shell.** As in the wing: back = Y mirror, border clamped to y <= -3 mm so the side strip does not degenerate, side strip of
   quads on every border edge (`s5_close.py`; same idea as `skin_close.close_skin`): 0 bad edges, positive volume.
5. **UV and adjustments (artist, rec_09).** Then QA (`q1`-`q5`): UV repack (`pack_islands(rotate=False, margin=0.010)`) -> 94 islands, 0 overlap,
   gap >= 8 px at 2048, 29.5 % coverage; guard hooks snapped to the ref depth (vertices only, UV intact); one concave UV quad fixed.
6. **Bake** (`b1.py`, `bake_robust`, Cycles OPTIX, 2048). The `REFERENCE` in the .blend had lost its material (IndexError): re-import the GLB
   and give the low a material slot first. 0.348 % invalid texels on pass 1, 0.017 % after pass 2, 214 texels inpainted.
7. **Delivery v3** (`d1.py`): `wire_pbr`, PBR previews, FBX + GLB. AgX washed the red out: previews use the **Standard** view transform.
8. **The artist sees it: the sword is crooked.** Bake is done, so we leave the ref: shear x by the centre line per z (15 knots; `axis_knots` measures them), cut at x = 0, keep the right half, mirror it **with the same UVs** (`symmetrize.py`): 734 verts, 728 quads + 8 tris, closed.
   The mirrored UV overlaps on purpose (both halves share the texture); `qa_uv` overlap is expected and must be said in the listing.
   The saved blend came out with an empty material ("cadê a textura?"): `t1.py` re-wires the maps. Look at the render before saying done.
9. **Colour.** "Muito brilhante, mais força no vermelho": multiply the base colour (a first boost went coral; target (1.02, 0.50, 0.48)),
   raise roughness. No metal in the maps (metal without reflections goes black in Godot).
10. **TextureCraft** (the user insisted: "tem que usar o texture craft"). The MCP server had no file roots, so the **CLI** was used
    (`docs/04-uv-bake/texturecraft-cli.md`): maps imported as layers, procedural detail (edge wear, dirt, sharpen) = v4; then
    hand-painted retouch of the blurry guard hooks and volutes through a saved camera "Guarda" (left hook strokes mirrored) = v5.
    `tool.strokeUv` was offset on the mirrored UV; 3D strokes through the camera worked.
11. **Crystal (v6).** "Cristal mais chamativo, bem vermelho com roughness altíssimo": faces picked by position (`c1.py`: |x| < 4.2 cm,
    y < -1.2 cm, 0.296 < z < 0.372), their UV polygons as a mask (`cry_mask.png`), saturated red + roughness 0.97 + metallic 0 written
    into the maps. Before/after sheets: `output/antes_depois.png`, `output/cristal_antes_depois.png` (`before_after.py`).
12. **Into the game** (Braziletto repo). `item_28.glb` through `docs/tooling/build_melee_gear.py` (`SPECS["item_28"]`, grip at 0.117 of the length),
    client-only fire (`SwordFire`: lit in combat, ignites on attack/cast, single flame sprite on the sword axis, trail on the strike).
    Feedback that shaped it: square particles -> one real flame sprite; orange wash -> no light/glow. Details: Braziletto `docs/models-3d.md`.
13. **Listing** (`listing_shots.py`, `fab_package.py`, `fab-upload.md`): thumbnail 1920x1080 + 2 detail images, `description.md` (says 1464 tris,
    mirrored UV), one FBX zip (Fab converts to GLTF/GLB/USDZ). Standard licence, 1.99 / 4.99 USD. **Submitted for review**; automatic publication.

## Final numbers
1464 tris (728 quads + 8 tris), 734 verts, 1 material, 5 maps 2048, 1.19 x 0.33 x 0.06 m, UV 94 islands (mirrored halves overlap).

## What did not pass / was not verified
- The 8 triangles (pommel base, grip top) were kept and reported, not hidden.
- `qa.py` fit on the closed pre-symmetry mesh: worst IoU 0.72 (< 0.80) at the guard hooks (shell +-24 mm deep vs +-34 mm in the ref); `shape`: thin ornaments.
  Not re-run on the symmetric mesh.
- Not tested in a live match (other players, mounted). The Fab AI-usage question was answered **No** by the user, although the shape
  comes from an AI reference: check Fab's current rule before publishing the next one.

## Lessons (all of them cost time)
1. Read every stage guide first; "from scratch" never turns the rules off. 2. Show an image after each risky step; verify in perspective.
3. The artist's open Blender is read-only; work on copies; recordings are a backup. 4. A .blend can lose the ref's material and the low's slot:
check before the bake. 5. Preview with Standard, not AgX, when the asset is saturated red. 6. Symmetry after the bake = mirrored UV; say so.
7. Python writes with `encoding="utf-8"`; JSON for TextureCraft without a BOM.

## New tools born here
`tools/02-retopology/symmetrize.py`, `tools/general/rec_rebuild.py`, `tools/04-uv-bake/texturecraft_cli.py`,
`tools/05-delivery/{listing_shots,fab_package,before_after}.py`. Candidates not built yet (needs the next listing to test): a browser-harness
script that fills the Fab form (`fab-upload.md` has every selector), and a reference-matrix recovery from `events.jsonl`.
