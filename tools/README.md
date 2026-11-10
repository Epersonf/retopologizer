# tools/ — índice

| arquivo | onde roda | para quê |
|---|---|---|
| inspect_glb.py | `blender --background --python` | tris/bbox/materiais de um GLB |
| render_views.py | dentro do Blender (MCP) | renders workbench ortho; `fit_to` fixa enquadramento |
| slice_profile.py | dentro do Blender | bbox por fatias de um mesh denso (numpy) |
| mesh_lib.py | dentro do Blender | box, loft, rect_sweep, prism, pentagon, to_object |
| compare_mesh.py | dentro do Blender | distância ref↔novo (mm, % da diagonal) + pontos críticos |
| overlay.py | `python` normal (PIL) | sobreposição de silhuetas ref × novo |
| finalize_export.py | dentro do Blender | coleções, UV, material, orçamento, .blend, FBX |
| bake_maps.py | dentro do Blender | bake de 5 mapas high→low numa imagem (junta partes; cage opcional) |
| wire_material.py | dentro do Blender | liga PNGs no Principled + exporta FBX só dos low |
| qa_all.py | dentro do Blender | portão de QA: backfaces + UV (levanta erro) |
| qa_faces.py | dentro do Blender | raycast multi-direção: nenhuma backface exposta; fix_flipped |
| qa_uv.py | dentro do Blender | overlap/gap/limites de UV; unwrap_atlas (smart project + pack) |
| make_lean_blend.py | dentro do Blender | .blend enxuto p/ git (sem ref, imagens empacotadas) |
| export_from_blend.py | `blender -b` | regenera PNGs + FBX a partir do .blend enxuto |
| verify_inputs.py | `python` | confere GLBs pesados (sha256 em inputs.json) |

Blender: `C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe` (5.2.3).
Uso no MCP: `exec(open(r"<caminho>").read())`. Fluxo completo: docs/workflow-retopology.md.
