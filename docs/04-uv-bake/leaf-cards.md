# Leaves, feathers, cloth strips as cutout planes (render once, reuse)

Case: the Curupira skirt. 20 leaves + 2 drapes + belt became 228 quads (456 tris) with one 1024 atlas
(color + alpha, and a normal map). Tools: `tools/02-retopology/plane_cards.py` (measure) and `tools/04-uv-bake/ortho_atlas.py` (render).
Not hair cards (those are `07-fibercards`): here each plane is fitted to one existing piece of the ref.

## Idea (the user's)
When a ref has many copies of one modelled piece, **render the piece once** (color + depth), make a normal map from the
depth, and make each copy **one plane** that wears that tile. The planes share one UV block on purpose: the QA overlap
of the shared block is expected, so run `qa_uv` on a copy without the duplicates (it reported 0 overlap and gap >= 8 px).

## Process
1. **Lean file**: copy the blend, keep only the pieces; a mirror modifier that points at a deleted object breaks the
   mirror (the leaves came out on one side only): replace the target by an empty at the same place.
2. **Atlas tiles** (`ortho_atlas.raster` on the template piece and on each cloth that is unique): orthographic rays from
   the +n side give mask (alpha = silhouette), height and UV.y of the hit. Color: if the source color was a ColorRamp over
   UV.y, copy its stops and evaluate over the hit UV.y (`ramp`); flat cloth gets one flat color. Keep MARGIN 6 px and bleed
   the color outwards (`fill_out`) or the alpha edge shows a dark halo.
3. **Normal from depth** (`to_normal`): remove the large shape with a mask-weighted blur (it comes from the plane
   geometry) and use the remaining relief only; **outside the eroded core the normal is flat**. Without both, the cut border
   shows colored bands (the void leaks into the high-pass). OpenGL Y+ (Godot).
4. **Fit each piece** (`plane_cards`): `components` (a mirror makes the other side a separate piece), `leaf_frame`
   (PCA: u width, v length, n outward; the base is the higher end, or the one closer to the body axis), `cell_offset`
   (offset along n per grid node: a 1 x 3 quad plane gets the curve of the leaf). Big cloth: 3 x 4 planes following the
   surface. A belt: a 24 x 6 ring built by hull rings; fix each face's winding outward.
5. **Game**: `Albedo<Nome>.png` (alpha) and `Normal<Nome>.png` make Braziletto's `BodyProps` use alpha scissor 0.5 and
   no culling (planes are seen from both sides). `export_game_prop.py` writes the FBX in skeleton space; the placement
   is the inverse of the bone rest (`docs/body-props.md` in the game).

## Check by eye
- The base/tip guess decides which end of the gradient is up: render it. The Curupira original ramp was inferred from the
  vein chevrons; if it is backwards, invert the ramp in the atlas, not the geometry.
- Look from 3 sides: plane thickness is zero, so from the side a leaf must still read through its curve.
