r"""Sends the raw recordings (projects/*/session/rec_NN) to a Hugging Face DATASET repo: they are heavy (2.2 GB here) and git is the wrong place.
  hf auth login                                   # once, by YOU (a write token); this script never sees or stores a token
  python tools/general/hf_push.py --repo <user>/retopo-sessions                 # dry run: lists what would go and how big
  python tools/general/hf_push.py --repo <user>/retopo-sessions --go            # uploads, PRIVATE repo by default
  python tools/general/hf_push.py --repo ... --go --public                      # only if you decide to publish
  python tools/general/hf_refs.py                                              # first: adds ref.npz to every recording (needs Blender)
Layout in the repo: projects/<project>/<rec_NN>/{actions.jsonl, events.jsonl, meta.json, checkpoint_*.json, shot_*.png}.
Scrubbing: text files are copied to a temp folder with the Windows user name and absolute paths replaced (`<home>`) before upload;
a rec already on the Hub (same file list) is skipped, so it can be re-run after every session. Empty recordings (no actions) are skipped.
Also writes a README.md (dataset card) with the schema and the licence chosen with --license (default cc-by-4.0)."""
import argparse, glob, hashlib, json, os, re, shutil, sys, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TEXT = (".json", ".jsonl", ".txt", ".md")
CARD = """---
license: {lic}
task_categories: [other]
tags: [retopology, 3d, blender, imitation-learning]
---
# Retopology sessions (Blender)
Licence: **CC BY 4.0**: free for any use, commercial included, training models included; the only condition is attribution.
Attribution: "Retopology sessions by Eperson, https://huggingface.co/datasets/Eperson/retopo-sessions, CC BY 4.0".

Raw recordings of an artist retopologizing game assets by hand (Blender 5.x, `session_recorder.py`). One folder per project and recording, all under `projects/`.
- `actions.jsonl`: one line per trigger {{t, n, obj, mode, triggers, actions:[select|add_vertex|move_vertex|add_face|topology_change]}} (vertex ids, local/world coordinates).
- `events.jsonl`: keys, mouse, operators with properties (extrude, translate, resize, rotate, loop cut, merge...), time in seconds.
- `checkpoint_NNN.json`: full mesh snapshot at each Ctrl+S / Tab; `shot_NNNN.png`: viewport screenshots; `meta.json`: Blender version, view, snap settings.
- `projects/<project>/refs/<hash>.npz`: the reference (shared by every recording of the project that used it; each recording's `ref.json` has `ref_npz` pointing to it).
  The reference is what the artist was following, as 60000 area-weighted surface points (`<object>__points` float32, `<object>__normals` float16) in world space, same space as the recording's `world` coordinates; the recording's `ref.json` has vertex/triangle counts, area and world matrices (made by `hf_refs.py`).
- The last `checkpoint_NNN.json` is the final state of the edited mesh (what the artist left, not necessarily approved).
Paths and user names are scrubbed.
"""


def scrub(src, dst, user):
    s = open(src, encoding="utf-8", errors="replace").read()
    s = re.sub(r"[A-Za-z]:(\\\\|\\|/)+Users(\\\\|\\|/)+[^\\/\"']+", "<home>", s)
    if user: s = s.replace(user, "user")
    open(dst, "w", encoding="utf-8").write(s)


def ref_path(r, name):
    f = os.path.join(r, "ref.npz")
    if not os.path.exists(f): return None
    h = hashlib.md5(open(f, "rb").read()).hexdigest()[:10]
    return "/".join(name.split("/")[:2]) + "/refs/%s.npz" % h


def recs():
    for r in sorted(glob.glob(os.path.join(ROOT, "projects", "*", "session", "rec_*"))):
        a = os.path.join(r, "actions.jsonl")
        if os.path.exists(a) and os.path.getsize(a) > 0: yield r


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", required=True); ap.add_argument("--go", action="store_true")
    ap.add_argument("--public", action="store_true"); ap.add_argument("--license", default="cc-by-4.0"); ap.add_argument("--no-shots", action="store_true")
    a = ap.parse_args(); user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    items = [(r, "projects/" + os.path.relpath(r, os.path.join(ROOT, "projects")).replace(os.sep + "session" + os.sep, "/").replace(os.sep, "/")) for r in recs()]
    tot = 0
    for r, name in items:
        files = [f for f in os.listdir(r) if not (a.no_shots and f.endswith(".png"))]; sz = sum(os.path.getsize(os.path.join(r, f)) for f in files); tot += sz
        print("%-28s %4d files %8.1f MB" % (name, len(files), sz / 1e6))
    print("total %.2f GB in %d recordings" % (tot / 1e9, len(items)))
    if not a.go: print("dry run: add --go to upload (private unless --public)"); return
    from huggingface_hub import HfApi
    api = HfApi(); who = api.whoami()["name"]; print("logged in as", who)
    api.create_repo(a.repo, repo_type="dataset", private=not a.public, exist_ok=True)
    if a.public: api.update_repo_settings(a.repo, repo_type="dataset", private=False)   # create_repo(exist_ok) does not change visibility
    have = set(api.list_repo_files(a.repo, repo_type="dataset"))
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "README.md"), "w", encoding="utf-8").write(CARD.format(lic=a.license))
        api.upload_file(path_or_fileobj=os.path.join(tmp, "README.md"), path_in_repo="README.md", repo_id=a.repo, repo_type="dataset")
        from huggingface_hub import CommitOperationAdd, CommitOperationDelete
        have = set(api.list_repo_files(a.repo, repo_type="dataset")); ops = []   # one commit for all reference changes (the Hub rate-limits commits)
        for r, name in items:
            shared = ref_path(r, name)   # the reference is stored once per project and content hash, not once per recording
            if shared and shared not in have:
                ops.append(CommitOperationAdd(shared, os.path.join(r, "ref.npz"))); have.add(shared)
            rj = os.path.join(r, "ref.json")
            if shared and os.path.exists(rj) and ((name + "/ref.json") not in have or (name + "/ref.npz") in have):
                j = json.load(open(rj, encoding="utf-8")); j["ref_npz"] = shared; t = os.path.join(tmp, name.replace("/", "_") + ".ref.json")
                open(t, "w", encoding="utf-8").write(json.dumps(j, indent=1)); ops.append(CommitOperationAdd(name + "/ref.json", t))
            if (name + "/ref.npz") in have: ops.append(CommitOperationDelete(name + "/ref.npz")); have.discard(name + "/ref.npz")
        if ops: api.create_commit(a.repo, ops, repo_type="dataset", commit_message="references once per project"); print("refs commit:", len(ops), "operations")
        for r, name in items:
            if (name + "/actions.jsonl") in have: print("skip", name); continue
            d = os.path.join(tmp, name); os.makedirs(d)
            for f in os.listdir(r):
                if (a.no_shots and f.endswith(".png")) or f in ("ref.npz", "ref.json"): continue
                (scrub if f.endswith(TEXT) else lambda s, t, u: shutil.copy(s, t))(os.path.join(r, f), os.path.join(d, f), user)
            api.upload_folder(folder_path=d, path_in_repo=name, repo_id=a.repo, repo_type="dataset", commit_message="add " + name)
            shutil.rmtree(d); print("uploaded", name)

if __name__ == "__main__":
    main()
