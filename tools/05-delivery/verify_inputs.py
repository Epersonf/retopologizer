"""Check that heavy, git-ignored inputs listed in inputs.json are present and unchanged.
Usage: python tools/05-delivery/verify_inputs.py   (exit code 1 if something is missing/changed)"""
import hashlib, json, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
bad = 0
for project, e in json.loads((root / "inputs.json").read_text()).items():
    p = root / "projects" / project / "input" / e["file"]
    if not p.exists():
        print(f"MISSING  {p}  (restore from your backup; sha256 {e['sha256'][:12]}...)"); bad += 1; continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    print(("OK       " if h == e["sha256"] else "CHANGED  ") + str(p)); bad += h != e["sha256"]
sys.exit(1 if bad else 0)
