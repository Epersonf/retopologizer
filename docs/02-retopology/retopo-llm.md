# Retopology of characters and organic shapes (`tools/02-retopology/retopo`)

The agent does what the artist does in Blender with snap and RetopoFlow: draws rings (contours) around the tubes,
decides how many vertices each ring has, closes with quads and snaps everything onto the reference. No remesh. Full example:
Cuca (`projects/stylized-cuca/cuca_*.py`). Hard parts: `docs/02-retopology/retopo-snap-mirror.md`. Cloth with an opening (hat, hood): `docs/02-retopology/retopo-shell-field.md`. Theory: `docs/02-retopology/topology.md`.

## Loading (inside Blender: worker or one-shot, see `docs/00-rules-and-tools/blender-automation.md`)
```python
import sys; sys.path.insert(0, r"<repo>/tools")
import importlib, retopo; importlib.reload(retopo); from retopo import *   # the reload picks up code edits
R = Ref("HiPoly")                 # reference in world space; BVH cached between calls
T = Topo(R)                       # new mesh; Topo(R, start="LowPoly_user") continues the artist's mesh
```

## The workflow
Work **by parts**, one round and one delivery per part (hand, leg, foot, tail...): `docs/02-retopology/retopo-by-parts.md`.
1. **Topology plan** before any vertex: parts, the count of each ring, where the poles go and which loops
   pass from one part to the next. Cuca:
   - torso in box layout, 20 around (per half: front 4 columns, side 2, back 4); 2×2 hole for the
     arm (ring of 8) and a hole at the top for the neck (12 around);
   - 8-sided arm with 3 rings at the elbow; 12-sided leg with 3 at the knee; 12-sided neck;
   - hand: wrist 12 → palm → knuckles 14 → 3 fingers of 6 (columns 0, 2, 4) with claws;
   - foot in box rings (top 3, sides 2, sole 5) → 3 toes; tail of 12, one ring in each gap between scales.
2. **One part per file** (`cuca_arm.py`...). Each one runs in a namespace with `T`, `R` and `L` (named loops:
   `L["wrist"]`, `L["arm_root"]`...) and leaves in `L` the loop where the next one starts: same count at the seam.
3. **Half mesh** (x ≥ 0) with a Mirror modifier (Clipping, Merge 1 mm) while working; seam at x = 0.
4. **Write and look**: `T.orient(); T.write("Cuca_retopo")`, then `wire_overlay` of the view that matters, show it
   to the user, fix what is visibly wrong. One part at a time, short cycles.
5. **Check**: `topo_qa("Cuca_retopo", R, seam_x=0.0)` and then `docs/03-qa/qa.md`.

Example drivers: `cuca_build.py` (new mesh, `PARTS` in order) and `cuca_user_build.py` (continues the artist's mesh).

## Package tools
| module | use for |
|---|---|
| `Ref` | `nearest(p)`, `ray(o, d)`, `hits(o, d)`; `snap(p, n)` = snap to face (with the expected normal `n` it does not jump to the neighbor); `exit(c, d)` = where the ray leaves the volume, from inside; `outer(c, d)` = outermost hull |
| `curves` | `ring` (loop around an axis), `arc` (part of a loop; half turn for the mirror), `line` (n segments over the surface), `arcline`, `resample`, `sample` |
| `contour` | `track` (spine of a tube: center, axis, radius), `centred` (center of the cut), `cring` (closed ring, evenly spaced on the real cut), `chalf` (half ring from x=0 to x=0), `align` (ring without twist relative to the previous one), `box_ring` (flattened cut: palm, foot), `at_width` |
| `Topo` | `v`, `vs` (vertices already snapped), `f`, `strip(A, B)` (strip of quads between rings), `fan`, `grid(B, Tp, L, R)` (Grid Fill with snap), `old(i)` (artist's vertex by original index), `relax`, `orient`, `chain`, `mirror_x`, `write` |
| `patches` | `solve_spokes` + `poly_patch`: 3- or 5-sided hole closed with quads around a pole |
| `digits` | `digit(T, R, root, p_inside, tip)`: finger, claw or horn grown from an even ring to the tip, following the curve |
| `qa` | `topo_qa(name, ref, seam_x)`: holes, non-manifold, duplicates, winding, inward faces, poles, distance |
| `part` | `part_object(low, base, name)`: only the round's faces as its own object; `export_obj(name, path)`: OBJ of that part |

## Quick measuring (outside Blender)
Export the reference once to numpy and cut as many times as you like with `tools/general/slice_plot.py` (PNG with a cm grid):
```python
import bpy, numpy as np                        # inside Blender, once
H = bpy.data.objects["HiPoly"]; me = H.data
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
M = np.array(H.matrix_world); W = (co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]).astype(np.float32)
me.calc_loop_triangles(); tri = np.empty(len(me.loop_triangles) * 3, np.int32)
me.loop_triangles.foreach_get("vertices", tri)
np.savez(r"<repo>\projects\<name>\draft\hi_world.npz", V=W, T=tri.reshape(-1, 3))
```
`python tools/general/slice_plot.py draft/hi_world.npz draft/renders/sl_z.png z 0.60 0.70 --box -0.2 0.2 -0.1 0.1`
(z axis: plots x,y; `--low low.npz` draws the retopo on top). The cuts give centers and widths of the limbs and where the
knee, elbow and wrist are.

## Continuing the artist's mesh
The full cycle (copy of the current file, isolate the region, image, separate the part, OBJ, integration) is in
`docs/02-retopology/retopo-by-parts.md`. Specific to this package:
- `Topo(R, start="LowPoly_user")` starts from their untouched mesh; `T.old(53, 61)` picks vertices by the indices that
  `wire_overlay` + `label_png` show.
- Keep their counts at the seams; clean up only what prevents quads (nearly duplicate pairs, a vertex that would become
  valence 2: `cuca_fix.py`).

## Patterns that worked (Cuca)
- **Tube** (arm, leg, neck): `track` for the spine, `cring`/`chalf` at each station, `align` with the previous
  ring, `T.strip` between rings. Stations by shape: deltoid, arm, 3 at the elbow, forearm, wrist.
- **5-sided region** (back + top of the shoulder): `poly_patch` with a 5-pole; inner points projected from a
  point **inside** the body (`inside=`), so the patch does not cross the mesh.
- **Hand and foot**: box rings (palm, instep); fingers with `digit`: even root, one ring on each side of the claw base,
  vertex at the tip.
- **Tail with scales**: one segment per scale; half ring in each gap (where the dorsal height drops), none between gaps.

## Pitfalls
| symptom | cause | fix |
|---|---|---|
| vertex jumped to the neighboring arm or skirt | snap by nearest point | `snap(p, n)` with the expected normal, or `exit` from the center |
| ring catches an ear or horn in the way | the ray from the center hits another part | change the station or the center (`snap_section.py` has `despike`) |
| twisted strip between rings | rings starting at different angles | `align(P, Q)` |
| patch crosses the body | inner points projected along the normal | project from an inner point (`inside=`) |
| crooked claw | straight spine from root to tip | `digit` (spine re-centered at each cut) |
| code edit did not take effect | module cached in Blender | `importlib.reload(retopo)` |
| `.blend` opens in EDIT in the worker | it was saved in Edit Mode | `bpy.ops.object.mode_set(mode='OBJECT')` first |
