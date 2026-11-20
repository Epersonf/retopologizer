"""Draw vertex indices on a wire_overlay PNG (normal python + PIL), so a script can refer to vertices by index.
  python tools/label_png.py renders/x.png [out.png]     (reads renders/x_labels.json written by wire_overlay)"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else src[:-4] + "_lab.png"
im = Image.open(src).convert("RGB"); d = ImageDraw.Draw(im)
try:
    font = ImageFont.truetype("arial.ttf", 11)
except OSError:
    font = ImageFont.load_default()
for i, u, v in json.load(open(src[:-4] + "_labels.json")):
    d.ellipse([u - 2, v - 2, u + 2, v + 2], fill=(255, 255, 0))
    d.text((u + 3, v - 12), str(i), fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
im.save(dst)
print(dst)
