# Rear paw toes: why the artist did it that way (and what the agent must do instead)
Companion of `toes-artist-analysis.md` (the measurements). Each decision: what was observed, the evidence, the reason, the rule for the agent.
Reasons are **inferred** from behaviour; evidence is measured. Where a number is a parameter, it is the artist's own, from `events.jsonl`.

## 1. The recipe of one toe (the finding that matters most)
A toe is a **tube grown by repeating one move: extrude the cap, translate along the toe axis, scale uniformly, rotate about X (curl)**.
| step | left toe | middle toe | right toe |
|---|---|---|---|
| 0 flatten the cap: `resize [1,0,1]` (Y = 0) | 219 s | 356 s | 442 s |
| extrusion 1: scale / curl | .63 / 43 deg | .82 / 13 deg | .83 / 17 deg |
| extrusion 2 | 1.42 (re-grow) / - | .93 / 14 deg | .95 / 19 deg |
| extrusion 3 | .29 | .88 | .66 / 10 deg |
| extrusion 4 | .42 / 24 deg | .83 / 19 deg | .46 / 32 deg |
| tip collapse | - | .94, then **.108** / 36 deg | .30 (.81) |
| total curl (sum of rotations about X) | 68 deg | 82 deg | 78 deg |
Middle and right share the first two scales (.82/.83 and .93/.95, 1% apart): the artist carries one mental template from toe to toe.
Cross-section of every tube: **8 vertices around + 1 centre vertex** (cap patch); the claw tip is the cap scaled to 0.1-0.3 of the previous ring and merged (poles of valence 3-6; ring radius at the tip 1.3 / 0.7 / 0.7 mm).
Ring radii from the tip backwards (middle toe): 0 / 5.1 / 9.8 / 12.2 / 13.4 / 15.6 mm; centre-to-centre steps 3.2 / 7.1 / 8.7 / 7.2 / 4.6 mm.

## 2. Decisions
**D1 Start at the outer toe, from the seam's end vertex.** Evidence: first new vertices 120, 121 hang off seam vertex 115; the region then grows inward. Reason (inferred): the outermost column is on the silhouette, so its position is unambiguous from one view; it fixes the base line the next toes are measured from. Rule: build outer to inner, each toe finished (Tab out, Ctrl+S) before the next (checkpoints 234, 380, 468 s).
**D2 Grow the base by hand, one vertex + one `F` at a time, for 197 s.** Reason (inferred): the zone between the 14 seam columns and three round tubes has no regular pattern (poles, gaps); a vertex-by-vertex build keeps every valence-3/5/6 decision visible. Rule: this zone is the hard part for the agent; it needs the explicit constraints of section 4, not relaxation.
**D3 Two loop cuts through the whole leg (12 -> 14 columns), made before the toe that needed them (135 s, 402 s).** Evidence: v148 and v228 split seam edges (108,109) and (108,119); 14 is the documented pattern (`retopo-tube-network.md` 12-ring seam -> 14-ring knuckle). Reason: three 8-ring tubes plus two gap columns need 14 attachment points. Rule: if the seam has N columns and the toes need 14, cut loops on the **leg**, in the outer two columns, before building; never invent vertices in the base.
**D4 Flatten first (`resize` Y = 0, seen from the front view).** Evidence: the same op at the start of each of the 3 tubes; Numpad 1 at 220 and 358. Reason (inferred): it puts the cap on a plane perpendicular to the toe axis, so all later translate/scale/rotate keep the tube coaxial. Rule: ring k is planar and perpendicular to the toe axis at its centre.
**D5 Uniform scale, never non-uniform.** Evidence: every scale in the toe phase is uniform (all 16) except the 3 flattens. Reason: the ref toe is near-circular; elliptical sections come from the snap, not from the scale. Rule: radius_k = radius_ref(slice k) (measured, not scaled from a template).
**D6 Curl about X, most of it in the last step.** Evidence: last extrusion carries 32-36 deg of 78-82 (40%) together with the strongest scale (.108-.46). Reason: the claw bends down and ends in a point; its last ring is smaller and tilted most. Rule: ring normals follow the ref axis (slices), tip ring <= 0.3 of the previous radius, then collapse.
**D7 13.4 `move_vertex` per vertex, median surface distance 0.66 mm.** Reason: after each uniform step the ring is round while the ref toe is not; every vertex is dragged to the surface by eye. Rule: that is `ref.snap(p, normal)`; the agent does it in one pass, but must do it **per ring, before the next extrusion**, not once at the end.
**D8 Left toe: stack, rip, delete, re-extrude (248-311 s), 9 undos in a row.** Evidence: 5 duplicate clusters, twisted face 141, 5.7 mm nudge needed. Reason: the left toe lies against the narrow gap, its cap overlapped the neighbour. Rule: the agent must run `find_doubles` (0.6 mm) and `qa_faceshape` after every tube; here the artist forgot "merge by distance".
**D9 Face select mode before each tube (210, 285, 314, 347, 433 s), vertex mode for the fit.** Reason: extrude a region of faces keeps the cap patch (centre vertex) intact; vertex mode for the per-vertex fit.

## 3. Why the agent's fused-toe paw was wrong (measured against the above)
| agent | artist | consequence |
|---|---|---|
| copied the front paw's fused toes (6-ring, 3 rings long) | 8-ring tubes, 4-5 rings, measured per toe | wrong cross-section and length; toes squeezed into 5 mm blobs by relaxation |
| one rigid anchor for 3 toes | every toe positioned on its own ref toe | left and middle toe missing / off the surface |
| Laplacian untangle at the end (up to 20 mm) | fit per ring, per vertex, 13 times | faces trade defects (twist <-> inverted); 2-3 always left |
| tests on faces only | the artist's eye: "is there a toe here, does it follow the toe" | 0 defects reported while a whole toe was collapsed |
| no merge by distance, no toe-presence test | (also missed merge) | needs `qa_toes` (section 4) |

## 4. Rules and tests derived (what to implement)
1. `toe_axes(ref, seam)`: slice the ref with planes perpendicular to the paw direction every 2 mm; the slice with 1 component splits into 3: each component's centroid track is a toe axis; tips = last slice. **Check:** 3 tips within 3 mm of the artist's tips (-174,144), (-156,118), (-128,118) mm.
2. `toe_tube(ref, axis, base)`: 8 vertices + centre per ring, ring planes perpendicular to the axis, radius from the slice, spacing 0.55-0.7 x radius (7-9 mm in the body, 3-5 at the tip), last ring <= 0.3 x previous, collapse and merge; snap every ring before the next. **Check:** surface distance mean < 1.5 mm, ring radius within 25% of the slice.
3. `base_connect`: 14 seam columns (cut loops 0-1 and 11-0 on the leg), bridge columns to the three bases, poles only at the gaps. **Check:** 0 border edges except the leg's open end.
4. `qa_toes`: every ref claw tip has a mesh vertex within 3 mm; every toe has >= 4 rings; `find_doubles` 0.6 mm = 0; border edges = leg end only.
5. Merge by distance (0.6 mm) is part of every build; `Topo.write` raises if doubles remain.

## 5. Status of the automation (honest)
| piece | state |
|---|---|
| merge by distance | **done** `merge_doubles.py`, run by every paw build; `Topo.write` refuses duplicates |
| cleanup of defects without destroying the work | **done** `face_polish.py` (the artist's mesh: 5 vertices, <= 5.7 mm) |
| toes present and covering the ref | **done as a test** `qa_cover` (artist 0.67%, agent's paw 4.77%) |
| each toe on its own ref toe (transplant) | done `toe_fit.py`, but it still reuses a template: not the recipe |
| `toe_axes` (rule 1: direction, split depth, 3 axes and tips from the ref) | **not working**: a first version took the principal axis of the nearby ref points, which on a paw that bends 90 deg at the ankle is the body, not the toes; needs the ground/forward direction or the leg's own flow as input |
| `toe_tube` (rule 2) and `base_connect` (rule 3, the 197 s hand base) | **not started**; these are what makes it work "without help". The recipe of section 1 is complete enough to implement them |
