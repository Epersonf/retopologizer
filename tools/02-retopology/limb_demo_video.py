"""Animated demo of the ring technique on an arm: ring -> shrink -> second ring -> shrink -> bridge -> all the rings.
  python tools/02-retopology/limb_demo_video.py [data.json] [out.mp4]       (data from limb_demo_data.py; needs matplotlib + ffmpeg)
Pure numpy/matplotlib drawing of the json (no Blender at render time), so it is fast and repeatable."""
import json, math, os, subprocess, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

DATA = sys.argv[1] if len(sys.argv) > 1 else "projects/limb-demo/data.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "projects/limb-demo/limb_rings.mp4"
FPS, W, H = 24, 1280, 720
YAW0, YAW1 = float(os.environ.get('YAW0', 65)), float(os.environ.get('YAW1', 15))   # degrees of camera azimuth sweep
D = json.load(open(DATA)); V = np.array(D["ref_v"]); RF = D["ref_f"]; RG = D["rings"]; FC = D["faces"]; N = len(RG[0]["end"])
END = [np.array(r["end"]) for r in RG]; C = [np.array(r["c"]) for r in RG]
START = [C[i] + (END[i] - C[i]) / np.linalg.norm(END[i] - C[i], axis=1)[:, None] * RG[i]["R"] for i in range(len(RG))]
PIV = np.mean(np.concatenate(END), axis=0)
PT, PR = np.array(D["profile"]["t"]), np.array(D["profile"]["r"]) * 1000; RAW = np.array(D["profile"]["raw"]) * 1000; EXT = D["extrema"]; ST = D["stations"]; T0 = 4.5   # profile intro
ease = lambda t: 3 * t * t - 2 * t ** 3
clamp = lambda t: min(1.0, max(0.0, t))


def proj(P, yaw, pitch=0.35):
    q = np.asarray(P, float) - PIV; c, s = math.cos(yaw), math.sin(yaw)
    x, y, z = q[..., 0] * c - q[..., 1] * s, q[..., 0] * s + q[..., 1] * c, q[..., 2]
    return np.stack([x, z * math.cos(pitch) + y * math.sin(pitch)], -1), y * math.cos(pitch) - z * math.sin(pitch)


def timeline():
    """[(ring, t_appear, t_shrink_start, t_shrink_end, t_bridge_end)] and the end time of the build."""
    t, out = T0, []
    for i in range(len(RG)):
        a, s, b = (1.4, 1.6, 0) if i == 0 else (0.9, 1.1, 1.0) if i == 1 else (0.12, 0.3, 0.25)
        out.append((i, t, t + a, t + a + s, t + a + s + b)); t += a + s + b
    return out, t


TL, T_BUILD = timeline(); T_END = T_BUILD + 4.5


def caption(t):
    if t < 2.5: return "0. Perfil: a área da seção ao longo do braço"
    if t < T0: return "Máximos e mínimos (a derivada troca de sinal): ali entra um anel"
    if t < TL[0][2]: return "1. Ring: um círculo de %d pontos ao redor do braço" % N
    if t < TL[0][3]: return "2. Shrink: cada ponto encolhe até encostar na superfície"
    if t < TL[1][3]: return "3. Outro ring, em outra região do braço"
    if t < TL[1][4]: return "4. Bridge: quads ligam os dois anéis"
    if t < T_BUILD: return "Um anel em cada máximo, mínimo e junta"
    K = D["check"]; return "Resultado: %d anéis, %d quads | desvio máx. %.1f° | avanço mín. +%.1f mm | %d faces invertidas" % (len(RG), len(FC), K["axis_dev_deg"], K["min_rung_mm"], K["flipped_faces"])


def inset(t, ax2):
    ax2.clear(); ax2.set_facecolor("#1c2027"); [s.set_color("#444b57") for s in ax2.spines.values()]; ax2.tick_params(colors="#8b93a1", labelsize=8)
    k = ease(clamp(t / 2.0)); m = max(2, int(len(PT) * k)); ax2.plot(PT[:m], RAW[:m], color="#555d6b", lw=1); ax2.plot(PT[:m], PR[:m], color="white", lw=1.6)
    ax2.set_xlim(0, 1); ax2.set_ylim(RAW.min() - 3, RAW.max() + 6); ax2.set_title("raio equivalente da seção (mm) ao longo do braço", color="#8b93a1", fontsize=9)
    if t >= 2.0:
        for x, kind, r in EXT: ax2.plot(x, r * 1000, "^" if kind == "max" else "v", color="#f87171" if kind == "max" else "#60a5fa", ms=9)
    for (i, ta, ts, te, tb) in TL:
        if t >= ta: ax2.axvline(ST[i], color="#2dd4a0" if t >= te else "#facc15", lw=1.2, alpha=0.8)


def frame(t, ax, ax2):
    yaw = math.radians(YAW0 + (YAW1 - YAW0) * t / T_END); ax.clear(); ax.set_axis_off()
    fade = 1 - 0.8 * ease(clamp((t - T_BUILD) / 1.0))                       # the reference fades out at the end
    P, dep = proj(V, yaw); polys = [(np.mean([dep[k] for k in f]), [P[k] for k in f]) for f in RF]
    polys.sort(key=lambda p: -p[0])
    ax.add_collection(PolyCollection([p[1] for p in polys], facecolors=(0.72, 0.74, 0.78, 0.34 * fade), edgecolors=(0.5, 0.52, 0.56, 0.12 * fade), linewidths=0.3))
    for i, ta, ts, te, tb in TL:
        if t < ta: continue
        k = ease(clamp((t - ts) / (te - ts))); pts = START[i] * (1 - k) + END[i] * k
        if i and t >= ts:                                                   # bridge faces from ring i-1 to ring i
            g = ease(clamp((t - te) / max(tb - te, 1e-6)))
            F = [f for f in FC if max(f) // N == i and min(f) // N == i - 1]
            if g > 0 and F:
                S, _ = proj(np.concatenate([END[i - 1], END[i]]) * 0 + np.concatenate([END[i - 1], pts]), yaw)
                loc = {j: S[j - (i - 1) * N] for j in range((i - 1) * N, (i + 1) * N)}
                ax.add_collection(PolyCollection([[loc[v] for v in f] for f in F], facecolors=(0.95, 0.55, 0.15, 0.55 * g), edgecolors=(0.4, 0.2, 0.0, 0.9 * g), linewidths=0.8))
        S, _ = proj(pts, yaw); done = k >= 1
        col = (0.1, 0.75, 0.45) if done else (1.0, 0.8, 0.1)
        ax.plot(*np.append(S, S[:1], axis=0).T, color=col, lw=2.2); ax.scatter(*S.T, color=col, s=26, zorder=5)
        if i == 0 and k < 1 and t >= ts:                                    # radial guides during the shrink
            Sc, _ = proj(C[0], yaw); [ax.plot([Sc[0], p[0]], [Sc[1], p[1]], color=(1, 1, 1, 0.25), lw=0.6) for p in S]
    inset(t, ax2)
    ax.text(0.5, 0.06, caption(t), transform=ax.transAxes, ha="center", color="white", fontsize=16)


def main():
    used = sorted({k for f in RF for k in f}); P, _ = proj(V[used], math.radians((YAW0 + YAW1) / 2)); lo, hi = P.min(0), P.max(0); pad = 0.06
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor="#14171c"); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor("#14171c"); ax2 = fig.add_axes([0.58, 0.64, 0.38, 0.30])
    ctr, half = (lo + hi) / 2, max((hi - lo)[0] / 2 * 0.9 + pad, (hi - lo)[1] / 2 * 1.6 + pad)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", OUT]
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True); pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(int(T_END * FPS)):
        frame(f / FPS, ax, ax2); ax.set_xlim(ctr[0] - half * W / H, ctr[0] + half * W / H); ax.set_ylim(ctr[1] - half, ctr[1] + half)
        fig.canvas.draw(); pipe.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
    pipe.stdin.close(); pipe.wait(); print("wrote", OUT, "%.1fs" % T_END)


main()
