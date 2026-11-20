# Snap + mirror retopology (lid v5 method)

Reproduces what an artist does by hand (vertex by vertex with *snap to face*, `Mirror` when symmetric),
but by script, so it is measured, repeatable and passes QA. Result on the chest lid: 340 tris, mean
new→ref error 3.4 mm (p95 11 mm), 0 backfaces, 0 UV overlap, 0 z-fight. Before, with fitted simple
shapes, the lid had 248 tris and lost the straps, blocks, chamfers, cavity and clasp.

Code: `tools/02-retopology/snap_retopo.py` (loads `snap_surface.py` + `snap_mesh.py`), `tools/general/ref_part.py`,
full example in `examples/chest-lid/build_lid_v5.py`.

> **Quads only.** Lid v5 predates the rule and has triangles and n-gons (end cap, rim, welded slivers).
> On a new piece, swap those three spots for the quad versions given in steps 5 and 7.

## When to use
A piece with detail the AI generated (straps, blocks, chamfers, clasp, rivets) that has to stay faithful
for the bake to work. For boxes/simple shapes, `mesh_lib.py` + fitting by `compare_mesh.py` is enough.
Characters and organic shapes (limbs, hands, tail): `docs/02-retopology/retopo-llm.md`.

## Step by step
1. **Isolate the piece from the reference** (`ref_part(ref, "chest_lid", "REF_LID", radius=0.06)`).
   It copies only the ref triangles near the piece and puts them in the **piece's local space** (the lid in the
   closed pose, symmetry axis aligned to X). Careful: the ref may have a rotated matrix_world (+90° X) and
   `BVHTree.FromObject` is local; that is why the BVH is built in world coordinates.
2. **Measure before modeling**: heights by raycast as a function of x (`h(x)`) find where there is a strap,
   step, end block and chamfer. Note the positions in x (lid: strap |x|<0.055 +14 mm,
   block 0.225–0.31 +22 mm, chamfer up to 0.326, cavity up to 0.26, rim z=0.06).
3. **Cuts by angle**: from a center `c` inside the piece, `Surface.outer(x, c, angle)` returns the hull
   point; `Surface.inner` the cavity one. With `simplify(cut, 6 mm)` (Douglas-Peucker) the arc's
   **corners** come out (lid: 9 outer, 8 for the cavity). Use these same angles in all rings:
   same vertex count = quad strips without stray triangles.
4. **Rings of half a side only (x ≥ 0)**: strap, step, body, step, end block, chamfer, end
   cap. A step is two rings at the same x (flat wall, no slope). The ring ends (at the
   rim) use a **horizontal** ray on the wall (`wall_y`): the slanted ray oscillates ±1.5 cm on the
   AI's roughness. Every vertex is projected onto the ref (snap), never typed in.
5. **Strips** `Mesh.strip(A, B)` between neighboring rings, cavity as another strip. End cap: quad grid
   (ring with even count, closed as a grid or with a pole in the middle), never an n-gon. Quad slivers of 2 mm: merge the
   two rings into one instead of welding (welding becomes a triangle).
6. **Mirror**: `Mesh.mirror_x()` = Mirror + apply + weld the center plane. Only half is built.
7. **Flat rim** between the outer loop and the cavity one: give both loops the **same count** (same angles) and
   connect with `Mesh.strip` = one strip of quads. `fill_flat_ring` (used in v5) triangulates: no longer fit for delivery.
   `bridge_loops` with different counts crossed triangles and produced UV overlap.
8. **Protruding details** (clasp, rivets) with `Mesh.prism(base, normal, height, embed=4 mm, snap)`:
   the base is **projected onto our own mesh and sunk 4 mm** (no bottom face); the top sits
   on the ref surface; clasp hole = `Mesh.dimple`. Prism top with a 4-sided base (or even, closed as a
   grid): an n-gon top violates the quads-only rule. A floating base lets the ray into the slab
   and QA flags a backface. Overlapping corner plates: space them 3 mm apart (coplanar = z-fight).
9. **Check**: `fit_report` (error both ways, cells without detail), `section_overlay` (cuts
   colored ref × white low), `qa_all` (backfaces, UV, z-fight: `docs/03-qa/qa.md`), `unwrap_atlas(angle=66)` (89°
   folded the arc's islands), then `bake_robust` (`docs/04-uv-bake/uv-bake.md`).

## Why it works
- Snap on 100% of the vertices: the mesh is born on the surface, so the high→low bake has little error.
- Same angles in all rings: clean topology, quads aligned with the shape, easy to UV.
- Mirror: half the work, exact symmetry, easier UV.
- Everything in script (`build_*.py`): if the ref or the measurement changes, run it again.

## Pitfalls already seen
| symptom | cause | fix |
|---|---|---|
| piece extracted in the wrong place | ref with rotated matrix_world, local BVH | BVH in world space (`ref_part`) |
| folded UV islands | smart_project 89° on arcs | 66° |
| crossed triangles at the rim | `bridge_loops` with different counts | loops with the same count + `strip` |
| backface on the clasp slab | floating base | project onto the mesh and sink 4 mm |
| black squares in Cycles | coplanar plates (z-fight) that the BVH didn't see | `qa_zfight` with AABB; space 3 mm apart |

## Adapting to another piece
Change `C`, `A_OUT`, `A_IN`, `XS` and the `build_*` (lid = arc extruded along X). For pieces
with radial symmetry use rings around the axis; for no symmetry, build everything without `mirror_x`.
