"""Paths and names shared by the wing scripts. All come from the environment (run_all.py sets them), nothing is hardcoded.
RETOPOLOGIZER_ROOT = repo root; WING_DIR = project folder (draft/, output/); WING_EX = this folder."""
import os, sys
R = os.environ.get("RETOPOLOGIZER_ROOT") or os.getcwd(); WING = os.environ.get("WING_DIR") or os.path.join(R, "projects", "wing")
EX = os.environ.get("WING_EX") or os.path.join(R, "examples", "wing"); DRAFT = os.path.join(WING, "draft"); OUT = os.path.join(WING, "output")
for p in (EX,):
    if p not in sys.path:
        sys.path.insert(0, p)


def load_tool(*parts):
    """exec a tools/ file into the caller's globals: load_tool('02-retopology', 'skin_close.py')."""
    import inspect
    exec(compile(open(os.path.join(R, "tools", *parts), encoding="utf-8").read(), parts[-1], "exec"), inspect.currentframe().f_back.f_globals)
