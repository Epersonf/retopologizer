"""Opens a .blend in Blender with the session recorder on, in a new rec_NN folder (never overwrites old recordings).
  python tools/general/record_session.py <file.blend> <sessions_dir>      e.g. ... projects/wing/draft/x.blend projects/wing/session
BLENDER_EXE env var changes the executable (default: Steam, Blender 5.3)."""
import os, subprocess, sys

EXE = os.environ.get("BLENDER_EXE", r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe")
blend, base = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
os.makedirs(base, exist_ok=True)
n = 1
while os.path.exists(os.path.join(base, "rec_%02d" % n)) and os.listdir(os.path.join(base, "rec_%02d" % n)):
    n += 1
rec = os.path.join(base, "rec_%02d" % n); os.makedirs(rec, exist_ok=True)
rec_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_recorder.py")
subprocess.Popen([EXE, blend, "--python", rec_py], env={**os.environ, "REC_DIR": rec}, creationflags=0x00000008 if os.name == "nt" else 0)
print("gravando em", rec)
