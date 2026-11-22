# Publishing the retopo sessions (Hugging Face)
Raw recordings (`projects/*/session/rec_NN`) are heavy (2.2 GB) and `projects/` is not in git, so they live in a public dataset:
**https://huggingface.co/datasets/Eperson/retopo-sessions** (23 recordings, 1806 files, 2.21 GB). `dataset/` in git keeps only the small converted episodes (`dataset-spec.md`).

## After every recording session
1. `python tools/general/hf_refs.py` : adds `ref.npz` + `ref.json` to every recording that lacks them (60000 surface points + normals of the reference in WORLD space,
   the 2 biggest non-edited meshes of the .blend the recording started from). Launches Blender in the background; needs `BLENDER_EXE` or the Steam path.
2. `hf auth login` (once, a Write token from huggingface.co/settings/tokens; the scripts never read or store a token).
3. `python tools/general/hf_push.py --repo Eperson/retopo-sessions` : dry run, lists recordings and sizes. Add `--go --public` to upload.
   Re-running is safe: recordings already on the Hub are skipped; one that gained a `ref.npz` is re-sent (unchanged files are deduplicated).
Options: `--no-shots` leaves the PNGs out; `--license <id>` sets the card's licence (default `cc-by-4.0`); without `--public` a NEW repo is private.

## What is uploaded
`projects/<project>/rec_NN/{actions.jsonl, events.jsonl, meta.json, checkpoint_*.json, shot_*.png, ref.npz, ref.json}`; schema in the repo's README (dataset card, written by `hf_push.py`).
Text files are scrubbed first (Windows user name and absolute paths -> `<home>`). Recordings without actions are skipped.

## Limits (read before training)
- The last `checkpoint` is the state the artist left, not a verdict of approval (only guara-wolf rec_02 is known to be approved).
- Some recordings are almost empty (0-15 actions: espada rec_01-03, curupira rec_04, rec_10); they weigh little.
- The reference is a 60000-point sample, not the mesh; curupira's 18M-vertex trunk (rec_03-06) is thinly sampled.
- Screenshots are not inspected one by one: if one shows something private, delete it from the Hub and from `session/` and tell the maintainer.
- Licence: **CC BY 4.0** (any use, commercial and model training included, attribution only; the text is in the dataset card). The artist decided this; the reference meshes inside `ref.npz` are covered by the same licence.
