"""Blender side of the auto-rigger: world-space Mesh of one or more objects (modifiers applied) and loading the
benchmark cases (projects/autorig-bench/input/<case>.blend: one mesh "Body", <case>_gt.json: reference joints)."""
import json
import bpy
import numpy as np
from .sections import Mesh


def mesh_of(objects):
    dg = bpy.context.evaluated_depsgraph_get(); V, F, n = [], [], 0
    for o in objects:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); me.calc_loop_triangles()
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        W = np.array(o.matrix_world); co = co @ W[:3, :3].T + W[:3, 3]
        tri = np.empty(len(me.loop_triangles) * 3, int); me.loop_triangles.foreach_get("vertices", tri)
        V.append(co); F.append(tri.reshape(-1, 3) + n); n += len(co)
        oe.to_mesh_clear()
    return Mesh(np.concatenate(V), np.concatenate(F))


def bench_case(folder, case):
    """Empty scene with the case's "Body" linked; returns (object, reference joints {name: np.array})."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load("%s\\%s.blend" % (folder, case)) as (src, dst):
        dst.objects = ["Body"]
    o = dst.objects[0]; bpy.context.scene.collection.objects.link(o)
    gt = {k: np.array(v) for k, v in json.load(open("%s\\%s_gt.json" % (folder, case))).items()}
    return o, gt
