"""Shows the limb_demo scheme LIVE in the artist's Blender: ring -> shrink onto the surface -> next ring -> bridge into quads.
Replaces the per-case live_setup/live_leg/live_toes scripts. Runs inside the user's Blender (MCP 9876): it only ADDS a collection
(default "Live") and never touches their objects, camera or light.
  python tools/general/blender_rpc.py -c 'exec(open(r"<repo>/tools/general/live_rings.py").read()); setup(r"<ref.glb>")'
  python tools/general/blender_rpc.py -c 'exec(open(r"<repo>/tools/general/live_rings.py").read()); play(r"<data.json>", speed=1)'
data.json (worker side, from the build): {"rings": [{"c": [x,y,z], "R": radius_of_start_circle, "end": [[x,y,z], ...]}, ...],
  "faces": [[a,b,c,d], ...], "ring_idx": [[vertex ids of ring 0], ...]  (optional: default consecutive blocks),
  "view": {"loc": [x,y,z], "dist": 0.5}  (optional), "captions": [..4 strings..] (optional)}
`end` = final snapped vertices; each starts on a circle of radius R around c and shrinks to its end."""
import bpy, json, math, time
from mathutils import Vector, Euler

ease = lambda t: 3 * t * t - 2 * t ** 3
clamp = lambda t: min(1.0, max(0.0, t))


def _obj(col, name, rgba, wire):
    for o in [o for o in bpy.data.objects if o.name == name]: bpy.data.objects.remove(o)
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); col.objects.link(o)
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.diffuse_color = rgba
    me.materials.append(m); o.show_in_front = True; o.hide_select = True
    if wire: o.display_type = "WIRE"
    else: o.show_wire = True
    return o


def _collection(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    return col


def setup(glb=None, name="HiPoly", coll="Live"):
    """Puts the reference (imported once from glb, or the object called `name`) in the collection as a translucent ghost."""
    if name not in bpy.data.objects and glb:
        before = set(bpy.data.objects.keys()); bpy.ops.import_scene.gltf(filepath=glb)
        new = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - before if bpy.data.objects[n].type == "MESH"]
        new[0].name = name
    H = bpy.data.objects[name]; col = _collection(coll)
    for c in list(H.users_collection): c.objects.unlink(H)
    col.objects.link(H)
    m = bpy.data.materials.get("live_ref") or bpy.data.materials.new("live_ref"); m.diffuse_color = (0.75, 0.75, 0.78, 0.22)
    H.data.materials.clear(); H.data.materials.append(m); H.show_transparent = True; H.hide_select = True
    return {"tris": len(H.data.polygons)}


def _timeline(n):
    t0, TL = 0.0, []
    for i in range(n):  # primeiro anel devagar, o segundo medio, o resto rapido (a ideia ja foi entendida)
        a, s, b = (1.4, 1.6, 0) if i == 0 else (0.9, 1.1, 1.0) if i == 1 else (0.12, 0.3, 0.25)
        TL.append((t0, t0 + a, t0 + a + s, t0 + a + s + b)); t0 += a + s + b
    return TL, t0 + 5.0


def play(path, speed=1.0, coll="Live"):
    D = json.load(open(path)); RG, FC = D["rings"], D["faces"]; n = len(RG)
    RI = D.get("ring_idx") or [list(range(i * len(RG[0]["end"]), (i + 1) * len(RG[0]["end"]))) for i in range(n)]
    cap = D.get("captions") or ["1. Ring: circulo de pontos ao redor da parte", "2. Shrink: cada ponto encolhe ate a superficie",
                                "3. Outro ring, no proximo maximo/minimo do perfil", "4. Bridge: quads ligam aneis vizinhos"]
    END = [[Vector(p) for p in r["end"]] for r in RG]
    START = [[Vector(r["c"]) + (p - Vector(r["c"])).normalized() * r["R"] for p in e] for r, e in zip(RG, END)]
    TL, T_END = _timeline(n); col = _collection(coll)
    RINGS = _obj(col, "Live_Rings", (1, 0.85, 0.1, 1), True); FACES = _obj(col, "Live_Faces", (1, 0.5, 0.1, 0.6), False)
    area = next((a for w in bpy.context.window_manager.windows for a in w.screen.areas if a.type == "VIEW_3D"), None)
    r3d = area.spaces[0].region_3d if area else None
    v = D.get("view") or {}
    if r3d:
        r3d.view_perspective = "PERSP"; r3d.view_location = v.get("loc", RG[n // 2]["c"]); r3d.view_distance = v.get("dist", 0.5)
    t_start = time.time()

    def caption(t):
        if t < TL[0][1]: return cap[0]
        if t < TL[0][2]: return cap[1]
        if t < TL[1][3]: return cap[2]
        if t < TL[-1][3]: return cap[3]
        return "Resultado: %d aneis, %d quads" % (n, len(FC))

    def tick():
        t = (time.time() - t_start) * speed
        P, E, F, base = [], [], [], {}
        for i in range(n):
            ta, ts, te, tb = TL[i]
            if t < ta: continue
            k = ease(clamp((t - ts) / (te - ts))) if te > ts else 1.0
            base[i] = len(P); P += [tuple(s.lerp(e, k)) for s, e in zip(START[i], END[i])]
            m = len(END[i]); E += [(base[i] + j, base[i] + (j + 1) % m) for j in range(m)]
        shown = {v for i in base for v in RI[i]}
        pos = {v: P[base[i] + j] for i in base for j, v in enumerate(RI[i])}
        keep = [f for f in FC if all(x in shown for x in f) and t >= TL[max(i for i in base if any(x in RI[i] for x in f))][2]]
        order = {v: j for j, v in enumerate(sorted(shown))}
        RINGS.data.clear_geometry(); RINGS.data.from_pydata(P, E, [])
        FACES.data.clear_geometry(); FACES.data.from_pydata([pos[v] for v in sorted(shown)], [], [[order[x] for x in f] for f in keep])
        for w in bpy.context.window_manager.windows: w.workspace.status_text_set(caption(t))
        if r3d:
            yaw = math.radians(65 - 50 * clamp(t / T_END)) + math.radians(75)
            r3d.view_rotation = Euler((math.radians(75), 0, yaw), "XYZ").to_quaternion()
        for w in bpy.context.window_manager.windows[:1]:
            for a in w.screen.areas: a.tag_redraw()
        if t >= T_END:
            for w in bpy.context.window_manager.windows: w.workspace.status_text_set(None)
            return None
        return 1 / 30
    bpy.app.timers.register(tick, first_interval=0.05)
    return {"started": True, "duration_s": round(T_END / speed, 1)}
