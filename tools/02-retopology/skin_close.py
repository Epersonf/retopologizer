"""Close a one-sided retopo skin (a relief traced from the front) into a solid shell, and make it touch separate parts.
Inside Blender: exec(open(...).read()), then
  bm = skin_bmesh(obj)                                   # skin in world space (the object itself is not changed)
  moved = touch_parts(bm, part_objects, max_dist=0.055, inside=0.004, where=lambda v: v.co.x < 0.02)
  V, F, info = close_skin(bm, back_depth=lambda x, z: y_of_the_ref_back)   # extrude the border to the plane P and mirror
  new_obj = make_object("WING", V, F, material)
Convention: Y is the depth axis (front = -Y). The mirror is the SAME mesh inverted (same topology on both sides, good for UV and rig).
Why not Solidify: it offsets along vertex normals, so it crumples a skin with sharp feather steps; extrude + mirror keeps the silhouette."""
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def skin_bmesh(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world); bm.verts.ensure_lookup_table(); return bm


def _nearest(parts_bvh, p):
    best = None
    for t in parts_bvh:
        loc, nor, idx, dist = t.find_nearest(p)
        if loc is not None and (best is None or dist < best[0]):
            best = (dist, loc, nor)
    return best


def touch_parts(bm, parts, max_dist=0.055, inside=0.004, where=None, spread=2, falloff=0.5):
    """Move the border vertices closer than `max_dist` to a part until they sink `inside` metres into it; neighbours follow with a falloff.
    `where(v)` limits which vertices may move (keeps the far tip of the skin untouched). Returns the number of vertices moved."""
    trees = []
    for o in parts:
        b = bmesh.new(); b.from_mesh(o.data); b.transform(o.matrix_world); trees.append(BVHTree.FromBMesh(b)); b.free()
    border = [v for v in bm.verts if any(len(e.link_faces) == 1 for e in v.link_edges)]
    disp = {}
    for v in border:
        n = _nearest(trees, v.co)
        if n and n[0] < max_dist and (where is None or where(v)):
            disp[v.index] = (n[1] - n[2] * inside) - v.co
    for _ in range(spread):
        new = {}
        for v in bm.verts:
            if v.index in disp:
                continue
            ds = [disp[e.other_vert(v).index] for e in v.link_edges if e.other_vert(v).index in disp]
            if ds:
                new[v.index] = sum(ds, Vector()) / len(ds) * falloff
        disp.update(new)
    for i, d in disp.items():
        bm.verts[i].co += d
    return len([1 for v in border if v.index in disp])


def close_skin(bm, plane=None, back_depth=None, margin=0.003):
    """Extrude the border along +Y to the plane y=P and mirror everything across it. P = plane, else the mean of the midpoints between the skin
    and `back_depth(x, z)` (the reference's back surface), never below the deepest border vertex + margin. Returns (V, F, info)."""
    border_y = [v.co.y for v in bm.verts if any(len(e.link_faces) == 1 for e in v.link_edges)]
    if plane is None:
        plane = float(np.mean([(back_depth(v.co.x, v.co.z) + v.co.y) / 2 for v in bm.verts])) if back_depth else max(border_y) + 0.01
    P = max(plane, max(border_y) + margin)
    ext = bmesh.ops.extrude_edge_only(bm, edges=[e for e in bm.edges if len(e.link_faces) == 1])
    for g in ext["geom"]:
        if isinstance(g, bmesh.types.BMVert):
            g.co.y = P
    bm.verts.ensure_lookup_table(); bm.verts.index_update(); bm.faces.ensure_lookup_table()
    V = [tuple(v.co) for v in bm.verts]; F = [[v.index for v in f.verts] for f in bm.faces]
    ring = {i for i, v in enumerate(V) if abs(v[1] - P) < 1e-7}; n = len(V); idx = {}; V2 = []
    for i, v in enumerate(V):
        if i in ring:
            idx[i] = i
        else:
            idx[i] = n + len(V2); V2.append((v[0], 2 * P - v[1], v[2]))
    F2 = [[idx[i] for i in f[::-1]] for f in F]
    return V + V2, F + F2, {"plane": round(P, 5), "border_verts": len(ring), "thickness_max_mm": round(2 * (P - min(v[1] for v in V)) * 1000, 1)}


def make_object(name, V, F, material=None, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update(); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    b = bmesh.new(); b.from_mesh(me); bmesh.ops.recalc_face_normals(b, faces=b.faces); b.to_mesh(me); b.free()
    for p in me.polygons:
        p.use_smooth = smooth
    if material:
        me.materials.append(material)
    return ob


def pull_parts_to_shell(parts, shell, max_dist=0.025, inside=0.004):
    """The other direction of touch_parts: move the vertices of the parts that are closer than `max_dist` to the closed shell onto its surface
    (sunk `inside` metres), so bars and plates close the thin slits left next to the skin. Returns the moved vertex count per part."""
    b = bmesh.new(); b.from_mesh(shell.data); b.transform(shell.matrix_world); t = BVHTree.FromBMesh(b); b.free(); out = {}
    for o in parts:
        n = 0
        for v in o.data.vertices:
            loc, nor, idx, dist = t.find_nearest(o.matrix_world @ v.co)
            if loc is not None and dist < max_dist:
                v.co = o.matrix_world.inverted() @ (loc - nor * inside); n += 1
        o.data.update(); out[o.name] = n
    return out
