"""Stylized cow, statue pose exactly as generated (no symmetry, head left as is): automatic quad retopo.
  exec(open(ROOT+r"\tools\auto_quad.py").read()); auto_quad("REFERENCE", "cow", faces=3000, mid_ratio=0.06)
Result: 3117 quads (6234 tris), one closed shell, fit new->ref mean 0.8 mm / p95 3.1 mm. Not done yet: UV, bake, export.
Known losses (QuadriFlow resolution): eyes, nostrils, hoof split, thin ear rim - restore by hand or raise `faces`."""
