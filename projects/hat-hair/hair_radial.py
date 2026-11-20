"""An object seen from outside as a height field about the vertical axis (worker; "HairFull" loaded): for NT azimuths t (from +y toward +x, so the
front, -y, is t = 180 deg) and every height z, a horizontal ray comes from 0.7 m to the axis A and the first hit gives the radius r(t, z) and the
normal (kept as its tangential and vertical parts); NaN where the object is absent (the face window, gaps) or the first hit is a face of material
"headfill" (the stand-in for the head). It is what the eye sees from outside: for the reference its ridges are the locks and its valleys the gaps.
Writes draft/<OUT>.npz (R[NT, NZ], NT_, NZ_, zs, A): hair_ridges.py, hair_base.py and hair_unwrap.py read the reference's (OUT = hair_radial),
hair_diff.py compares it with the low poly's (OBJ = "LowPoly", OUT = hair_radial_low). NT, DZ, OBJ, OUT may be set before running.
  python tools/general/blender_rpc.py --port 9877 projects/hat-hair/hair_radial.py"""
import bpy, math
import numpy as np
from mathutils import Vector
G = globals(); NT = G.get("NT", 360); DZ = G.get("DZ", 0.005); OBJ = G.get("OBJ", "HairFull"); OUT = G.get("OUT", "hair_radial"); ZS = np.arange(0.01, 0.60, DZ); A = Vector((-0.185, -0.03, 0.0))
exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\03-qa\qa_fit.py").read())                        # _world_tree
ob = bpy.data.objects[OBJ]; tree, _, tri2poly = _world_tree(ob)
fill = {i for i, m in enumerate(ob.data.materials) if m and m.name == "headfill"}; ign = {p.index for p in ob.data.polygons if p.material_index in fill}
R, NTG, NZ = (np.full((NT, len(ZS)), np.nan) for _ in range(3))
for i in range(NT):
    t = 2 * math.pi * i / NT; d = Vector((math.sin(t), math.cos(t), 0)); tg = Vector((math.cos(t), -math.sin(t), 0))
    for j, z in enumerate(ZS):
        h = tree.ray_cast(A + Vector((0, 0, z)) + d * 0.7, -d, 0.7)
        if h[0] is not None and tri2poly[h[2]] not in ign:
            n = h[1] if h[1].dot(d) > 0 else -h[1]                 # the normal that faces the viewer outside
            R[i, j], NTG[i, j], NZ[i, j] = 0.7 - h[3], n.dot(tg), n.z
np.savez(r"C:\Users\epers\Desktop\retopologizer\projects\hat-hair\draft\%s.npz" % OUT, R=R, NT_=NTG, NZ_=NZ, zs=ZS, A=np.array(A))
result = {"obj": OBJ, "NT": NT, "rows": len(ZS), "hit": float(np.isfinite(R).mean()), "r_min": float(np.nanmin(R)), "r_max": float(np.nanmax(R))}
