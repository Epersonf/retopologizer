# docs: index by workflow stage

One folder per stage, in the order a project advances; each guide points to the next. General entry point: `../README.md`.
Paths in the guides: always `docs/<folder>/<file>.md`, from the repo root.

| folder (pipeline stage) | file | read when |
|---|---|---|
| 00-rules-and-tools (always) | retopology-rules.md | before creating any mesh |
| | blender-automation.md | before running code in Blender: MCP, worker, one-shot, pitfalls |
| | human-in-the-loop.md | the artist retopologizes by hand: record, understand, continue their mesh, lessons |
| | session-recorder.md | recording the artist's session in Blender (what is logged, how to run, limits) |
| | dataset-spec.md | the versioned `dataset/` (by stage and actor), fields, what is missing, publishing cautions |
| 01-input-and-measurement (0 and 1) | workflow-retopology.md | when starting: folders, measuring the reference, order of stages, checking the shape |
| 02-retopology (2 and 3) | README.md | choosing the right method for each type of part |
| | topology.md | deciding loops, poles, counts and budget (the artist's theory) |
| | retopo-by-parts.md | splitting the model, one round per part, delivering and integrating |
| | retopo-snap-mirror.md | hard part or prop: rings by angle + mirror (chest lid) |
| | retopo-llm.md | character or organic with the `tools/02-retopology/retopo` package (Cuca) |
| | retopo-shell-field.md | cloth with an opening (hat, hood, sleeve): rings by Laplace field |
| | retopo-hair-tubes.md | fused strands/tubes (hair): one separate mesh per tube, strand detector, polygon budget |
| | retopo-tube-path.md | thin parts along a planar curve (sword guard, grip, curved blade): rings of rays with per-direction reach, buried ends |
| | retopo-ring-tubes.md | closed tube along a curved band open on one side (headband, bracelet): spine by angular slices, hull ring per slab |
| 03-qa (4) | qa.md | checking the mesh before UV, bake and export |
| 04-uv-bake (5 and 6) | uv-bake.md | UV, PBR maps, high-to-low bake, artifacts |
| | texturecraft-cli.md | painting/retouching in TextureCraft through the CLI (the MCP cannot read files) |
| | leaf-cards.md | many copies of one piece (leaves, feathers, cloth) as cutout planes: render once into an atlas, one plane per piece |
| 05-delivery (7 and 9) | delivery.md | FBX, Godot (Braziletto game), prop attached to the head + editor, thumbnail and Fab store |
| | fab-upload.md | publishing the listing on Fab with browser-harness: form fields, files, technical details, submit |
| | git-reproduction.md | what to commit, regenerating `output/`, heavy GLBs |
| 06-rig (8) | rigging.md | humanoid auto-rig, hand rig, weights, tail |
| 07-fibercards (alternative to mesh hair) | fibercards.md | fiber card sheet (color + normal) generated and rendered in Blender |
| 08-cases (whole pipeline, one asset) | wing.md | the wing end to end: artist's retopo, shell, UV, bake, engraved handle, rig, export; how to reproduce it |
| | sword.md | the sword end to end: artist's shell, closing, UV, bake, symmetry, TextureCraft, game item, Fab listing |
