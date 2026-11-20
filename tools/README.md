# tools/ — índice

Cada arquivo começa com um docstring de uso (assinaturas e exemplos). Como rodar o Blender:
`docs/blender-automacao.md`. Fluxo de um projeto: `docs/workflow-retopology.md`.

"dentro do Blender" = carregar com `exec(open(r"<repo>\tools\x.py", encoding="utf-8").read())` (MCP, worker ou
one-shot) e chamar a função. Os pacotes `retopo/` e `autorig/` são importados (`sys.path` + `import`).

## Rodar o Blender
| arquivo | onde roda | para quê |
|---|---|---|
| blender_rpc.py | `python` | cliente do socket (MCP 9876 ou worker 9877): roda um arquivo ou `-c "código"`, imprime `result` |
| blender_worker.py | `blender -b cópia.blend --python blender_worker.py -- 9877` | Blender headless com o protocolo do MCP, para construir e renderizar numa cópia |
| blender_once.py | `blender -b --factory-startup --python blender_once.py -- script.py` | roda um script de worker sem worker no ar; resultado na linha `RESULT_JSON:` |

## Inspecionar e medir
| arquivo | onde roda | para quê |
|---|---|---|
| inspect_glb.py | `blender --background --python inspect_glb.py -- model.glb` | tris/verts, bbox, materiais e 3 perfis de silhueta de um GLB |
| render_views.py | dentro do Blender | vistas workbench (front/back/left/right/top/persp); `fit_to` fixa o enquadramento |
| slice_profile.py | dentro do Blender | bbox por fatia ao longo de um eixo (numpy, sem Edit Mode) |
| slice_plot.py | `python` (matplotlib) | cortes da ref em PNG com grade em cm, a partir de `hi_world.npz`; `--low` sobrepõe a retopo |
| ref_part.py | dentro do Blender | recorta a parte da ref que pertence a uma peça, no espaço local dela |

## Construir à mão (retopologia)
| arquivo | onde roda | para quê |
|---|---|---|
| mesh_lib.py | dentro do Blender | props simples: `box`, `loft`, `rect_sweep`, `prism`, `pentagon`, `to_object` |
| snap_retopo.py | dentro do Blender | peças duras: carrega os três abaixo (`docs/retopo-snap-mirror.md`) |
| snap_surface.py | via snap_retopo | `Surface`: `nearest`, `ray`, `outer`, `inner` na ref; `simplify` (Douglas-Peucker) |
| snap_mesh.py | via snap_retopo | `Mesh`: `v`, `f`, `strip`, `cap`, `prism`, `dimple`, `fill_flat_ring`, `mirror_x`, `to_object` |
| snap_section.py | via snap_retopo | `ring(S, c, axis, up, n)`: anel de corte por raycast do centro (`zmin`, `despike`) |
| retopo/ | dentro do Blender (`import retopo`) | personagens e orgânicos: `Ref`, `Topo`, contornos, patches, dedos, `topo_qa`, `part_object`/`export_obj` (`retopo/README.md`) |

## Conferir a forma
| arquivo | onde roda | para quê |
|---|---|---|
| compare_mesh.py | dentro do Blender | distância ref↔novo (mm e % da diagonal) nos dois sentidos + pontos críticos (`hot_k`) |
| fit_report.py | dentro do Blender | erro novo→ref e ref→novo (mm) de uma peça + células de 5 cm onde falta detalhe |
| overlay.py | `python` (PIL) | silhuetas ref × novo: vermelho só ref, ciano só novo, cinza os dois |
| section_overlay.py | dentro do Blender | PNG de cortes: ref colorida × low branca |
| wire_overlay.py | dentro do Blender | render workbench + wireframe da low (só arestas visíveis): a vista do artista |
| label_png.py | `python` (PIL) | escreve os índices dos vértices no PNG do wire_overlay |

## QA
| arquivo | onde roda | para quê |
|---|---|---|
| qa_all.py | dentro do Blender | portão único: backfaces + UV (2048 e 4096) + z-fighting; levanta erro se falhar |
| qa_faces.py | dentro do Blender | raycast de 400 direções: nenhuma backface exposta; `fix_flipped` |
| qa_zfight.py | dentro do Blender | faces quase paralelas sobrepostas a < 1 mm (z-fighting), broad phase por AABB |
| qa_uv.py | dentro do Blender | overlap, limites 0–1, área zero, gap entre ilhas; `unwrap_atlas` (smart project + pack) |

## Bake
| arquivo | onde roda | para quê |
|---|---|---|
| bake_robust.py | dentro do Blender | bake com validação por texel (hit/backface/distância), re-bake multi-passada, inpaint por ilha |
| bake_maps.py | dentro do Blender | bake simples de 5 mapas high→low numa imagem (junta as peças; cage opcional) |
| bake_inpaint.py | numpy puro | inpaint e dilate restritos à ilha UV (clone automático) |

## Entrega
| arquivo | onde roda | para quê |
|---|---|---|
| wire_material.py | dentro do Blender | liga os PNGs num Principled e exporta o FBX só dos low-poly |
| finalize_export.py | dentro do Blender | coleções, UV, material, orçamento, `.blend` e FBX |
| render_thumbnail.py | dentro do Blender | thumbnail 1920x1080 para loja (Cycles, estúdio, chão brilhante) |
| make_lean_blend.py | dentro do Blender | `.blend` enxuto para o git (sem a ref, imagens empacotadas) |
| export_from_blend.py | `blender -b <projeto>.blend -P export_from_blend.py -- outdir prefixo` | regenera PNGs + FBX a partir do `.blend` enxuto |

## Rig
| arquivo | onde roda | para quê |
|---|---|---|
| rig_mixamo.py | dentro do Blender | armature com nomes Mixamo a partir das juntas, skin por bone heat (máx. 4), export FBX |
| autorig/ | `blender -b --factory-startup --python autorig/cli.py -- modelo saida.fbx` | auto-rig humanoide estilo Mixamo: juntas pela malha, dedos, cauda, skin, QA (`autorig/README.md`) |

Blender: `C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe` (5.3).
