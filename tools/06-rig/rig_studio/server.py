"""Local server of the rig studio (Mixamo-style auto-rigger page): python tools/06-rig/rig_studio/server.py [--port 8765] [--model file.fbx] [--once]
POST /prep?id=&name=&yaw=&flip=  (body = the model file, empty = reuse the upload) -> preview.glb of the oriented model
POST /done {id}  -> copies rigged.fbx/.glb to done/ and, with --once, stops the server (the caller waiting on it is told)
POST /rig  {id, markers|null, lod, symmetry}                                           -> rigged.glb/.fbx + QA"""
import argparse, json, os, re, shutil, subprocess, threading, sys, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__)); RIG = os.path.dirname(HERE)
WORK = os.path.join(HERE, "work")
EXE = os.environ.get("BLENDER_EXE", r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe")
ONCE = False
START = None                                        # --model: file the page loads by itself
TYPES = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".glb": "model/gltf-binary", ".fbx": "application/octet-stream"}


def blender(script, *args):
    r = subprocess.run([EXE, "-b", "--factory-startup", "--python", script, "--", *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def to_blender(p):                                  # three.js (Y up, faces +Z) -> Blender (Z up, faces -Y)
    return [p[0], -p[2], p[1]]


def prep(q, body):
    wid = q.get("id", [""])[0] or uuid.uuid4().hex[:8]; d = os.path.join(WORK, wid); os.makedirs(d, exist_ok=True)
    if body:
        for f in os.listdir(d):
            if f.startswith("model."): os.remove(os.path.join(d, f))
        ext = os.path.splitext(q.get("name", ["m.fbx"])[0])[1].lower()
        open(os.path.join(d, "model" + ext), "wb").write(body)
    model = next(f for f in os.listdir(d) if f.startswith("model."))
    code, out = blender(os.path.join(HERE, "prep.py"), os.path.join(d, model), d, q["yaw"][0], q["flip"][0])
    return {"ok": "PREP_OK" in out, "id": wid, "glb": "/work/%s/preview.glb?%d" % (wid, time.time()), "log": out[-600:]}


def done(req):
    d = os.path.join(WORK, re.sub(r"\W", "", req["id"])); out = os.path.join(HERE, "done"); os.makedirs(out, exist_ok=True)
    for f in ("rigged.fbx", "rigged.glb"):
        shutil.copy(os.path.join(d, f), os.path.join(out, f))
    print("STUDIO_DONE " + os.path.join(out, "rigged.fbx"), flush=True)
    return {"ok": True}


def rig(req):
    d = os.path.join(WORK, re.sub(r"\W", "", req["id"])); m = req.get("markers")
    args = [os.path.join(d, "norm.blend"), os.path.join(d, "rigged.fbx"), "--glb", os.path.join(d, "rigged.glb"), "--front=-Y"]
    if m:
        json.dump({k: to_blender(v) for k, v in m.items()}, open(os.path.join(d, "markers.json"), "w"))
        args += ["--markers", os.path.join(d, "markers.json")]
    if req.get("lod") == "nofingers": args.append("--no-fingers")
    if not req.get("symmetry", True): args.append("--asym")
    code, out = blender(os.path.join(RIG, "autorig", "cli.py"), *args)
    qa = next((l[12:] for l in out.splitlines() if l.startswith("AUTORIG_QA: ")), None)
    return {"ok": qa is not None, "glb": "/work/%s/rigged.glb?%d" % (req["id"], time.time()), "fbx": "/work/%s/rigged.fbx" % req["id"],
            "qa": json.loads(qa) if qa else None, "log": out[-800:]}


class H(BaseHTTPRequestHandler):
    def reply(self, code, data, ctype="application/json"):
        b = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        path = urlparse(self.path).path; path = "/index.html" if path == "/" else path
        if path == "/startup":
            return self.reply(200, {"name": START and os.path.basename(START)})
        if path == "/startup/file" and START:
            return self.reply(200, open(START, "rb").read(), "application/octet-stream")
        f = os.path.normpath(os.path.join(HERE, path.lstrip("/")))
        if not f.startswith(HERE) or not os.path.isfile(f) or f.endswith(".py"):
            return self.reply(404, {"error": "not found"})
        self.reply(200, open(f, "rb").read(), TYPES.get(os.path.splitext(f)[1], "application/octet-stream"))

    def do_POST(self):
        u = urlparse(self.path); body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            r = prep(parse_qs(u.query), body) if u.path == "/prep" else done(json.loads(body)) if u.path == "/done" else rig(json.loads(body))
            self.reply(200, r)
            if u.path == "/done" and ONCE:
                threading.Timer(0.5, lambda: os._exit(0)).start()
        except Exception as e:
            self.reply(500, {"ok": False, "log": repr(e)})


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8765); ap.add_argument("--model", help="model to open already loaded"); ap.add_argument("--once", action="store_true", help="exit after Finish"); a = ap.parse_args()
    ONCE = a.once; START = a.model and os.path.abspath(a.model)
    os.makedirs(WORK, exist_ok=True); print("rig studio on http://127.0.0.1:%d" % a.port, flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()
