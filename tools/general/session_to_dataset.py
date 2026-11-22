"""Converts a raw recording (session_recorder.py) into a dataset episode: steps (trigger -> actions) + initial and final state.
  python tools/general/session_to_dataset.py <rec_dir> <episode_dir> [--name name]
v3 recordings already have actions.jsonl; the old ones (v1/v2) are rebuilt from snap_NNNN.json (difference between consecutive snapshots).
Output: episode.jsonl (one step per line), initial_state.json, final_state.json, episode_meta.json."""
import json, os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from session_actions import diff


def scrub(o):
    """Remove absolute paths and the user name before publishing."""
    if isinstance(o, str):
        return re.sub(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/]+", "<user>", o).replace("\\", "/")
    if isinstance(o, list):
        return [scrub(x) for x in o]
    if isinstance(o, dict):
        return {k: scrub(v) for k, v in o.items()}
    return o


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []


def mat_apply(mw, co):
    return [round(sum(mw[r][c] * (list(co) + [1])[c] for c in range(4)), 5) for r in range(3)]


def rebuild(rec, events):
    """Rebuilds the actions from the snapshots (recordings without actions.jsonl)."""
    steps, prev, last_t = [], {}, 0.0
    for fp in sorted(glob.glob(os.path.join(rec, "snap_*.json"))):
        s = json.load(open(fp, encoding="utf-8")); obj = s.get("obj", "RETOPO")
        cur = {"V": s["verts"], "E": s["edges"], "F": s["faces"], "sel": s["sel"]}
        trig = ["key:" + e["type"] for e in events if e["kind"] == "key" and last_t < e["t"] <= s["t"]] + \
               ["op:" + e["id"] for e in events if e["kind"] == "op" and last_t < e["t"] <= s["t"]]
        last_t = s["t"]
        if obj in prev:
            acts = diff(prev[obj], cur, lambda co, mw=s["mw"]: mat_apply(mw, co), lambda w: None)
            if acts:
                steps.append({"t": s["t"], "n": s["n"], "obj": obj, "mode": s["mode"], "triggers": trig, "actions": acts})
        prev[obj] = cur
    return steps


def main(rec, out, name):
    os.makedirs(out, exist_ok=True)
    events = load(os.path.join(rec, "events.jsonl")); acts = load(os.path.join(rec, "actions.jsonl"))
    steps = acts or rebuild(rec, events)
    with open(os.path.join(out, "episode.jsonl"), "w", encoding="utf-8") as f:
        for k, st in enumerate(steps):
            f.write(json.dumps({"step": k, **st}) + "\n")
    snaps = sorted(glob.glob(os.path.join(rec, "snap_*.json")))
    if snaps:
        json.dump(json.load(open(snaps[0], encoding="utf-8")), open(os.path.join(out, "initial_state.json"), "w"))
        json.dump(json.load(open(snaps[-1], encoding="utf-8")), open(os.path.join(out, "final_state.json"), "w"))
    kinds = {}
    for st in steps:
        for a in st["actions"]:
            kinds[a["type"]] = kinds.get(a["type"], 0) + 1
    meta = load(os.path.join(rec, "meta.json")) if False else (json.load(open(os.path.join(rec, "meta.json"), encoding="utf-8")) if os.path.exists(os.path.join(rec, "meta.json")) else {})
    json.dump({"name": name, "source": os.path.basename(os.path.abspath(rec)), "steps": len(steps), "action_counts": kinds, "duration_s": steps[-1]["t"] if steps else 0,
               "recorder": scrub(meta), "from_actions_jsonl": bool(acts)}, open(os.path.join(out, "episode_meta.json"), "w", encoding="utf-8"), indent=1)
    print(name, len(steps), "passos", kinds)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], a[a.index("--name") + 1] if "--name" in a else os.path.basename(a[0]))
