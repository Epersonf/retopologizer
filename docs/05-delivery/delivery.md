# Delivery: FBX, Godot and store (Fab)

## Prop (static)
- `wire_and_export(lows, mat_name, outdir, prefix, fbx_name, maps=(...))` (`wire_material.py`): wires the PNGs into a
  Principled material and exports **only the low-polys** (selection). The reference never goes to `output/`.
- `finalize(lows, ref, fbx, blend, budget=2000, report=True)` (`finalize_export.py`): collections, UV, material, checks the budget,
  saves the `.blend`, exports and writes `<fbx>_report.html` (`qa_report.py`: counts, poles, battery rows against the ref, views; `report=False` skips it, `report="x.html"` picks the file).
- PNGs and FBX in `projects/<nome>/output/`; working `.blend` in `draft/`; the lean one at the project root
  (`docs/05-delivery/git-reproduction.md`).
- Never `img.reload()` before exporting: what the artist painted in Blender lives in the packed image of the `.blend`, and
  the PNG on disk is still the old bake (this has already wiped out an edit).

## Character (rig)
`export_fbx(path, rig, mesh_name, textures=False)` (`rig_mixamo.py`): armature + mesh, no leaf bones, no animation.
How to build the rig: `docs/06-rig/rigging.md`.

## Godot (Braziletto game)
- Godot 4.7: `C:\Program Files (x86)\Steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`.
  `--headless --path <projeto> --import` imports; `--script <arquivo>` runs a script (with a window, saves screenshots).
- Characters go to `Braziletto/frontend/godot-client/assets/characters/` as `<Nome>.fbx` + `Albedo<Nome>.jpg`
  (rig `<Nome>_Rig`). Godot imports `mixamorig:` as `mixamorig_`. In the game: `tools/retarget_fbx.gd` (imports →
  retargets → imports) and `world/human_body.gd` (PATHS, BARE, BODY_BY_MODEL).
- The FBX points the material at the image next to it; a 1024 JPG albedo is enough for the game. Example:
  `examples/cuca-rig/cuca_rig_export.py`.

Characters with a normal map: also drop `Normal<Nome>.png` (1024) next to the albedo; `HumanBody` wires it when it exists.
A rig from Mixamo goes straight in (delete the FBX `.import` before retargeting a new rig): `docs/08-cases/curupira.md`.

## Prop attached to the head in the game (hat, cap, hair, pipe)
A static FBX hung on a `BoneAttachment3D` on the `Head` bone follows the head during animation. Examples: the Saci's cap, hair
and pipe; the Cuca's hat (`examples/hat-hair/hat_to_cuca.py`).
1. **Export** (Blender, one-shot on the `.blend` with the baked mesh): the script loads the character's rig
   (`bpy.data.libraries.load`), puts the prop on the head (scaled by head width) and moves the vertices into bone
   space (`head.inverted() @ placement`). Same options as the body (`FBX_SCALE_UNITS`,
   `bake_space_transform=True`). The output goes to `assets/characters/`: `<Modelo>.fbx`, `Albedo<Modelo>.jpg` (the FBX material
   points at it) and, if present, `Normal<Modelo>.png` (1024, saved by PIL: Godot 4.7 does not read Blender 5's JPEG).
   The placement is only a starting point: on the Cuca's hat the bone axes did not match and the user rotated ~80/−139/−136°
   in the editor. Open the editor and let the user adjust; do not try to get it right by the numbers.
2. **Register in the game**: `world/body_props.gd`, `SETS` table: `"<corpo>": {"models": [...], "placements":
   "res://data/<corpo>_props.json"}`. `HumanCharacter` already calls `BodyProps.attach(skeleton, human.body)`; the material
   is flattened like the body's and `Normal<Modelo>.png` is wired in if it exists.
3. **Import and test**: `godot --headless --path frontend/godot-client --import`; test in `test/<corpo>_body_test.gd`
   (prop on the `Head` bone, textures). If the body test counts meshes, discount those of the `BodyProps.NODE` node.
4. **Manual adjustment (the user)**: open the editor with a window, in the background:
   `godot --path frontend/godot-client res://tools/prop_editor.tscn -- --model=<id>` (101 Saci, 137 Cuca; ids in
   `BODY_BY_MODEL`). Click selects, W/E/R move/rotate/scale, right button orbits, wheel zooms, "Save" (bottom
   right corner) writes `data/<corpo>_props.json` (position, rotation in degrees and scale in bone space).
5. **Commit in Braziletto** after the user saves: FBX + `.import`, textures, the json, `body_props.gd`, tests.
   Never the `.codex/` folder (local configuration).

## Store listing (Fab)
Generate at the end, with the final material wired, in `projects/<nome>/listing/`.
- **Thumbnail**: `render_thumbnail(parts, "listing/thumbnail.jpg", samples=768)` (`render_thumbnail.py`):
  1920×1080 (Fab's minimum), jpg/png/webp ≤ 3 MB (comes out ~0.2 MB), Cycles with a studio setup (AgX, warm softbox, cool fill,
  2 rims, spot on a glossy floor, 85 mm, light DOF), ~1 min at 768 samples. Test with `samples=64`, adjust `cam` and
  `look_at` to the scale and **open the file** before uploading (framing, nothing cropped, final texture).
- **description.md**: title, what is included, technical table (tris, meshes, UV, size, pivot, format), QA checks,
  limitations (e.g. albedo only) and generative AI notice (check Fab's current rules). Example:
  `projects/stylized-chest/listing/description.md`.
- Albedo only: `wire_and_export(..., maps=("basecolor",))`.
- Several images of one long prop: `listing_shots(...)` (`listing_shots.py`); before/after sheet: `before_after.py`.
- Upload: `fab_package.py` (one zip per format) and `fab-upload.md` (the whole Publisher Portal flow).

## Rigged prop with maps (`tools/05-delivery/export_package.py`)
`wire_pbr` wires basecolor/roughness/metallic/normal into the materials (optional white `Tint` multiplier on chosen materials), `render_previews` renders Cycles views,
`export_package` writes FBX + GLB (animation baked, no leaf bones) and copies the maps next to them. FBX/glTF cannot carry the Tint: export with plain image materials and recolor with
`albedo_color` in Godot (it multiplies the albedo); keep the Tint version in the saved `.blend`. Example: `examples/wing/s4_rig_export.py`.

## Animated creature in the game (Braziletto `Creature`)
1. `export_clips(...)` -> `frontend/godot-client/creatures/<name>.glb` (1024 PNG textures; Godot 4.7 does not read Blender 5's JPEG).
2. `creatures/creatures.json`: `"<shape>": {"model": "<name>.glb", "pace": 1.2, "clips": {"idle": "Idle", "walk": "Walk", "attack": "Attack", "death": "Death"}}`
   (without `death` the box tips over; with it the clip plays through the alive/dead transition).
3. Scenes `world/entities/creature_<shape>.tscn` (copy of an existing creature) and `monster_<shape>.tscn`; register in `EntityScenes.MONSTERS`.
4. Species: `tools/data/species.json` (`shape`, `tint`; white tint keeps the painted colours) and the generated `data/species/<id>.tres` (edit by hand when
   `build_data.gd` would also regenerate items/skills). Import: `godot --headless --path frontend/godot-client --import`.
5. Test (`test/<shape>_test.gd`: shape supported, clips, bones, textured mesh) and **see it**: `godot --path frontend/godot-client res://tools/model_viewer.tscn -- --creature=<ids>`
   (keys 2 walk, 4 attack, 6 die; `--dead --shot=<dir> --yaws=40` takes a capture). Extend that viewer, do not write another.
6. `make godot-test` needs `godot` on PATH (copy the Steam exe to a `godot.exe` in a PATH dir for the run).
Store listing of an animated model: `listing_renders.pose_shots` (bite close-up, walk, death) and FBX with all actions (`fab-upload.md`).

After this, **do the post mortem**: `docs/05-delivery/post-mortem.md`.
