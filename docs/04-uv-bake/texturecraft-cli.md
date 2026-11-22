# TextureCraft through the CLI

Use when TextureCraft must read a mesh or write maps and the MCP server cannot ("file access is not granted": the headless MCP has no
`--read-root/--write-root`, and the bridge needs the app started with `--control <port>`). The CLI has no such limit. Wrapper:
`tools/04-uv-bake/texturecraft_cli.py` (pure Python). CLI: `C:\Program Files\TextureCraft\texturecraft-cli.exe` (not on PATH).
When TextureCraft is required (new model without high-poly, or the user asks: "tem que usar o texture craft"), **do not paint with PIL instead**.

## Commands that matter
| CLI | what for |
|---|---|
| `info <proj\|mesh>` | texture sets, layers, triangles, UV report as JSON |
| `commands [--filter x]` | engine command ids and params (`layer.add.image`, `layer.add.paint`, `tool.*`, `effect.add.*`, `camera.*`, `bake.run`) |
| `batch script.json` | `{"open": mesh_or_proj, "steps": [{"id", "params"}], "save": out.tcraft}` |
| `export <proj> <dir> --preset "glTF PBR Metal Roughness" --padding dilation` | `mesh_<MATERIAL>_{BaseColor,Normal,OcclusionRoughnessMetallic}.png` |
| `render <proj> out.png --size WxH [--camera name] [--view 3d\|2d]` | LOOK at the result before trusting it |

## Recipe used for the sword
1. `import_maps(glb, maps_dir, "t0.tcraft", prefix)`: the baked maps as UV image layers (+ normal/AO as mesh maps). Optional
   `bake.run {maps:["curvature"], curvatureMethod:"normalMap"}` gives edge-wear generators something to follow.
2. Procedural pass: `effect.add.generator` (edge wear accepts `mode`/sizes, dirt does not accept `mode`), `effect.add.filter` sharpen,
   `layer.blend {layer, channel:"all", opacity}` to keep it subtle. Render, compare.
3. Hand retouch of blurry spots: `add_camera(...)` looking at the area, then `paint(...)` with `Stroke`s in viewport pixels
   (`mirror_w` paints the mirrored stroke too for a symmetric prop). Render, correct, repeat.
4. `export(...)`, put the PNGs in `output/vN/`, re-run the delivery (`d1.py`-style) and render the previews.

## Rules (each one cost a failed run)
- Write the JSON from Python (UTF-8, no BOM, forward slashes). PowerShell's BOM breaks `batch`.
- `tool.stroke` paints through the **session camera**: `camera.select` first, or nothing is painted. `tool.strokeUv` is offset or partial on a
  mirrored/overlapping UV: use 3D strokes.
- In `tool.material` set `height` and `normal` `enabled: false`, or each stroke flattens the normal map.
- Metal stays out of the maps for the Braziletto game (metal with no reflections renders black in Godot).
- Mention in the report which maps came from TextureCraft and which were not painted.

## Retouching a defect: look at the normal map FIRST (alligator, leg-hole patch)
- A texture defect that survives a base-color fix (radial fan, swirl of rainbow colors, dark disc, "dish" look) is almost always the
  **normal map** (and the baked AO mesh map), not the albedo and not the mesh. Where the bake hit a hole or the interior of the
  reference, the normal shows a rainbow fan. Crop `*_normal.png` and `*_ao.png` at the UV spot before touching the albedo.
- The TextureCraft viewport and export use the **mesh-map normal** as the base surface: masking the normal image layer does nothing.
  Fix the source maps (flat `128,128,255` normal, white AO in the patch) and `textureSet.meshMap.set` them, or clone good belly detail over it.
- A flat color fill over a stripe/scale pattern still reads as a patch. Clone neighbouring detail (`tool.clone`) instead.
- Check the base color, normal, AO and roughness crops of the same UV box side by side before choosing the fix.

## Clone tool through the CLI (what worked for the alligator belly patch)
- `tool.select clone`, `tool.cloneSource {x,y,viewport}` then `tool.stroke`: the source follows the stroke with a **fixed screen offset**
  (source point = first stroke point). Re-set `cloneSource` before each stroke.
- **Brush size is in "percent": ~16 px per unit in a 1280x800 view.** Size 20 painted a 330 px blob and wrecked the area; use 1.5-2.5 for a 25-40 px brush.
- Shift a clean neighbour column sideways in rows (every ~18 px), then clone the painted result again for the next column.
  Keep `normal` enabled in `tool.material` so the clone brings the belly seams too. UV-space clone (`tool.strokeUv`) did nothing: stay in 3D.
- Seam drips from the source column: clone over them with a second pass from the clean interior.
