"""Tail chain: walked back from the tail's tip to where it flows into the body. Tail1 sits at the root, the next
joints are evenly spaced along the walk and Tail_End is the tip."""
import numpy as np
from . import tube as T

BONES = 5


def tail(B, v, hips, n=BONES):
    """{"Tail1".."Tail<n>", "Tail_End": np.array} for the tail whose tip is vertex v."""
    M, H = B.M, B.H; tip = M.V[v]
    d = (hips - tip) / np.linalg.norm(hips - tip)
    path = T.walk(M, tip + d * 0.005 * H, d, 0.004 * H, 1.2 * H, stop=T.jump(1.6))
    S = path[-1][3]
    names = ["Tail%d" % (i + 1) for i in range(n)] + ["Tail_End"]
    return {name: T.at_length(path, S * (1 - i / n)) if i < n else tip for i, name in enumerate(names)}
