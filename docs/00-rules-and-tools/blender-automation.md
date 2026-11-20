# Running code in Blender

Blender 5.3: `C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe` (below, `B`).

## Three ways
| way | when | how |
|---|---|---|
| User's MCP (port 9876) | read the scene the user has open | `python tools/general/blender_rpc.py script.py` or `-c "code"` |
| headless worker (port 9877) | build, render and bake in a working `.blend` | `"$B" -b <copy.blend> --python tools/general/blender_worker.py -- 9877` in the background, then `python tools/general/blender_rpc.py --port 9877 script.py` |
| one-shot | script that opens its own files, or no worker running | `"$B" -b --factory-startup --python tools/general/blender_once.py -- script.py`; the result comes out on the `RESULT_JSON: {...}` line |

The CLIs run directly: `"$B" -b --factory-startup --python tools/06-rig/autorig/cli.py -- model.fbx output.fbx`.

- The user's Blender is **read-only**: they work at the same time (sometimes in another instance). Building and
  rendering go to a **copy** of their `.blend`, in the worker.
- The worker keeps state between calls (e.g. the cached BVH of `retopo.Ref`); `{"type": "quit"}` shuts it down. It dies
  at the background shell's time limit (2 h); after that use one-shot or start another.
- `blender_rpc` waits up to 2 h for the response (long bakes and renders fit).

## Script contract
- The script defines `result` (a JSON-serializable dict); stdout comes back with it.
- Standalone tools: `exec(open(r"<repo>\tools\03-qa\qa_all.py", encoding="utf-8").read())`.
  They share the namespace: do not reuse global names between tools and scripts (e.g. `T`).
- Packages (`retopo`, `autorig`): `sys.path.insert(0, r"...\tools")`, `import` and `importlib.reload` after editing.
- Each socket call gets a fresh namespace: `import bpy` in every one, without relying on variables from the previous one.

## Pitfalls
- **Never Edit Mode on the reference** (500k+ tris freezes Blender): read with `foreach_get` + numpy, BVH and raycast.
- **Never `raise SystemExit`** through the MCP: it closes the user's Blender and loses whatever was not saved.
- The MCP blocks `bpy.ops.wm.read_factory_settings`: clear the scene by removing objects.
- A file saved in Edit Mode opens in EDIT in the worker: `bpy.ops.object.mode_set(mode='OBJECT')` before touching anything.
- An imported GLB comes with a rotated `matrix_world` (+90° X) and `BVHTree.FromObject` is local: convert to world (`Ref` and
  `ref_part` already do).
- A reference hidden with `hide_set` makes the bake fail ("No valid selected objects").
- The worker may be attached to a different `.blend` than the open copy (it once overwrote `hat_uv.blend`, the user's UV
  file, in a `save_mainfile`). Before saving, print `bpy.data.filepath`; save only with `save_as_mainfile(filepath=<copy>)`.
- Always UTF-8 files (`open(..., encoding="utf-8")`): the Windows default is cp1252.

## Showing to the user
Render in the worker (`render_views`, `wire_overlay`, `render_thumbnail`), save to `draft/renders/`, open the image
to check it, and only then show it. An early image is worth more than a long report.
