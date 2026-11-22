r"""QA: twisted quads (two triangles folded onto each other), faces looking into the model, stamped (pinched) faces. Zero tolerance.
Core in tools/general/face_shape.py: r = qa_faceshape("Obj", ref="HiPoly"); r["twisted"], r["stamped"], r["inverted"] (inverted needs the ref)."""
import os as _os
_g = _os.path.join(_os.environ.get("RETOPOLOGIZER_ROOT") or (_os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..")) if "__file__" in globals() else _os.getcwd()), "tools", "general", "face_shape.py")
exec(open(_g, encoding="utf-8").read())
