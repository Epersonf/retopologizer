"""Before/after image: two renders side by side, same height, with a label on each (the user asks for this at the end of a
texture or retouch round: "mostre antes e depois"). Pure Python (PIL).
  python tools/05-delivery/before_after.py before.png after.png out.png [--labels Antes Depois] [--height 1100]
Use the SAME view for both (`render_previews` views); a different camera makes the comparison useless."""
import argparse
from PIL import Image, ImageDraw, ImageFont


def before_after(a, b, out, labels=("Before", "After"), height=1100, gap=24):
    ims = []
    for p in (a, b):
        im = Image.open(p).convert("RGB")
        ims.append(im.resize((round(im.width * height / im.height), height), Image.LANCZOS))
    W = sum(i.width for i in ims) + gap
    canvas = Image.new("RGB", (W, height), (20, 20, 24)); x = 0
    try: font = ImageFont.truetype("arial.ttf", max(24, height // 28))
    except OSError: font = ImageFont.load_default()
    d = ImageDraw.Draw(canvas)
    for im, text in zip(ims, labels):
        canvas.paste(im, (x, 0)); d.text((x + 18, 14), text, fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0)); x += im.width + gap
    canvas.save(out)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("before"); p.add_argument("after"); p.add_argument("out")
    p.add_argument("--labels", nargs=2, default=["Before", "After"]); p.add_argument("--height", type=int, default=1100)
    r = p.parse_args(); print(before_after(r.before, r.after, r.out, tuple(r.labels), r.height))
