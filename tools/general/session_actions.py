"""Difference between two mesh states -> semantic action (used by session_recorder.py, no bpy needed).
State: {"V": [[x,y,z],...], "E": [[a,b],...], "F": [[...],...], "sel": [ids]}
diff(prev, cur, to_world, to_screen) returns a list of actions:
  add_vertex   {id, local, world, screen, linked_to}   new vertex; linked_to = old vertices joined to it by a new edge (where the extrusion came from)
  add_face     {id, verts}                             new face (F)
  move_vertex  {id, from, to, world, screen}           moved vertex (G / snap)
  topology_change {nverts_before, nverts_after}        deletion/undo (indices shift, vertices cannot be matched one by one)
  select       {verts}                                 selection changed"""
EPS = 1e-5


def _far(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) > EPS * EPS


def diff(prev, cur, to_world, to_screen):
    acts = []
    pv, cv = prev["V"], cur["V"]
    if len(cv) < len(pv) or len(cur["F"]) < len(prev["F"]):
        acts.append({"type": "topology_change", "nverts_before": len(pv), "nverts_after": len(cv),
                     "nfaces_before": len(prev["F"]), "nfaces_after": len(cur["F"])})
    else:
        pe = {frozenset(e) for e in prev["E"]}
        new_e = [e for e in cur["E"] if frozenset(e) not in pe]
        for i in range(len(pv), len(cv)):
            link = sorted({a if b == i else b for a, b in new_e if i in (a, b) and (a < len(pv) or b < len(pv))
                           and (a if b == i else b) < len(pv)})
            w = to_world(cv[i])
            acts.append({"type": "add_vertex", "id": i, "local": cv[i], "world": w, "screen": to_screen(w), "linked_to": link})
        for i in range(len(pv)):
            if _far(pv[i], cv[i]):
                w = to_world(cv[i])
                acts.append({"type": "move_vertex", "id": i, "from": pv[i], "to": cv[i], "world": w, "screen": to_screen(w)})
        for i in range(len(prev["F"]), len(cur["F"])):
            acts.append({"type": "add_face", "id": i, "verts": cur["F"][i]})
    if sorted(prev["sel"]) != sorted(cur["sel"]):
        acts.append({"type": "select", "verts": cur["sel"]})
    return acts
