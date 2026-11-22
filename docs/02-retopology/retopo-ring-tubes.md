# Ring tubes: headband, bracelet, collar (a curved band open on one side)

Case: the Curupira headband, 224 quads = 448 tris, 28 rings x 8 sides, fit checked on renders. Tool: `retopo.ring_tube`
(`tools/02-retopology/retopo/ring_tube.py`), rebuilt from the original script and giving the same 224 quads.

## When
A thin band that wraps a body part and does not close (horseshoe). `track` (spine by contour) has nothing to follow on a
band this thin, and `lock` expects a given axis. Here the spine comes from the shape itself.

## Process
1. **Spine**: group the ref vertices by angle around the vertical axis (180 bins, skip bins with < 50 points), take the
   centroid of each, smooth by 2. The seam of the angle must sit in the **opening** (`gap_dir`, here the front, -Y in Blender),
   otherwise the spine starts in the middle of the band and the first and last rings overlap.
2. **Rings**: resample the spine to N rings; the tangent is the ring normal. The section is a thin slab of the ref
   (|axial| < 4 mm) **and** within 6 cm of the ring center: without the distance filter the slab also catches the other
   tip of the horseshoe and the tube grows long spikes. Project on the ring plane, take the PCA major axis as the ring's
   "u" (keep its sign continuous with the previous ring or the tube twists), and the radius at each of the 8 angles is the
   farthest point within +-14 deg. The tube keeps the flat oval of the real band, not a circle.
3. Strips between rings, `fan` caps at both tips, `T.orient()`, `topo_qa`, `fit_report`, `wire_overlay`.
4. UV: seam along the inner line plus the end rings, `uv.unwrap(CONFORMAL)`, `average_islands_scale`, `pack_islands`,
   `qa_uv`. The bake is a normal map from the ref; a source with no texture (toon material only) gets a flat albedo
   (`bake_robust` needs a Principled material, so do not use it there).

## Pitfalls seen
- Empty slabs near the tips (the ref ends before the ring): lower the number of rings or check `min_pts`; `hull_section`
  falls back to the mean radius for angles with no point.
- Ring sign flips (`u @ prev_u < 0`) are what twist a tube; `hull_section` already handles it, but a custom spine must
  keep the rings in order along one direction.

## One call around a limb
`retopo/limb.py` (`limb_ring`, `limb_tube`, `bridge`): see `retopo-convex-parts.md` (ring, shrink, bridge, density from the rig, demo video).
