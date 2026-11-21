"""Drive TextureCraft through its CLI from plain Python (the MCP server is headless with no file roots: it cannot read the mesh
or write the maps, so the CLI is the way: `docs/04-uv-bake/texturecraft-cli.md`). Pure Python, no Blender.
  import sys; sys.path.insert(0, r"<repo>\\tools\\04-uv-bake"); from texturecraft_cli import *
  S = import_maps(MESH_GLB, maps_dir, "t0.tcraft", prefix="espada")          # mesh + the baked maps as image layers
  add_camera("t0.tcraft", "t0.tcraft", "Guarda", target=(0, 0.37, 0), distance=0.62)          # a saved camera to paint through
  paint("t0.tcraft", "t1.tcraft", camera="Guarda", layer="Retoque", strokes=[Stroke("#b87a22", 3.0, [(385,420),(430,455)])], mirror_w=1280)
  export("t1.tcraft", out_dir)      # -> mesh_<MATERIAL>_{BaseColor,Normal,OcclusionRoughnessMetallic}.png (glTF PBR, dilated)
  render("t1.tcraft", "r.png", size="1280x800", camera="Guarda")            # ALWAYS look at it before trusting the paint
Rules learnt: JSON written by Python (UTF-8, no BOM; PowerShell's BOM breaks `batch`), forward slashes in paths;
`tool.stroke` paints THROUGH the session camera, so `camera.select` first or nothing is painted; `tool.strokeUv` was unreliable
on a mirrored/overlapping UV; turn height/normal OFF in `tool.material` or the stroke flattens the normal map."""
import json, os, subprocess, tempfile
from dataclasses import dataclass

CLI = os.environ.get("TEXTURECRAFT_CLI", r"C:\Program Files\TextureCraft\texturecraft-cli.exe")


@dataclass
class Stroke:
    color: str            # "#rrggbb"
    size: float
    pts: list             # [(x, y)] in viewport pixels of the selected camera
    rough: float = 0.4
    metal: float = 0.0
    hardness: int = 70
    opacity: int = 80


def _p(path): return str(path).replace("\\", "/")


def batch(open_, steps, save=None):
    """One `texturecraft-cli batch`: opens `open_` (mesh or .tcraft), runs the steps, saves to `save`. Returns stdout."""
    doc = {"open": _p(open_), "steps": steps}
    if save: doc["save"] = _p(save)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(doc, f); name = f.name
    try:
        r = subprocess.run([CLI, "batch", name], capture_output=True, text=True, encoding="utf-8")
    finally:
        os.remove(name)
    if r.returncode: raise RuntimeError(r.stderr or r.stdout)
    return r.stdout


def import_maps(mesh, maps_dir, save, prefix):
    """Mesh + `<prefix>_{basecolor,roughness,metallic,normal}.png` as UV image layers; normal and AO also as mesh maps."""
    d = _p(maps_dir)
    steps = [{"id": "resource.import", "params": {"path": f"{d}/{prefix}_{k}.png"}} for k in ("basecolor", "roughness", "metallic", "normal")]
    for ch, k in (("baseColor", "basecolor"), ("roughness", "roughness"), ("metallic", "metallic"), ("normal", "normal")):
        steps.append({"id": "layer.add.image", "params": {"name": f"{prefix}_{k}.png", "channel": ch, "projection": "uv"}})
    steps.append({"id": "textureSet.meshMap.import", "params": {"files": [{"path": f"{d}/{prefix}_normal.png", "map": "normal"},
                                                                           {"path": f"{d}/{prefix}_ao.png", "map": "ambientOcclusion"}]}})
    return batch(mesh, steps, save)


def dense(pts, n=10):
    """Interpolates a polyline so the brush gets a continuous stroke."""
    out = []
    for (a, b), (c, d) in zip(pts, pts[1:]): out += [[a + (c - a) * t / n, b + (d - b) * t / n] for t in range(n)]
    return out + [list(pts[-1])]


def stroke_steps(s, viewport, mirror_w=None):
    """Steps for one stroke; `mirror_w` = viewport width: also paints the mirrored one (x -> w - x) for a symmetric object."""
    out = []
    for mirror in ((False, True) if mirror_w else (False,)):
        pts = [[mirror_w - x, y] if mirror else [x, y] for x, y in s.pts]
        m = lambda **k: {"id": "tool.material", "params": k}
        out += [m(channel="baseColor", color=s.color), m(channel="roughness", value=s.rough), m(channel="metallic", value=s.metal),
                m(channel="height", enabled=False), m(channel="normal", enabled=False),
                {"id": "tool.brush", "params": {"size": s.size, "hardness": s.hardness, "opacity": s.opacity, "backfaceCulling": True}},
                {"id": "tool.stroke", "params": {"points": dense(pts), "viewport": list(viewport)}}]
    return out


def add_camera(open_, save, name, target, distance, yaw=0, pitch=0, fov=40):
    """Saves a named camera in the project (`paint`/`render` use it). Sword guard: yaw 0, pitch 0, distance 0.62, target (0, 0.37, 0)."""
    return batch(open_, [{"id": "camera.set", "params": {"yaw": yaw, "pitch": pitch, "distance": distance, "fov": fov, "target": list(target)}},
                         {"id": "camera.add", "params": {"name": name}}], save)


def paint(open_, save, camera, layer, strokes, viewport=(1280, 800), mirror_w=None):
    """The camera must already exist in the project (`add_camera`)."""
    steps = [{"id": "camera.select", "params": {"name": camera}}, {"id": "layer.add.paint", "params": {"name": layer}},
             {"id": "tool.select", "params": {"tool": "paint"}}]
    for s in strokes: steps += stroke_steps(s, viewport, mirror_w)
    return batch(open_, steps, save)


def export(project, out_dir, preset="glTF PBR Metal Roughness", padding="dilation"):
    os.makedirs(out_dir, exist_ok=True)
    r = subprocess.run([CLI, "export", _p(project), _p(out_dir), "--preset", preset, "--padding", padding], capture_output=True, text=True, encoding="utf-8")
    if r.returncode: raise RuntimeError(r.stderr or r.stdout)
    return sorted(os.listdir(out_dir))


def render(project, png, size="1280x800", camera=None, view="3d"):
    cmd = [CLI, "render", _p(project), _p(png), "--size", size, "--view", view] + (["--camera", camera] if camera else [])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode: raise RuntimeError(r.stderr or r.stdout)
    return png
