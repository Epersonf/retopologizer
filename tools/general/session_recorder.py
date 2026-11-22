"""Session recorder: logs what the artist does in Blender so the agent can analyze it, continue the process and, later, train a model.
Usage: blender file.blend --python tools/general/session_recorder.py   (REC_DIR = output folder; REC_OBJ = fixed object name, else follows the active one)
Writes to REC_DIR (full format: docs/00-rules-and-tools/session-recorder.md):
  meta.json            version, .blend (md5), reference, snap, view, conventions
  events.jsonl         operators, keys/clicks (with position), mode, active object, NOTES, saves, new vertices/faces
  actions.jsonl        semantic actions per mesh change (add_vertex + linked_to + screen, add_face, move_vertex...) with their triggers (keys/operators)
  snap_NNNN.json       keyframe: full mesh + selection + view (every 25 changes; REC_FULL=1 writes all);  shot_NNNN.png  viewport (one every 10 s)
  checkpoint_NNN.json  mesh of every object (except REFERENCE) at each Ctrl+S"""
import bpy, json, os, sys, time, hashlib
from mathutils import Vector
from bpy_extras import view3d_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from session_actions import diff
from session_state import js, area3d, view, snap, mesh_state
from session_meta import write_meta, write_checkpoint, is_reference

VERSION = 3
OUT = os.environ.get("REC_DIR") or os.path.join(os.path.expanduser("~"), "blender_rec", time.strftime("%Y%m%d_%H%M%S"))
FIXED = os.environ.get("REC_OBJ")
KEY = 1 if os.environ.get("REC_FULL") else 25   # full mesh every KEY changes (the actions are enough to rebuild the rest)
os.makedirs(OUT, exist_ok=True); T0 = time.time()
S = {"op": None, "n": 0, "shot_t": 0, "snap_t": 0, "mode": None, "active": None, "notes": None, "view": False, "modal": False,
     "keys": {}, "state": {}, "trig": [], "ck": 0, "since": 999}
SKIP = {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE', 'TIMER', 'TIMER_REPORT', 'TIMER0', 'TIMER1', 'TIMER2', 'WINDOW_DEACTIVATE', 'NONE'}


def append(name, d):
    with open(os.path.join(OUT, name), "a", encoding="utf-8") as f:
        f.write(json.dumps(d, default=str) + "\n")


def log(kind, **d):
    d.update(t=round(time.time() - T0, 2), kind=kind)
    append("events.jsonl", d)


class REC_OT_input(bpy.types.Operator):
    bl_idname = "rec.input"; bl_label = "rec input"

    def modal(self, ctx, ev):
        if ev.type not in SKIP and ev.value in ('PRESS', 'CLICK', 'DOUBLE_CLICK'):
            S["trig"].append("key:" + ev.type + ("+shift" if ev.shift else "") + ("+ctrl" if ev.ctrl else ""))
            log("key", type=ev.type, value=ev.value, mx=ev.mouse_region_x, my=ev.mouse_region_y, shift=ev.shift, ctrl=ev.ctrl, alt=ev.alt,
                area=ctx.area.type if ctx.area else None)
        return {'PASS_THROUGH'}

    def invoke(self, ctx, ev):
        ctx.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def log_ops():
    lst = list(bpy.context.window_manager.operators)
    if not lst:
        return
    ptrs = [o.as_pointer() for o in lst]
    new = lst if S["op"] not in ptrs else lst[ptrs.index(S["op"]) + 1:]
    for o in new:
        p = {}
        for k in o.properties.keys():
            try:
                p[k] = js(getattr(o.properties, k))
            except Exception:
                pass
        S["trig"].append("op:" + o.bl_idname)
        log("op", id=o.bl_idname, props=p)
    S["op"] = ptrs[-1]


def shot(path):
    try:
        w, a, r = area3d()
        with bpy.context.temp_override(window=w, area=a, region=r):
            bpy.ops.screen.screenshot_area(filepath=path)
    except Exception as e:
        log("err", msg="shot " + repr(e))


def emit_actions(ob, cur, n):
    prev = S["state"].get(ob.name); S["state"][ob.name] = cur
    if prev is None:
        return
    mw = ob.matrix_world; w, a, r = area3d(); rv = a.spaces[0].region_3d if a else None
    to_world = lambda co: [round(c, 5) for c in (mw @ Vector(co))]

    def to_screen(wc):
        p = view3d_utils.location_3d_to_region_2d(r, rv, Vector(wc)) if rv else None
        return [round(p.x, 1), round(p.y, 1)] if p else None
    acts = diff(prev, cur, to_world, to_screen)
    if acts:
        append("actions.jsonl", {"t": round(time.time() - T0, 2), "n": n, "obj": ob.name, "mode": ob.mode, "triggers": S["trig"], "actions": acts})
        S["trig"] = []


def snapshot(ob):
    V, E, F, sel, act = mesh_state(ob)
    key = hashlib.md5(json.dumps([V, F, sel]).encode()).hexdigest(); prev = S["keys"].get(ob.name, {"key": None, "nv": 0, "nf": 0})
    if key == prev["key"] or time.time() - S["snap_t"] < 0.3:
        return
    S["snap_t"] = time.time(); S["n"] += 1; n = S["n"]
    S["keys"][ob.name] = {"key": key, "nv": len(V), "nf": len(F)}
    d = {"n": n, "obj": ob.name, "t": round(time.time() - T0, 2), "mode": ob.mode, "verts": V, "edges": E, "faces": F, "sel": sel, "active_vert": act,
         "mw": [list(r) for r in ob.matrix_world], "mods": [(m.type, m.name) for m in ob.modifiers], "snap": snap(), "view": view(),
         "objects": [o.name for o in bpy.data.objects], "selected": [o.name for o in bpy.context.selected_objects]}
    S["since"] += 1
    if S["since"] >= KEY or ob.mode != S["mode"]:
        S["since"] = 0; json.dump(d, open(os.path.join(OUT, "snap_%04d.json" % n), "w", encoding="utf-8"))
    if time.time() - S["shot_t"] > 10:
        S["shot_t"] = time.time(); shot(os.path.join(OUT, "shot_%04d.png" % n))
    emit_actions(ob, {"V": V, "E": E, "F": F, "sel": sel}, n)
    log("mesh", n=n, obj=ob.name, nverts=len(V), nfaces=len(F),
        new_verts=[[i, V[i]] for i in range(prev["nv"], len(V))], new_faces=[[i, F[i]] for i in range(prev["nf"], len(F))], sel=sel, mode=ob.mode)


def tick():
    try:
        w, a, r = area3d()
        if a and not S["view"]:
            S["view"] = True; log("start", snap=snap(), out=OUT, view=view()); write_meta(OUT, VERSION)
        if a and not S["modal"]:
            S["modal"] = True
            with bpy.context.temp_override(window=w, area=a, region=r):
                bpy.ops.rec.input('INVOKE_DEFAULT')
        log_ops()
        act = bpy.context.view_layer.objects.active; an = act.name if act else None
        if an != S["active"]:
            S["active"] = an; log("active", name=an)
        ob = bpy.data.objects.get(FIXED) if FIXED else act
        # A referência glTF pode ter milhões de polígonos; ela nunca é editada.
        # Registrar sua malha inteira por amostra deixa o Blender sem resposta.
        if ob and ob.type == 'MESH' and not is_reference(ob):
            if ob.mode != S["mode"]:
                S["mode"] = ob.mode; log("mode", mode=ob.mode)
            snapshot(ob)
        tx = bpy.data.texts.get("NOTES")
        if tx and tx.as_string() != S["notes"]:
            S["notes"] = tx.as_string(); log("note", text=S["notes"])
    except Exception as e:
        log("err", msg=repr(e))
    return 0.3


@bpy.app.handlers.persistent
def on_save(*_):
    S["ck"] += 1
    write_checkpoint(OUT, S["ck"], round(time.time() - T0, 2))
    log("save", file=bpy.data.filepath, checkpoint=S["ck"])


bpy.utils.register_class(REC_OT_input)
bpy.app.handlers.save_post.append(on_save)
bpy.app.timers.register(tick, first_interval=1.5, persistent=True)
