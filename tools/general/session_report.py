"""Reads the artist's recording and describes the METHOD in numbers (what they did, not what you would have done).
  python tools/general/session_report.py <rec_dir> [--old N] [--obj NAME]
--old N: vertices that existed before the session (the seam); default = smallest add_vertex id in actions.jsonl.
Prints: timeline (per 30 s: actions by type), operators seen, and for the last checkpoint: face sizes, valence histogram,
border edges, BFS layers from the seam (vertices and new faces per layer), poles. No Blender needed."""
import argparse, collections, glob, json, os


def load(rec):
    acts = [json.loads(l) for l in open(os.path.join(rec, "actions.jsonl"), encoding="utf-8") if l.strip()]
    acts = [a for a in acts if "actions" in a]
    cps = sorted(glob.glob(os.path.join(rec, "checkpoint_*.json")))
    return acts, (json.load(open(cps[-1], encoding="utf-8")) if cps else None)


def timeline(acts, step=30):
    rows = collections.defaultdict(collections.Counter)
    for a in acts:
        for x in a["actions"]:
            rows[int(float(a["t"]) // step)][x["type"]] += 1
    for k in sorted(rows):
        print("  %4d-%4d s  %s" % (k * step, (k + 1) * step, dict(rows[k])))


def operators(rec):
    ops = collections.Counter()
    p = os.path.join(rec, "events.jsonl")
    for l in open(p, encoding="utf-8") if os.path.exists(p) else []:
        for t in json.loads(l).get("triggers", []) if l.startswith("{") else []:
            if t.startswith("op:"): ops[t[3:]] += 1
    return ops


def mesh_stats(m, old):
    V, F = m["verts"], m["faces"]
    val, edges = collections.Counter(), collections.Counter()
    adj = collections.defaultdict(set)
    for f in F:
        for i, a in enumerate(f):
            b = f[(i + 1) % len(f)]; edges[tuple(sorted((a, b)))] += 1; adj[a].add(b); adj[b].add(a)
    for v in range(len(V)): val[len(adj[v])] += 1
    border = [e for e, c in edges.items() if c == 1]
    print("  vertices %d (new %d), faces %d: %s" % (len(V), max(0, len(V) - old), len(F),
          dict(sorted(collections.Counter(len(f) for f in F).items()))))
    print("  valence histogram (all):", dict(sorted(val.items())))
    print("  border edges:", len(border))
    layer = {v: 0 for v in range(min(old, len(V)))}; front = list(layer)
    while front:
        nxt = []
        for v in front:
            for w in adj[v]:
                if w not in layer: layer[w] = layer[v] + 1; nxt.append(w)
        front = nxt
    byl, facel = collections.Counter(layer.values()), collections.Counter()
    for f in F:
        if any(v >= old for v in f): facel[max(layer.get(v, 0) for v in f)] += 1
    print("  layers from the seam (L: vertices / new faces / poles):")
    for L in sorted(byl):
        if L == 0: continue
        pol = [v for v, d in layer.items() if d == L and len(adj[v]) not in (4, 2)]
        print("    L%d: %d / %d / %s" % (L, byl[L], facel[L], sorted(collections.Counter(len(adj[v]) for v in pol).items())))
    return layer, adj


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("rec"); ap.add_argument("--old", type=int); ap.add_argument("--obj")
    a = ap.parse_args(); acts, cp = load(a.rec)
    n = collections.Counter(x["type"] for r in acts for x in r["actions"])
    ids = [x["id"] for r in acts for x in r["actions"] if x["type"] == "add_vertex"]
    old = a.old if a.old is not None else (min(ids) if ids else 0)
    print("actions:", dict(n), "| duration %.0f s | seam = first %d vertices" % (float(acts[-1]["t"]) if acts else 0, old))
    print("timeline:"); timeline(acts)
    ops = operators(a.rec)
    if ops: print("operators:", dict(ops.most_common(12)))
    if cp:
        for name, m in cp["objects"].items():
            if a.obj and name != a.obj: continue
            print("object %s (last checkpoint t=%s):" % (name, cp.get("t"))); mesh_stats(m, old)


if __name__ == "__main__":
    main()
