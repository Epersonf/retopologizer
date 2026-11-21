# Examples

Real scripts used to produce assets with this repository, cleaned up to serve as templates. They run inside Blender
(workers and `blender_once.py`, see `tools/README.md`) or in plain Python. Each expects you to run it from the repo root
(or set `RETOPOLOGIZER_ROOT`); the project data (`projects/<nome>/input|draft|output`) is yours and stays out of git.

| Example | Where it was applied | How to run | Doc |
|---|---|---|---|
| `chest-lid/build_lid_v5.py` | chest lid: half built from rings with vertices snapped to the reference, then mirrored | `exec` inside Blender after `tools/02-retopology/snap_retopo.py`; needs the `REF_LID` object | `docs/02-retopology/retopo-snap-mirror.md` |
| `cuca-rig/cuca_rig.py` | Mixamo-style rig of the Cuca (fingers, tail) and automatic skin on the LowPoly | `python tools/general/blender_rpc.py --port 9877 examples/cuca-rig/cuca_rig.py` | `docs/06-rig/rigging.md` |
| `cuca-rig/cuca_rig_export.py` | export the rigged Cuca (FBX + albedo JPG) to the game client | same, with `GAME_ASSETS=<game characters folder>` | `docs/05-delivery/delivery.md` |
| `autorig-bench/pose_test.py` | deformation test of the auto-rigged models: hard pose next to the rest pose | `blender -b --factory-startup --python tools/general/blender_once.py -- examples/autorig-bench/pose_test.py` | `docs/06-rig/rigging.md` |
| `hat-hair/hair_pick.py` | cap hair: picks the reference pieces that become hair locks (quad budget) and their Bezier points | `python -I examples/hat-hair/hair_pick.py QUADS=1100` (needs the `.npz` files from `hair_pieces.py`) | `docs/02-retopology/retopo-hair-tubes.md` |
| `hat-hair/hat_to_cuca.py` | the hat as a prop on the Cuca's `Head` bone, for the Godot client | `blender -b <hat_baked.blend> --python tools/general/blender_once.py -- examples/hat-hair/hat_to_cuca.py` | `docs/05-delivery/delivery.md` |
| `fibercards/blonde_sheet.py` | blonde fiber card sheet (12 cards sparse → dense) for the Cuca's hair | `python -I examples/fibercards/blonde_sheet.py [out] [seed]` | `docs/07-fibercards/fibercards.md` |
| `fibercards/head_cards.py` | cards fitted on the Cuca's head: strips with UV = sheet cell, layers dense to sparse, messy sway; needs the rig .blend and the sheet in `projects/cuca-hair` | `blender -b --factory-startup --python tools/general/blender_once.py -- examples/fibercards/head_cards.py` | `docs/07-fibercards/fibercards.md` |

| `wing/run_all.py` (+ `s1..s4`, `support.py`, `pattern_cabo.py`, `_cfg.py`) | the wing: artist's skin -> closed shell + handle (`prepare`), then bake -> engraved gold handle -> rig + flap -> FBX/GLB (`finish`) | `python examples/wing/run_all.py prepare --skin-blend X.blend` / `finish --uv-blend Y.blend` (`BLENDER_EXE`) | `docs/08-cases/wing.md` |

Variables: `RETOPOLOGIZER_ROOT` (repo root; default: current folder), `GAME_ASSETS` (folder where the game keeps characters), `BLENDER` (executable).
