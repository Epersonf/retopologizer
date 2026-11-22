# Character modeling: index (where to read, nothing repeated here)

Only pointers. Each row says the question and the one section that answers it; read that section, not the whole file.
Paths from the repo root. Add a row here when a new character topic is documented; never copy the content.

## 1. Before modeling
| question | read |
|---|---|
| which method for this part (tube, patch, mirror, cloth)? | `docs/02-retopology/README.md` |
| rules that apply to any mesh | `docs/00-rules-and-tools/retopology-rules.md` |
| loops, poles, counts, vocabulary (artist's theory) | `docs/02-retopology/topology.md` § Principles, § Vocabulary |
| where the rig will bend: extra loops | `docs/02-retopology/topology.md` § Deformation (characters) |
| triangle budget per region | `docs/02-retopology/topology.md` § Budget; density by deformation: `retopo-convex-parts.md` § 4 and 4b |
| reference measurements, folders, order of stages | `docs/01-input-and-measurement/workflow-retopology.md` |

## 2. Building the body
| question | read |
|---|---|
| order of work: tubes first, then trunk, then junctions, face last | not written yet; plan in `docs/02-retopology/retopo-convex-parts.md` § 6 (limits) |
| limb as a tube of rings (stations, extrema, no overlap, budget) | `retopo-convex-parts.md` § 1 to 4b |
| bridge between rings with different N | `retopo-convex-parts.md` § 3 |
| split the model into parts, one round each, integrate | `docs/02-retopology/retopo-by-parts.md` § Splitting the model, § One round |
| the package for characters (load, workflow, tools, pitfalls) | `docs/02-retopology/retopo-llm.md` |
| patterns that worked (shoulder hole, 5-pole, back) | `retopo-llm.md` § Patterns that worked; `topology.md` lines on shoulder and hip |
| mirror a half | `docs/02-retopology/retopo-snap-mirror.md` |
| fingers and hand | `retopo-llm.md` (tools `digit`, `lock`); `docs/08-cases/curupira.md` § Hand swap and junction |
| feet and toes (what fails in scripts) | `docs/08-cases/alligator.md` § Where the scripts failed: feet and toes |
| groin, shoulder, neck junctions | `topology.md` § Deformation; `retopo-convex-parts.md` § 6 (branches); no tool yet |
| face (eyes, mouth, ears) | `retopo-convex-parts.md` § 6 (Face); do last, by hand |
| hair, cloth, headband, skirt on a character | `retopo-hair-tubes.md`, `retopo-shell-field.md`, `retopo-ring-tubes.md` |
| working with the artist's hand-made mesh | `docs/00-rules-and-tools/human-in-the-loop.md` |

## 3. After the mesh
| question | read |
|---|---|
| QA battery, shape fidelity, topology checks | `docs/03-qa/qa.md` |
| UV, bake, PBR maps | `docs/04-uv-bake/uv-bake.md` |
| auto-rig, joint rules, weights, hand rig | `docs/06-rig/rigging.md` § Auto-rig, § Where the joints go, § Hand rig |
| rig page with markers (Rig Studio) | `tools/06-rig/rig_studio/`; `docs/06-rig/rigging.md` |
| quadruped or creature | `rigging.md` § Quadruped; `docs/08-cases/alligator.md` |
| non-standard feet (backwards) | `docs/08-cases/curupira.md` § Rig |
| delivery to Godot, store | `docs/05-delivery/delivery.md`, `fab-upload.md` |
| what was learned (mandatory) | `docs/05-delivery/post-mortem.md` |

## 4. Cases
`docs/08-cases/`: `curupira.md` (biped, backwards feet), `alligator.md` (quadruped, 3000 tris). Cuca (`projects/stylized-cuca`): see `retopo-by-parts.md`.
