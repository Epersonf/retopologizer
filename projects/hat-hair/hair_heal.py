"""Heals the folds of the capped shells (Hair_hood by default; worker) until the strict reversed-face gate passes (qa_strict.py).
Raises = rejected. Run before the tubes are built (hair_build.py does it), so the tubes attach to the final shells.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_heal.py"""
import bpy
Q = r"C:\Users\epers\Desktop\retopologizer\tools\03-qa"
exec(open(Q + r"\qa_faces.py").read()); exec(open(Q + r"\qa_strict.py").read())
result = heal_flipped(globals().get("SHELLS", ["Hair_hood"]))
