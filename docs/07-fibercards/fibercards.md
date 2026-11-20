# Fiber cards (hair as planes with a strand texture)

An alternative to mesh hair: simple planes with a strand texture (color + normal + alpha). The back face may show; in the game the material enables
*backface / render both sides*. Manual retopology does not apply: the hair becomes planes fitted to the head (project `projects/cuca-hair`).

## Generate the card sheet (`tools/07-fibercards/`)
The generator is a port of the `epersonf/fiber-card-gen` app (commit `eccffc9`); the render is done by Blender (Cycles, orthographic, transparent background).

    python -I tools/07-fibercards/fibercards.py --out DIR --tag blonde --blonde [--seed 1] [--samples 32] [--lighting soft|flat] [--blend f.blend] [--set chave=valor ...]

- `fc_params.py`: app state (same keys as the "copy state" JSON, so a preset pastes into the app and back) and the `BLONDE` preset.
- `fc_strands.py`: strands (mulberry32, tilted elliptical spawn disc, spread/clump, curl, frizz, centripetal Catmull-Rom). The frizz noise is value noise; the app uses open-simplex.
- `fc_blender.py`: each strand becomes an 8-sided tube (radius and color per ring: root→tip gradient), one mesh per card; orthographic camera looking down −z.
- `fibercards.py`: builds the sheet (grid of `cardsPerSheet` cards, from sparsest to densest along the quantity curve) and calls Blender. Output: `<tag>_color.png`,
  `<tag>_normal.png` (RGBA, `baseSize` px), `<tag>_preview.png`, `<tag>_preset.json`. 12 cards at 2048 px: about 8 s on the GPU.
- `soft` color: sun at (0,10,5) + gray world, Principled with the preset's glossiness/sheen; `flat`: pure albedo. Normal: view normal × 0.5 + 0.5, raw space (no sRGB).
- Card layout as in the app: x across the width (0 at the middle of the cell), y up from the bottom edge, root at the top, strands hanging down.
- The 5 % per-strand brightness variation is an extension of this port.

## Before generating hair: ask the user
Do not start with a default hairstyle. Ask first (or say you will decide, if the user prefers): neat or messy/unkempt, length (bangs, sides, back), straight / wavy / curly,
parting, how dense, which colour. "Messy" changes the sheet and the fitting (below), so it has to be known before the first render.

## Fitting cards to a head: avoid these
- **All strands end at the same point.** The default (`fixed_length_size=true`) gives every strand the same length, so each card ends in a straight line.
  For natural or messy hair generate the sheet with different lengths: `--set fixed_length_size=false minimum_length=3 maximum_length=20` (strands end at 23 %..100 % of the card).
  Also raise `frizz_scale`, `clump_tip`, `curl_amount` for messy hair. Check the preview before fitting.
- **Cards hug the scalp and every card bends the same way.** A rigid lift of a few mm looks like a helmet. Lift the cards off the head toward the tips, vary the lift,
  length (±35 %), width, root height and azimuth per card, and let each path sway sideways (a drift plus a couple of sines). Add outer layers of sparse wisps.
- **Visible polygon folds.** Few segments along the length show the bends as hard creases. Use 14+ segments per card, smooth shading, a cupped cross-section (a middle
  vertex lifted a little, 2 quads across) and a twist along the length so the planes do not read as flat sheets. Keep the lift of the wisps small: a large lift makes them float.
- **Dark roots read as black patches.** The gradient root colour is dark; where cards lie flat on the scalp they look like holes. Start the gradient lighter
  (`hair_gradient_stops`) and keep the normal map strength low (0.25) on the card material.
- **Jagged, saw-tooth cards.** Two causes: a low-poly skull whose hits and push-outs make the path jitter (smooth the centreline with a few [1 2 1] passes, root and tip fixed),
  and a card width taken from a fixed azimuth, which collapses when the path runs sideways. Take the width across the travel: `tangent x (point - head centre)`, sign kept continuous along the card.
- **Floating sheets on the crown.** A flat card is wider than the skull is flat: a 12 cm card on a 10 cm dome leaves the surface by ~2 cm at its edges. Wrap the edge vertices
  onto the skin too (ray from the head centre through the edge point, offset by the lift), keep the cup shallow and cap the lift off the skin (1.6 cm). Make it a gate in the script:
  after building, no vertex of the scalp region may be farther than 4 cm from the body (`find_nearest`), otherwise stop with the card name. Always look at the top view and the profile.
- **Too full / eyes covered.** Cap the length over the forehead (about 8 cm for a 20 cm head), 50 cards and ~3300 triangles were enough for shoulder length; ask the user how full.
- Use only the part of the cell the strands occupy (the strands spread wider with frizz): crop the UV to it, root at the top of the cell.
- The cards get no collision with the body except a push-out of their points: check shoulders and neck from the back.
Worked example: `examples/fibercards/head_cards.py` (cards on the Cuca's head) and `projects/cuca-hair` (the project, local).

## Recipe used for the Cuca (long, straight, blonde; `projects/cuca-hair`)
    python -I tools/07-fibercards/fibercards.py --out OUT --tag hair_long --blonde --seed 9 --set fixed_length_size=false minimum_length=11 maximum_length=20 \
      frizz_scale=0.9 clump_tip=1000 curl_amount=5 root_thickness=0.034 tip_thickness=0.016 hair_amount_max=170 hair_amount_min_percent=0.25 \
      'hair_gradient_stops=[{"pos":0,"color":"#c8963a"},{"pos":0.4,"color":"#e9c15c"},{"pos":1,"color":"#fadf88"}]'
Blonde must be golden (`#c8963a` -> `#fadf88`); pale stops such as `#cdb98a` render grey under the soft lighting and read as white/grey hair.
