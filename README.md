# retopologizer

Turns AI-generated 3D models (Hunyuan3D and the like: 500k+ triangles, dirty mesh, no topology) into game assets:
hand-made low-poly with snap onto the reference, UV, baked textures, QA, FBX, Mixamo-style rig, Godot
and a store page (Fab). Everything runs in Blender by script, driven by an agent: you.

This README is the entry point. Read the rules and the way of working, find the stage you are at and open only its
guide; each guide points to the next.

## Non-negotiable rules
1. **Retopology is always manual**: every vertex is decided and snapped onto the reference. Never QuadriFlow, Remesh,
   Instant Meshes or Decimate to generate the delivered mesh, not even "as a first pass" (`docs/00-rules-and-tools/retopology-rules.md`).
2. **Quads only**: the delivered retopology has no triangles and no n-gons (`topo_qa(...)["quad_only"]`).
3. Automatic tools **measure and check** (raycast, BVH, fit, QA); they do not generate the mesh.
4. The reference is never edited (Edit Mode on a 500k-tri mesh freezes Blender) and never goes to `output/` or git.
5. The Blender the user has open (MCP, port 9876) is **read-only**: build and render on a copy, in the worker
   (port 9877) or in one-shot (`docs/00-rules-and-tools/blender-automation.md`).
6. Files of at most 150 lines (split by responsibility). Commit only when the user asks, never with
   `Co-Authored-By` or AI attribution.
7. **"Do it from scratch / without the manual" does not switch rules 1-6 off.** If the user says so, confirm once what
   they want to skip (e.g. the Fab text, not the manual retopology) before building anything.

## Definition of done
A request such as "retopologize this model" or "do the retopology of X" means the **whole pipeline up to stage 7**
(stage 8 only if it is a character; stages 9 and **10, the post mortem,** whenever the model is delivered to a game or a store), not stage 2. Do not say "done" before every line below is true and shown:
1. **Faithful**: the `qa.py` battery (`docs/03-qa/qa.md`) passes, `fit` included (mean IoU ≥ 0.88, worst ≥ 0.80), and
   `fit_report` / `compare_mesh` give mean, p95 and max in mm. Ornamented parts (volutas, filigree, medallions) must
   follow the ref's shape: if `wire_overlay` shows a part reduced to a "mass", the mesh is not ready, however clean it is.
2. **Quads only** and clean (`topo_qa`, `qa_mesh`): 0 open borders, non-manifold, duplicates, **0 intersecting faces** (`qa_intersect`).
3. **UV** with no overlap, inside 0-1, islands ≥ 8 px apart at 2048 (`qa_uv`). Never bake over a failing UV.
4. **Bake** (basecolor, normal, roughness, metallic, AO) with `bake_robust`; report the invalid-texel %.
   **New model with no high-poly**: nothing to bake, so paint the texture in **TextureCraft** and **ask the user the style
   first** (`docs/04-uv-bake/uv-bake.md`).
5. **Delivery**: FBX/GLB + PNGs in `output/`, lean `.blend`, project `README.md` with counts and errors.
6. **Shown**: one `wire_overlay` image, one render with the baked texture, and a list of what was NOT checked.
7. **Post mortem done** after the last delivery (game wired, listing submitted, files handed over): `projects/<name>/POST_MORTEM.md`, tools
   created, old docs corrected, case written (`docs/05-delivery/post-mortem.md`, `python tools/general/post_mortem.py <name>`).
   **Mandatory**: an asset without its post mortem is not done.

Stopping earlier (e.g. at the OBJ of a part, `docs/02-retopology/retopo-by-parts.md`) is a checkpoint the user asked
for, not the delivery: say "checkpoint, UV and bake pending", never "done".

## How an expert works here
- **Measure before modeling**: cuts, profiles and raycasts give the positions in meters; nothing by eye.
- **Small goal, early image**: build one part, render one view (`wire_overlay`), show it, fix what is visibly
  wrong. Long rounds of analysis without an image frustrate the user.
- **By parts**: propose splitting the model (hand, leg without the foot, foot, tail...) and doing one part per round, delivered
  on its own (OBJ) and integrated by the user before the next (`docs/02-retopology/retopo-by-parts.md`).
- **Check with number and image**: error in mm (`fit_report`, `compare_mesh`), where it is off (`overlay`,
  `section_overlay`), pass or fail (`qa_all`, `topo_qa`).
- **Apply the documented pattern first**: for organic parts everything is a tube and tubes join into one mesh (`docs/02-retopology/retopo-tube-network.md`).
  Write a 5-line plan (pattern, seam ring, reuse, measures, deviations) and get a yes before building; never alter a ring the artist approved.
- **Continue the artist's work**: if the user started the mesh, start from it and keep the counts at the seams.
- **Everything in script** (`projects/<name>/*.py`, local, outside git; examples in `examples/`), reproducible. After the user has done the UV, only move vertices.
- **Half mesh + mirror** when there is symmetry; a crooked statue stays "as is" (do not symmetrize unless asked).
- **Low, justified budget**: every loop exists for silhouette, deformation or bake (`docs/02-retopology/topology.md`).
- Conventions: Z up, front = −Y, character's left = +X, meters.

## Pipeline
| # | stage | result | tools | guide in `docs/` |
|---|---|---|---|---|
| 0 | input | GLB in `input/`, with a copy outside the repo | `inspect_glb` | workflow-retopology |
| 1 | understand and measure | views, cuts, measurements | `render_views`, `slice_profile`, `slice_plot`, `ref_part` | workflow-retopology |
| 2 | retopology | quad low-poly snapped onto the ref | `mesh_lib`, `snap_retopo`, `retopo/` | topology, retopo-by-parts, retopo-snap-mirror, retopo-llm, retopo-shell-field, retopo-tube-path |
| 3 | check the shape | error in mm, overlaps | `fit_report`, `compare_mesh`, `overlay`, `section_overlay`, `wire_overlay` | workflow-retopology |
| 4 | mesh QA | 0 backface, 0 z-fight, clean topology | `qa_all`, `topo_qa` | qa |
| 5 | UV | 0–1 atlas without overlap, gap ≥ 8 px | `qa_uv`, `unwrap_atlas` | uv-bake |
| 6 | bake | basecolor, normal, roughness, metallic, AO | `bake_robust` | uv-bake |
| 7 | delivery | FBX + PNGs, lean `.blend` | `wire_material`, `make_lean_blend`, `export_from_blend` | delivery, git-reproduction |
| 8 | rig | Mixamo armature + weights | `autorig/`, `rig_mixamo` | rigging |
| 9 | game and store | Godot, thumbnail, description, listing form | `render_thumbnail`, `export_clips`, `listing_renders`, `fab_form` | delivery, fab-upload |
| 10 | **post mortem (mandatory)** | `POST_MORTEM.md`, new tools, corrected docs, case | `post_mortem.py` | post-mortem |

## I need... → read
| I need | read |
|---|---|
| run code in Blender, MCP or worker error | `docs/00-rules-and-tools/blender-automation.md` |
| start a project (folders, measure the reference, order of stages) | `docs/01-input-and-measurement/workflow-retopology.md` |
| decide loops, poles, counts, budget | `docs/02-retopology/topology.md` |
| choose the retopo method by type of part | `docs/02-retopology/README.md` |
| organic body (limbs, paws, fingers, toes, neck, tail, chest): tubes that join | `docs/02-retopology/retopo-tube-network.md` |
| retopo of a whole model: split into parts, order, one round, OBJ delivery | `docs/02-retopology/retopo-by-parts.md` |
| retopo of a hard part or prop (chest, lid, box) | `docs/02-retopology/retopo-snap-mirror.md` |
| retopo of a character or organic (body, hand, claws, tail) | `docs/02-retopology/retopo-llm.md` |
| retopo of cloth with an opening (hat, hood, sleeve, drooping tip) | `docs/02-retopology/retopo-shell-field.md` |
| retopo of a thin part along a curve (sword guard, grip, curved blade) | `docs/02-retopology/retopo-tube-path.md` |
| know whether the mesh is ready | `docs/03-qa/qa.md` |
| UV, PBR maps, bake, black spots in the bake | `docs/04-uv-bake/uv-bake.md` |
| export FBX, take it to Godot, thumbnail and store text | `docs/05-delivery/delivery.md` |
| the delivery is finished (game, store, handoff): what to do before saying "done" | `docs/05-delivery/post-mortem.md` |
| an animated creature (quadruped, clips, death, mouth) | `docs/06-rig/rigging.md`, `docs/08-cases/alligator.md` |
| put a hat/prop on a character's head in the game and adjust it in the editor | `docs/05-delivery/delivery.md` |
| humanoid rig, weights, tail | `docs/06-rig/rigging.md` |
| what to commit, regenerate `output/`, heavy GLB | `docs/05-delivery/git-reproduction.md` |
| the artist retopologizes by hand and the agent continues (recording, dataset) | `docs/00-rules-and-tools/human-in-the-loop.md`, `session-recorder.md`, `session-sharing.md` (upload to Hugging Face), `dataset-spec.md` |
| a curved band open on one side (headband, bracelet) | `docs/02-retopology/retopo-ring-tubes.md` |
| leaves, feathers or cloth strips as cutout planes with one shared texture | `docs/04-uv-bake/leaf-cards.md` |
| a whole asset end to end, reproducible (the wing: skin, shell, UV, bake, engraved handle, rig, export) | `docs/08-cases/wing.md`, `examples/wing/` |
| how to call a tool | `tools/README.md` and the file's docstring |

## Tools
All in `tools/<stage>/` (same folders as `docs/`; those used by more than one stage in `tools/general/`), each with a usage docstring. Table with how to call them: `tools/README.md`.
- **Running Blender**: `blender_rpc` (socket client), `blender_worker` (headless Blender on a copy, port 9877),
  `blender_once` (runs a script and exits; result in `RESULT_JSON:`).
- **Inspect and measure**: `inspect_glb` (tris, bbox, materials), `render_views` (workbench views), `slice_profile`
  (bbox per slice), `slice_plot` (PNG cuts with a cm grid, outside Blender), `ref_part` (piece of the ref in a
  part's local space).
- **Build by hand**: `mesh_lib` (box, loft, sweep, prism: simple props); `snap_retopo` with `snap_surface`,
  `snap_mesh` and `snap_section` (rings snapped onto the ref + mirror: hard parts); `retopo/` package (Ref, Topo, contours,
  3- and 5-sided patches, fingers and claws, `topo_qa`, `part_object`/`export_obj` to separate and deliver a part:
  characters).
- **Check the shape**: `fit_report` and `compare_mesh` (error in both directions and where detail is missing), `overlay`
  (silhouettes), `section_overlay` (cuts), `wire_overlay` + `label_png` (wireframe over the ref, with indices).
- **QA**: `qa_all` (single gate), `qa_faces` (backfaces, `fix_flipped`), `qa_zfight`, `qa_uv` (`unwrap_atlas`).
- **Bake**: `bake_robust` (per-texel validation, re-bake, inpaint), `bake_maps` (simple bake, optional cage),
  `bake_inpaint` (numpy).
- **Delivery**: `wire_material` (material + FBX of the lows only), `finalize_export`, `render_thumbnail` (Fab),
  `make_lean_blend`, `export_from_blend`.
- **Rig**: `autorig/` (Mixamo-style humanoid auto-rig from the command line), `rig_mixamo` (Mixamo armature from
  joints, skin, FBX).

## Repo map
```
README.md           this file
docs/               guides by subject (index: docs/README.md)
tools/              tools by stage, like docs/ (index: tools/README.md); retopo/ and autorig/ are Python packages
projects/<name>/    scripts and notes of your project (local, outside git; models in `examples/`)
  input/            original GLB (outside git; keep a copy outside the repo)
  draft/            working .blend with the reference, renders, backups (outside git)
  output/           FBX + PNGs (outside git; regenerable)
  <name>.blend      lean .blend (low-poly + packed textures), when the project closes
```

## Projects (examples to copy)
| project | state | study it for |
|---|---|---|
| stylized-chest | done: 813 tris in 2 pieces, bake 2048, Fab listing | hard prop with snap + mirror (`build_lid_v5.py`); README with measurements |
| stylized-tree | done: 380 tris, bake | rings around axes; ref with inner shells (`snap_tree.py`) |
| stylized-saci | done: 2864 tris, Mixamo rig, in Godot | one-legged character (scripts only in `draft/`, outside git) |
| stylized-cuca | done: 3756 tris, rig with tail, in Godot | character by parts with `tools/02-retopology/retopo` (`cuca_*.py`); hand rig (`cuca_rig.py`) |
| stylized-cow | in progress: torso, legs, head and extras in rings with snap | "as is" statue, parts in separate shells |
| hat-hair | hat done (960 quads, closed at the bottom, user's UV, bake 2048); hair to do | cloth shell by Laplace field (`hat_*.py`) |
| autorig-bench | auto-rig test bench (7 cases) | calibrate and validate `tools/06-rig/autorig` |
