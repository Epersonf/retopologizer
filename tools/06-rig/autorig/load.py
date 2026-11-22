"""Blender side of the auto-rigger: world-space Mesh of one or more objects (modifiers applied) and loading the
benchmark cases (projects/autorig-bench/input/<case>.blend: one mesh "Body", <case>_gt.json: reference joints)."""
import json, os
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


IMPORT = {".fbx": lambda p: bpy.ops.import_scene.fbx(filepath=p), ".obj": lambda p: bpy.ops.wm.obj_import(filepath=p),
          ".glb": lambda p: bpy.ops.import_scene.gltf(filepath=p), ".gltf": lambda p: bpy.ops.import_scene.gltf(filepath=p)}


def load_model(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".blend":
        bpy.ops.wm.open_mainfile(filepath=path)
    elif ext in IMPORT:
        bpy.ops.wm.read_factory_settings(use_empty=True); IMPORT[ext](path)
    else:
        raise SystemExit("autorig: unsupported input " + ext)
    for a in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        for c in a.children:                           # keep the meshes where they are without their old rig
            mw = c.matrix_world.copy(); c.parent = None; c.matrix_world = mw
        bpy.data.objects.remove(a)
    for act in list(bpy.data.actions):                 # its animations would be baked onto the new rig
        bpy.data.actions.remove(act)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes:                                     # a .blend of loose objects (in no scene): take them all
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
        for o in meshes:
            bpy.context.scene.collection.objects.link(o)
    return meshes
