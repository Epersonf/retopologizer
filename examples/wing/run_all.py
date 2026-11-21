"""Reproduce the wing from the artist's files, stage by stage (each stage is one Blender one-shot; paths come from the environment).
  python examples/wing/run_all.py prepare            # artist's skin blend  -> closed shell + handle parts (open it, do the UV, adjust the shape, save)
  python examples/wing/run_all.py finish             # artist's UV blend    -> bake -> handle relief -> rig -> export
  python examples/wing/run_all.py bake|relief|rig    # one stage of `finish`
Options: --wing-dir DIR (default projects/wing), --skin-blend F, --uv-blend F, --export-dir D.  BLENDER_EXE overrides the Blender path.
The two human steps in between (UV, shape adjustments) are NOT automated: the pipeline never rewrites a mesh after the artist's UV."""
import argparse, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EXE = os.environ.get("BLENDER_EXE", r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe")
STAGES = {"prepare": "s1_prepare_for_uv.py", "bake": "s2_bake.py", "relief": "s3_relief.py", "rig": "s4_rig_export.py"}


def run(stage, env):
    r = subprocess.run([EXE, "-b", "--factory-startup", "--python", os.path.join(ROOT, "tools", "general", "blender_once.py"), "--", os.path.join(HERE, STAGES[stage])],
                       env=env, capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if l.startswith("RESULT_JSON")]
    print(f"[{stage}]", line[0][13:] if line else "NO RESULT\n" + r.stdout[-1500:] + r.stderr[-800:]); return bool(line)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("stage", choices=["prepare", "finish", "bake", "relief", "rig"]); p.add_argument("--wing-dir"); p.add_argument("--skin-blend")
    p.add_argument("--uv-blend"); p.add_argument("--export-dir"); a = p.parse_args(); env = dict(os.environ, RETOPOLOGIZER_ROOT=ROOT, WING_EX=HERE)
    for k, v in (("WING_DIR", a.wing_dir), ("SKIN_BLEND", a.skin_blend), ("UV_BLEND", a.uv_blend), ("EXPORT_DIR", a.export_dir)):
        if v:
            env[k] = os.path.abspath(v)
    for s in (["bake", "relief", "rig"] if a.stage == "finish" else [a.stage]):
        if not run(s, env):
            sys.exit(1)
