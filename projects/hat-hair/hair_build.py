"""The whole hair the way a human does it (normal python; the worker on 9877 holds HairFull, a copy of draft/hair_work.blend):
  1 hair_radial.py        the height field of the reference about the vertical axis (only with `radial`; draft/hair_radial.npz)
    hair_pieces.py + hair_piece_axes.py   the reference's own lock pieces and their centrelines (only with `pieces`; draft/hair_pieces.npz, hair_piece_axes.json)
  2 hair_base.py          blockout: a solid base with very few polygons, only for the form                        -> Hair_hood
  3 hair_pick.py          the locks: the pieces that stand proud of the base within a quad budget -> Bezier control points -> draft/hair_curves.json
                          (with `hand`: hair_curves.py, the hand-drawn polylines of hair_locks_def.py instead)
    hair_curves_build.py  Bezier curves (radius per point, Alt+S) -> tube / ribbon meshes buried in the base                -> Hair_curve_NN, Hair_tube_NN
  4 hair_join.py          joins them and runs the whole QA battery; saved and exported only when everything passes
  python -I projects/hat-hair/hair_build.py [radial] [pieces] [hand] [fast] [NAME=value ...]
`fast`: the battery with the quick strict check (iterate with it; the final run is without). NAME=value is set in the workers before the scripts
(PCT, PCT_Z, NT, NZ, MARGIN, FILL for the base; ROOTK, RES_U (1 by default), DMAX for the tubes) and handed to hair_pick.py (QUADS, SIDES, TOL, MINSEG, PROUD, BMIN),
e.g. PCT=60 QUADS=900. Output: one short line per step."""
import subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent; ROOT = H.parent.parent; sys.path.insert(0, str(ROOT / "tools" / "general"))
import blender_rpc
args = sys.argv[1:]; kv = dict(a.split("=", 1) for a in args if "=" in a); flags = [a for a in args if "=" not in a]
pre = "".join("%s = %s\n" % (k, v) for k, v in {"RES_U": 1, **kv}.items()) + ("FAST = True\n" if "fast" in flags else "")


def worker(script, extra=""):
    r = blender_rpc.run(pre + extra + (H / script).read_text(encoding="utf-8"), port=9877)
    return (None, r.get("message", "")) if r.get("status") == "error" else (r.get("result"), r.get("stdout", ""))


if "radial" in flags:
    res, out = worker("hair_radial.py"); print("radial", res)
if "pieces" in flags:
    print("pieces", worker("hair_pieces.py")[0]); print("axes", worker("hair_piece_axes.py")[0])
res, out = worker("hair_base.py"); print("base", res if res else out[-600:])
worker("hair_radial.py", 'OBJ = "Hair_hood"; OUT = "hair_radial_base"\n')              # the base seen as a height field: how far the locks stand proud of it
picks = [a for a in args if "=" in a and a.split("=")[0] in ("QUADS", "SIDES", "TOL", "MINSEG", "PROUD", "BMIN")]
r = subprocess.run([sys.executable, "-I", str(H / ("hair_curves.py" if "hand" in flags else "hair_pick.py"))] + ([] if "hand" in flags else picks), capture_output=True, text=True); print((r.stdout + r.stderr[-400:]).rstrip())
res, out = worker("hair_curves_build.py"); print("tubes", {"quads": res["quads"], "locks": len(res["locks"])} if res else out[-600:])
res, out = worker("hair_join.py")
if res:
    print("join: ALL PASS, saved draft/hair_lowpoly_v3.blend, %d triangles" % res["triangles_equiv"])
else:
    print("join:", out[out.index("REJECTED"):].replace("\\n", "\n") if "REJECTED" in out else out[-800:])
