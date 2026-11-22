r"""Live alarm while the artist (or the agent) retopologizes: faces of one loose part that cut through each other are painted RED in the
3D view and the status bar says how many, refreshed about every second. Runs inside Blender (the artist's too: it only draws, never
edits or selects anything). Zero tolerance: nothing red may remain before the part is handed on (`docs/03-qa/qa.md`).
  exec(open(r"<repo>\\tools\\general\\live_intersect.py", encoding="utf-8").read()); start()      # default 1 s
  stop()
Looks at every mesh in Edit Mode, or at the active mesh in Object Mode. Meshes over `MAX_TRIS` triangles are skipped (heavy)."""
import bpy, bmesh, os, gpu
from gpu_extras.batch import batch_for_shader

MAX_TRIS = 20000
_ns = {"__name__": "face_intersect"}
exec(open(os.path.join(os.environ.get("RETOPOLOGIZER_ROOT", r"C:\Users\epers\Desktop\retopologizer"), "tools", "general", "face_intersect.py"), encoding="utf-8").read(), _ns)
_S = bpy.app.driver_namespace.setdefault("live_intersect", {"tris": [], "n": 0, "h": None, "on": False})


def _scan():
    tris, n = [], 0
    objs = [o for o in bpy.context.selected_objects + [bpy.context.object] if o and o.type == "MESH"]
    for o in {o.name: o for o in objs}.values():
        if o.name in ("HiPoly",) or len(o.data.polygons) * 2 > MAX_TRIS: continue
        if o.mode == "EDIT": bm = bmesh.from_edit_mesh(o.data); free = False
        else: bm = bmesh.new(); bm.from_mesh(o.data); free = True
        M = o.matrix_world; V = [v.co.copy() for v in bm.verts]; F = [[v.index for v in f.verts] for f in bm.faces]
        pairs = _ns["face_intersections"](V, F); part = _ns["loose_parts"](F, len(V))
        bad = {f for a, b in pairs if part[a] == part[b] for f in (a, b)}
        n += len(bad)
        for fi in bad:
            vs = [M @ V[i] for i in F[fi]]
            for k in range(1, len(vs) - 1): tris += [tuple(vs[0]), tuple(vs[k]), tuple(vs[k + 1])]
        if free: bm.free()
    _S["tris"], _S["n"] = tris, n


def _draw():
    if not _S["tris"]: return
    try: sh = gpu.shader.from_builtin("UNIFORM_COLOR")
    except Exception: sh = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
    gpu.state.blend_set("ALPHA"); gpu.state.depth_test_set("NONE")
    sh.bind(); sh.uniform_float("color", (1.0, 0.0, 0.0, 0.85))
    batch_for_shader(sh, "TRIS", {"pos": _S["tris"]}).draw(sh)
    gpu.state.depth_test_set("LESS_EQUAL"); gpu.state.blend_set("NONE")


def _tick():
    if not _S["on"]: return None
    try: _scan()
    except Exception as e: _S["n"] = -1; print("live_intersect:", e)
    msg = "OK: nenhuma face em interseção" if _S["n"] == 0 else "ATENÇÃO: %d faces em interseção (vermelho)" % _S["n"]
    for w in bpy.context.window_manager.windows: w.workspace.status_text_set(msg)
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas: a.tag_redraw()
    return 1.0


def start(interval=1.0):
    stop(); _S["on"] = True
    _S["h"] = bpy.types.SpaceView3D.draw_handler_add(_draw, (), "WINDOW", "POST_VIEW")
    bpy.app.timers.register(_tick, first_interval=0.1)
    return {"started": True}


def stop():
    _S["on"] = False
    if _S["h"]:
        bpy.types.SpaceView3D.draw_handler_remove(_S["h"], "WINDOW"); _S["h"] = None
    for w in bpy.context.window_manager.windows: w.workspace.status_text_set(None)
    return {"stopped": True}
