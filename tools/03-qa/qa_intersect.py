"""QA: faces of the same loose part must never intersect or fold over each other (core in tools/general/face_intersect.py).
  r = qa_intersect("Obj"); r["pass"], r["faces"]; select_faces("Obj", r["faces"]) shows them. Zero tolerance: the mesh is rejected."""
import os as _os
_g = _os.path.join(_os.environ.get("RETOPOLOGIZER_ROOT") or (_os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..")) if "__file__" in globals() else _os.getcwd()), "tools", "general", "face_intersect.py")
exec(open(_g, encoding="utf-8").read())
