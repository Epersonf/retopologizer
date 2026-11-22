# Everything is a tube: one mesh made of tubes that join (read this first for any organic part)

Rule from the artist (guara-wolf, 2026-11-22): in the end **everything is tubular**: feet, hands, chest, neck, fingers, toes, claws,
tail, breasts, horns, hair locks. A character is several tubes that join into ONE mesh. The exceptions are the **face** (eyes, mouth,
nose) and the **ears**: organic shapes, done last and by hand (`retopo-convex-parts.md` section 6).

Before building a part, answer: what tube is it, where does it start (seam ring), where does it end (a tip or a seam ring for the
next tube), and which tubes branch from it. Then follow this guide. Do not invent a topology (a mitten with dome caps, a patch grid)
when the pattern below exists: the case `docs/08-cases/guara-wolf.md` is what that costs.

## 1. One tube
1. **Seam ring**: a closed ring with an EVEN count that already exists in the mesh (the end of the previous tube). It is a contract:
   never replace or move a ring the artist approved.
2. **Stations**: where the section changes (`retopo-convex-parts.md` section 4: extrema of dr/dt), plus 3 rings at every joint
   that bends (`topology.md`). The budget decides how many survive (`max_rings`).
3. **Rings by extrusion**: extrude the previous ring, then scale (taper), rotate (follow the axis) and move it to the next station,
   snapped onto the reference. A script does the same with `limb_tube` / `digit`; the artist does it with extrude + S + R + G.
4. **Loop cut** at the next deformation (claw base, knuckle) instead of another full ring.
5. **End**: a tip (the last ring shrinks and closes with a quad fan, a pole) or an open ring left on purpose for the next tube.

## 2. Joining tubes (where scripts failed)
- **Parent to children** (hand to fingers, paw to toes, torso to neck/legs/tail): the parent's end ring has to become the roots
  of the children. For children that are **fused** (side by side, sharing walls) the root ring is a **knuckle ring** where the
  children share web vertices: `N = k*m - 2*(k-1)` for k children of m vertices in a row (3 toes of 6: 3*6 - 4 = 14).
  This is the Cuca pattern in `retopo-llm.md` ("knuckles 14, 3 fingers of 6"), and what the artist did on the paw.
- **12 to 14 is done by hand**, one vertex at a time (extrude a vertex, `F` to make the quad), never with a triangle. It leaves
  poles in the web area (valence 3 and 6): accepted there, because the webs do not deform like a joint.
- **Fused children stay tubes**: each child is its own 6-ring extruded to its tip; the groove between two children is the edge
  loop that the shared web vertices start. No mitten, no dome caps, no `poly_patch` for toes. `poly_patch` only closes a 3- or
  5-sided hole.
- **Separate children** (not touching): each one gets its own even root ring from the parent (`digit`), as the gator toes.
- Count changes make poles: decide where they go before the first vertex (`topology.md`, "Changing the density").

## 3. Order of the tubes
Trunk (torso, chest) first, then the tubes that leave it (neck, tail, legs), then paws and hands, then fingers and toes, then claws;
extras (horns, breasts, hair locks) next; face and ears last. Each tube is one round (`retopo-by-parts.md`): one image, one number,
the artist integrates, next.

## 3b. Tips and webs must not cross themselves
Tips of toes, claws and webs are tiny quads (1-3 mm): where faces cut each other. After every build run `qa_intersect`; keep
`live_intersect.py` on while building by hand. Anchor a copied block by the NEW seam ring, never only by a global fit.

## 4. What the end of a tube must match
The tip of a toe, claw or tail is part of the silhouette. Check the **extent**, not only the topology: the farthest point of the part
along each axis, low versus reference, in mm (`fit_report`; the bbox of both). A part that stops 1 cm short of the claws fails even if
`topo_qa` is clean. The paw rounds stopped at domes 1.5 cm before the claws and nobody noticed until the artist redid them.

## 5. What a script may and may not do
- May: measure (profiles, slices, extrema), place the first ring, run `limb_tube` for the straight parts, snap vertices, check.
- May not: decide the branching topology of fused children. The artist's recorded method is the reference (`session_report.py` reads it).
- To reuse an approved part elsewhere (rear paw, the other side) use `tools/02-retopology/transplant.py`: it moves the artist's
  topology and snaps it; it does not invent a new one. Reuse beats fitting a bad part (`docs/08-cases/alligator.md`).

## 6. Before you build: write the plan (5 lines) and show it
Pattern used (file and section), seam ring (indices, count), what is reused, what will be measured, deviations from the guide and why.
Build only after the artist says yes. If you feel like deviating, that is the moment to ask.

## 7. Closing holes and joining loops (`tools/02-retopology/hole_fill.py`, test `tools/03-qa/test_hole_fill.py`)
- `boundary_loops(bm)` ordered border loops (pinched ones are skipped; `pinches(bm)` lists them: fix by hand first).
- `fill_loop(bm, loop, ref)` quads only. Tries every corner placement and side split (a + b = n / 2) and keeps the one with corners at the real turns and square cells;
  a Coons grid, snapped to the ref, old vertices never move. An odd loop gets one loop cut first (the cheapest quad strip whose cut makes it even).
- `loop_bridge(bm, A, B, ref, rings)` quad strip between two loops with the same count, snapped rings in between, start and direction chosen by total rung length.
  Different counts raise: the count change is a pole pair made by hand (section 2).
- Checked: a hole in a sphere (8 quads, closed), an odd 35-edge loop of the wolf (cut + 77 quads, 0 crossings, centres 2 mm from the ref), a face loop of the wolf's hind leg removed and rebuilt (28 quads, 0.6 mm, 0 new defects).
- Limits: a grid fill suits a hole that is topologically one rectangle (a cap, a flank); a hole with a leg ring on its border is not one: join that leg with `loop_bridge` first.
