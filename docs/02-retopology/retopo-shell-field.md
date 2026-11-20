# Field-based shell retopology (beanie, hood, sleeve, sack)

For cloth pieces with an opening (beanie, hood, sleeve, bag, saci hat): the mesh is made of **concentric rings
from the opening to the tip**, like the rows of a knitted beanie. What decides where each ring goes is a harmonic
field (Laplace) measured on the outer surface of the reference: its level lines go around the piece and
never cross or split, even where the piece folds or turns into a drooping tail. The field only **measures**; each vertex is
placed by the script and snapped to the ref (rules: `docs/00-rules-and-tools/retopology-rules.md`).

Full example: `projects/hat-hair/` (beanie with a drooping tip: 960 quads, closed at the bottom, `quad_only`, 0 holes,
mean error on the shell 0.04 mm). Characters and simple tubes: `docs/02-retopology/retopo-llm.md`. Ring and pole theory: `docs/02-retopology/topology.md`.

## When to use
- The piece is a thin shell (cloth with thickness), open on one side, and its axis bends (the tip falls sideways, the hood
  folds). Plane cuts or rings around a straight axis cross each other inside the curve.
- Not for hard pieces with corners (`docs/02-retopology/retopo-snap-mirror.md`) nor for bodies with arms/legs (`docs/02-retopology/retopo-llm.md`).

## The process (3 scripts, run in this order)
1. **Measure in Blender** (`hat_measure.py`, worker): export the part's vertices, normals and triangles (in world space), the tip
   and which vertices are on the **outside** of the cloth. Outside = some ray leaving the vertex (directions with
   `d·n > 0.15`) escapes to open space, **using only directions that don't look through the opening** (`d·A < -0.1`, A = axis
   of the opening). Without this filter, the inner wall seen through the opening counts as outside.
2. **Plan the rings outside Blender** (`hat_field.py`, plain Python + scipy):
   - **weld** the vertices by position (the GLB duplicates vertices at the UV seams; without welding the graph falls apart);
   - keep only the outside triangles and the largest connected component;
   - **zero = largest border loop** of that surface (the cloth edge around the opening), **one = vertices near the
     tip**; solve Laplace with cotangent weights (`spsolve`);
   - for each level (400 levels by quantiles of `u`, denser near the tip), take **all** the points where the
     line cuts the edges; form the ring by sorting by angle in the best-fit plane (PCA), median per angle
     slice (loose pieces from holes lose the vote), smooth, resample with `n` points;
   - distance along the piece `s` = sum of the median distances between neighboring levels (not the geodesic from the border,
     which shortens the tail when it passes near the opening);
   - choose rings with step = perimeter / n (square quads, minimum 2.5 cm) and **halve the count**
     (48 → 24 → 12) when the edge gets smaller than 2 cm. Saves `draft/hat_rings.npz`.
3. **Build in Blender** (`hat_outer.py`): each ring becomes vertices with snap (`T.vs`), aligned to the previous one with
   `align` (at the 4:2 cut, to the previous ring skipping by 2); `T.strip` between equal rings, 4:2 band between different
   counts (3 quads per group: pole of 3 on the wide ring, of 5 on the narrow one; never a pole of 6), `T.fan` at the tip
   (12 → vertex, 6 quads), `T.relax`, and the opening **cap**: 12 × 12 grid (`T.grid`, `snap=False`) with the bottom
   side at the quarter of the lowest ring. Finally `T.orient`, `write`, `topo_qa`.
4. Check with `hat_views.py` (`wire_overlay`, hair cut with `clip`) and show a view to the user.

## Beanie numbers
| part | rings | quads |
|---|---|---|
| body (48 around) | 11 | ~530 |
| transition (24) and tail (12) | 16 | ~260 |
| tip (fan) | — | 6 |
| bottom cap (12 × 12) | — | 144 |
| total | 28 | 960 (requested limit: 1500) |

## Pitfalls already seen
| symptom | cause | fix |
|---|---|---|
| field zero almost everywhere, empty contours | GLB with duplicated vertices at the UV seam | weld by position before the graph |
| open level lines (arcs, not rings) | the "zero" was a rim found by ray, which is not the border of the outside surface | zero = largest border loop of the outside mask |
| outside mask with holes near the tail | outside decided by normal x skeleton | visibility: ray that escapes, without looking through the opening |
| jumping perimeters, half rings | following cut edges in one direction breaks on dirty meshes | all points of the level + sort by angle (PCA) |
| rings bunched at the tip, few on the tail | levels at uniform `u` / `s` by the geodesic from the border | levels by quantile of `u`, `s` by distance between levels |
| rings crossing the cavity, dome uncovered | rings interpolated (lerp) between the mouth and the base of the tail | Laplace field on the surface |
| relax pulls the cap onto the inner wall | relax snaps back to the ref | make the cap after the relax |

## Adapting to another piece
In `hat_measure.py` change the opening axis `A`, the part cut (`X_HAT`) and the starting point of the tip `track`;
in `hat_field.py` the counts `COUNTS` and `MIN_EDGE`. Piece with two openings (sleeve): zero on one border, one on the other.
Afterwards: UV without overlap (`docs/04-uv-bake/uv-bake.md`), GPU bake (`hat_bake.py`: small extrusions, 0.02/0.04 m, because the shell
is stuck to the ref and a large extrusion makes the dome's ray hit the tail), delivery by part (`docs/02-retopology/retopo-by-parts.md`).
