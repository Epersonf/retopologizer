"""QA battery from the command line: runs qa_suite.py in the Blender worker and prints one line per check. Exit code 1 if any fails.
  python -I tools/03-qa/qa.py LowPoly --ref HairFull [--only shape,fit] [--skip strict] [--fast] [--budget 3000] [--port 9877] [--json]
--fast: strict with 100 directions (iterate with it, run the full one before delivering). Without --ref the fit check is skipped."""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "general"))
import blender_rpc

ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("--ref"); ap.add_argument("--only", default=""); ap.add_argument("--skip", default="")
ap.add_argument("--fast", action="store_true"); ap.add_argument("--budget", type=int, default=3000); ap.add_argument("--port", type=int, default=9877); ap.add_argument("--json", action="store_true")
a = ap.parse_args()
code = "exec(open(r%r, encoding='utf-8').read())\nr = qa_suite(%r, ref=%r, only=%r, skip=%r, fast=%r, budget=%r)\nresult = r if %r else {k: r[k] for k in ('pass', 'failed', 'lines')}\n" % (
    str(ROOT / "tools/03-qa/qa_suite.py"), a.name, a.ref, [x for x in a.only.split(",") if x], tuple(x for x in a.skip.split(",") if x), a.fast, a.budget, a.json)
r = blender_rpc.run(code, port=a.port)
if r.get("status") == "error":
    print(r.get("message"), r.get("stderr", ""))
    sys.exit(2)
res = r["result"]
print(json.dumps(res) if a.json else "\n".join(res["lines"]) + "\n" + ("ALL PASS" if res["pass"] else "REJECTED: " + ", ".join(res["failed"])))
sys.exit(0 if res["pass"] else 1)
