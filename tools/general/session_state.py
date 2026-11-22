"""Reads Blender state for session_recorder.py (3D view, snap, mesh). Functions only, no global state."""
import bpy, bmesh, json


def js(v):
    try:
        json.dumps(v); return v
    except Exception:
        pass
    try:
        return [js(x) for x in v]
    except Exception:
        return str(v)


def area3d():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == 'VIEW_3D':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


def view():
    w, a, r = area3d()
    if not a:
        return None
    rv = a.spaces[0].region_3d
    return {"persp": rv.view_perspective, "matrix": [list(x) for x in rv.view_matrix], "dist": rv.view_distance, "w": r.width, "h": r.height}


def snap():
    ts = bpy.context.scene.tool_settings
    keys = ("use_snap", "snap_elements", "snap_elements_base", "snap_elements_individual", "snap_target", "use_snap_project",
            "use_snap_backface_culling", "use_snap_self", "use_mesh_automerge", "use_proportional_edit", "transform_pivot_point")
    return {k: js(getattr(ts, k)) for k in keys if hasattr(ts, k)}


def mesh_state(ob):
    """(vertices, edges, faces, selected, active vertex) in local coordinates; reads the bmesh in Edit Mode."""
    if ob.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(ob.data); bm.verts.ensure_lookup_table()
        act = bm.select_history.active
        return ([[round(c, 5) for c in v.co] for v in bm.verts], [[v.index for v in e.verts] for e in bm.edges],
                [[v.index for v in f.verts] for f in bm.faces], [v.index for v in bm.verts if v.select], act.index if hasattr(act, "index") else None)
    me = ob.data
    return ([[round(c, 5) for c in v.co] for v in me.vertices], [list(e.vertices) for e in me.edges], [list(p.vertices) for p in me.polygons],
            [v.index for v in me.vertices if v.select], None)
