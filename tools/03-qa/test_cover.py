r"""Regression of qa_cover: a mesh that skips a patch of the ref must fail, the full one pass. Run inside Blender (exec), result["ok"]."""
import bpy, bmesh, os
_R = os.environ.get("RETOPOLOGIZER_ROOT") or r"C:\Users\epers\Desktop\retopologizer"
exec(open(os.path.join(_R, "tools", "general", "qa_coverage.py"), encoding="utf-8").read())
for n in ("_cov_ref", "_cov_full", "_cov_hole"):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])


def sphere(name, drop=False):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.05)
    if drop:  # tira uma tampa de ~25% (como um dedo ausente)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x > 0.02], context="FACES")
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o


sphere("_cov_ref"); sphere("_cov_full"); sphere("_cov_hole", drop=True)
full = qa_coverage("_cov_full", "_cov_ref", border_skip=False); hole = qa_coverage("_cov_hole", "_cov_ref", border_skip=False)
for n in ("_cov_ref", "_cov_full", "_cov_hole"): bpy.data.objects.remove(bpy.data.objects[n])
result = {"ok": full["pass"] and not hole["pass"], "full_pct": full["uncovered_pct"], "hole_pct": hole["uncovered_pct"]}
