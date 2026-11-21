# Working with an artist who retopologizes by hand (record, understand, continue)

Used on the wing (`docs/08-cases/wing.md`). The artist does the retopology (and later the UV); the agent records, reads the method, continues
where they stopped, and does the stages that scripts do well (shell, bake, relief, rig, export).

## Loop
1. **Open a copy of the start file with the recorder running** (`tools/general/record_session.py`). Confirm the recording is alive (the folder grows) and tell the
   artist which view to use (orthographic front) before they start. Never open the file they are editing for your own work: the Blender they have open is theirs.
2. **Artist works, saves, tells you.** Make a backup copy of their saved file first (`*_user_<n>.blend`); never overwrite it.
3. **Analyze**: convert the recording (`session_to_dataset.py`), render the saved mesh over the reference (`wire_overlay`), look at the image, and describe the method
   in numbers (strip size, how rows join, where it starts). Reconstruct what they did, not what you would have done.
4. **Continue THEIR mesh**: append to their object (same vertices, same counts at the seams). A new mesh next to theirs is not a continuation; we got that wrong once and
   the artist said so ("you should have continued from mine").
5. **Show an image, early**: one view, the problem circled. If the artist circles something, fix exactly that and re-render; long analysis without an image frustrates.
6. **After the artist's UV, only move vertices.** Re-running a builder recreates the mesh and loses the UV. Bake, textures and rig are layered on top.
7. **Compare saves** to learn their adjustments (`tools/general/blend_diff.py`): they may have joined objects, thinned the wing, moved the handle.

## Lessons from the wing
- Automatic retopo attempts (feather layers, ring extrusion, chain sweep) were rejected; the artist's demonstrations plus careful continuation worked.
- Read the circled problems literally: gaps (touch the parts), overlaps (bury bar ends in the plate), disconnected (extend the neck into the plate), "texture is bad" (the handle
  needs its own texture path, not the high-poly bake).
- Say what you verified and what you did not (the QA battery failing on tests that are for hair tubes; the Godot import never run).
- Everything the artist did while not recorded is recovered by comparing saves and stored as `adjust`/`uv` records, separate from the retopology episodes.

## Data hygiene
Separate by stage and by actor in `dataset/` (`dataset-spec.md`): what the artist did (`user`) is the demonstration; what the agent ran (`agent`) is a recipe.
Scrub paths and the user name before anything is versioned (`dataset_pack.py` does it).
