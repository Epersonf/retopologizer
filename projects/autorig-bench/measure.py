"""Raw landmarks of the benchmark cases next to their reference joints (heights as fractions of H above the feet), to
calibrate the joint rules of tools/06-rig/autorig.  python tools/general/blender_rpc.py --port 9877 projects/autorig-bench/measure.py"""
import sys, importlib
import numpy as np
ROOT = r"C:\Users\epers\Desktop\retopologizer"
sys.path.insert(0, ROOT + r"\tools\06-rig")
import autorig.sections as S, autorig.geodesic as G, autorig.tube as T, autorig.load as LD
for _m in (S, G, T, LD):
    importlib.reload(_m)
IN = ROOT + r"\projects\autorig-bench\input"
CASES = globals().get("CASES") or ["male", "female", "saci", "cuca"]
out = {}
for case in CASES:
    o, gt = LD.bench_case(IN, case)
    M = LD.mesh_of([o]); z0, H = M.lo[2], M.hi[2] - M.lo[2]; x0 = (M.lo[0] + M.hi[0]) / 2
    zh = lambda z: round(float((z - z0) / H), 3)
    rel = lambda p: [round(float((p[0] - x0) / H), 3), round(float(p[1] / H), 3), zh(p[2])]
    prof = [(z, S.section(M, np.array([x0, 0, z]), (0, 0, 1))) for z in np.linspace(z0, z0 + H, 201)[1:-1]]
    rows = []
    for z, loops in prof[::5]:
        rows.append([zh(z)] + [[rel(L.c)[0], rel(L.c)[1], round(L.area / H ** 2, 4), round(L.extent((1, 0, 0)) / H, 3),
                                round(L.extent((0, 1, 0)) / H, 3)] for L in sorted(loops, key=lambda L: -L.area)[:4]])
    tipL = M.V[np.argmax(M.V[:, 0])]
    walk = T.walk(M, tipL + np.array([-0.01 * H, 0, 0]), (-1, 0, 0), 0.006 * H, 0.6 * H,
                  stop=lambda L, h: L.size > 0.22 * H)
    arm = [[round(s / H, 3)] + rel(c) + [round(L.area / H ** 2, 5), round(L.size / H, 3)] for c, d, L, s in walk[::3]]
    ctr = prof[int(0.6 * len(prof))][1]
    c0 = min(ctr, key=lambda L: abs(L.c[0] - x0)).c
    src = int(np.argmin(np.linalg.norm(M.V - c0, axis=1)))
    D = G.dijkstra(M, [src])
    ext = [rel(M.V[v]) + [round(min(p, 9) / H, 3)] for v, p in G.peaks(M, D, 0.06 * H)]
    keys = ["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "HeadTop_End", "LeftShoulder", "LeftArm", "LeftForeArm",
            "LeftHand", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "LeftToe_End", "RightUpLeg", "RightFoot",
            "LeftHandThumb1", "LeftHandThumb2", "LeftHandThumb4", "LeftHandIndex1", "LeftHandIndex2", "LeftHandIndex3",
            "LeftHandIndex4", "LeftHandMiddle1", "LeftHandMiddle4", "Tail1", "Tail5", "Tail_End"]
    out[case] = {"H": round(float(H), 3), "x0": round(float(x0), 3), "gt": {k: rel(gt[k]) for k in keys if k in gt},
                 "rows": rows, "arm": arm, "ext": ext}
result = out
