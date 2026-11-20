"""Clean-up of the artist's start mesh: the nostril floor was a hexagon with two pairs of near-double vertices
(152/156 at 0.4 mm, 147/145 at 2.2 mm). Merging each pair turns it into a quad (+ 2 triangles on the nostril rim).
58 (border notch of the neckline, only 2 edges) is dissolved: it would become a valence-2 vertex (doublet) once the
shoulder is filled; its quad becomes the triangle 49-42-59."""
import bmesh

_a, _b, _c, _d = T.old(152, 156, 145, 147)
for keep, drop in ((_a, _b), (_c, _d)):
    keep.co = (keep.co + drop.co) / 2
    bmesh.ops.pointmerge(T.bm, verts=[keep, drop], merge_co=keep.co)
T.bm.verts.ensure_lookup_table()
bmesh.ops.dissolve_verts(T.bm, verts=T.old(58))
T.bm.verts.ensure_lookup_table()
