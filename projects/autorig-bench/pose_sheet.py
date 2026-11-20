"""One image from the pose test renders: a row per case (rest front, pose front, pose 3/4).
  python projects/autorig-bench/pose_sheet.py"""
import os
from PIL import Image, ImageDraw
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "pose")
cases = [c for c in ("male", "female", "saci", "cuca") if os.path.exists(os.path.join(D, c + "_pose_front.png"))]
cols = ("rest_front", "pose_front", "pose_persp")
tiles = [[Image.open(os.path.join(D, "%s_%s.png" % (c, k))).convert("RGB") for k in cols] for c in cases]
w, h = tiles[0][0].size
sheet = Image.new("RGB", (w * len(cols), h * len(cases)), (40, 40, 44))
for r, row in enumerate(tiles):
    for c, im in enumerate(row):
        sheet.paste(im, (c * w, r * h))
    ImageDraw.Draw(sheet).text((8, r * h + 8), cases[r], fill=(20, 20, 20))
out = os.path.join(os.path.dirname(D), "pose_test.png"); sheet.save(out); print(out)
