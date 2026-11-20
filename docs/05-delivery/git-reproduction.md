# What goes into git and how to reproduce it

- **Included**: `tools/`, `docs/` and `examples/` (example scripts from real assets).
- **Left out** (`.gitignore`): all of `projects/` (your models, `.blend` files, working scripts, input GLBs, outputs), `*.blend1`,
  `__pycache__/`. Keep your projects in a private repo or in the cloud.
- The input GLB is the only thing that cannot be recreated: keep a copy outside the repo (cloud or drive) and note its origin
  in the project's `README.md`.
- The models come from generations (Hunyuan3D), not from procedure: the low-poly mesh lives in the `.blend`; the project
  scripts show how it was built from the reference.

## Commands
- Lean `.blend` (inside Blender): `make_lean_blend(["chest_base", "chest_lid"], "chest_mat", path)`.
- Regenerate `output/` (identical PNGs + FBX) on any machine:
  `blender -b projects/<nome>/<nome>.blend -P tools/05-delivery/export_from_blend.py -- projects/<nome>/output <prefixo>`.
- Redo the bake from scratch: import the GLB, name it `REFERENCE`, open the lean `.blend`, `bake_robust` (`docs/04-uv-bake/uv-bake.md`).

## Commits
- Only when the user asks.
- Never `Co-Authored-By`, "Generated with" or any AI attribution.
- Before committing a `.blend`, confirm it is the lean one (without the reference).
