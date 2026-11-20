# Merged tubes and locks: one separate mesh per tube (hair, tentacle, horn, cable)

Status: **direction approved, being tuned** (`projects/hat-hair`: 1176 quads = 2352 tris, limit 3000: hood 352 + 19 tubes 824).
One command rebuilds everything: `hair_build.py`. **No visible inverted normal is accepted** (see "Strict gate"). The first attempt (connected
mesh, via rays) was discarded: slow, inverted normals.

## The idea
When the ref is a block of tubes that cross each other (curly hair, tentacles), don't try a single continuous mesh.
**Each tube is its own closed mesh, unconnected** to the others and to the base; they overlap as in the ref. For games the user
accepts this, it is much cheaper in polygons, and each tube is born with correct normals. The base (head/torso) is another mesh.

## Before starting
**Ask for the polygon budget** (quads or triangles?) and split it between base and tubes. For the hair, 1410 quads (2800 tris) was
too big; the target became 1000. The budget decides the ring spacing, the number of sides and which tubes make the cut.

## Process
1. **Base**: Laplace shell over the outer envelope (`retopo-shell-field.md`; `hair_part.py hood 32,16,8` = dome + front in a single shell; before, `dome 24,12,6`: lower
   counts in the rings = fewer quads; 24,12,6 gave 174 quads, 48,24,12 gave 552).
2. **Find the locks without picking by hand** (`hair_locks.py [persistence_m]`, plain Python + scipy): weld the UV-duplicated
   vertices by position; geodesic on the surface starting from the base faces; tips = maxima; merge tree with
   persistence (0.03 m finds 20 locks, 0.05 m finds 17); branch = tip → saddle path pulled to the medial axis by the EDT
   (3 mm voxels). Output: points and radius per lock. `hair_locks_plot.py` generates the numbered plot.
3. **One tube per lock** (`hair_tubes.py [min_len] [budget]`, pure Python, seconds): smooth the axis, resample, rings of 6
   sides (8 if radius ≥ 3.2 cm) with parallel transport, smoothed EDT radius, **linear taper from half the length down to
   30 % at the tip**, cap of 3 or 4 quads at both ends. Face orientation comes out right from the construction (strip by the direction
   of the rings, cap by the shared edge). If it exceeds the budget, the ring spacing grows ×1.08 until it fits.
4. **Front (extra cover)**: the dome cuts off at ±100° from the nape and leaves out the bangs and the top of the front (34 % of the top-view
   silhouette uncovered). A second Laplace shell, `hair_part.py front 16,8,4` (window PH 100..260, TH 0..70; the azimuth
   window may exceed 180), covers that with 116 quads and brought the uncovered area down to 12.7 %.
5. **Check in Blender** (`hair_tubes_load.py`): one object per tube, error to the ref (mean 3 to 4 mm, up to 20 mm on tubes
   the ref flattens), signed volume > 0 (normals outward), edges without repeated direction (closed).
   Then join everything into one object (`LowPoly`) for the user to see and check the winding (0 bad edges).

## Strict gate: no visible inverted normal (zero tolerance)
`qa_strict.py` casts rays from 400 directions; if the first hit of **any** ray is the back of a face (the red of Face
Orientation), the model is **rejected** and nothing is saved. A closed surface with outward winding never fails; failing
means a fold, an open border or an inverted face. What caused failures here and the fix:
- **Open shell seen from below**: close it with a cap (`hair_cap.py`: one vertex inside the head + n/2 quads, vertex searched
  on a grid where no cap quad flips). Cheaper than solidify (which folds the faces).
- **Two shells overlapping** (dome + front cover): folds and caps cutting each other, 35 to 50 rejected faces. A single shell
  (`hair_part.py hood`: merged direction windows, `ALSO`) has no seam or overlap and passes; the lower cut at
  polar 120 (not 140) avoids the folded border under the locks.
- **Twisted quads at the border** (depth jump between locks): `heal_flipped` relaxes the vertices of the rejected faces
  (stronger and wider each round). Run it **before** attaching the tubes (it moves vertices; afterwards contact is lost).
- **Lone ray that escapes through the corner**: numerical noise; it only counts if 4 rays at 1/3 pixel also hit the back.
Never "fix" it by flipping the face (`fix_flipped`): a face seen from both sides turns red from the other.

## Ugly shape: tips and strands (what bothered the user and the test)
The user selected in Blender what bothered them; three kinds, all passing normals and contact:
- **Spike on the hood border**: a border vertex stuck to the tip of a ref lock, stretched like a needle. Test: ratio
  `|v - neighbor center| / mean edge` > 0.8 (seven vertices, two were the selected ones). Fix: `heal_spikes()` relaxes and
  then `heal_flipped()` again (each undoes the other: loop until both pass; `hair_heal.py`).
- **Tube ending in a point**: taper down to 35 % + cap vertex at 0.6 r = needle cone (final ring of 0.6 cm on a 2.5 tube).
  Test: radius of the final ring < 40 % of the middle radius (layered BFS along the tube; the axis is the line of layer centers).
  Fix: free tip only down to 65 % and never below 55 % of the fattest ring; cap at 0.25 r.
- **Thin tube**: strands of 1 cm radius next to tubes of 3 cm look like pimples. Thick and thin hair mixed only make sense
  in tied-up hair; here the thickness is similar (a calf wider than the knee is real shape, this is not). Fix: minimum radius
  2.4 cm (`RMIN`), strands with median radius < 1.3 cm discarded (`RDROP`). Test: middle radius < 2.2 cm.
`qa_shape.py` is part of the gate (`hair_join.py` does not save if there is a spike, thin tip or thin tube) and runs on any model.
The old file failed: 7 spikes, 16 thin tips, 8 thin tubes; the new one passes. When the user points at a new defect,
first write the test that finds it (and that fails the old file), then fix it.

## Nothing floats, nothing too thin
- `qa_floating.py` returns the gap and the target point; `hair_connect.py` moves the nearest tip to that point (+ half the
  thickness inward) and repeats. Always run it when splitting an object into several meshes (`expected` = real loose parts of the ref).
- **Thin necks**: hair does not thin out at the junction. Radius never below 0.75 of the median; only a free tip thins (last 30 % down to
  35 %); a tip that was attached to another piece keeps its full radius. (Thinness only makes sense where the real shape changes, like the
  calf wider than the knee, or tied-up hair.)

## How to know what is missing
`hair_cover.py` (worker): renders the silhouette of the ref and of the low poly from several views and paints red what the ref has and the low
poly does not, with the percentage. This is how the front bangs were found; looking only at the front view was misleading (the curtains
hid the gap). Use top, sides and 3/4.

## Pitfalls
- Rays from inside out through the merged ref exit through the neighbor's wall (ray of 5 to 10 cm in a 2 cm tube): that is why the tube is
  parametric, not raycast. TEASAR, cuts by z and the dome hull on the sides also failed (steps, merged lobes).
- Winding: `T.orient()` on the whole mesh is not reliable with tubes that cross each other. Build it right per tube and verify with the signed
  volume (per face, "normal vs nearest axis" gives false positives on tight curves and concave borders).
- Loose curl tips (4 to 6 cm, which do not start on another tube) end up **floating**; discard them (`min_len` 0.06).
- The global QA (`topo_qa` `inward_area`) sits at ~25 % on the dome because of the ref's hollow walls; don't use it as a criterion here.
- Tips that don't taper as in the ref: the EDT radius at the tip is already small, but smoothing erases it; hence the
  explicit taper.

## Status: NOT approved by the battery (`qa.py`), and why
The user pointed out three defects in a `hair_lowpoly_v3.blend` that passed all the old gates. Each became a test:
| what was seen | cause | test that finds it | number on v3 |
|---|---|---|---|
| "should be filled" / "valley that doesn't exist in the original" | the shell does not cover the back lobe or the top of the front; the cap fan shows up as a valley | `qa_fit` (silhouette IoU, uncovered ref by region) | IoU 0.77–0.79; 9 % of the ref uncovered (back-low, front-top) |
| "normal flip" at the top of a tube | tube cap piercing the parent's surface: from afar no ray sees it, up close it shows | `qa_local` | 30 faces |
| "loose tip even though it is connected" | tube held only by touching (the `qa_floating` gap ≤ 3 mm counts as connected) | `qa_attach` | 8 of 13 tubes not buried |
The old gates (mesh, budget, shape, floating, strict) pass; the three new ones fail. `hair_join.py` now runs the whole battery and
only saves `hair_lowpoly_v3.blend` if everything passes (otherwise `hair_lowpoly_rejected.blend` + the lines). The `v3` on disk is the last one that passed only
the old gates: **not approved**.

What was tried to get it to pass and was not enough (so as not to repeat):
- Buried root by tangent extension, by target point 1 radius below the surface, and by perpendicular rod (`hair_connect.py`:
  inner point + outer point on the normal): it reduces, but 8 tubes remain without a cap inside the parent. Most of the detected strand tips
  are 5–10 cm from the hood, i.e. the tubes hang from other tubes and from nowhere; the rod has to cross a gap.
- Joining strands that continue one another (`hair_chain.py`, 5 cm, cos > 0.3): no pair joins with these strands.
- Hood down to TH 135/150 (back lobes): the coverage of the hood alone barely changes and the cap stops closing without folds.
Likely path: back lobes as thick tubes (radius 6–8 cm, today the RDROP/budget filter loses them) and a flat cap at the
height of the border instead of the fan; attach each tube to the hood by a rod that starts inside it, never on another tube.

## Hybrid approach: cylindrical shell (`hair_cyl.py`), what worked
Manual choices (vertical axis through the head, columns, rows, "head fill" radius) + parametric fit to the ref (horizontal rays
from outside toward the axis, first hit = radius). Hanging hair is star-shaped around the vertical axis, so the grid **does not fold**
and there is no cap to position: just the two fans (top and bottom). Where the ref has no hair (face window, gaps) the radius is the head's
(material `headfill`, hidden by the head, ignored by `qa_fit`). Each column has its own top and bottom (the irregular hem).
Result, without tubes (the hat-hair build with `notubes`): 1008 quads = 2016 triangles, passes mesh, budget, shape,
floating, attach, **local and strict (the normals that failed the old model)**; fails only `fit` (IoU 0.87, ~16 % of the ref uncovered,
~13 % excess, at 3 cm): the loose curls do not exist and the hem/window are coarse. It looks like a smooth hair hood,
not curls. With tubes on top (`hair_build.py` without `notubes`) the tubes become sticks coming out of the shell and still fail `local`.
Going beyond that calls for a style decision: clean shell (approvable), or shell + ribbon curls (wavy, not straight prisms).

## Still open
- Uncovered silhouette: 10 to 16 % in the views (curl tips, corners). The detector in `z` mode (`hair_locks.py 0.04 z`) found the
  tubes that the geodesic missed (lower locks). **The right reference for coverage is `HairFull`**: `HiPoly` includes the cap and
  inflated the number to 35 %.
- Extended root tips may come out the other side of the hood (short spikes).
- Thin coiled curls become smooth curves (6 sides, rings at 2.5 cm).
- Locks flattened in the ref (error up to 20 mm): swap for an elliptical cross-section.
