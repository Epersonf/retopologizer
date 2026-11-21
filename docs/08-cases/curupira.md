# Case: Curupira (character with backwards feet, rig, game)

Humanoid retopology (3550 verts, 3558 faces) painted in TextureCraft, rigged by Mixamo and delivered to Braziletto.
Lessons that cost time; each one is also in the guides.

## Rig: follow the feet, not the face
- The Curupira's feet point backwards. The **auto-rig** (`tools/06-rig/autorig`) looks the way the face looks and puts the
  foot bones forward, so in the game the character walked opposite to its feet.
- **Mixamo** places the skeleton by the markers and the feet: its rig looks toward the toes (the back of the mesh), and
  the game walks it feet-first with the face behind. That is the wanted result. For such characters rig in Mixamo:
  `tools/06-rig/export_for_mixamo.py` (mesh only, albedo embedded), download "With Skin" FBX, drop it in the game.
- Validate a Mixamo rig by importing it in Blender: 65 bones, left/right sides, `LeftFoot` -> `LeftToeBase` pointing the
  same way as the mesh feet, then render front and side (`tools/06-rig/pose_check.py` for a forced pose).
- Never scale or apply scale on the **armature object** to resize the character: the skin exploded into spikes in Godot.
  Resize the mesh before rigging, or use the game's per-model `scale`.
- Flipping only the foot and toe bones 180 deg in the auto-rig did not fix it; the whole rig must face the feet.

## Hand swap and junction (low-poly)
- Replace the hand with an OBJ: align by chamfer distance (4 rolls x mirror), scale by wrist ring radius, build the quads
  by hand. A thin bridge band leaves a notch: reshape about 6 cm of wrist with extra loops instead.
- Mirror the corrected arm: flip coordinates, `reverse_faces`, `remove_doubles` at the seam, check 0 open edges.
- Make the UV by hand (no overlap), transfer the old painting 3D->3D with a Cycles EMIT bake from the old low (old UV) to
  the new low (new UV), and rebake the normal from the high.

## Shading: clear the custom normals
- A `custom_normal` attribute (CORNER INT16_2D) left by the retopo leaks into glTF and TextureCraft previews and into the
  tangent basis of the normal bake: the hands looked jagged and no painting fixed it. In Blender run
  `bpy.ops.mesh.customdata_custom_splitnormals_clear()`, then re-bake. A `sharp_face` attribute (all smooth) appears: fine.

## TextureCraft (painting)
- `textureSet.meshMap.import` of the normal gave jagged shading in the preview: do not import it; paint color.
- Flatten a region of the normal: `tool.material channel=normal enabled=True color=#8080ff`.
- Fill faces by box: `tool.select polygonFill` + `tool.fillMode polygon` + `tool.fillSelection {hitTest: containedCenter,
  visibleOnly: False}` + `tool.click {x0,y0,x1,y1,viewport}`. `uvIsland` fills the whole island (hand and arm share one).
- Brush size is screen-based; `backfaceCulling` False paints back faces; `mirror_w=1280` mirrors strokes.
- Game maps: albedo + normal only (metal without reflection renders black in Godot), 1024 px.

## Game delivery (Braziletto)
`assets/characters/<Nome>.fbx` + `Albedo<Nome>.jpg` + `Normal<Nome>.png`; register the body in `world/human_body.gd`
(`PATHS`, `BARE`, `BODY_BY_MODEL`) and `tools/retarget_fbx.gd`. Delete the FBX `.import` before re-retargeting a new rig
(the script skips files that already have a bone map). See `docs/05-delivery/delivery.md`.
