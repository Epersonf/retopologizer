# O que vai para o git e como reproduzir

- **Entra**: `tools/`, `docs/`, scripts e notas dos projetos e **um `.blend` enxuto por projeto**
  (`projects/<nome>/<nome>.blend`): low-poly + UV + material + imagens baked empacotadas.
- **Fica fora** (`.gitignore`): `projects/*/input/` (GLB), `projects/*/output/`, `projects/*/draft/`, `*.blend1`,
  `__pycache__/`. Nada da referência de 500k tris (46 MB), backups ou renders de debug.
- O GLB de entrada é a única coisa que não se recria: guarde uma cópia fora do repo (nuvem ou HD) e anote a origem
  no `README.md` do projeto.
- Os modelos nascem de gerações (Hunyuan3D), não de procedimento: a malha low-poly mora no `.blend`; os scripts do
  projeto mostram como ela foi construída a partir da referência.

## Comandos
- `.blend` enxuto (dentro do Blender): `make_lean_blend(["chest_base", "chest_lid"], "chest_mat", path)`.
- Regenerar `output/` (PNGs idênticos + FBX) em qualquer máquina:
  `blender -b projects/<nome>/<nome>.blend -P tools/export_from_blend.py -- projects/<nome>/output <prefixo>`.
- Refazer o bake do zero: importar o GLB, nomear `REFERENCE`, abrir o `.blend` enxuto, `bake_robust` (`uv-bake.md`).

## Commits
- Só quando o usuário pedir.
- Nunca `Co-Authored-By`, "Generated with" ou qualquer atribuição a IA.
- Antes de commitar um `.blend`, confirmar que é o enxuto (sem a referência).
