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
