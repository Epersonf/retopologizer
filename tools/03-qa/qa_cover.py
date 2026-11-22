r"""Wrapper: does the mesh cover the ref near it (missing / collapsed toe)? Core in tools/general/qa_coverage.py."""
import os
_R = os.environ.get("RETOPOLOGIZER_ROOT") or (os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) if "__file__" in globals() else os.getcwd())
exec(open(os.path.join(_R, "tools", "general", "qa_coverage.py"), encoding="utf-8").read())


def qa_cover(name, ref):
    return qa_coverage(name, ref if isinstance(ref, str) else getattr(ref, "name", "HiPoly"))
