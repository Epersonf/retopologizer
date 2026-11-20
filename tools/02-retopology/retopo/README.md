# tools/02-retopology/retopo — manual character retopology, driven by the agent

Every vertex is decided and snapped to the reference; no remesh. Guide: `docs/02-retopology/retopo-llm.md`. Full example:
`projects/stylized-cuca/cuca_*.py`.

```python
import sys; sys.path.insert(0, r"<repo>/tools")
import importlib, retopo; importlib.reload(retopo); from retopo import *
R = Ref("HiPoly"); T = Topo(R)      # ... T.strip(A, B); T.orient(); T.write("Nome_retopo"); topo_qa("Nome_retopo", R)
```

| file | what it does |
|---|---|
| ref.py | `Ref`: BVH of the high-poly in world space, cached between calls: `nearest`, `ray`, `hits`, `snap`, `exit`, `outer` |
| curves.py | loops and lines on the surface: `ring`, `arc`, `line`, `arcline`, `resample`, `sample` |
| contour.py | contours on the real cross-section: `cring`, `chalf`, `track` (tube spine), `centred`, `align`, `box_ring`, `at_width` |
| topo.py | `Topo`: bmesh builder with snap (`v`, `vs`, `f`, `strip`, `fan`, `grid`, `old`, `write`) |
| topo_ops.py | `Topo` operations: `relax` with snap, `orient` (winding outward), `chain`, `mirror_x` |
| lock.py | `lock` (closed tube per hair lock/tentacle/horn along a given axis), `section` (ring by exit rays with a radius window), `stations`; guide and known problems: `docs/02-retopology/retopo-hair-tubes.md` |
| patches.py | `solve_spokes` + `poly_patch`: 3- or 5-sided hole closed with quads around a pole |
| digits.py | `digit`, `claw_base`, `spine`: finger, claw or horn grown from a ring to the tip |
| qa.py | `topo_qa`: counts, holes, non-manifold, duplicates, winding, inward faces, poles, distance |
| part.py | `part_object` (only the faces of the round, as its own object) and `export_obj` (OBJ of the part for the artist); see `docs/02-retopology/retopo-by-parts.md` |
| \_\_init\_\_.py | exports everything; `importlib.reload(retopo)` reloads the submodules in the right order |
