"""Fiber cards rendered in Blender: a sheet of cards (cardsPerSheet in a grid, the first with few strands and the last dense) of strands generated like the app
epersonf/fiber-card-gen (fc_strands.py, fc_params.py: same state keys, a preset JSON pastes into the app), turned into tubes and rendered by fc_blender.py
(Cycles, orthographic, transparent): <tag>_color.png and <tag>_normal.png (RGBA, `size` px square), <tag>_preview.png (on grey, grid lines), <tag>_preset.json.
  python -I tools/07-fibercards/fibercards.py --out DIR [--tag blonde] [--preset p.json | --blonde] [--seed 1] [--samples 32] [--lighting soft|flat] [--blend f.blend]
                                              [--set chave=valor ...]       e.g. --set hair_amount_max=90 cardsPerSheet=16 baseSize=1024
BLENDER=<exe> overrides the Blender path. Cards are laid out like the app: x across (0 = the middle of the cell), y up from the bottom edge of the cell, the root at the top."""
import argparse, json, math, os, subprocess, sys, tempfile
import numpy as np
from pathlib import Path
from PIL import Image
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T))
import fc_params, fc_strands
BLENDER = os.environ.get("BLENDER", r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe")


def gradient(s, f, rnd, jitter=0.05):                                         # colour along a strand, root = 0 (the app's gradient stops), a little brightness jitter per strand
    j = 1 + jitter * (2 * rnd() - 1)
    if not s["gradient_color_enabled"] or len(s["hair_gradient_stops"]) < 2:
        return np.tile(np.array(s["hair_color"][:3]) * j, (len(f), 1)).clip(0, 1)
    st = sorted(s["hair_gradient_stops"], key=lambda k: k["pos"]); col = np.array([[int(k["color"].lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)] for k in st])
    return (np.column_stack([np.interp(f, [k["pos"] for k in st], col[:, c]) for c in range(3)]) * j).clip(0, 1)


def job_cards(s, seed):
    W = int(s["baseSize"] * s["percentage"]); n = s["cardsPerSheet"]; cols = math.ceil(math.sqrt(n)); rows = math.ceil(n / cols); cw, ch = W / cols, W / rows
    mx = max(1, int(s["hair_amount_max"])); mn = max(1, int(mx * min(max(s["hair_amount_min_percent"], 0), 1))); cards = []
    for idx in range(n):
        r, c = divmod(idx, cols); t = idx / (n - 1) if n > 1 else 1.0; k = max(1, int(mn + (mx - mn) * {"quad": t * t, "sqrt": math.sqrt(t)}.get(s["hair_amount_curve"], t)))
        x0, x1, y0, y1 = round(c * cw), round((c + 1) * cw), round(r * ch), round((r + 1) * ch); rnd = fc_strands.mulberry32(seed + idx + 77); st = []
        for P, rad in fc_strands.strands(seed + idx, k, x1 - x0, y1 - y0, s):
            st.append({"p": P.round(3).tolist(), "r": rad.round(3).tolist(), "c": gradient(s, np.linspace(0, 1, len(P)), rnd).round(4).tolist()})
        cards.append({"cell": [x0, y0, x1 - x0, y1 - y0], "strands": st}); print("card %2d: %3d strands" % (idx + 1, k), flush=True)
    return W, cols, rows, cards


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--tag", default="fibers"); ap.add_argument("--preset"); ap.add_argument("--blonde", action="store_true")
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--samples", type=int, default=32); ap.add_argument("--lighting", default="soft", choices=["soft", "flat"]); ap.add_argument("--blend"); ap.add_argument("--set", nargs="*", default=[])
    a = ap.parse_args(); over = {k: json.loads(v) for k, v in (x.split("=", 1) for x in a.set)}; s = fc_params.load(a.preset, **{**(fc_params.BLONDE if a.blonde and not a.preset else {}), **over})
    W, cols, rows, cards = job_cards(s, a.seed); out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    job = {"size": W, "tag": a.tag, "out": str(out), "lighting": a.lighting, "samples": a.samples, "glossiness": s["glossiness"], "sheen": s["sheen"], "tools": str(T.parent), "blend": a.blend, "cards": cards}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(job, f); jp = f.name
    r = subprocess.run([BLENDER, "-b", "--factory-startup", "--python", str(T.parent / "general" / "blender_once.py"), "--", str(T / "fc_blender.py")], env={**os.environ, "FC_JOB": jp}, capture_output=True, text=True)
    os.unlink(jp)
    if "RESULT_JSON" not in r.stdout:
        sys.exit((r.stdout + r.stderr)[-2500:])
    print([l for l in r.stdout.splitlines() if l.startswith(("device", "RESULT_JSON"))])
    n = Image.open(out / (a.tag + "_normal.png")).convert("RGBA"); arr = np.array(n); arr[arr[..., 3] == 0, :3] = (128, 128, 255); Image.fromarray(arr).save(out / (a.tag + "_normal.png"))
    c = Image.open(out / (a.tag + "_color.png")).convert("RGBA"); bg = Image.new("RGBA", c.size, (40, 40, 40, 255)); bg.alpha_composite(c); pv = np.array(bg)
    for i in range(1, cols):
        pv[:, round(i * W / cols) - 1] = 100
    for i in range(1, rows):
        pv[round(i * W / rows) - 1] = 100
    Image.fromarray(pv).convert("RGB").resize((1024, 1024), Image.LANCZOS).save(out / (a.tag + "_preview.png")); (out / (a.tag + "_preset.json")).write_text(json.dumps(s, indent=1)); print("wrote", out)


if __name__ == "__main__":
    main()
