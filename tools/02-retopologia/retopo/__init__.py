"""retopo: toolkit for hand-style retopology driven by an LLM through the Blender MCP socket.
Every vertex is placed on purpose and snapped to the reference (no automatic remesh). Guide: docs/02-retopologia/retopo-llm.md.

  ref.py      Ref: BVH of the high-poly in world space (cached between calls): nearest, ray, hits, snap, exit, outer
  curves.py   ring / arc / line / arcline / resample / sample: loops and lines drawn on the surface
  contour.py  cring / chalf / track / align / box_ring: contour rings on the real cross-section, tube spines
  topo.py     Topo: bmesh builder (v, vs, f, strip, fan, grid, write) + topo_ops.py (relax, orient, chain, mirror_x)
  patches.py  solve_spokes / poly_patch: 3- or 5-sided holes filled with quads around one pole
  digits.py   digit / claw_base: finger, toe or claw grown from a root ring to its tip (claw step, tip cap)
  lock.py     lock / stations: a closed tube along a given spine (hair clumps, tentacles, horns), rings on the cross-section
  qa.py       topo_qa: counts, holes, non-manifold, doubles, winding, inward faces, poles, distance
  part.py     part_object / export_obj: the faces of one round as their own object, OBJ for the artist

Inside Blender (MCP) -- importlib.reload(retopo) also reloads every submodule, in dependency order:
  import sys; sys.path.insert(0, r"C:/Users/epers/Desktop/retopologizer/tools")
  import importlib, retopo; importlib.reload(retopo); from retopo import *
"""
import importlib, sys

for _m in ("ref", "curves", "contour", "topo_ops", "topo", "patches", "digits", "lock", "qa", "part"):
    if __name__ + "." + _m in sys.modules:
        importlib.reload(sys.modules[__name__ + "." + _m])

from .ref import Ref
from .curves import ring, arc, line, arcline, resample, sample, basis, centroid
from .contour import cring, chalf, track, centred, align, frame, co, box_ring, at_width
from .topo import Topo
from .patches import solve_spokes, poly_patch
from .digits import digit, claw_base, spine
from .lock import lock, stations
from .qa import topo_qa
from .part import part_object, export_obj


def reload():
    importlib.reload(sys.modules[__name__])


__all__ = ["Ref", "Topo", "topo_qa", "ring", "arc", "line", "arcline", "resample", "sample", "basis", "centroid",
           "solve_spokes", "poly_patch", "cring", "chalf", "track", "centred", "align", "frame", "co",
           "digit", "claw_base", "spine", "lock", "stations", "box_ring", "at_width", "part_object", "export_obj"]
