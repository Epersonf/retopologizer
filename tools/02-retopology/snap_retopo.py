"""Manual-style retopology helpers: place vertices ON the reference surface (like Blender's
snap-to-face), build half of a symmetric part and mirror it (like the Mirror modifier + apply).
Inside Blender (MCP):  exec(open(...).read())
  S = Surface("REF_LID")                       # reference in the SAME local space as the part
  S.nearest(p)            -> closest surface point (snap to face)
  S.ray(p, d, both=True)  -> closest hit along +-d
  S.outer(x, c, ang_deg)  -> (y,z) of the OUTER hull hit from centre c along angle (section at x)
  S.inner(x, c, ang_deg)  -> first hit going outward from c (cavity wall)
  simplify(poly, eps)     -> Douglas-Peucker (corner picking for a section polyline)
  Mesh(): v(p)->vertex (welded), f(*vs), strip(ringA, ringB), mirror_x(), to_object(name)
Sections are star-shaped around c; the same angle list is reused for every ring so that rings
share topology and can be stitched with quad strips (the usual hand-retopo ring workflow)."""
import os
_D = os.path.join(os.environ.get("RETOPOLOGIZER_ROOT") or (os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) if "__file__" in globals() else os.getcwd()), "tools", "02-retopology")
exec(open(_D + "/snap_surface.py").read())
exec(open(_D + "/snap_mesh.py").read())
exec(open(_D + "/snap_section.py").read())
