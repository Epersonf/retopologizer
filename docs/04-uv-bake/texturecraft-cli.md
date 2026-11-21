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
