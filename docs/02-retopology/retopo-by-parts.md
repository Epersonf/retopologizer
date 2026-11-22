# Retopology by parts (the cycle that worked on Cuca)

A whole model in a single round is slow, errors get mixed together and the user only sees the result at the end. By parts,
each round has a small goal, an image in minutes and a deliverable the user approves and integrates. This is how
Cuca's hand, leg, foot and tail came out approved, each in a few passes.

> The OBJ of a part (step 8) is a **checkpoint**, not the delivery. The model is done only with the README's
> "Definition of done" (UV, bake, QA, delivery). If the user did not ask for rounds, still work by parts but go on
> through UV and bake before reporting.

**Suggest this to the user** when the request is "retopologize the model" or when a part is not coming out well:
propose the split and the order, and start with the part they choose. It works for any method: characters with
`tools/02-retopology/retopo` (`docs/02-retopology/retopo-llm.md`) and hard-surface pieces with snap + mirror (`docs/02-retopology/retopo-snap-mirror.md`).

## Splitting the model
- **One part = one shape with a clear boundary**: hand, leg without the foot, foot, tail, head, ear; lid, handle.
- **The boundary is a ring**: the part starts at a ring that already exists (the wrist of the artist's arm, 12 vertices) and ends
  closed (fingertips) or at an open ring left on purpose for the next one (the ankle of the leg). The count of that
  ring is the contract between the two parts: even and equal on both sides, 1:1 fit.
- **Order: from the trunk to the extremities**. The trunk defines the limb holes (arm, neck, leg rings);
  then arm → hand, leg → foot, neck → head; last the extras (tail, ears, horns) and the seams that
  close the rest (hip, skirt). Prop: main body → attached pieces → details (clasp, rivets).
- A part that touches a region that does not exist yet ends at a hidden open ring and stays as a separate piece until the
  neighbor is ready (Cuca's leg starts at a ring under the skirt).

On Cuca, the artist made the head, torso and arms. The rounds were: hand → leg (without the foot, ring of 12 at the ankle) →
foot → tail (with the scales).

## One round
1. **Current base**: copy the user's latest `.blend` (`draft/cuca.blend` → `draft/cuca_retopo_vN.blend`), open
   it in the worker and switch to `OBJECT`. They may have edited the mesh since the last round: no stale indices.
2. **Keep their mesh untouched** as a datablock (`LowPoly_user`, fake user). It is the starting point of each
   attempt (`cuca_user_build.py`) and the basis for separating the part afterwards.
3. **Isolate the region**:
   - measure only it: `slice_plot --box` around the part, raycasts and profiles only there (where the fingers separate, the dorsal
     profile of the tail);
   - view only it: `wire_overlay([...], path, view, center=<part center>, size=<width in m>)`, in the views where the
     shape reads (hand: persp and top; foot: side and sole; tail: side and top);
   - find the seam ring: `wire_overlay` + `label_png` show the indices; `T.old(...)` grabs those vertices;
   - if the neighbors confuse the snap (fingers stuck together in the ref), `ref_part` cuts out only the part's reference.
4. **Short plan**: count of each ring, where the poles go, what stays open (`docs/02-retopology/topology.md`).
5. **Build** in a script for the part (`projects/<name>/<name>_<part>.py`), run by the driver with `PARTS = [...]`.
6. **One image right away**: render one view, open it, show it. Fix what is visibly wrong and repeat. Other
   views (top, bottom, side) only once this one is good.
7. **Separate and check only the part** (`tools/02-retopology/retopo/part.py`):
   ```python
   p = part_object("LowPoly", "LowPoly_user", "Cuca_pe")   # faces new or changed in this round
   topo_qa("Cuca_pe", R)                                    # seam_x=0.0 if the part is on the mirror plane
   ```
   Expected: `quad_only` True (0 tris, 0 n-gons), open border only on the seam rings, 0 non-manifold, 0 duplicates,
   0 conflicting winding, 0% inward area. Faces the artist started for this part come in with
   `also=[indices]`.
8. **Deliver only the part**: `export_obj("Cuca_pe", r"<folder>/cuca_pe.obj")`. It uses Blender's default
   axes: imported with the default options, it lands in place. Save the copy with the part already attached.
9. **Report**: file, faces and whether they are all quads, which ring stayed open and with how many edges (fits 1:1 with what),
   where the next part starts, how to redo it (driver + `PARTS`) and what you did not check.
10. **The user integrates** it in their file (imports the OBJ, welds the seam) and approves. The next round goes back to step 1
    with the new file.

Checked in Cuca's rounds: leg 108 quads with 24 open edges (ring under the skirt + ankle), foot 136 quads
with 12 (ankle), half tail 72 quads with only the half ring under the skirt open (besides the x = 0 seam).

## What the user said → what it was → what to do
| they said | what it was | what to do |
|---|---|---|
| "one stuck to the other" (fingers) | finger rings starting before the real separation | measure where the fingers separate (rays from inside the palm outward, at several heights) and start each finger after the web |
| web entering the finger (foot) | web out of place | web at the deepest point between the toes |
| "the tail could have fewer loops" | density without reason | one segment per scale, a ring only in the gaps |
| "the triangles on top of the tail" | dorsal scales missing | 2-vertex crest on the seam, rising to the top of the scale |
| "it's taking long" | long analysis without an image | build right away, show one view, fix afterwards |

## Why it works
- Small goal: the image comes out in minutes and the user corrects early.
- The error stays local: one bad part does not contaminate the rest, and redoing costs one round.
- The user's file is the source of truth: they integrate and can edit by hand between rounds.
- The seam ring is a contract: same count, 1:1 fit, no seam triangles.
- Each part is a script: redoing is running it again.

## Pitfalls
- Vertex indices change when the user edits: re-read with `label_png` every round and note in the script where they
  came from (`cuca_foot.py`: ankle ring = indices 732–743 of that version's LowPoly).
- A `.blend` saved in Edit Mode opens in EDIT in the worker: `mode_set(mode='OBJECT')` before anything.
- Part on the mirror plane (tail): build only half, with the seam at x = 0 and `topo_qa(..., seam_x=0.0)`. The OBJ
  comes out as a half and the user's Mirror completes it.
- If the round changed the artist's faces (cleanup at the seam), `part_object` includes them: tell the user to delete the
  old ones when importing.
