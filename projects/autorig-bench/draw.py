"""Auto-rig skeleton (red) over the reference one (green) on each benchmark mesh, front and side views:
output/autorig_bench.png (cases in columns).  python projects/autorig-bench/draw.py [out.png]"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
PANEL, BG, SKIN = 440, (32, 33, 38), (150, 152, 160)
GT, AUTO = (90, 220, 110), (240, 70, 60)


def panel(case, r, view):
    m = np.load(os.path.join(OUT, case + "_mesh.npz")); V, F = m["V"], m["F"]
    u = (lambda p: p[..., 0] - r["x0"]) if view == "front" else (lambda p: p[..., 1])
    s = PANEL * 0.9 / max(r["H"], np.ptp(u(V)))
    ctr = (u(V).max() + u(V).min()) / 2
    to = lambda p: np.stack([(u(p) - ctr) * s + PANEL / 2, PANEL * 0.95 - (p[..., 2] - r["z0"]) * s], -1)
    img = Image.new("RGB", (PANEL, PANEL), BG); d = ImageDraw.Draw(img)
    for t in to(V[F]):
        d.polygon([tuple(q) for q in t], fill=SKIN)
    for key, col, w in (("gt", GT, 4), ("J", AUTO, 2)):
        P = {k: to(np.array(v)) for k, v in r[key].items()}
        for n, p in r["bones"]:
            if n in P and p in P:
                d.line([tuple(P[p]), tuple(P[n])], fill=col, width=w)
        for q in P.values():
            d.ellipse([q[0] - w, q[1] - w, q[0] + w, q[1] + w], fill=col)
    if view == "front":
        mean = np.mean(list(r["err"].values()))
        d.text((8, 8), "%s  mean error %.1f%% H" % (case, mean), fill=(255, 255, 255))
    return img


def main(path):
    R = json.load(open(os.path.join(OUT, "eval.json")))
    sheet = Image.new("RGB", (PANEL * len(R), PANEL * 2), BG)
    for c, (case, r) in enumerate(R.items()):
        for v, view in enumerate(("front", "side")):
            sheet.paste(panel(case, r, view), (c * PANEL, v * PANEL))
    sheet.save(path); print(path)


main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "autorig_bench.png"))
