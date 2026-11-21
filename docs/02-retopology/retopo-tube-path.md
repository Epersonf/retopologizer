# Tubes along a path (cutlass guard, grip, flat curved blade)

Thin parts that run along a curve lying in one plane: a sword's crossguard, knuckle bow, grip and pommel, and the
flat curved blade itself. Each part is a run of rings along a 2D path; every ring vertex is a ray hit on the
reference. Result on the cutlass (1.5M-tri Hunyuan3D reference): 4 meshes, 396 quads / 784 tris, quads only, blade
mean new→ref error 1.9 mm, guard 2.3–4.6 mm, `topo_qa` clean (no holes, no non-manifold, no winding conflicts).

Code: `examples/cutlass/` (`measure_raster.py`, `blade_centerline.py`, `cutlass_blade.py`, `tube_lib.py`,
`cutlass_guard.py`, `cutlass_grip.py`, `cutlass_uvbake.py`, `cutlass_deliver.py`).

## When to use
- The part is long and thin, and its axis is a curve in one plane (the model's plane of symmetry).
- Tubes: crossguard, knuckle bow, handle, pommel, staff, bow limb, chain link. Flat blades: same idea with a
  hand-picked cross-section (edge, bevel, spine) instead of a ring of rays.
- Hard corners with detail (chest lid, clasp): `retopo-snap-mirror.md`. Organic parts that deform: `retopo-llm.md`.

## Step by step
1. **Apply the import transform** (`measure_raster.py`). The glTF import adds a rotation to the object and
   `BVHTree.FromObject` works in local space: rays cast in world coordinates miss (7k hits instead of 40k). Apply the
   transform once and save `draft/<name>.blend`; the reference geometry in world space does not change.
2. **Raster the silhouette and thickness**: a ray along −Y and one along +Y every 2 mm on the XZ plane →
   `draft/raster.npz` (front/back hit per cell). Plot `yf - yb` as an image: the silhouette, the thickness (blade 41 mm,
   guard up to 120 mm) and where parts overlap all show up. Every later measurement reads this raster, not the mesh.
3. **Path per part**: a rough polyline read off the plot (5–9 points), smoothed (Chaikin ×2), resampled to N rings,
   and each inner point re-centred across the silhouette (`recenter`). The blade's centre line comes from
   cuts across the chord guard→tip (`blade_centerline.py`), plus the tip point, which the cuts stop short of.
4. **Blade rings** (`cutlass_blade.py`): 6 vertices (edge, end of bevel, spine; front and back), from the thickness
   profile across the blade: the bevel ends where the thickness reaches 90% of the plateau. Rings denser near the
   tip (`1 - (1-u)^1.4`). Each vertex is `S.nearest` of its raster point.
5. **Tube rings** (`tube_lib.tube_ring`): 8 rays from the path point around the tangent, first ray at 22.5° so flat
   faces sit front/back. **The reach depends on the direction**: along ±Y nothing crosses the tube, so up to 8 cm;
   in the XZ plane the reach is the silhouette half width (+4 mm), divided by the cosine to the in-plane normal
   with a floor (`FLOOR`). An unlimited in-plane ray exits through the blade or the neighbouring tube.
6. **Bury the ends** that meet another part: copy the end ring and push it 2–3.5 cm along the tangent, into the
   neighbour, unsnapped (`bury=`). Measuring rings right at the junction catches the neighbour's width.
7. **Separate shells instead of a T-junction**: the knuckle bow leaves the crossguard sideways; it is its own tube,
   buried in the crossguard and in the pommel. Quads only, and the hidden intersection does not show after the bake.
8. **Close the ends** with 3 quads per octagon (`(0,1,2,3), (0,3,4,7), (4,5,6,7)`), or 2 quads for the 6-vertex blade.
9. **Check per part**: `wire_overlay` front/persp **and back/bottom** (a buried ring can poke out the far side),
   `fit_report`, `topo_qa`. Then one UV atlas and `bake_robust` for all parts (`cutlass_uvbake.py`).

## Numbers (cutlass)
| part | rings × sides | quads | mean / p95 new→ref |
|---|---|---|---|
| blade | 23 × 6 (incl. 1 buried) | 130 | 1.9 / 6.0 mm |
| crossguard | 9 × 8 | 70 | 4.6 / 15.6 mm |
| knuckle bow | 12 × 8 + 2 buried | 110 | 2.3 / 10.2 mm |
| grip + pommel | 17 × 8 + 1 buried | 142 | 4.7 / 23 mm (pommel facets) |

`inward_area_pct` of 7% on the guard and grip is the buried rings and the crossguard inside the blade: the nearest
reference surface there belongs to the other part. Bake: 3.8% of texels inpainted, almost all on hidden faces.

## Pitfalls already seen
| symptom | cause | fix |
|---|---|---|
| a fraction of the expected hits | `BVHTree.FromObject` is local; the glTF import rotates the object | apply the transform before building the BVH |
| ring spikes into the blade | unlimited in-plane ray exits through the neighbour | in-plane reach = silhouette half width |
| crossguard ring spreads over the blade | where the blade crosses, the silhouette is continuous and the half width is huge | cap to the part's typical half width (`wide=`) |
| pommel ring shrinks to the grip width | the cap above also hit the pommel (11 cm wide) | raise the measuring range `r` so only truly continuous cuts are capped |
| pommel vertices pulled onto the knuckle bow | long diagonal rays (`FLOOR=0.3`) | `FLOOR=0.6` on the pommel |
| blade base ring twisted, error 40 mm | the cut next to the guard measures the guard | inherit the neighbour's profile and put the centre on its line |
| buried ring visible behind the guard | buried too deep (3.5 cm) through a thin guard | 2 cm, and always render the back view |
| `wire_overlay` "cannot save" | the PNG is open in an image viewer (Windows locks it) | write each round to a new file name |
| `bake_robust` IndexError on `material_slots[0]` | low-poly parts without a material | give all parts one shared material before the bake |

## Adapting to another piece
- New path: change the polyline points and ring counts; keep `bury` where parts meet.
- Thicker or rounder sections: more sides (10–12) and a smaller `FLOOR`.
- Part out of the XZ plane: rotate the reference so its plane of symmetry is XZ before step 2.
