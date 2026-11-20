"""Blonde fiber-card sheet rendered by Blender (the generator of tools/07-fibercards), as used for the Cuca's hair.
Writes hair_color.png, hair_normal.png and hair_preview.png in `out/`: 12 cards (4x3) from sparse to dense, transparent background.
Run from the repo root (normal python, it starts Blender itself; set BLENDER if it is not on the default path):
  python -I examples/fibercards/blonde_sheet.py [out_dir] [seed]
Cards become planes in Blender: UV = the card's cell of the sheet, material with backface visible (render both sides)."""
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
out = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "projects" / "cuca-hair" / "fibercards" / "out")
seed = sys.argv[2] if len(sys.argv) > 2 else "1"
subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "07-fibercards" / "fibercards.py"), "--out", out, "--tag", "hair",
                "--blonde", "--seed", seed, "--samples", "32", "--set", "hair_amount_max=130"], check=True)
