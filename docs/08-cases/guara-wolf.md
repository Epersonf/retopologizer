# Case: guara-wolf (quadruped, fused toes, what the agent got wrong and the artist did right)

Reference: AI wolf, 1,499,790 tris, 0.37 x 1.18 x 0.53 m (Y long, snout -Y, Z up), mouth open, leaf-like fur tufts. Budget: 4000 tris
maximum, under 3000 preferred. Started with the front-left leg (the other legs and the body come from it by reuse).

## Leg and paw: the derivative scheme worked
`limb_tube(ref, a, b, "auto", n=12, cap=False, max_rings=10)` from a = (0.045, -0.205, 0.19) to b = (0.043, -0.268, 0.027).
- 10 rings x 12 = 108 quads, 0 flipped faces, 0% inward, only the two end rings open. The artist approved it.
- The start height matters (scan it before choosing; n = 8, same end point): z = 0.19 passed, 0.17 barely (min rung 0.22 mm),
  0.15 and 0.13 failed (profile up to 86-89 mm, 16 flipped faces) and 0.21 failed (80 mm spike): rays leave through chest fur.
  Leave the shoulder for the trunk round.
- 8 vs 12 vertices: 12 chosen because 3 toes of 4 per ring leave room for a knuckle ring.
- The LAST ring is oblique (the tube axis is tilted 21 degrees): its top vertices land on the toe knuckles (y -29 to -30 cm), its
  bottom ones at the heel. That ring is the right toe-base ring. The agent read it as a fold and replaced it.

## Toes, attempt 1 (agent, rejected)
12-ring "mitten" with `box_ring` rings at y = -0.272, -0.281, -0.290, columns on the two grooves, and dome caps made with quads
(hexagon 3 quads, octagon 4 quads, hexagon 3 quads, two chord vertices). 154 quads, 0 tris, inward 0.65%, vertices snapped
(0 mm), and still wrong: it stopped at y -0.31 with no claws, and it replaced the approved ring. Why it happened: the guide pointed
at what fails (alligator toes) and at `poly_patch` for branches, not at the working pattern; and the agent checked only topology.

## Toes, attempt 2 (artist, recorded: `projects/guara-wolf/session/rec_01`, 5.5 min)
Started from the approved end ring (12 vertices, indices 108-119). Operators: 159 select, 40 translate, 29 edge_face_add (F),
26 extrude_region_move, 18 resize, 8 rotate, 3 loopcut_slide. 67 new vertices, 72 new faces, all quads.
- **Phase 1, 0-220 s, vertex by vertex** (add_vertex, extrude, F): 12-ring to a **14-ring knuckle** (3 toes x 6, 4 shared web
  vertices). Layer 1 from the seam: 14 vertices, valences 3, 3, 6, 6 and ten of 4.
- **Phase 2, 221-321 s**: each toe is a 6-ring extruded 2-3 times with resize / rotate / translate (taper and follow the toe), one
  loopcut at the claw base, tip closed in quads. Layers 2-5: 16, 18, 14, 5 vertices. New faces per toe: 21, 27, 24.
- Claw tips reach y = -32.4 cm (reference -32.6).
- Result (187 vertices, 180 quads, 0 tris, border 12): distance to the reference mean 0.32 mm, p95 2.1, max 5.8; inward 0%;
  poles 3: 14, 5: 2, 6: 4.

## What changed in the pipeline because of this
- New guide `docs/02-retopology/retopo-tube-network.md` (everything is tubes; how tubes join; plan before building).
- `character-index.md`, `retopo-convex-parts.md` section 6 and `retopo-by-parts.md` fixed (they pointed to patches and to failures).
- Tools: `tools/general/session_report.py` (reads a recording), `tools/02-retopology/transplant.py` (reuse an approved part),
  `tools/general/live_rings.py` (rings, shrink and bridge live in the artist's Blender).
- Rule in `README.md`: apply the documented pattern first, declare deviations, never alter approved geometry.

## Reuse test (transplant.py)
The artist's left front leg and paw (187 vertices, 180 quads) mirrored across x = 0, rigid ICP onto the wolf, snapped along vertex
normals: mean 0.51 mm, p95 2.5, max 6.7, 0 inward (the original left side: 0.48 / 2.6 / 6.7). Topology unchanged, so the right leg and
the rear legs start from the artist's method instead of a script's guess.

## Right front paw (agent alone, no artist help)
Leg: `limb_tube` mirrored (a x = -0.045, z = 0.19; dx = 0, z 0.19 and 0.17 pass, 0.21 fails), 10 x 12, 0 flipped, 0% inward. Toes: the
recorded pattern (12 quads to a 14-ring, three 6-ring toes), seam aligned to MY end ring (7 mm mean offset, vertices re-snapped).
`projects/guara-wolf/i4_paw_right.py`. 180 quads, winding 0, inward 0.01%, claws at y -323.8 mm (ref -326.0). Open: skew faces at the webs.

## Error: faces cutting each other at the claws (artist, 2026-11-22)
The rear paw (and the front one) delivered with faces crossing at the toe tips: 64 pairs / 34 faces on the rear paw, 4 on the front; the artist
selected them in Blender. The agent only looked at `topo_qa` (no intersection test existed) and at images. Cause: the toe block was copied with a global
rigid fit, not anchored to the NEW leg's seam ring, then pulled onto the surface; tips of 1-3 mm fold over each other easily. First "fix"
(relax + project) reached 0 pairs by throwing claw vertices up to 49 mm away: the number was 0 and the paw was wrong. Final fix:
`transplant.anchor` (ring Procrustes; rear paw: ICP for the toe direction, then translation only), `conform(max_move)`, `untangle(max_move)`.
Front paw: 0 pairs, claws at y -324.7 (ref -326.0), 0.0% inward. Rear paw: 0 pairs, claws at 114.9 (ref 113.0), 0.4% inward; the outer toe tip is still irregular.
New: `qa_intersect` (battery, `topo_qa`, `Topo.write` raises), `live_intersect.py`, `untangle.py`, rule 7 in `retopology-rules.md`.

## Error 2: twisted quads at the rear toe tip (artist, 2026-11-22)
After the intersection fix the artist selected one toe tip and said it was not fitted to the toe and two faces were "stamped on each other". No test saw it:
nothing crossed and all vertices were 0 mm from the surface. Numbers: face 170 had its two triangles folded onto each other (cosine -0.99), 168 and 171
too (-0.88, -0.84); faces 127 and 178 looked into the toe (normal vs surface -0.88, -0.84); 127 was 2-3 mm behind 170-172. The front paw had one (face 120).
New test `qa_faceshape` (rule 8, `docs/03-qa/qa.md`).

## Toe refinement after `qa_faceshape` (2026-11-22)
`l1_build_paw.py` now loads `face_shape.py`, so `untangle` also repairs twisted/stamped/inverted faces. Front paw: clean with `max_move` 8 mm.
Rear paw: stuck at 13 bad faces with 8 and 12 mm (the template seam is 10.7 mm from the new leg ring), clean with 20 mm (`MAX_MOVE` in `l2_run_hind.py`),
claw tip 113.8 mm vs ref 113.0. Both paws: `qa_intersect` and `qa_faceshape` pass. `qa_shape` still reports 1 pointed vertex (claw tip) and 1.1% slivers: natural for a claw.

## Rear toes, round 2 (artist, 2026-11-22): right toe good, middle worse, left "non-existent"
Passing the tests was not enough: the 20 mm untangle had squeezed the outer toes into 5 mm blobs. Cause: one global anchor for three toes that are
spread differently in the rear paw, then a Laplacian relaxation that trades one bad face for another. New: `toe_fit.py` (k-means splits the fused
toes, each one is fitted by similarity ICP on its own ref toe: 0.6-1 mm mean distance), then conform/untangle with 4 mm, then `face_polish.py`
(hill-climbing per vertex) for what is left. Result: 0 intersecting/twisted/stamped/inverted faces, claw tip 114.4 mm (ref 113.0). Parameters in `l2_run_hind.py`.
Still open: `qa_shape` slivers 2.8% around the claw tips; the artist judges the look.

## Rear toes, round 3: the artist rebuilt them on camera (2026-11-22)
The artist deleted the toes of the rear leg and rebuilt them in 490 s with the recorder on. Full measurement: `toes-artist-analysis.md`; reasons and rules: `toes-artist-why.md`. Clean version of the artist's mesh (merge by distance + 5 vertices nudged <= 5.7 mm, 0 defects): `draft/artist_hind_clean.json`.

## Whole-body state after rec_03 (2026-11-22, agent's reading of the saved `guara_mirror.blend`)
Right half: 697 vertices, 652 faces in 2 parts. Part A (608 v): both legs, hip, rump, tail base, flank and belly strips; part B (89 v): top of head and ears.
Open boundaries: A has ONE hole loop of 59 edges (odd: a quad-only fill is impossible without a loop cut or a triangle) that holds the shoulder, chest and the neck
opening and the front leg's open top ring (9 free vertices); B has a 35-vertex border. Everything forward of the shoulder (chest, neck, jaw, face) and the tail
does not exist yet. `qa_suite`: intersect pass; faceshape 2 inverted (peito (-64,-187,224) mm, orelha (-80,-389,507) mm); 11 tris + 1 heptagon (one tri at the rump, the heptagon in the head).
Missing tools for the agent to continue alone: `hole_fill` (quad fill of an arbitrary loop with poles, parity fixed by a loop cut) and `loop_bridge` (rings between two loops with different counts). Spikes: separate leaf-card models (`docs/04-uv-bake/leaf-cards.md`).
