# Case: Alligator (quadruped, 3000 tris, mirrored half)

Retopology by parts of an AI-generated alligator with the user finishing by hand (recording `projects/alligator/session/rec_02`).
What the artist did that the scripts did not, measured from the recording and the final mesh.

## What worked in the scripts
- Rings of 12 around the body axis (profile by radial rays, opening filter, snap): body, tail, neck and snout came out at 0.4-1.5 mm mean error.
- Crests as separate shells sunk about 6 mm, no bottom face. Central ones need vertices exactly on X=0 and a cap split along X=0 (hexagon ring) or the Mirror cannot merge them.
- Open mouth: two shells (skull + upper jaw, lower jaw) instead of one tube. One tube snapped onto the lower jaw only.
- One object, half the mesh (`x >= 0`), Mirror modifier on; the pieces stay separate islands.

## Where the scripts failed: feet and toes
The artist's front leg has 159 faces: 28 for thigh and shin, about 130 for the foot (3 toes of 15-29 faces). Mine gave the toes 8 quads.
- **Toes are not parallel.** Measured splay of the three toes: -17, +3, +13 degrees from -Y. I split the foot into equal X bins and built every claw along -Y; the cones missed the toes.
- **A toe is a tube with segments** (knuckle, pad, claw), each ring sized from the toe's own cross-section, sunk into the foot. A claw alone (4 rings of 4) loses the volume.
- **Measure per toe, not per foot slab.** Points of the lowest 6 cm in Y only reach the tips; the toe axis needs the base too (cluster the toe, take the axis base to tip, rings perpendicular to it).
- Thigh and shin were fine as 3-5 rings of 8, so spend the budget on the foot.
- The rear foot of the ref had 2 toes; the artist copied the front leg to the back (13 mm mean error, accepted) instead of fitting a bad leg. Reuse a good part before modelling a second one.

## What else the artist changed
- About 620 vertex moves on the head right after my rings: eye and brow regions need hand nudges, rings are a base.
- Central crests cut to 4-8 faces each (mine had 9 to 20) and the crests near the legs removed.
- Mesh ended with 6 triangles and 7 heptagons from joining pieces; quads-only still has to be checked at the end.

## Teeth (done by script after the artist's mesh)
Method that worked: points of the ref more than 6 mm outside the final mesh, clustered with a KD-tree (radius 3.2 mm), one pyramid per cluster:
axis = base (closest points) to tip (farthest), 3 rings of 4 sized by percentile of the cross-section, base sunk 3.5 mm, cap quad (9 quads each).
Upper teeth merge with the palate in one cluster: keep only the points below the palate band, then cluster again.
13 teeth at 1.5 mm mean error; the back teeth were not outside the artist's mesh and are missing.
Scripts: `projects/alligator/t1_teeth_pts.py`, `t2_teeth_fit.py`, `t3_teeth_build.py`.
- A defect that stays visible after fixing the albedo is the normal map (or AO) first: see texturecraft-cli.md, alligator case.

## After the mesh: texture, rig, game, store (post mortem, 2026-11-22)
Full post mortem: `projects/alligator/POST_MORTEM.md` (local; the lessons are copied into the guides). Pipeline of the second half, with the tool of each step:
1. **Texture retouch in TextureCraft** (mandatory): ID-map colour selections for teeth and spines (uniform colours), eye strokes (a yellow-face mask polluted the snout, strokes worked),
   leg-removal hole = normal map + AO fan: flatten the mesh maps, then clone belly lines (`tool.clone`, size ~1.6). `docs/04-uv-bake/texturecraft-cli.md`.
2. **Rig and clips**: `r1_rig.py` (hand skeleton, numeric weights), `pose_actions.py`: Idle, Walk, Bite, TailAttack, Attack, Death (belly up: roll about the animal's length). `docs/06-rig/rigging.md`.
3. **Game**: `export_clips` GLB, Creature shape `gator`, mobs 146 and 177, test, viewer `--creature`. `docs/05-delivery/delivery.md`.
4. **Store**: `export_clips` FBX (all actions) + `fab_package`, `listing_renders` (bite, walk, death), `fab_form`. US$1.99 / 3.99, 10 tags, AI answer = the user's. `docs/05-delivery/fab-upload.md`.
Final blend with all six clips: `draft/gator_rig_v3_clips.blend`. Numbers: 3,396 tris (budget 3,000), 28 bones, 6 clips, 2048/1024 textures. Open: ~20 px UV overlap, no roughness/metallic/AO, FBX not reopened elsewhere.
