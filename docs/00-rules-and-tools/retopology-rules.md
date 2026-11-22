# Non-negotiable retopology rules

1. **Never use automatic retopology** to generate the delivered mesh: QuadriFlow, Remesh (voxel/quad), Instant
   Meshes, Decimate/Planar as the final result, shrinkwrap of a generated mesh. This mistake was already made on the cow (3117 quads,
   6234 tris, uniform grid with no intent) and rejected by the user. Do not repeat it, not even "as a first pass".
2. **Always manual: vertex by vertex with snap** onto the reference, with a mirror when there is symmetry. Hard part:
   `tools/02-retopology/snap_retopo.py` + `docs/02-retopology/retopo-snap-mirror.md`; character or organic: `tools/02-retopology/retopo/` + `docs/02-retopology/retopo-llm.md`.
3. **Quads only**: the delivered mesh is 100% quads, **no triangles and no n-gons** (`topo_qa(...)["quad_only"]`
   must be `True`). A cone tip becomes a pole with quads around it; an odd contour is solved by changing counts, not
   with a triangle (`docs/02-retopology/topology.md`). The engine triangulates on import; that is no reason to deliver tris.
4. **Good practices**: edge loops following the shape (rings around legs, neck, muzzle, eyes, joints), few poles
   (and away from areas that deform), density only where there is silhouette/deformation, small details stay in the
   texture. Full theory: `docs/02-retopology/topology.md`.
5. **Budget**: start from a low target (cow: ~2000 tris after triangulating, ~1000 quads) and justify every loop.
6. Automatic tools only **measure** (BVH, raycast, fit_report); they do not generate the final mesh.
7. **No face may cut through another face of the same loose part** (intersection or fold-over), anywhere, at any moment. It is a defect
   of the geometry, not of looks: the mesh is rejected. Detect with `qa_intersect` (zero tolerance, in `qa.py`, `topo_qa` and
   `Topo.write`) and keep `tools/general/live_intersect.py` running while you work: faces cutting each other turn red. Never "fix"
   by hiding it (smoothing until the number is 0 can throw tips onto another part: check the distance to the ref afterwards).
8. Statue in "as is" mode: if the reference is crooked/asymmetric, the user fixes it later; do not symmetrize
   or edit the reference without being asked.
