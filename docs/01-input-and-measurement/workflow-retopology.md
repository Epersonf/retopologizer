# Workflow of a project (AI reference → game asset)

> **AUTOMATIC retopology is FORBIDDEN** (QuadriFlow, Remesh, Decimate as a deliverable). See `docs/00-rules-and-tools/retopology-rules.md`.

AI-generated models have hundreds of thousands of triangles and no topology intent. Instead of "cleaning" that
mesh, you **measure the reference and rebuild the shape** with few polygons, checking with numbers and images.
Never enter Edit Mode on the reference mesh (it freezes Blender). How to run Blender: `docs/00-rules-and-tools/blender-automation.md`.

## Project structure
```
projects/<name>/input/    original model (.glb), outside git; keep a copy outside the repo
projects/<name>/draft/    working .blend (with the reference), renders, backups; outside git
projects/<name>/output/   .fbx of the low-polys + baked PNGs, NEVER the reference; outside git
projects/<name>/*.py      scripts that build the mesh (local; examples in examples/)
projects/<name>/README.md origin, measurements, counts, result, pending items
```

## Stages
1. **Prepare**: `blender --background --python tools/01-input-and-measurement/inspect_glb.py -- model.glb` → tris, bbox, materials. Note the
   GLB's origin in the project README. Agree the tri budget with the user (`docs/02-retopology/topology.md`).
2. **Import** the GLB into a `.blend` in `draft/`, name the reference (`REFERENCE`, `HiPoly`) and lock its selection.
   Set Cycles to **GPU** right away if the PC has one (`use_gpu()` from `tools/general/cycles_gpu.py`; here: OPTIX, RTX 3060).
3. **Understand the shape**: `render_views(names, outdir, prefix, fit_to=[ref])` (front/right/top/persp, workbench).
   Separate independent parts (base + lid; body + clothes) and fix the axes: **Z up, front = −Y, character's
   left = +X, meters**.
4. **Measure** the reference (below).
5. **Manual retopology, by parts** (one part per round, delivered and integrated before the next:
   `docs/02-retopology/retopo-by-parts.md`), choosing the method:
   - simple shape (box, cylinder, plank): `mesh_lib.py` (`box`, `loft`, `rect_sweep`, `prism`) with the measurements;
   - hard part with detail: `docs/02-retopology/retopo-snap-mirror.md`;
   - character or organic shape: `docs/02-retopology/retopo-llm.md`.
6. **Check the shape** at every iteration (below) and show the user an image.
7. **QA** (`docs/03-qa/qa.md`) → **UV and bake** (`docs/04-uv-bake/uv-bake.md`) → **delivery** (`docs/05-delivery/delivery.md`) → **rig**, if it is a character
   (`docs/06-rig/rigging.md`) → **git** (`docs/05-delivery/git-reproduction.md`).
8. Record in the project's `README.md`: measurements, counts, final error, tris, pending items.

## Measuring the reference
- `slice_profile(name, axis=2, step=0.04)`: bbox per slice (numpy, no Edit Mode) → band heights, walls.
- `slice_plot.py` (pure Python, over a `hi_world.npz`; see `docs/02-retopology/retopo-llm.md`): PNG cuts with a cm grid → centers and
  widths of limbs, where the knee, elbow and wrist are.
- Raycast as a function of x (`h(x)`) finds straps, steps, blocks and chamfers (chest lid).
- Articulated parts: sweep the angle that minimizes the bbox area in the rotation plane → opening angle. Model in the
  closed pose and rotate around the pivot (solve the pivot linearly).
- `ref_part(ref, part, "REF_X", radius)`: only the part of the ref that belongs to a piece, in its local space.

## Checking the shape
- `fit_report(low, ref)` / `compare_mesh.compare(...)`: mean/p95/max in mm in both directions + where. ref→new high =
  missing detail or wall; new→ref high = extra or floating geometry.
- `overlay.py ref.png new.png out.png`: red ref only, cyan new only, gray both (renders with the same `fit_to`).
- `section_overlay`: cuts with the ref colored and the low white, to see where a ring is off.
- `wire_overlay` (wireframe of the low over the shaded ref, visible edges only) + `label_png` (vertex indices):
  the artist's view; it is the image to show the user.

## Measurement pitfalls
- "Minimum z of the vertices" is misleading in flat regions: confirm with an overlay.
- An error of ~2 cm only showed up when comparing silhouettes (the top of the chest base was 0.355, not 0.385).
- Closed walls (front and back of the lid) only showed up at the critical points (`hot_k`); the error went away once they were closed.
- The AI surface is rough: a slanted ray oscillates ±1.5 cm. Measure walls with a ray perpendicular to them.
- Reference with inner shells: the first hit is misleading; use the outermost hit (`Ref.outer`, `snap_tree.py`).
