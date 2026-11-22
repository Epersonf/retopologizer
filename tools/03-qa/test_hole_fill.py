r"""Test of tools/02-retopology/hole_fill.py (blender -b --python test_hole_fill.py): a hole in a sphere is filled with quads only and the sphere stays
closed; a ring removed from a cylinder is rebuilt by loop_bridge; an odd hole is fixed with a loop cut. Prints 'ok' lines and raises on failure."""
import bmesh, math, os
from mathutils import Vector
for _f in ("hole_fill.py", "loop_bridge.py"): exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "02-retopology", _f), encoding="utf-8").read())


def closed(bm): return all(len(e.link_faces) == 2 for e in bm.edges)


def sphere():
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0); return bm


bm = sphere(); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if (f.calc_center_median() - Vector((1, 0, 0))).length < 0.55 and len(f.verts) == 4], context="FACES_ONLY")
for v in [v for v in bm.verts if not v.link_faces]: bm.verts.remove(v)
L = boundary_loops(bm); assert len(L) == 1, len(L)
info = fill_loop(bm, L[0]); bm.faces.ensure_lookup_table()
assert closed(bm), "sphere not closed"; assert all(len(bm.faces[i].verts) == 4 for i in info["faces"]), "non-quad in the fill"
print("ok sphere hole", info["n"], "edges ->", len(info["faces"]), "quads", "(loop cut for parity)" if info["cut"] else "")

bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=12, radius1=1, radius2=1, depth=2)
bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1], cuts=3, use_grid_fill=True)
bm.faces.ensure_lookup_table(); mid = [f for f in bm.faces if 0.1 < f.calc_center_median().z < 0.4]
bmesh.ops.delete(bm, geom=mid, context="FACES_ONLY")
for v in [v for v in bm.verts if not v.link_faces]: bm.verts.remove(v)
L = [l for l in boundary_loops(bm) if abs(sum(v.co.z for v in l) / len(l)) < 0.9]; assert len(L) == 2 and len(L[0]) == len(L[1]) == 12, [len(l) for l in L]
f, nv = loop_bridge(bm, L[0], L[1], None, rings=1)
assert all(len(x.verts) == 4 for x in f); assert len(boundary_loops(bm)) == 2, "the bridge left a hole (only the 2 open ends of the cylinder may remain)"
print("ok bridge", len(f), "quads, border rings kept")
try: loop_bridge(bm, boundary_loops(bm)[0], boundary_loops(bm)[1][:10], None); raise SystemExit("count mismatch should raise")
except ValueError: print("ok mismatch raises")

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "02-retopology", "seam_close.py"), encoding="utf-8").read())
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=1.0)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x > 0.01], context="FACES")      # the left half: border = the plane x = 0
bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.calc_center_median().x) < 0.45 and f.calc_center_median().z > 0.3 and f.calc_center_median().y < 0.2], context="FACES_ONLY")
for v in [v for v in bm.verts if not v.link_faces]: bm.verts.remove(v)
runs = axis_runs(bm); op = [i for i, (k, vs) in enumerate(runs) if k == "OPEN"]; assert len(op) == 1, runs
i = op[0]; info = fill_half(bm, runs[i][1], runs[i - 1][1][-1], runs[(i + 1) % len(runs)][1][0], None)
bm.faces.ensure_lookup_table(); assert all(len(bm.faces[j].verts) == 4 for j in info["faces"])
assert all(abs(e.verts[0].co.x) < 1e-6 and abs(e.verts[1].co.x) < 1e-6 for e in bm.edges if e.is_boundary), "a border is left off the plane"
print("ok fill_half", len(info["faces"]), "quads, only the mirror plane is a border")
