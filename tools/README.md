# tools/: index by workflow stage

Same folders as `docs/`. Each file starts with a usage docstring (signatures and examples). How to run Blender:
`docs/00-rules-and-tools/blender-automation.md`. Flow of a project: `docs/01-input-and-measurement/workflow-retopology.md`.

**Rule:** a tool lives in the folder of the stage that uses it. If it is used by more than one stage (or by all), it goes in
`general/`. When creating a new tool, put it in its own stage; if a second stage starts using it, move it to `general/`
and update the paths (`grep -rn "tools.<folder>.<name>"`).

"inside Blender" = load with `exec(open(r"<repo>\tools\<folder>\x.py", encoding="utf-8").read())` (MCP, worker or
one-shot) and call the function. The packages (`retopo/`, `autorig/`, `rig_mixamo`) are imported: put their folder on
`sys.path` (`<repo>\tools\02-retopology` for `retopo`, `<repo>\tools\06-rig` for `autorig` and `rig_mixamo`).

`<repo>` is your clone of this repository. Tools that load other tools find the repo root from their own location, or from the
`RETOPOLOGIZER_ROOT` environment variable, or, inside Blender without `__file__`, from the current directory: run from the
repo root or set `RETOPOLOGIZER_ROOT`.

## general/: used by more than one stage
| file | where it runs | what for |
|---|---|---|
| blender_rpc.py | `python` | socket client (MCP 9876 or worker 9877): runs a file or `-c "código"`, prints `result` |
| blender_worker.py | `blender -b cópia.blend --python tools/general/blender_worker.py -- 9877` | headless Blender with the MCP protocol |
| blender_once.py | `blender -b --factory-startup --python tools/general/blender_once.py -- script.py` | runs a script without a worker; result in `RESULT_JSON:` |
| cycles_gpu.py | inside Blender | `use_gpu()`: Cycles on the GPU; call before every bake/render (bake and thumbnail) |
| render_views.py | inside Blender | workbench views (front/back/left/right/top/persp); `fit_to` fixes the framing |
| ref_part.py | inside Blender | crops the part of the ref that belongs to a piece, in the piece's local space |
| slice_plot.py | `python` (matplotlib) | ref cross-sections as PNG with a cm grid; `--low` overlays the retopo |
| qa_uv.py | inside Blender | overlap, 0–1 bounds, gap between islands; `unwrap_atlas` (QA and UV/bake) |
| session_recorder.py (+ `session_actions/state/meta.py`) | `blender x.blend --python ...` or `record_session.py <blend> <sessions_dir>` | records the artist's manual session (actions, mesh, view) so the agent can continue and a model can be trained: `docs/00-rules-and-tools/session-recorder.md` |
| bh.sh | `tools/general/bh.sh <<'PY' ... PY` | runs code in the user's Chrome through browser-harness (fixes the Git Bash path and PowerShell BOM errors) |
| post_mortem.py | `python tools/general/post_mortem.py <project> --delivery godot,fab` | scaffolds `projects/<p>/POST_MORTEM.md` and lists what the pipeline still owes (mandatory after every delivery: `docs/05-delivery/post-mortem.md`) |
| session_actions.py, session_meta.py, session_state.py | imported by `session_recorder.py` | diff of mesh states into actions, metadata/checkpoints, Blender state readers (no direct use) |
| session_to_dataset.py | `python` | converts a recording into a dataset episode (trigger -> actions steps), scrubs paths |
| dataset_pack.py | `python` | puts episodes and stage records into the versioned `dataset/<stage>/<asset>/<id>` (gzip, scrubbed, index.json): `docs/00-rules-and-tools/dataset-spec.md` |
| rec_rebuild.py | inside Blender or `python` | rebuilds the artist's mesh from a recording (`replay`, `rebuild`) when no .blend survived |
| session_report.py | `python tools/general/session_report.py <rec_dir>` | reads a recording: timeline of operators, face sizes, valences, border, layers from the seam ring |
| live_rings.py | `python` + user's Blender (MCP 9876) | shows rings, shrink and bridge growing live in the artist's Blender (`play`) |
| qa_cover.py | inside Blender | `qa_coverage`: ref near the part not covered (missing/collapsed toe), calibrated on the artist's toes: `docs/03-qa/qa.md` |
| hf_refs.py (+ hf_ref_worker.py) | `python` (launches Blender) | adds ref.npz/ref.json (60000 surface points + normals of the reference, world space) to every recording |
| hf_push.py | `python` | uploads the raw recordings (`projects/*/session`, 2.2 GB, not in git) to the Hugging Face dataset `Eperson/retopo-sessions`, paths scrubbed, resumable; dry run by default; how: `docs/00-rules-and-tools/session-sharing.md` |
| merge_doubles.py | python | merge by distance on lists (V, F); `Topo.write` refuses vertices closer than 0.6 mm |
| toe_fit.py | inside Blender | `fit_toes`: each toe of a transplanted fused-toe block becomes a rigid+scale body fitted (ICP) on its OWN toe of the ref |
| face_polish.py | inside Blender | `polish`: one vertex at a time, random steps projected on the ref, kept only if twisted/inverted/crossing penalty drops |
| face_shape.py | inside Blender | `qa_faceshape`, `twisted_quads`, `stamped_pairs`, `inverted_vs_ref`: faces wrong by themselves |
| face_intersect.py | inside Blender | exact face-vs-face intersection per loose part: `qa_intersect`, `select_faces`, `face_intersections(V, F)` |
| live_intersect.py | inside Blender (the artist's too) | `start()`: faces cutting each other red, twisted/stamped magenta, live + count in the status bar; `stop()` |
| blend_diff.py | inside Blender (one-shot) | what the artist changed between two saves: counts, bbox, moved vertices, thickness, UV (`compare_blends`, `edit_record`) |

## 01-input-and-measurement/
| file | where it runs | what for |
|---|---|---|
| inspect_glb.py | `blender --background --python inspect_glb.py -- model.glb` | tris/verts, bbox, materials and 3 silhouette profiles |
| slice_profile.py | inside Blender | bbox per slice along an axis (numpy, no Edit Mode) |
| depth_map.py | inside Blender | front/back depth maps of a relief reference on a grid (`depth_map`, `sampler`): sample the surface, choose the mirror plane, place parts |

## 02-retopology/ (build by hand and check the shape)
| file | where it runs | what for |
|---|---|---|
| untangle.py | inside Blender | removes intersecting faces / collapsed tips by moving only those vertices (relax + project, `max_move`) |
| transplant.py | inside Blender | reuses an approved part elsewhere (matrix or mirror) and snaps it to the target ref: no new topology |
| mesh_lib.py | inside Blender | simple props: `box`, `loft`, `rect_sweep`, `prism`, `pentagon`, `to_object` |
| snap_retopo.py | inside Blender | hard-surface pieces: loads the three below (`docs/02-retopology/retopo-snap-mirror.md`) |
| snap_surface.py | via snap_retopo | `Surface`: `nearest`, `ray`, `outer`, `inner` on the ref; `simplify` |
| snap_mesh.py | via snap_retopo | `Mesh`: `v`, `f`, `strip`, `cap`, `prism`, `dimple`, `fill_flat_ring`, `mirror_x`, `to_object` |
| snap_section.py | via snap_retopo | `ring(S, c, axis, up, n)`: cross-section ring by raycast from the center |
| tube_path.py | inside Blender, after snap_retopo | thin parts along a planar curve: `load_raster`, `build_tube(S, R, name, points, rings, bury=, floor=)`, `tube_ring` (`docs/02-retopology/retopo-tube-path.md`) |
| retopo/ | inside Blender (`import retopo`) | characters and organics: `Ref`, `Topo`, contours, patches, digits, `lock` (tube per hair lock, `section`), `topo_qa`, `part_object`/`export_obj` (`retopo/README.md`) |
| plane_cards.py | inside Blender | each leaf/feather/cloth strip of a ref becomes one plane: `components`, `leaf_frame` (PCA frame, base/tip, outward), `cell_offset` (curvature); `docs/04-uv-bake/leaf-cards.md` |
| compare_mesh.py | inside Blender | ref↔new distance (mm and % of the diagonal) in both directions + critical points |
| fit_report.py | inside Blender | new→ref and ref→new error (mm) + 5 cm cells where detail is missing |
| overlay.py | `python` (PIL) | ref × new silhouettes: red ref only, cyan new only, gray both |
| section_overlay.py | inside Blender | cross-section PNG: colored ref × white low |
| wire_overlay.py | inside Blender | workbench render + low wireframe (visible edges only) |
| label_png.py | `python` (PIL) | writes the vertex indices on the wire_overlay PNG |
| symmetrize.py | inside Blender | straighten + cut on the axis + mirror one half with identical UVs (sword): `symmetrize`, `axis_knots` |
| skin_close.py | inside Blender | one-sided retopo skin -> closed shell: `touch_parts` (skin reaches separate parts), `close_skin` (extrude border to a plane + mirror), `pull_parts_to_shell`; `docs/08-cases/wing.md` |

## 03-qa/
| file | where it runs | what for |
|---|---|---|
| qa_all.py | inside Blender | single gate: backfaces + UV (2048 and 4096) + z-fighting; raises an error on failure |
| qa_faces.py | inside Blender | raycast in 400 directions: no exposed backface; `fix_flipped` |
| qa_orient.py | inside Blender | face-orientation views like Blender's overlay (blue front, red back): a model with no red from any view is clean |
| qa_shape.py | inside Blender | ugly shapes: spikes, thin-tipped tubes, thin tubes, narrow faces; `heal_spikes` |
| qa.py | command line (worker 9877) | **the battery**: runs all tests and prints one line per test + `fix:` + where (`--only`, `--skip`, `--fast`, `--json`) |
| qa_suite.py | inside Blender | `qa_suite(nome, ref=..)`: the battery as a function (mesh, budget, shape, floating, attach, local, strict, fit) |
| qa_mesh.py | inside Blender | quads, open border, non-manifold, winding, duplicates, degenerates |
| qa_local.py | inside Blender | inverted normal seen up close (gaps, folds, tube cap poking through) |
| qa_attach.py | inside Blender | tube connected only by touching / cap outside the parent ("loose tip despite being connected") |
| qa_fit.py | inside Blender | fidelity to the ref, visible part only: silhouette IoU in 14 directions, holes (ref without coverage), bumps the ref does not have (first-hit depth) |
| qa_strict.py | inside Blender | zero-tolerance gate: no ray out of 400 directions may hit the back of a face; `heal_flipped` relaxes folds and raises an error if any remain |
| qa_floating.py | inside Blender | no loose piece floating: groups of parts that touch; returns the gap and the point to reach |
| qa_faceshape.py | inside Blender | twisted quads, faces looking into the model, stamped faces: zero tolerance (core `general/face_shape.py`) |
| test_intersect.py | inside Blender | regression of qa_intersect + qa_faceshape: bad meshes must fail, good ones pass |
| qa_intersect.py | inside Blender | faces of one loose part cutting/folding over each other (zero tolerance; core `general/face_intersect.py`) |
| qa_zfight.py | inside Blender | nearly parallel faces overlapping at < 1 mm, AABB broad phase |
| qa_mark.py | inside Blender | points out defects on the mesh itself (idea from the TopoToolkit add-on): `qa_*` attributes (border, non-manifold, orphan, doubles, tris, n-gons, poles 3..N) and selects one type, so the `.blend` opens in Edit Mode with them marked |
| qa_report.py | inside Blender | report of an object as HTML (tables + inline views), TXT or CSV: counts, edge types, valence histogram, battery rows (`battery=True`) |

## 04-uv-bake/
| file | where it runs | what for |
|---|---|---|
| bake_robust.py | inside Blender | bake with per-texel validation, multi-pass re-bake, per-island inpaint |
| bake_maps.py | inside Blender | simple bake of 5 high→low maps into one image (optional cage) |
| bake_inpaint.py | pure numpy | inpaint and dilate restricted to the UV island |
| texturecraft_cli.py | `python` | TextureCraft through the CLI: `import_maps`, `add_camera`, `paint` (`Stroke`), `export`, `render`; `docs/04-uv-bake/texturecraft-cli.md` |
| ortho_atlas.py | inside Blender | one piece rendered once into an atlas tile by orthographic raycast: color (ramp), alpha, normal from depth (`raster`, `to_normal`, `paste`); `docs/04-uv-bake/leaf-cards.md` |
| texel_paint.py | inside Blender | procedural detail written straight into atlas texels of one material: `texels` (position + tangents per texel), `height_to_normal`, `write_map` with margin |

## 05-delivery/
| file | where it runs | what for |
|---|---|---|
| export_game_prop.py | inside Blender | a prop that rides a bone in the game (headband, skirt): FBX in skeleton space + albedo + normal, ready for a placement equal to the inverse bone rest |
| wire_material.py | inside Blender | wires the PNGs into a Principled material and exports the FBX of the low-polys only |
| export_package.py | inside Blender | `wire_pbr` (with optional white Tint), `render_previews` (Cycles GPU), `export_package` (FBX + GLB + maps, animation baked) |
| finalize_export.py | inside Blender | collections, UV, material, budget, `.blend` and FBX |
| listing_shots.py | inside Blender | tilts/centres a long prop and renders every listing image in one call |
| fab_package.py | `python` | one zip per format (FBX, GLB) with the textures, for the Fab upload |
| before_after.py | `python` (PIL) | before/after sheet from two renders of the same view |
| render_thumbnail.py | inside Blender | 1920x1080 store thumbnail (Cycles, studio) |
| make_lean_blend.py | inside Blender | lean `.blend` for git (no ref, packed images) |
| export_clips.py | inside Blender | `export_clips`: animated creature to GLB (game clips) + FBX with every action baked (store), swapping 1024/2048 textures; refuses actions without fake user |
| listing_renders.py | inside Blender | `pose_shots`: store images in different clips/poses (bite, walk, death) with the thumbnail studio |
| fab_form.py | browser-harness | Fab Publisher Portal helpers (inputs dump, numbers, radios, tags, prices, safe click by text, guarded `fab_submit`): `docs/05-delivery/fab-upload.md` |
| export_from_blend.py | `blender -b <projeto>.blend -P export_from_blend.py -- outdir prefixo` | regenerates PNGs + FBX from the lean `.blend` |
| verify_inputs.py | `python` | checks `inputs.json` (`inputs.json` was removed from the repo, so it is **obsolete**) |

## 06-rig/
| file | where it runs | what for |
|---|---|---|
| rig_mixamo.py | inside Blender | armature with Mixamo names from the joints, skin by bone heat (max. 4), FBX export |
| pose_actions.py | inside Blender | clips by script: `PoseAnim` (keyframes with fake user), `local_axis`/`rot_about`/`lift_up` (rotate in the right bone-local axis), `check_pose` (z range and bone positions at a frame); quadruped case in `docs/06-rig/rigging.md` |
| export_for_mixamo.py | `blender -b --factory-startup --python tools/06-rig/export_for_mixamo.py -- model.blend Mesh albedo.png out.fbx` | one mesh, Y-up FBX with albedo embedded, for the Mixamo auto-rigger |
| pose_check.py | `blender -b ... --python tools/06-rig/pose_check.py -- rigged.blend outdir` | deformation check: forced poses, front and perspective renders |
| rig_chain.py | inside Blender | rig for a limb-like prop (wing, tail, cape): bone chain, numeric positional weights, looping flap animation |
| autorig/ | `blender -b --factory-startup --python tools/06-rig/autorig/cli.py -- modelo saida.fbx` | humanoid auto-rig, Mixamo style (`autorig/README.md`) |
| rig_studio/ | `python tools/06-rig/rig_studio/server.py` then open http://127.0.0.1:8765 | Mixamo-style auto-rigger page: upload, orient (green arrow = front), markers (chin, wrists, elbows, knees, groin) or fully automatic, LOD, symmetry, skeleton + test pose preview, FBX download |
| limb_demo_data.py, limb_demo_video.py | worker, then `python tools/02-retopology/limb_demo_video.py` | animated demo of ring, shrink and bridge on an arm (`docs/02-retopology/retopo-convex-parts.md`) |

Blender: `C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe` (5.3).

## 07-fibercards/ (hair as planes with a strand texture)
| file | where it runs | what for |
|---|---|---|
| fibercards.py | `python` | fiber card sheet: generates the strands (like the fiber-card-gen app), calls Blender and writes `<tag>_color.png`, `_normal.png`, `_preview.png`, `_preset.json` |
| fc_blender.py | Blender one-shot (called by fibercards.py) | strands as tubes, orthographic camera, Cycles with a transparent background |
| fc_strands.py, fc_params.py | `python` | card strands and state/preset (`BLONDE`); same keys as the app's JSON |
