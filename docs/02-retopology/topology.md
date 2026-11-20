# Topology: what an artist decides (and why)

Theory for deciding loops, poles and counts before placing vertices. Repo rules: `docs/00-rules-and-tools/retopology-rules.md`.
Practical methods: `docs/02-retopology/retopo-snap-mirror.md` (hard parts) and `docs/02-retopology/retopo-llm.md` (characters and organics).

## What the low-poly mesh is for
- **Silhouette**: it is what you see in profile. Polygons go where the outline changes; flat areas need few.
- **Deformation** (characters): loops at the joints so the volume does not collapse when bending.
- **Bake**: the low has to stay close to the high (small error = clean normal map). Small detail (wrinkles, seams,
  fine scales, screws) goes to the texture, not to the mesh.
- **UV**: clean loops give straight islands and seams that are easy to hide.

The engine triangulates everything: the budget is counted in **triangles**.

## Vocabulary
| term | what it is |
|---|---|
| quad / tri / n-gon | face with 4 / 3 / 5+ sides |
| edge loop | edges in sequence crossing quads through the opposite side (the ring around the arm) |
| edge ring | the parallel edges a loop cuts (what a "loop cut" creates) |
| pole | vertex with valence ≠ 4: 3-pole (N), 5-pole (E), 6+ (avoid) |
| contour | ring drawn around a tube (limb, finger, tail, neck) |
| manifold | every edge has 1 face (border) or 2; 3+ = non-manifold |
| T-junction | vertex in the middle of another face's edge: opens a crack, the bake and QA ray goes through |
| sliver | very thin face: bad shading, bad UV |
| winding | order of the face's vertices = side of the normal; neighbors must agree |

## Principles
1. **Quads only, no exception** (repo rule): no triangles, no n-gons. Quads deform and subdivide predictably,
   form loops and give clean UVs. A cone or claw tip = one pole vertex with quads around it (even ring:
   `Topo.fan`); a flat cap = grid or patch with a pole (`Topo.grid`, `poly_patch`), never an n-gon.
2. **Loops follow the shape**: rings perpendicular to the axis on arm, leg, neck, tail and fingers; concentric on
   eyes, mouth and nostrils; along edges and creases. A loop runs across the piece without dying midway.
3. **Constant count on a tube**: the same number of vertices on every ring gives strips of quads without loose
   triangles. Changing the count requires planned poles.
4. **Poles are tools**: they change the direction or density of the loops. In flat areas that do not deform (chest, back,
   top of the head), never in the middle of a fold. Never 6+.
5. **Parity**: a region closes with quads only if the contour has an **even** number of edges. That is why the root of a
   finger is an even ring and the fingers come out in alternating columns (finger, web, finger...).
6. **4-sided hole** = grid (`Topo.grid`, like Grid Fill). **3- or 5-sided hole** = a 3- or 5-pole in the
   middle and grids in the corners (`retopo.poly_patch`).
7. **Density only where it pays**: silhouette, deformation, bake. Every loop needs a reason; what is only color or shallow
   relief stays in the texture.
8. **Symmetry**: build only x ≥ 0 and mirror (`Mirror` with Clipping + Merge ~1 mm). Seam vertices exactly
   at x = 0.

## Changing the density
- Every count change creates poles; decide where they go beforehand.
- Parity rules: on a strip, **3 → 1** and **4 → 2** close with quads only; **2 → 1** does not (odd contour). In that case
  change the counts (use 3 → 1 or 4 → 2, or adjust a neighboring ring) until the contour is even; a triangle is not the way out.
- **3 → 1** (or 1 → 3) = two 3-poles and two 5-poles. Example: the back of Cuca's hand (`cuca_hand.py`), where 3 palm
  edges become 5 at the finger knuckles so the fingers come out of columns 0, 2 and 4.
- 5-sided region with a 5-pole: Cuca's back and top of the shoulder (`cuca_back.py`); `solve_spokes` says how many
  edges each spoke takes from the edges on each side.

## Deformation (characters)
- **A joint that bends = 3 loops**: one at the center of the bend and one on each side (Cuca's elbow and knee). Fingers: one
  ring at each joint.
- **Shoulder and hip**: loops that follow the deltoid and the groin. The arm comes out of a hole in the torso (Cuca: 2×2 hole =
  8-ring of the arm).
- **Wrist, ankle, neck**: 1–2 loops, with the count of the limb that arrives.
- **The bone bends where there is a loop**: in the rig, the joints go to the rings (`tools/06-rig/autorig/rings.py`). Cuca's tail bends
  in the gaps between scales, one segment per scale.
- **A face that animates**: concentric loops on eyes and mouth. Static stylized face: only the silhouette matters.

## Hard parts (props)
- Silhouette with few cuts; 1-segment chamfer on the edges that catch light (helps the bake).
- A protruding detail (rivet, clasp, plate) can be a separate shell **sunk ~4 mm** into the piece, with no bottom face.
  Never floating (leaks rays) nor coplanar with another face (z-fight: offset 2–4 mm).
- Boxes always closed: an open box leaves a backface in view.
- A hard edge (split normals) needs a UV seam on the same edge, otherwise the normal map marks the edge.

## Budget (triangles)
Start from a low target and justify every loop. In this repo:

| asset | tris |
|---|---|
| chest (2 pieces) | 813 (target < 1000, max 2000) |
| stylized tree | 380 |
| cow (statue) | target ~2000 (the automatic 6234 version was rejected) |
| Saci (character) | 2864 |
| Cuca (character with tail and scales) | 3756 |

Orders of magnitude in games: small prop 100–1000, medium prop 1–5 thousand, stylized character 3–10 thousand.

## Checklist before calling it done
- 100% quads: `topo_qa(...)["quad_only"]` is `True` (0 tris, 0 n-gons).
- No 6+ poles; poles away from folds.
- Closed rings around each limb and joint; equal counts at the seams.
- No holes, non-manifold, duplicates, conflicting winding or inward-facing faces (`topo_qa`, see `docs/03-qa/qa.md`).
- Small new→ref error (chest lid: mean 3.4 mm) and no large detail missing (`fit_report`).
