"""Headless Blender worker with the same socket protocol as the MCP add-on (JSON + \\0), so long builds and renders
run in a separate Blender on a working copy, without touching the file the artist has open in the UI.
  "<blender.exe>" -b <working_copy.blend> --python tools/blender_worker.py -- 9877
  python tools/blender_rpc.py --port 9877 script.py          (or -c "code")
Each request runs in a fresh namespace (bpy imported) and may set `result` (a dict); stdout is captured.
Module state persists between requests (e.g. the BVH cache of retopo.ref). {"type": "quit"} stops the worker."""
import bpy, contextlib, io, json, socket, sys, traceback

PORT = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else 9877


def _recv(conn):
    buf = b""
    while not buf.endswith(b"\0"):
        chunk = conn.recv(65536)
        if not chunk:
            break
        buf += chunk
    return json.loads(buf.rstrip(b"\0").decode("utf-8"))


def _run(code):
    ns, out = {"bpy": bpy, "__name__": "__worker__"}, io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            exec(compile(code, "<worker>", "exec"), ns)
        return {"status": "success", "result": ns.get("result"), "stdout": out.getvalue()}
    except Exception:
        return {"status": "error", "message": traceback.format_exc(), "stdout": out.getvalue()}


def serve(port=PORT):
    srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port)); srv.listen(1)
    print("blender worker listening on", port, "with", bpy.data.filepath, flush=True)
    while True:
        conn, _ = srv.accept(); req = {}
        try:
            req = _recv(conn)
            resp = {"status": "success", "result": "bye"} if req.get("type") == "quit" else _run(req.get("code", ""))
            conn.sendall((json.dumps(resp, default=str) + "\0").encode("utf-8"))
        except Exception:
            traceback.print_exc()
        finally:
            conn.close()
        if req.get("type") == "quit":
            break


serve()
