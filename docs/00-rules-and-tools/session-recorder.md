# Session recorder (manual retopo -> data for the agent and for a future model)

The artist retopologizes by hand in Blender; the recorder logs everything so that (1) the agent can continue from where the artist stopped,
using the artist's own method, and (2) the sessions can become a dataset to train a model that redoes the retopology (`dataset-spec.md`).

## How to record
```
python tools/general/record_session.py <file.blend> <sessions_dir>      # opens Blender and creates the next empty rec_NN
```
`BLENDER_EXE` overrides the Blender path. Env of `session_recorder.py`: `REC_DIR` (output), `REC_OBJ` (fixed object; default = the active one),
`REC_FULL=1` (full mesh at every change; heavy). The artist works as usual (orthographic front view, extrude one point at a time + F for faces,
snap onto the reference) and saves with Ctrl+S. The `NOTES` text of the .blend is logged on every change: use it to write the intention
("rim of feather 3"). Closing Blender without saving keeps the logs but not the .blend.
**Check it is running** before the artist starts (the folder grows: `events.jsonl`, `shot_*.png`); a closed Blender window means no recording.

## What `rec_NN/` contains
| file | content |
|---|---|
| `meta.json` | recorder/Blender versions, .blend name + md5 at the start (no path), reference (triangles, size), snap settings, view, conventions |
| `events.jsonl` | `op` (operator + properties), `key` (key/click + region position), `mode`, `active`, `note`, `save`, `mesh` (counts, new vertices/faces) |
| `actions.jsonl` | one line per mesh change: `triggers` (keys/operators since the previous one) + `actions` |
| `snap_NNNN.json` | keyframe: full mesh (vertices, edges, faces, selection, active vertex), object matrix, 3D view, snap. Every 25 changes and on mode change |
| `shot_NNNN.png` | 3D viewport, one every 10 s |
| `checkpoint_NNN.json` | mesh of every object (without the reference) at each Ctrl+S |

The first version wrote a full snapshot per change: 15 minutes = 48 MB. Now the actions are always written and the full mesh only on keyframes
(the actions rebuild everything in between).

### Actions (`actions.jsonl`, built by `session_actions.py`)
`add_vertex` (id, local, world, screen, `linked_to` = old vertices joined by a new edge = where the extrusion came from), `add_face` (id, verts),
`move_vertex` (id, from, to, world, screen), `select` (verts), `topology_change` (deletion/undo: indices shift, cannot match vertex by vertex).
Conventions: Z up, front = -Y, metres; `screen` = pixels of the 3D region (origin bottom-left).

## From raw recording to dataset episode
```
python tools/general/session_to_dataset.py <rec_NN> <episode_dir> --name <name>      # episode.jsonl, initial/final_state.json, episode_meta.json
python tools/general/dataset_pack.py episode --stage retopology --asset wing --id wing_rec04 --rec <rec_NN> [--final-mesh final.json]
```
`dataset_pack.py` writes the gzip-compressed, path-scrubbed episode into the versioned `dataset/` folder (layout in `dataset-spec.md`).
Recordings of the old format (no `actions.jsonl`) are rebuilt from the snapshots. Raw sessions (keyframes, screenshots; tens of MB) stay out of git.

## Known limits
- View navigation (orbit, pan, zoom) only shows as keys/wheel; the view matrix is in the keyframes.
- Deletions and undo do not match vertex by vertex (`topology_change`).
- Only the active object is recorded (if the artist switches objects, the recorder follows); the reference never enters the logs.
- Edits made while the recorder was NOT running (UV, later shape adjustments) are recovered afterwards by comparing saves: `tools/general/blend_diff.py`
  (`edit_record`) -> `dataset_pack.py record --stage uv|adjust`.

## What the alligator recordings taught (read before using one)
- The recording shows **what the artist reuses**: the rear leg (2-toe reference) was replaced by a copy of the front leg moved back. Reuse beats fitting a bad part.
- Vertex moves right after a scripted pass (about 620 on the head) mark what scripts cannot do (eyes, brows, toes): schedule those for the user, not for more scripts.
- Deleted parts (crests near the legs) show the budget the artist wants: fewer faces where nothing deforms or reads.
- The user records heavy objects (1.5M triangles): keep the recorder light (actions every change, full mesh on keyframes) and warn before opening such a blend.
- Corrections said aloud are data too: write them in the case file the same day (`post-mortem.md`, section 4).

## Sharing
Raw recordings go to the public Hugging Face dataset, not to git: `session-sharing.md` (refs with `hf_refs.py`, upload with `hf_push.py`, limits).
