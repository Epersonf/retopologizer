# Retopology: which method for which model

Stage 2 of the pipeline. Here the choice is **per part**, not for the whole model. Rules that hold for every method
(`docs/00-rules-and-tools/retopology-rules.md`): retopo is always manual, vertex by vertex with snap onto the ref;
quads only; the automatic tool measures and checks, it does not generate the mesh; the ref is never edited.

## 1. Classify the part
| the part is... | method | guide | example in the repo |
|---|---|---|---|
| hard part with corners and detail (chest, lid, box, handle) | rings by angle + mirror | `retopo-snap-mirror.md` | `projects/stylized-chest` |
| simple prop (box, tube, prism) | `mesh_lib` (box, loft, sweep) | `tools/README.md` | `projects/stylized-chest` |
| trunk, tube or tree around an axis | rings around the axis with snap | `retopo-snap-mirror.md` | `projects/stylized-tree` |
| character or organic (body, hand, claws, tail, head) | `tools/02-retopology/retopo` package (rings, patches, fingers) | `retopo-llm.md` | `projects/stylized-cuca` |
| cloth with an opening and a crooked axis (hat, hood, sleeve, drooping tip) | rings by Laplace field | `retopo-shell-field.md` | `projects/hat-hair` |
| many fused strands/tubes (hair, tentacles) | shell for the base + one separate mesh per tube | `retopo-hair-tubes.md` | `projects/hat-hair` |
| thin part along a curve in one plane (crossguard, knuckle bow, grip, pommel, flat curved blade) | rings along a 2D path, rays with per-direction reach, buried ends | `retopo-tube-path.md` | `examples/cutlass` |
| crooked or asymmetric statue | "as is", parts in separate shells, no symmetrizing | `retopo-llm.md` | `projects/stylized-cow` |

Torn between two: does it fit in a **shell with an opening**? Laplace. Does it have **hard corners**? Snap + mirror. Does it **deform** or have
arms/legs? `tools/02-retopology/retopo`.

## 2. Decide loops, poles and counts
**Before starting, ask the user for the polygon budget of each part and of the whole** (and whether the limit is in quads or in
triangles: 1 quad = 2 triangles; Blender shows triangles). With no target, the result comes out too big and gets redone (the `hat-hair`
hair: 1410 quads = 2800 triangles, the user wanted up to 1000). Split the budget among the parts before building.
Before any vertex: `topology.md` (loops at joints, poles away from folds, budget). Every loop needs a
reason: silhouette, deformation or bake.

## 3. If the whole is hard, split it
`retopo-by-parts.md`: one part per round, delivered as OBJ and integrated by the user before the next.
- A part is a shape with a clear boundary; the boundary is a **ring** with an even count, equal on both sides.
- Order: from the trunk to the extremities; extras (tail, ears) and seams last.
- Each part picks its own method from the table above (e.g. body with `tools/02-retopology/retopo`, hat by field, buckle by snap).
- If a method fails on the same part twice, switch methods or split further, instead of tweaking parameters.

## 4. Before delivering the part
Show a view (`wire_overlay`), check the error in mm (`fit_report`) and `topo_qa(...)["quad_only"]`. Then, stage 3
(`docs/03-qa/qa.md`).

## 5. Record what you found out
A new method that worked on a piece becomes its own guide in this folder (as happened with `retopo-shell-field.md`, from the hat):
when to use it, the process in steps, numbers from the example, pitfalls with symptom and fix, how to adapt it to another piece.
Then add the line to the table in section 1 and to `docs/README.md`.
