# Rear paw toes: the artist's recording, measured (guara-wolf, rec_02, 2026-11-22)

Source: `projects/guara-wolf/session/rec_02` (490 s, 738 action lines, 2605 events, 5 checkpoints), task = "the rear leg tube with its toes removed, rebuild the toes".
Every number below was measured from the recording or from the final mesh; a line marked **(inferred)** is the reason I read from the evidence, not something the artist said.
The artist's verdict on the result: "not perfect, but one I would approve", and "a merge by distance was probably missing".

## 1. The result, as measured
| item | value |
|---|---|
| geometry added | 141 vertices, 143 faces (the agent's fused-toe paw added 67 and 72) |
| faces | 249 quads + 2 tris as saved; after merge by distance 239 quads + 10 tris (tris = collapsed claw tips and 1 gap face) |
| duplicates in the saved mesh | 5 clusters (139/176/177/179, 202/210/216, 211/212/217): the left toe stack. `find_doubles` 0.6 mm: 261 -> 252 vertices, border edges 22 -> 14 (the 14 left are the leg's open top ring: the gap between left and middle toe closed by itself) |
| valence | 4: 216, 3: 25, 5: 5, 6: 6 (poles at the toe gaps and at each claw tip) |
| surface distance, new vertices | mean 1.9 mm, median 0.66 mm, p95 3.4 mm (the max is an artefact of the cropped ref) |
| edge length, toe region | median 9.3 mm, p5 0.9 mm (tips), p95 23.6 mm; the leg above: median 13.5 mm |
| defects as saved | 1 twisted quad (141, cos -0.55), 1 face looking into the ref (152), 0 crossings, 0 stamped |
| after merge + 5 vertices nudged <= 5.7 mm | 0 twisted, 0 inverted, 0 stamped, 0 crossings, 0% inward: `draft/artist_hind_clean.json` |

## 2. Timeline (what happened, in order)
| t (s) | phase | evidence |
|---|---|---|
| 0-19 | looks around, enters Edit Mode (Tab at 8 s), selects seam vertices | `select`, Numpad `.` (view selected) at 5, 13 |
| 19-216 | **hand-grown base**: one vertex at a time out of the seam, then `F` (edge_face_add) to close a quad | 48 `edge_face_add`, 43 `extrude_region_move` of single vertices, 70 `translate`; first vertices 120,121 hang off seam vertex 115 (the outer edge) and the region grows inward: 120-127 (outer toe base), 128-139 (inner side), 150-163 (the gap) |
| 135 | **loop cut #1 on the leg**: every ring of the leg gets one more vertex between columns 0 and 1 (13 columns) | v148 splits edge (108,109) of the seam ring; v140-147 the same edge of the 8 rings above |
| 178 | loop cut #2 in the new base (a row between base and tube) | v152, v153 split edges 139-150 |
| 210-251 | **left toe** tube: Face mode, front view (Numpad 1), flatten, extrude x2, curl | Face select at 210; `resize [1,0,1]` at 219; rotate 0.75 rad at 224; resize x0.63, x1.42, x0.29, x0.42 |
| 253-311 | fixes the stack: Numpad `.` 253, `rip` x2, circle select, delete x2 (286, 290), re-extrudes 3 vertices | the cause of the 5 duplicate clusters is here (rip + re-extrude without merging) |
| 328-346 | knuckle row of the middle toe, **loop cut #3** | v183, v184, v185 (341 s) |
| 353-377 | **middle toe** tube: 4 extrusions | `resize [1,0,1]` at 356; scales .82 .93 .88 .83 .94 .108; rotations .23 .24 .34 .62 rad |
| 387-406 | **loop cut #4 on the leg** (13 -> 14 columns): v228 splits seam edge (108,119); closes the right-toe base | v219-227 the same edge on the 9 rings above (401 s) |
| 433-490 | **right toe** tube: 4-5 extrusions | `resize [1,0,1]` at 442; scales .83 .95 .66 .46 .30 (.81); rotations .30 .33 .17 .56 rad |
| 475 | **loop cut #5**: a row between the right tube base and the knuckle | v253-260 (474 s) |
| 506 | Shade Smooth + Auto Smooth (for looking, not part of the topology) | `OBJECT_OT_shade_smooth` |
Checkpoints (Ctrl+S) at 234, 380, 468, 484, 510 s: each right after a toe was finished (Tab out). Undo (Z) x31, clusters at 44, 207, 248-256 (9 in a row: the stack), 326-350.

Where the effort went: 490 s total, hand base 197 s (40%), three tubes 290 s (60%). 1869 `move_vertex`: vertices moved on average 13.4 times each (median 14, p90 21, max 44); only 3 of 141 never moved after creation.
