"""Zips for the Fab "product files" step: ONE zip per format, each with only that format + the textures.
Fab asks for a format first (FBX, GLB, GLTF...) and its upload accepts a single file type or a .zip containing it; a zip with
the FBX and the GLB together is not accepted for either. Upload FBX only: Fab converts it by itself to GLTF/GLB/USDZ
(`docs/05-delivery/fab-upload.md`), so the GLB zip is only needed if the conversion fails.
  python tools/05-delivery/fab_package.py <game_dir> <textures_dir> <out_dir> <Name> [--formats fbx glb]
  -> <out_dir>/<Name>_FBX.zip  (Espada.fbx + textures/*.png), <out_dir>/<Name>_GLB.zip
`<game_dir>` holds `<Name>.fbx` / `<Name>.glb` (`export_package`); textures are every *.png in `<textures_dir>`."""
import argparse, glob, os, sys, zipfile


def make_zips(game_dir, tex_dir, out_dir, name, formats=("fbx", "glb")):
    os.makedirs(out_dir, exist_ok=True)
    pngs = sorted(glob.glob(os.path.join(tex_dir, "*.png")))
    if not pngs: raise SystemExit("no .png in %s" % tex_dir)
    made = []
    for ext in formats:
        src = os.path.join(game_dir, f"{name}.{ext}")
        if not os.path.exists(src): raise SystemExit("missing %s" % src)
        dst = os.path.join(out_dir, f"{name}_{ext.upper()}.zip")
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(src, f"{name}.{ext}")
            for p in pngs: z.write(p, "textures/" + os.path.basename(p))
        made.append((dst, round(os.path.getsize(dst) / 1e6, 2)))
    return made


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("game_dir"); a.add_argument("tex_dir"); a.add_argument("out_dir"); a.add_argument("name")
    a.add_argument("--formats", nargs="+", default=["fbx", "glb"])
    r = a.parse_args()
    for dst, mb in make_zips(r.game_dir, r.tex_dir, r.out_dir, r.name, r.formats): print(f"{dst}  {mb} MB")
    sys.exit(0)
