# Dataset specification (manual retopo demonstrations, to publish on Hugging Face)

Goal: demonstrations of manual retopology (high-poly model -> quad mesh, vertex by vertex with snap) to train a policy that redoes it.
Recording and actions: `session-recorder.md`. Here: what to store, how it is organized, what to check before publishing.

## Unit of data
- **Asset**: a reference model + metadata + observations of it (depth/normal/mask maps in known views, with the camera).
- **Episode**: one session of one annotator on one asset (steps, keyframes, final mesh, notes).
- **Stage record**: what an actor did in another stage (UV layout, shape adjustments, bake/relief/rig recipes), so stages are not mixed.
- Split **by asset**, never by step (steps of the same asset leak between train and test).

## Layout in this repository: `dataset/` (versioned; everything gzip JSON(L), so it stays small)
```
dataset/README.md                           card: stages, actors, licences, limits
dataset/<stage>/<asset>/<id>/               stage = retopology | adjust | uv | bake | relief | rig
dataset/<stage>/<asset>/index.json          id, actor (user | agent), kind (episode | record), files, bytes, note   (rebuilt by dataset_pack.py index)
retopology/<asset>/<id>/episode.jsonl.gz    one step per line: trigger + actions
                        initial_state.json.gz, final_state.json.gz, final_mesh.json.gz, episode_meta.json, entry.json
adjust/<asset>/<id>/edit_record.json.gz     vertices the artist moved between two saves (before/after) + before/after summary (counts, thickness)
uv/<asset>/<id>/uv_layout.json.gz           faces with the UV of every corner, seams (the artist's unwrap)
bake|relief|rig/<asset>/<id>/<stage>_recipe.json.gz  what the agent ran (parameters, reports); actor = agent
```
`dataset_pack.py record` names the stored file after the input json (`edit_record.json`, `uv_layout.json`, `<stage>_recipe.json`).
Actor matters: `user` data is the demonstration to imitate; `agent` data documents a recipe and must not be mixed into the training targets.
Raw sessions (`projects/<name>/session/rec_NN`, tens of MB) and the reference GLB stay OUT of git.

## Fields of a step
`t` (s), `obj`, `mode`, `triggers` (keys/operators), `actions[]`: `add_vertex` (id, local, world, screen, `linked_to`), `add_face` (verts),
`move_vertex` (from, to, world, screen), `select` (verts), `topology_change`. Policy view: state = current mesh + view + asset observations;
action = next line of `actions`.

## What is captured and what is missing
| captured | missing |
|---|---|
| semantic actions, screen, view, snap, keyframes, notes, checkpoints | asset observations exported per view (depth/normal/mask + camera); `asset.json` with origin and licence |
| Blender and .blend metadata (md5, name without path) | `episode.json` status (partial/complete/reviewed); tag convention in `NOTES` (`#part=feather #layer=2`) |
| path and user-name scrubbing in the converter | undo/redo and long-pause markers; a final metric (QA, error to the reference) |
| UV and adjustments recovered by comparing saves | the edits made between recordings as real actions |

## Before publishing
- **Reference licence**: AI-generated models and game art have their own terms. Confirm they can be redistributed; if not, publish only derived
  observations or none, and say so on the card. The wing's depth map (`wing_front_depth.npz`) is NOT in `dataset/` until this is settled.
- **Rights to the demonstrations**: choose the licence (e.g. CC-BY-4.0) and record the annotator's consent.
- **Anonymization**: no paths, user name, e-mail, machine name; `annotator_id` hashed. The converter scrubs paths; check `.blend` files,
  screenshots (title bar, tabs) and the `NOTES` text before uploading.
- **Size**: the 1.5 M-triangle reference is 84 MB; do not upload it. Prefer compressed `.npz` and Parquet; Git LFS/xet on the Hub.
- **Quality**: flag partial episodes; say whether the mesh was reviewed or only recorded.
