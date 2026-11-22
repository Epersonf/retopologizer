"""Post mortem scaffold and checks. MANDATORY after every delivery (game, store, any handoff): `docs/05-delivery/post-mortem.md`.
  python tools/general/post_mortem.py <project> [--delivery godot,fab]
Creates projects/<project>/POST_MORTEM.md from the template (never overwrites) and prints what the pipeline still owes:
project scripts over 150 lines or with no docstring, a case file in docs/08-cases/, rows in docs/README.md and tools/README.md for new
tools (files in tools/ newer than the last post mortem commit), docs edited since the project started. It does not write the lessons
for you: the lessons are the work (read the guide)."""
import argparse, os, subprocess, sys, time
NL = chr(10) + "  "
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE = """# Post mortem: {name}
Date: {date} - delivered to: {delivery}

## 1. What was delivered (numbers)
tris / budget, UV, bake, rig bones, clips, textures, files, where it went (game / store listing id). What was NOT checked.

## 2. Timeline and where the time went
Stage -> rounds -> why. The longest loops and what caused each (wrong axis, wrong diagnosis, tool missing, waiting for the user).

## 3. Mistakes and the fix that worked (each one: symptom, wrong guess, real cause, rule)

## 4. What the user did that the agent did not (recordings, corrections, preferences)
Read the recordings/corrections again. Each item: what they did, why it works, which tool or rule it becomes.

## 5. Tools: created, extended, still missing
Table: tool | stage | what it replaces. Anything done by hand twice goes here as "missing".

## 6. Docs updated (old ones included)
List the old docs corrected because they were wrong, incomplete or contradicted by this project.

## 7. Next time (the 5 lines to read before the next asset of this kind)
"""


def sh(*a):
    return subprocess.run(a, cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0]); ap.add_argument("project"); ap.add_argument("--delivery", default="")
    a = ap.parse_args(); proj = os.path.join(ROOT, "projects", a.project)
    if not os.path.isdir(proj): sys.exit("no such project: %s" % proj)
    pm = os.path.join(proj, "POST_MORTEM.md")
    if not os.path.exists(pm):
        open(pm, "w", encoding="utf-8").write(TEMPLATE.format(name=a.project, date=time.strftime("%Y-%m-%d"), delivery=a.delivery or "?")); print("created", pm)
    else: print("exists (kept):", pm)
    bad = []
    for f in sorted(os.listdir(proj)):
        if f.endswith(".py"):
            t = open(os.path.join(proj, f), encoding="utf-8").read()
            if t.count("\n") + 1 > 150: bad.append("%s: %d lines (>150)" % (f, t.count("\n") + 1))
            if not t.lstrip().startswith(('"""', "'''")): bad.append("%s: no docstring (what it does, where it runs)" % f)
    print("project scripts to fix (%d, first 8):" % len(bad) if bad else "project scripts ok", *bad[:8], sep=NL)
    case = os.path.join(ROOT, "docs", "08-cases", a.project + ".md")
    print("case file:", "ok" if os.path.exists(case) else "MISSING docs/08-cases/%s.md" % a.project)
    new = [l for l in sh("git", "status", "--short", "tools", "docs").splitlines() if l]
    print("changed/new tools+docs not committed yet (check each is indexed in tools/README.md and docs/README.md):", *new, sep="\n  ")
    idx = open(os.path.join(ROOT, "tools", "README.md"), encoding="utf-8").read()
    unindexed = [f for d in os.listdir(os.path.join(ROOT, "tools")) if os.path.isdir(os.path.join(ROOT, "tools", d)) and not d.startswith("_")
                 for f in os.listdir(os.path.join(ROOT, "tools", d)) if f.endswith((".py", ".sh")) and f not in idx]
    print("tools missing from tools/README.md:", *unindexed, sep="\n  ")
    print("Now fill POST_MORTEM.md sections 1-7, update the old docs, and add a row for the lessons in the case file.")


if __name__ == "__main__":
    main()
