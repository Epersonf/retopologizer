# Rings, shrink and bridge: the body as convex parts (`retopo/limb.py`)

Technique: draw a circle of N points around a limb, shrink every point until it touches the reference, repeat at other stations,
bridge neighbouring rings, cap the ends. A ray from the centre of a convex section reaches every point of the contour, so one ring
per station is enough. The number of rings is chosen from where the rig deforms. Demo video: `projects/limb-demo/limb_rings.mp4`
(made by `tools/02-retopology/limb_demo_video.py`, see section 7).

## 1. The operation, step by step (what the code does)
1. **Centre** `c`: the point is moved inside its plane to the centroid of the cross-section (`contour.centred`, 2 iterations), so the
   ring is concentric with the limb whatever the joint position was.
2. **Inner radius** per angle: N rays from `c` outward; the point where each ray leaves the volume is the "inside" answer `f_k`
   (`curves.arc`, mode `exit`).
3. **Circle** of N points around the axis, radius `R = 1.6 x max |f_k - c|` (`margin`), first point toward `up` (default +Z).
4. **Shrink**: every circle point `s_k` casts a ray toward `c` (`Ref.ray`); the first surface hit is the final point. A hit is
   accepted only if `|hit - c| <= 1.25 x |f_k - c| + 2 mm`; otherwise the inside answer `f_k` is kept. This rejects a hit on a
   neighbour (torso beside the arm) and a miss.
5. **Rings along the limb**: for station `t` in 0..1 the centre is `a + (b - a) t`, re-centred; the axis is the direction from the
   previous centre (so a bent elbow bends the tube); each ring is `align`ed (rotated/reversed) to the previous one vertex by vertex.
6. **Bridge** each pair of rings (section 3), **cap** the ends (`cap=True`: quad fan to the centre, needs even N), `orient`, write.

`mode="out"` skips steps 3-4 and uses the inside rays only (identical on convex sections). Use `"in"` (default) near concavities:
the outer shrink does not leave through a gap.

## 2. API
| call | what |
|---|---|
| `wrap(ref, c, axis, n=12, up=(0,0,1), mode="in", margin=1.6)` | `(start, end)`: the circle and where each point lands |
| `limb_ring(ref, c, axis, n, name, mode)` | one wrapped ring as an object |
| `ring_stations(length, radius, joints=(), per_joint=3, straight=1)` | station fractions 0..1, denser at joints |
| `limb_tube(ref, a, b, stations, n, name, up, cap, mode)` | rings at the stations + bridges; `stations` is a count or a list; keeps `T.centers` |
| `bridge(T, A, B)` | faces between two rings (A, B lists of vertices) |

All return a `Topo` (or write one) and are exported by `retopo`. Run `topo_qa` afterwards.

## 3. Bridge
- **Same N**: `Topo.strip(A, B, closed=True)` quads, after `align`.
- **Different N** (e.g. 12 to 8, a joint to a straight part): B is rotated to start at the vertex nearest `A[0]`; both rings are walked by
  arc fraction: a quad when both advance together, a triangle when one side has to wait. 12 -> 8 gives 16 faces: 4 quads + 12 triangles.
  Prefer ratios of 2 (12 -> 6) to get a clean 2-to-1 transition; the triangles are the cost of an arbitrary ratio.

## 4. Where to put rings (density from the rig)
`ring_stations` implements the first rule; the others are the plan.
- **Joints** (implemented): `per_joint` rings around each joint fraction, spaced `radius / 2`; both ends; `straight` rings in a gap larger
  than `4 x spacing`. Female A-pose arm trimmed to 22%..100% of shoulder-wrist (radius 0.04, elbow at 0.34): stations
  `0, 0.26, 0.34, 0.42, 0.71, 1.0` = 6 rings.
- **Skin weights** (plan): where two bones share a vertex (about 50/50 in the heat weights) the surface bends; more rings there.
- **Range of motion** (plan): knee and elbow ~140 degrees, shoulder nearly free, wrist little; scale `per_joint` by it.
- **Surface curvature** (plan): curved at rest = more rings; a straight cylinder needs few.
- **N per ring** may change too: 12-16 at joints, 8 on straight parts, hence the different-N bridge.

The rig comes first: `autorig.detect` (or the Rig Studio markers) gives `a`, `b` and the joint fractions.

## 5. Example (Blender worker, female A-pose, left arm)
```python
import sys; sys.path[:0] = [r"<repo>/tools", r"<repo>/tools/06-rig"]
from retopo import Ref, limb_tube, ring_stations, topo_qa
from autorig.load import mesh_of
from autorig.detect import detect
from mathutils import Vector
ob = bpy.data.objects["Body"]; J, B, _ = detect(mesh_of([ob])); ref = Ref("Body")
a, e, h = [Vector(J[k]) for k in ("LeftArm", "LeftForeArm", "LeftHand")]
a = a + (h - a) * 0.22                      # past the shoulder, where the torso would catch the rings
L = (h - a).length
T = limb_tube(ref, a, h, ring_stations(L, 0.04, joints=[(e - a).length / L]), n=12, name="Arm")
```
Result: 6 rings x 12 = 72 vertices, 60 quads, every vertex within 0.1 mm of the surface (`Ref.nearest`), ring radii following the
taper (3.6 -> 3.3 cm on the forearm). Same N on all rings; a 12 -> 8 pair gives the 4 quads + 12 triangles above.

## 6. Limits (plan around them)
- **Concave sections** (arm against torso in A-pose, ears): mode `"in"` plus the 1.25 acceptance test copes with an arm beside the torso,
  but start the tube past the shoulder (22% of the way) or the first ring catches the torso. Deep C-shapes need splitting the part.
- **Branches** (shoulder, groin, hand with fingers): one ring cannot cover them. Use patches (`poly_patch`, `solve_spokes`) or separate
  tubes (`lock`, `digit`).
- **Face**: not a tube. Eyes and mouth are concentric loops around a hole (eyelid and lip flow), the ears are concave, the cheek, nose and
  forehead quads need poles on purpose. Use the tube for skull and neck only, place eye, mouth and nose loops from a centre point on the
  local surface plane, make ears and eyelids their own parts, and fill between loops with `solve_spokes` / `poly_patch`. Do the face last,
  with the artist deciding N and seams.
- Not built yet: automatic segmentation of the whole body, the interactive mode in the Rig Studio page (click a limb, ring appears),
  a clean 2-to-1 transition without triangles, density from skin weights and range of motion.

## 7. The demo video
```
python tools/general/blender_rpc.py --port 9877 tools/02-retopology/limb_demo_data.py   # writes projects/limb-demo/data.json
python tools/02-retopology/limb_demo_video.py [data.json] [out.mp4]                     # matplotlib + ffmpeg, 24 fps, 15 s
```
Timeline: ring appears (yellow) -> shrink (green, radial guides) -> second ring -> bridge (orange faces) -> the rest of the rings
(faster) -> result with the reference fading out. Camera azimuth sweeps from 65 to 15 degrees (`YAW0`, `YAW1` env) so the rings are
seen as ellipses first and the tube from the side at the end. The drawing is numpy/matplotlib from the json: no Blender at render time.
