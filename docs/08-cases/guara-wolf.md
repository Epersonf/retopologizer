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
