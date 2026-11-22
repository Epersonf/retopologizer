r"""Fills a hole that is cut by the mirror plane (x = 0) in a ONE-SIDED mesh: the hole of the half mesh is a chain of open border vertices plus the stretch of
the plane between its two axis end vertices, where no vertices exist yet. `fill_half` puts k vertices on that stretch (x = 0, snapped on the ref) and fills the
closed loop with `fill_loop`. After the Mirror modifier the hole is closed and symmetric.
Inside Blender:  exec(open(".../hole_fill.py").read()); exec(open(".../seam_close.py").read())
  runs = axis_runs(bm)                                  # [("AXIS"|"OPEN", [verts])] along the single border loop
  fill_half(bm, open_run, axis_a, axis_b, ref)          # axis_a / axis_b: the axis vertices joined to open_run[0] / open_run[-1]
Quads only; the old vertices never move."""
import bmesh
from mathutils import Vector


def pinches(bm):
    """Vertices where a boundary touches itself (more than 2 boundary edges): fix these by hand before filling."""
    return [v.index for v in bm.verts if sum(x.is_boundary for x in v.link_edges) > 2]


def axis_runs(bm, loop=None, tol=0.0015):
    loop = loop or max(boundary_loops(bm), key=len); runs = []
    for v in loop:
        ax = abs(v.co.x) < tol
        if not runs or runs[-1][0] != ax: runs.append((ax, []))
        runs[-1][1].append(v)
    if len(runs) > 1 and runs[0][0] == runs[-1][0]: runs[0][1][:0] = runs.pop()[1]   # the loop starts in the middle of a run
    return [("AXIS" if a else "OPEN", vs) for a, vs in runs]


def fill_half(bm, chain, a_first, a_last, ref=None, k=None):
    """chain: open border vertices in loop order; a_first / a_last: axis vertices joined to chain[0] / chain[-1]. k: vertices put on the plane (default: about as many
    as the chain so the grid cells come out square; adjusted for parity)."""
    k = len(chain) - 2 if k is None else k
    if (len(chain) + k + 2) % 2: k += 1
    pts = []
    for i in range(1, k + 1):
        p = a_last.co.lerp(a_first.co, i / (k + 1)); p = Vector((0.0, p.y, p.z))
        if ref is not None:
            q = Vector(ref.snap(p, None, 0.05)); p = Vector((0.0, q.y, q.z))
        pts.append(bm.verts.new(p))
    loop = list(chain) + [a_last] + pts + [a_first]        # chain[0] .. chain[-1], then the plane back to chain[0]
    bm.verts.index_update(); bm.edges.index_update()
    for a, b in zip(loop, loop[1:] + loop[:1]):
        if bm.edges.get((a, b)) is None: bm.edges.new((a, b))   # the new plane edges
    return fill_loop(bm, loop, ref)
