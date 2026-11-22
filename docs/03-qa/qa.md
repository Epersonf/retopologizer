# QA: when the mesh is ready

Run before the final UV, the bake and the export. Everything inside Blender; each test returns a dict with `pass`.
Theory of what a good mesh is: `docs/02-retopology/topology.md`.

## Single command: the battery (`qa.py`) — start here
```
python -I tools/03-qa/qa.py LowPoly --ref HairFull            # everything, one line per test (~25 s)
python -I tools/03-qa/qa.py LowPoly --ref HairFull --fast     # strict with 100 directions: for iterating (~8 s)
python -I tools/03-qa/qa.py LowPoly --only fit,attach         # only some (--skip drops some; --json returns the whole dict)
```
Exits with code 1 if any test fails; each FAIL carries a `fix:` line and **where** the problem is (coordinates and region,
`front-top-right` etc.), so the agent does not need to open 8 dicts. Inside Blender: `qa_suite(name, ref=..., only=..., fast=...)`.
Order (cheapest to most expensive): `mesh`, `intersect`, `budget`, `shape`, `floating`, `attach`, `local`, `strict`, `fit`.
Agent flow: **iterate with `--fast`, run the full one once before showing it to the user**; when the user points at a
defect that no test caught, write the test first (it must fail the bad file), then fix.

## What makes a model good (what each test protects)
1. **Faithful to the ref**: silhouette (IoU) from 14 directions, nothing of the ref uncovered (hole, notch), nothing in the model that the ref lacks (`fit`).
2. **Clean surface**: closed, quads only, no inverted normal seen from afar (`strict`) or up close, in gaps and folds (`local`).
3. **Pieces that hold**: nothing floating (`floating`) and each piece *buried* in what supports it, not just touching or with the
   cap piercing the surface (`attach`).
4. **Shape that reads well**: no spikes, needle tips, thin tubes (`shape`).
5. **Budget** (`budget`).
Passing all five together is the minimum; a model that passes only the surface ones (1 and 2 for normals) can still look terrible.

## Intersecting faces (`qa_intersect`, zero tolerance): never in a retopology
Faces of the SAME loose part that cut through each other, or lie folded over each other, reject the mesh (guara-wolf paws: 64 pairs
on the rear paw, the artist's selection showed it). `face_intersect.py` triangulates, takes BVH candidates and tests exactly (edge through
triangle, coplanar overlap, folded shared edge; faces of one polygon and neighbours that merely touch do not count). Parts buried in another
part are reported as `cross_part`, not failed. `select_faces(obj, r["faces"])` selects them; `untangle.py` moves only those vertices
(max_move limit) and the distance to the ref must be checked afterwards. While working: `live_intersect.py` paints them red and writes the
count in the status bar. Also run inside `topo_qa` (`self_intersections`) and `Topo.write` (raises).

## Face shape (`qa_faceshape`, zero tolerance): twisted, stamped, inverted faces
Guara-wolf rear paw: a toe tip had quads folded onto themselves although no face crossed another and every vertex was 0 mm from the surface
(distance to the ref cannot see it: corners on different sheets). `face_shape.py` (core of `qa_faceshape`):
| test | rule | calibration (artist's paw good / agent's rear paw bad) |
|---|---|---|
| twisted | min cosine between the normals of the two triangulations of a quad < 0 (bow-tie, quad folded on itself = "two faces stamped") | +0.16 / -0.99, -0.88, -0.84 |
| inverted | face normal . normal of the ref surface under it < -0.2 (the face looks into the model); needs `ref` | +0.22 / -0.88, -0.84 |
| stamped | two faces of one part, no shared vertex, opposite normals, overlapping, closer than 0.35 x the smaller edge (heuristic: thin margin, 0.43 on the artist's mesh) | 0.43 / 0.20-0.38 |
The tests do not replace the others: `qa_intersect` finds crossings, this finds faces that are wrong by themselves. Also in `topo_qa`
(`twisted_quads`, `stamped_faces`, `inverted_vs_ref`), `Topo.write` (raises), `untangle` (repairs them) and `live_intersect.py` (magenta).
`tools/03-qa/test_intersect.py` is the regression: bad meshes must fail, good ones pass; run it after touching either module.

## Coverage (`qa_cover`): does the mesh cover the ref near it?
Guara-wolf rear paw: every face was clean (`qa_intersect`, `qa_faceshape` pass) while the left toe was collapsed into a 5 mm blob and the tip of the middle toe missing:
no face-level test can see an absent toe. `qa_coverage.py` takes the ref vertices inside the mesh bounding box (+ 10 mm) whose nearest point on the mesh is between
6 mm and 30 mm (too far to be covered, too near to be another body part; points whose nearest face touches an open border are skipped: that piece belongs to the next part)
and reports the share (`uncovered_pct`) and the clusters (centroid in mm). Pass <= 1%.
| mesh | uncovered | clusters |
|---|---|---|
| artist's rear toes (rec_02, merged) | 0.67% (pass) | one, 242 points at (-126,168,42): the ref belly above the ankle, also in the leg alone |
| agent's rear paw, round 2 | 4.77% (fail) | (-136,129,38) 907 points (knuckle), (-165,193,10), (-175,145,2) the left toe tip, (-156,117,3) the middle tip |
| agent's front paw | 1.52% (fail) | (-28,-304,31) 484 points, (-54,-317,36) |
Limit: it sees a toe that is built badly or short, not a toe that lies outside the bounding box of a leg-only mesh (that is `qa_fit` / `budget`).
Regression: `tools/03-qa/test_cover.py` (a sphere with a cap missing must fail, the full one pass).

## Chest gate (`qa_all.py`: backfaces + UV + z-fighting)
`exec(open(r"<repo>\tools\03-qa\qa_all.py", encoding="utf-8").read()); qa_all(["chest_base", "chest_lid"])`
raises an error if any test fails (`raise_on_fail=False` just returns the report).

| test | tool | fails when | fix |
|---|---|---|---|
| backfaces | `qa_faces.py` | the first hit of some ray (400 directions × 200×200, open cavities included) is the back side of a face, the red of Face Orientation; grazing hits (\|n·d\| < 0.1) ignored | `fix_flipped()` flips faces seen only from behind; a face with 0 front votes was buried: delete it |
| **visible inverted normal (strict gate)** | `qa_strict.py` | **any** ray, from 400 directions around (200×200 each), whose first hit is the back of a face, confirmed by 4 neighboring rays; zero tolerance, the model is **rejected** (do not save, do not deliver) | `heal_flipped()` relaxes the rejected faces (stronger and wider each time) and reruns; if any remain, change the geometry (shell borders, cap), never "flip" |
| **ugly shapes** (tips, thin) | `qa_shape.py` | spike vertex (far from the neighbor center, ratio > 0.8); thin-tipped tube (final ring < 40 % of the middle radius); thin tube (radius < 2.2 cm); report of narrow faces (angle < 20° or > 165°, edge > 5× the smallest) | `heal_spikes()` relaxes the spike; tube: minimum radius, tip only down to 65 %, never to a point; discard strand < 1.3 cm |
| **inverted normal seen up close** | `qa_local.py` | rays leaving the front of each face, in a hemisphere (48), hit the back of another face (≥ 3 votes); points inside a solid (buried root) are ignored. Catches folds and tube caps piercing the shell, which no ray from afar sees | relax the faces (`_relax`) in the heal; bury the tube root deeper |
| **tube held only by touching** | `qa_attach.py` | the tip of a tube (cap + 1st ring) is not entirely inside another piece, or the deepest point is < 0.5 radius below the surface; this is the "loose tip even though connected" | `hair_connect.py`: moves the tip to 1.3 radius *below* the surface, along the normal, and deepens 0.4 per pass |
| **fidelity to the ref** | `qa_fit.py` | only what the eye sees (first hit of orthographic rays, 14 directions): mean IoU < 0.88 or worst < 0.80; > 6 % of the ref pixels without model or with the model > 3 cm behind (hole, "should be filled"); > 4 % of the model pixels without ref or in front of it > 3 cm (lump, valley that doesn't exist). Faces with the `headfill` material (head stand-in, caps) don't count. Shows clusters with region | cover the cluster with a shell or tube; remove what is in excess |
| **mesh** | `qa_mesh.py` | tris/n-gons, open border (hole), non-manifold, conflicting winding, loose vertex, duplicate, degenerate face | close it, redo the piece |
| floating parts | `qa_floating.py` | some group of loose pieces (union by intersection or < 3 mm) does not touch the largest; expected = number of groups in the ref (normally 1) | extend the piece's tip to the surface it should touch (`hair_connect.py`); **always run when splitting an object into several meshes or assembling separate pieces** |
| z-fighting | `qa_zfight.py` | two nearly parallel triangles < 1 mm apart with overlapping area (coplanar plate, face inside face) | space 2–4 mm apart or remove the face |
| UV | `qa_uv.py` | overlap between or within islands (at 2048 and 4096), outside 0–1, zero area, flipped, islands < 8 px apart | redo the UV (`docs/04-uv-bake/uv-bake.md`) |

## Topology (`tools/02-retopology/retopo/qa.py`)
`topo_qa("Cuca_retopo", Ref("HiPoly"), seam_x=0.0)`: faces/tris/quads/n-gons, triangles after triangulating, holes
(border edges), non-manifold, loose vertices, duplicates (< 0.5 mm), conflicting winding, inward faces
(against the ref normal), poles (3 / 5 / 6+), degenerate faces, distance to the ref.
Expected: `quad_only` True (0 tris, 0 n-gons: repo rule), hole only at the mirror seam (`seam_x`), and zero
non-manifold, duplicates, conflicts, inward faces and 6+ poles.

## Mark and report (`qa_mark.py`, `qa_report.py`; ideas from the user's TopoToolkit add-on)
- `qa_mark("Obj", select="border")`: writes boolean attributes `qa_border`, `qa_nonmanifold`, `qa_wire`, `qa_doubles`, `qa_tris`, `qa_ngons`, `qa_degenerate`, `qa_pole_3..8/n` and selects one type
  (`select="poles"` picks all poles). Save the `.blend`: when opened in Edit Mode the defects show up selected. `remove_marks("Obj")` deletes the attributes.
- `qa_report("Obj", "x.html", ref=..., battery=True)`: one file with counts, orphan/border/multiple edges, valence (pole 3..8 and N > 8), doubles, the battery lines and inline views. `.txt` and `.csv` too.
- Poles fail nothing in the battery (no defect the user pointed out was a pole); they appear in the report and in the marking.

## Shape (faithful to the reference)
- `fit_report(low, ref)`: new→ref (floating or excess faces) and ref→new (missing detail) in mm, plus the 5 cm
  cells where the ref is farthest.
- `compare([ref], [lows], hot_k=10)` (`compare_mesh.py`): the same in % of the diagonal, with the hot spots.
- `section_overlay` (cuts) and `overlay` (silhouettes) show where the error is.

## Causes that have shown up
- Boxes with open lid or bottom (`skip=` of `mesh_lib.box`): every box closed.
- Buried pieces piercing the cavity.
- T-junction between the lid bottom and the walls after moving vertices: the ray enters through the gap and exits behind
  the wall. Redo the bottom with `bmesh.ops.bridge_loops` between the outer loop and the cavity one.
- Coplanar plates with the border came out black in Cycles and `BVHTree.overlap` did not see them (it never flags coplanar
  triangles); that is why `qa_zfight` has its own AABB broad phase.
- `recalc normals` on an open mesh can flip the whole cavity. Red Face Orientation = normal pointing inward.
