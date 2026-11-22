# dataset/: recordings and stage results, versioned and separated by stage

What the artist did by hand (and what the agent ran after) on each asset, kept small (gzip JSON/JSONL) so it can live in git and later be published
(Hugging Face). Format and rules: `docs/00-rules-and-tools/dataset-spec.md`; how it is recorded: `docs/00-rules-and-tools/session-recorder.md`.

| folder | actor | what | how it was made |
|---|---|---|---|
| `retopology/<asset>/` | user | manual retopology episodes (one step per vertex/face action, with screen position) | `session_recorder.py` -> `dataset_pack.py episode` |
| `adjust/<asset>/` | user | vertices the artist moved after the retopology (shape adjustments), before/after, thickness | `blend_diff.edit_record` -> `dataset_pack.py record` |
| `uv/<asset>/` | user | the artist's UV layout (UV of every face corner, seams) | `blend_diff.edit_record` |
| `bake/`, `relief/`, `rig/<asset>/` | agent | recipes: parameters and reports of what the scripts ran | `examples/<asset>/run_all.py` output |

`<asset>/index.json` lists the entries (`id`, `actor`, `kind`, `files`, `bytes`, `note`); rebuild with `python tools/general/dataset_pack.py index`.

## Contents now
- `retopology/wing`: `wing_rec01` (preparation, 0 steps), `wing_rec02` (440 steps, 85 -> 131 vertices), `wing_rec03` (551 steps), `wing_rec04` (986 steps, 201 -> 333 vertices, with the final mesh).
- `adjust/wing`, `uv/wing`: the artist's thinning of the wing (85 -> 47 mm) and their atlas (91 islands, no overlap).
- `bake|relief|rig/wing`: the agent's recipes for the wing.

## Not here, on purpose
- The reference GLB and the raw sessions (`projects/<name>/session`, keyframes and screenshots): too big, and the reference is an AI-generated model whose redistribution terms are
  not confirmed. The wing's depth observations (`wing_front_depth.npz`) wait for the same answer.
- Anything with a path, user name or e-mail: `dataset_pack.py` scrubs them; check screenshots before ever adding any.
Licence of the demonstrations: not chosen yet (proposal: CC-BY-4.0, with the annotator's consent recorded).
