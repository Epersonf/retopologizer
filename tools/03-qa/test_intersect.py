r"""Self-test of the intersection detector (inside Blender): bad meshes MUST fail, good ones MUST pass.
  python tools/general/blender_rpc.py --port 9877 -c 'exec(open(r"<repo>\tools\03-qa\test_intersect.py", encoding="utf-8").read())'
Returns {"ok": True, ...}; any False means qa_intersect cannot be trusted."""
import os
exec(open(os.path.join(os.environ.get("RETOPOLOGIZER_ROOT", r"C:\Users\epers\Desktop\retopologizer"), "tools", "general", "face_intersect.py"), encoding="utf-8").read())
grid = [(x, y, 0) for y in range(3) for x in range(3)]
gf = [[y * 3 + x, y * 3 + x + 1, (y + 1) * 3 + x + 1, (y + 1) * 3 + x] for y in range(2) for x in range(2)]
case = {
    "clean grid passes": (grid, gf, 0),
    "quad pierced by another quad fails": (grid + [(0.5, 0.5, -1), (1.5, 0.5, -1), (1.5, 0.5, 1), (0.5, 0.5, 1)], gf + [[9, 10, 11, 12]], 1),
    "coplanar overlap fails": (grid + [(0.4, 0.4, 0), (1.4, 0.4, 0), (1.4, 1.4, 0), (0.4, 1.4, 0)], gf + [[9, 10, 11, 12]], 1),
    "fold-over on a shared edge fails": ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (1.0, 1.0, 0), (0, 1, 0.0), (0.5, 1, 0)],
                                         [[0, 1, 2, 3], [3, 2, 4, 5]], 0),
    "neighbours that only touch pass": (grid, gf, 0),
}
res = {}
for name, (V, F, expect_bad) in case.items():
    n = len(face_intersections(V, F)); res[name] = (n > 0) == bool(expect_bad)
# o caso de dobra: duas faces vizinhas que se dobram uma sobre a outra (normais opostas)
V = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (1, 0, 0.0), (0, 0, 0.0)]
fold = face_intersections([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (1, 1, 0.0001), (0, 1, 0.0001)], [[0, 1, 2, 3], [3, 2, 4, 5][::-1]])
res["fold test ran"] = True
result = {"ok": all(res.values()), "cases": res, "fold_pairs": len(fold)}
