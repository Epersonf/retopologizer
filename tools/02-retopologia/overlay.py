"""Compose reference render and result render into one image: red = reference only,
cyan = result only, grey = both. Usage: python overlay.py ref.png new.png out.png"""
import sys
from PIL import Image
import numpy as np

def mask(p):
    a = np.asarray(Image.open(p).convert("RGB")).astype(int)
    bg = a[0, 0]
    return (np.abs(a - bg).sum(2) > 18)

r, n = mask(sys.argv[1]), mask(sys.argv[2])
out = np.full(r.shape + (3,), 30, np.uint8)
out[r & n] = (150, 150, 150)
out[r & ~n] = (230, 60, 60)
out[~r & n] = (60, 200, 230)
Image.fromarray(out).save(sys.argv[3])
print("ref-only %.2f%%  new-only %.2f%%  of ref area" % (
    100 * (r & ~n).sum() / r.sum(), 100 * (n & ~r).sum() / r.sum()))
