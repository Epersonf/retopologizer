"""Put recordings and stage results into the versioned dataset/ folder, one sub-folder per stage and per actor (user / agent).
  python tools/general/dataset_pack.py episode --stage retopology --asset wing --id wing_rec04 --rec projects/wing/session/rec_04 [--final-mesh final.json]
  python tools/general/dataset_pack.py record  --stage uv --asset wing --id wing_uv01 --json uv_layout.json --actor user --note "UV by hand, no overlap"
  python tools/general/dataset_pack.py index                       # rebuilds dataset/<stage>/<asset>/index.json for everything
Layout (everything gzip-compressed JSON(L) so it stays small in git; raw sessions with keyframes and screenshots stay outside git):
  dataset/<stage>/<asset>/<id>/...      stage = retopology | adjust | uv | bake | relief | rig | export
  dataset/<stage>/<asset>/index.json    id, actor, files, bytes, note
`episode` converts a raw session (session_recorder.py) with session_to_dataset.py and scrubs paths and user names."""
import argparse, gzip, json, os, shutil, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import session_to_dataset as S


def gz_json(src, dst, jsonl=False):
    with open(src, "rb") as f, gzip.open(dst + ".gz", "wb", compresslevel=9) as g:
        shutil.copyfileobj(f, g)
    os.remove(src) if src.startswith(tempfile.gettempdir()) else None


def put_meta(d, **kw):
    json.dump(kw, open(os.path.join(d, "entry.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def cmd_episode(a):
    out = os.path.join(ROOT, "dataset", a.stage, a.asset, a.id); tmp = tempfile.mkdtemp(); os.makedirs(out, exist_ok=True)
    S.main(a.rec, tmp, a.id)
    for f in os.listdir(tmp):
        p = os.path.join(tmp, f)
        if f == "episode_meta.json":
            shutil.copy(p, os.path.join(out, f))
        else:
            with open(p, "rb") as fi, gzip.open(os.path.join(out, f + ".gz"), "wb", compresslevel=9) as g:
                g.write(json.dumps(S.scrub(json.loads(fi.read().decode()))).encode() if f.endswith(".json") else fi.read())
    if a.final_mesh:
        with open(a.final_mesh, "rb") as fi, gzip.open(os.path.join(out, "final_mesh.json.gz"), "wb", compresslevel=9) as g:
            g.write(fi.read())
    put_meta(out, id=a.id, stage=a.stage, asset=a.asset, actor=a.actor, kind="episode", note=a.note); shutil.rmtree(tmp); cmd_index(a)


def cmd_record(a):
    out = os.path.join(ROOT, "dataset", a.stage, a.asset, a.id); os.makedirs(out, exist_ok=True)
    data = json.dumps(S.scrub(json.load(open(a.json, encoding="utf-8")))).encode()
    name = os.path.splitext(os.path.basename(a.json))[0] + ".json"
    with gzip.open(os.path.join(out, name + ".gz"), "wb", compresslevel=9) as g:
        g.write(data)
    put_meta(out, id=a.id, stage=a.stage, asset=a.asset, actor=a.actor, kind="record", note=a.note); cmd_index(a)


def cmd_index(a):
    base = os.path.join(ROOT, "dataset")
    for stage in sorted(os.listdir(base)):
        for asset in sorted(os.listdir(os.path.join(base, stage))) if os.path.isdir(os.path.join(base, stage)) else []:
            d = os.path.join(base, stage, asset); items = []
            for e in sorted(os.listdir(d)):
                m = os.path.join(d, e, "entry.json")
                if os.path.exists(m):
                    meta = json.load(open(m, encoding="utf-8")); meta["files"] = sorted(os.listdir(os.path.join(d, e)))
                    meta["bytes"] = sum(os.path.getsize(os.path.join(d, e, f)) for f in meta["files"]); items.append(meta)
            json.dump(items, open(os.path.join(d, "index.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
    for n, fn in (("episode", cmd_episode), ("record", cmd_record), ("index", cmd_index)):
        s = sub.add_parser(n); s.set_defaults(fn=fn)
        if n != "index":
            s.add_argument("--stage", required=True); s.add_argument("--asset", required=True); s.add_argument("--id", required=True)
            s.add_argument("--actor", default="user"); s.add_argument("--note", default="")
        if n == "episode":
            s.add_argument("--rec", required=True); s.add_argument("--final-mesh")
        if n == "record":
            s.add_argument("--json", required=True)
    a = p.parse_args(); a.fn(a)
