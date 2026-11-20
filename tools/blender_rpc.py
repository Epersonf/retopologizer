"""Cliente do add-on MCP do Blender (porta 9876) ou do worker headless (tools/blender_worker.py, porta 9877).
Uso: python blender_rpc.py [--port 9877] arquivo.py  |  python blender_rpc.py [--port 9877] -c 'code'"""
import json, socket, sys

def run(code, host="localhost", port=9876, timeout=7200):
    s = socket.create_connection((host, port), timeout=timeout)
    s.sendall((json.dumps({"type": "execute", "code": code, "strict_json": False}) + "\0").encode("utf-8"))
    buf = b""
    while not buf.endswith(b"\0"):
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
    s.close()
    return json.loads(buf.rstrip(b"\0").decode("utf-8"))

if __name__ == "__main__":
    a = sys.argv[1:]; port = 9876
    if a[0] == "--port":
        port, a = int(a[1]), a[2:]
    code = a[1] if a[0] == "-c" else open(a[0], encoding="utf-8").read()
    r = run(code, port=port)
    if r.get("stdout"): print(r["stdout"])
    if r.get("status") == "error": print(r.get("message")); print(r.get("stderr", ""))
    else: print(json.dumps(r.get("result"), indent=1))
