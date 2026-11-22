"""Step 3: engraved gold + enamel on the handle, painted straight into the baked atlas (the high-poly bake cannot give a clean handle: our handle is a
set of simple shapes that sit 2-5 cm away from the sculpted original, so rays hit feathers or nothing).
One-shot: ... blender_once.py -- examples/wing/s3_relief.py     Env: BAKED_BLEND (input from step 2; the maps are read and rewritten in output/).
Order of what is written to the texels of the WING_GOLD material: procedural gold (3D value noise, so no seams) darkened in the engraving,
roughness up in the engraving, metallic 1 (0.15 on the enamel), AO from the height, normal map from the height function (texel_paint.height_to_normal).
Each handle shell is found by connectivity (vertices shared by its faces) and labelled by position: arm = longest in X, spine = lowest in Z,
the other four sorted by X = collar, neck, plate, eye."""
import bpy, os, sys, numpy as np
sys.path.insert(0, os.environ.get("WING_EX", "")); from _cfg import *
load_tool("04-uv-bake", "texel_paint.py"); import pattern_cabo as PT
bpy.ops.wm.open_mainfile(filepath=os.environ.get("BAKED_BLEND") or os.path.join(DRAFT, "wing_13_baked.blend")); size = int(os.environ.get("SIZE", 2048))
ob = bpy.data.objects["WING"]; me = ob.data; M = ob.matrix_world
T = texels(ob, "WING_GOLD", size); P = T["P"]
par = {}


def find(a):
    while par.setdefault(a, a) != a:
        par[a] = par[par[a]]; a = par[a]
    return a


gold = [p for p in me.polygons if me.materials[p.material_index].name == "WING_GOLD"]
for p in gold:
    for v in p.vertices[1:]:
        par[find(v)] = find(p.vertices[0])
verts = {}
for p in gold:
    verts.setdefault(find(p.vertices[0]), set()).update(p.vertices)
info = [(k, *(lambda c: (c.min(0), c.max(0)))(np.array([(M @ me.vertices[v].co)[:] for v in vs]))) for k, vs in verts.items()]
lab = {}; arm = max(info, key=lambda i: i[2][0] - i[1][0]); lab[arm[0]] = "arm"; rest = [i for i in info if i[0] != arm[0]]
sp = min(rest, key=lambda i: i[1][2]); lab[sp[0]] = "spine"; rest = [i for i in rest if i[0] != sp[0]]
for nm, i in zip(("collar", "neck", "plate", "eye"), sorted(rest, key=lambda i: i[1][0] + 0.001 * i[2][0])):
    lab[i[0]] = nm
bb = {lab[i[0]]: (i[1], i[2]) for i in info}; ctr = lambda n: (bb[n][0] + bb[n][1]) / 2
uv = lambda u, v: (-0.46 + u / 1000, 0.6 - v / 1000)
ARM = [uv(*p) for p in [(135, 235), (185, 200), (225, 165), (252, 130), (280, 100), (320, 65), (370, 47), (440, 30), (505, 17)]]; ARMH = [x / 2000 for x in [40, 46, 48, 46, 40, 34, 28, 22, 14]]
SP = [uv(*p) for p in [(115, 262), (105, 300), (80, 380), (60, 455)]]; SPH = [x / 2000 for x in [36, 40, 30, 20]]
cc, nc, pc, ec = ctr("collar"), ctr("neck"), ctr("plate"), ctr("eye")
FN = {"collar": lambda P: PT.collar(P, (cc[1], cc[2], 0.048, bb["collar"][0][0], bb["collar"][1][0])), "neck": lambda P: PT.neck(P, (nc[1], nc[2], 0.032, bb["neck"][0][0], bb["neck"][1][0])),
      "plate": lambda P: PT.plate(P, (pc[0], pc[2], 0.05)), "eye": lambda P: PT.eye(P, (ec[0], ec[2], 0.018)), "arm": lambda P: PT.bar(P, ARM, ARMH), "spine": lambda P: PT.bar(P, SP, SPH)}
face_lab = {i: lab[find(me.polygons[i].vertices[0])] for i in set(T["face"])}; L = np.array([face_lab[i] for i in T["face"]])


h = np.ones(len(P)); En = np.zeros(len(P))     # (height, enamel) per texel, from the part each texel belongs to
for n, fn in FN.items():
    m = L == n; h[m], En[m] = fn(P[m])
dT = np.zeros(len(P)); dB = np.zeros(len(P)); eps = 0.0005
for n, fn in FN.items():
    m = L == n
    dT[m] = (fn(P[m] + eps * T["T"][m])[0] - fn(P[m] - eps * T["T"][m])[0]) / (2 * eps); dB[m] = (fn(P[m] + eps * T["B"][m])[0] - fn(P[m] - eps * T["B"][m])[0]) / (2 * eps)
nx, ny = -0.0004 * dT, -0.0004 * dB; ln = np.sqrt(nx ** 2 + ny ** 2 + 1); nrm = np.stack([nx / ln, ny / ln, 1 / ln], 1) * 0.5 + 0.5
rng = np.random.default_rng(7)


def fbm(p, octaves=5, base=40.0):
    t = np.zeros(len(p)); a = 1.0; tot = 0
    for o in range(octaves):
        d = rng.normal(size=(3, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True); ph = rng.uniform(0, 6.28, 3)
        t += a * np.sin(p @ d.T * base * 2 ** o + ph).sum(1) / 3; tot += a; a *= 0.5
    return 0.5 + 0.5 * t / tot


n1, n2 = fbm(P, 5, 35.0), fbm(P, 3, 120.0); t = np.clip(0.6 + 0.8 * (n1 - 0.5) + 0.3 * (n2 - 0.5), 0, 1)
dark, light = np.array([0.60, 0.40, 0.10]), np.array([0.98, 0.80, 0.36]); col = (dark + (light - dark) * t[:, None]) * (0.45 + 0.55 * h)[:, None]
col = col * (1 - En[:, None]) + np.array([0.93, 0.93, 0.88]) * En[:, None]
rough = np.clip(0.2 + 0.2 * (n2 - 0.5) + 0.45 * (1 - h), 0.1, 0.8); rough = rough * (1 - En) + 0.3 * En
for name, vals in (("basecolor", col), ("roughness", rough), ("metallic", np.clip(1 - En * 0.85, 0, 1)), ("normal", nrm), ("ao", 0.7 + 0.3 * h)):
    write_map(os.path.join(OUT, f"wing_{name}.png"), T, vals, size, blocked=T["other"])
result = {"labels": {k: int((L == k).sum()) for k in set(L)}, "enamel_texels": int((En > 0.5).sum())}
