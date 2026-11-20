"""Walk along a tube of the body (finger, arm, tail) from a point inside it: every station cuts the mesh with the
plane across the walking direction, keeps the loop around the current centre and moves to its centroid; the direction
follows the centres. The walk stops where the tube flows into something bigger (stop(area) true) or leaves the mesh."""
import numpy as np
from .sections import section, pick


def walk(M, start, direction, step, max_len, stop=None, near=None, follow=0.5):
    """[(centre, direction, loop, arc length)] from `start` toward `direction`; each step the direction turns
    `follow` of the way toward the last centre-to-centre move (low: steadier through a hand's jumping centres)."""
    c, d = np.asarray(start, float), np.asarray(direction, float)
    d = d / np.linalg.norm(d); out, s = [], 0.0
    near = near or step * 4
    while s <= max_len:
        L = pick(section(M, c, d), c, near)
        if L is None:
            break
        m = L.c - d * np.dot(L.c - c, d)              # stay on this plane
        if stop is not None and out and stop(L, out):
            break
        if out:
            g = m - out[-1][0]
            if np.linalg.norm(g) > 1e-9:
                d = d * (1 - follow) + g / np.linalg.norm(g) * follow; d = d / np.linalg.norm(d)
        out.append((m, d.copy(), L, s))
        c = m + d * step; s += step
    return out


def bigger_than(factor, base=None):
    """Stop rule: the loop area jumps over factor x the median area seen so far (or a fixed base area)."""
    def rule(L, hist):
        ref = base if base is not None else float(np.median([h[2].area for h in hist]))
        return L.area > factor * ref
    return rule


def jump(factor, warm=6):
    """Stop rule: the loop area jumps over factor x the previous one (the tube reached something bigger; a tube that
    thickens slowly, like a tail toward its root, does not stop). The first `warm` stations are the tip's cap."""
    def rule(L, hist):
        return len(hist) >= warm and L.area > factor * hist[-1][2].area
    return rule


def at_length(path, s):
    """Centre of the walk at arc length s (interpolated)."""
    S = np.array([p[3] for p in path])
    i = int(np.clip(np.searchsorted(S, s), 1, len(S) - 1))
    f = (s - S[i - 1]) / max(S[i] - S[i - 1], 1e-12)
    return path[i - 1][0] * (1 - f) + path[i][0] * f
