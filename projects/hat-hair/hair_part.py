"""One hair shell part end to end (normal python; the worker must be up on draft/hair_work.blend with "HairFull" loaded:
hair_proxy.py with NPZ = draft/hair_in.npz, NAME = "HairFull"):
  select faces in Blender -> clean disk (hair_shell.py) -> rings (hair_field.py) -> build in Blender
  python -I projects/hat-hair/hair_part.py dome [counts]
PARTS: window of directions from the head centre (azimuth from the back +y toward +x = the character's left), closing and
opening rings for the disk, vertex counts of the rings."""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; ROOT = HERE.parent.parent
PARTS = {  # name: (PH, TH, CLOSE, OPEN, counts)
    "dome": ((-100, 100), (0, 140), 4, 8, "48,24,12"),
    "front": ((100, 260), (0, 70), 4, 8, "24,12,6"),
    "hood": ((-100, 100), (0, 120), 4, 8, "32,16,8"),       # dome + front cap as ONE shell (ALSO below): no seam, one rim, one lid
    "left": ((80, 180), (0, 140), 4, 8, "48,24,12"),
    "right": ((-180, -80), (0, 140), 4, 8, "48,24,12"),
}
part = sys.argv[1]; PH, TH, CLOSE, OPEN, COUNTS = PARTS[part]
COUNTS = sys.argv[2] if len(sys.argv) > 2 else COUNTS


def blender(script, **g):
    """Run a script in the worker with PART/PH/TH set; returns the worker's output."""
    pre = "".join("%s = %r\n" % kv for kv in g.items())
    tmp = HERE / "draft" / "_run.py"
    tmp.write_text(pre + "exec(open(r%r, encoding='utf-8').read())\n" % str(HERE / script), encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "tools/general/blender_rpc.py"), "--port", "9877", str(tmp)],
                       capture_output=True, text=True)
    print(r.stdout[-600:], r.stderr[-600:])
    return r.stdout


def run(*a):
    r = subprocess.run([sys.executable, "-I", *map(str, a)], capture_output=True, text=True); print(r.stdout, r.stderr[-800:])


blender("hair_shell_select.py", PART=part, PH=PH, TH=TH, ALSO=[((100, 260), (0, 70))] if part == "hood" else [])
run(HERE / "hair_shell.py", part, CLOSE, OPEN)
run(HERE / "hair_field.py", "hair_" + part, COUNTS)
blender("hair_shell_build.py", PART=part)
