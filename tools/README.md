# tools/: índice por etapa do workflow

Mesmas pastas de `docs/`. Cada arquivo começa com um docstring de uso (assinaturas e exemplos). Como rodar o Blender:
`docs/00-regras-e-ferramentas/blender-automacao.md`. Fluxo de um projeto: `docs/01-entrada-e-medicao/workflow-retopology.md`.

**Regra:** a ferramenta fica na pasta da etapa que a usa. Se é usada por mais de uma etapa (ou por todas), vai em
`general/`. Ao criar ferramenta nova, ponha na etapa dela; se uma segunda etapa passar a usá-la, mova para `general/`
e atualize os caminhos (`grep -rn "tools.<pasta>.<nome>"`).

"dentro do Blender" = carregar com `exec(open(r"<repo>\tools\<pasta>\x.py", encoding="utf-8").read())` (MCP, worker ou
one-shot) e chamar a função. Os pacotes (`retopo/`, `autorig/`, `rig_mixamo`) são importados: ponha a pasta deles no
`sys.path` (`<repo>\tools\02-retopologia` para `retopo`, `<repo>\tools\06-rig` para `autorig` e `rig_mixamo`).

## general/: usadas por mais de uma etapa
| arquivo | onde roda | para quê |
|---|---|---|
| blender_rpc.py | `python` | cliente do socket (MCP 9876 ou worker 9877): roda um arquivo ou `-c "código"`, imprime `result` |
| blender_worker.py | `blender -b cópia.blend --python tools/general/blender_worker.py -- 9877` | Blender headless com o protocolo do MCP |
| blender_once.py | `blender -b --factory-startup --python tools/general/blender_once.py -- script.py` | roda um script sem worker; resultado em `RESULT_JSON:` |
| cycles_gpu.py | dentro do Blender | `use_gpu()`: Cycles na GPU; chamar antes de todo bake/render (bake e thumbnail) |
| render_views.py | dentro do Blender | vistas workbench (front/back/left/right/top/persp); `fit_to` fixa o enquadramento |
| ref_part.py | dentro do Blender | recorta a parte da ref que pertence a uma peça, no espaço local dela |
| slice_plot.py | `python` (matplotlib) | cortes da ref em PNG com grade em cm; `--low` sobrepõe a retopo |
| qa_uv.py | dentro do Blender | overlap, limites 0–1, gap entre ilhas; `unwrap_atlas` (QA e UV/bake) |

## 01-entrada-e-medicao/
| arquivo | onde roda | para quê |
|---|---|---|
| inspect_glb.py | `blender --background --python inspect_glb.py -- model.glb` | tris/verts, bbox, materiais e 3 perfis de silhueta |
| slice_profile.py | dentro do Blender | bbox por fatia ao longo de um eixo (numpy, sem Edit Mode) |

## 02-retopologia/ (construir à mão e conferir a forma)
| arquivo | onde roda | para quê |
|---|---|---|
| mesh_lib.py | dentro do Blender | props simples: `box`, `loft`, `rect_sweep`, `prism`, `pentagon`, `to_object` |
| snap_retopo.py | dentro do Blender | peças duras: carrega os três abaixo (`docs/02-retopologia/retopo-snap-mirror.md`) |
| snap_surface.py | via snap_retopo | `Surface`: `nearest`, `ray`, `outer`, `inner` na ref; `simplify` |
| snap_mesh.py | via snap_retopo | `Mesh`: `v`, `f`, `strip`, `cap`, `prism`, `dimple`, `fill_flat_ring`, `mirror_x`, `to_object` |
| snap_section.py | via snap_retopo | `ring(S, c, axis, up, n)`: anel de corte por raycast do centro |
| retopo/ | dentro do Blender (`import retopo`) | personagens e orgânicos: `Ref`, `Topo`, contornos, patches, dedos, `lock` (tubo por madeixa, `section`), `topo_qa`, `part_object`/`export_obj` (`retopo/README.md`) |
| compare_mesh.py | dentro do Blender | distância ref↔novo (mm e % da diagonal) nos dois sentidos + pontos críticos |
| fit_report.py | dentro do Blender | erro novo→ref e ref→novo (mm) + células de 5 cm onde falta detalhe |
| overlay.py | `python` (PIL) | silhuetas ref × novo: vermelho só ref, ciano só novo, cinza os dois |
| section_overlay.py | dentro do Blender | PNG de cortes: ref colorida × low branca |
| wire_overlay.py | dentro do Blender | render workbench + wireframe da low (só arestas visíveis) |
| label_png.py | `python` (PIL) | escreve os índices dos vértices no PNG do wire_overlay |

## 03-qa/
| arquivo | onde roda | para quê |
|---|---|---|
| qa_all.py | dentro do Blender | portão único: backfaces + UV (2048 e 4096) + z-fighting; levanta erro se falhar |
| qa_faces.py | dentro do Blender | raycast de 400 direções: nenhuma backface exposta; `fix_flipped` |
| qa_zfight.py | dentro do Blender | faces quase paralelas sobrepostas a < 1 mm, broad phase por AABB |

## 04-uv-bake/
| arquivo | onde roda | para quê |
|---|---|---|
| bake_robust.py | dentro do Blender | bake com validação por texel, re-bake multi-passada, inpaint por ilha |
| bake_maps.py | dentro do Blender | bake simples de 5 mapas high→low numa imagem (cage opcional) |
| bake_inpaint.py | numpy puro | inpaint e dilate restritos à ilha UV |

## 05-entrega/
| arquivo | onde roda | para quê |
|---|---|---|
| wire_material.py | dentro do Blender | liga os PNGs num Principled e exporta o FBX só dos low-poly |
| finalize_export.py | dentro do Blender | coleções, UV, material, orçamento, `.blend` e FBX |
| render_thumbnail.py | dentro do Blender | thumbnail 1920x1080 para loja (Cycles, estúdio) |
| make_lean_blend.py | dentro do Blender | `.blend` enxuto para o git (sem a ref, imagens empacotadas) |
| export_from_blend.py | `blender -b <projeto>.blend -P export_from_blend.py -- outdir prefixo` | regenera PNGs + FBX a partir do `.blend` enxuto |
| verify_inputs.py | `python` | confere `inputs.json` (o `inputs.json` foi removido do repo, então está **obsoleta**) |

## 06-rig/
| arquivo | onde roda | para quê |
|---|---|---|
| rig_mixamo.py | dentro do Blender | armature com nomes Mixamo a partir das juntas, skin por bone heat (máx. 4), export FBX |
| autorig/ | `blender -b --factory-startup --python tools/06-rig/autorig/cli.py -- modelo saida.fbx` | auto-rig humanoide estilo Mixamo (`autorig/README.md`) |

Blender: `C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe` (5.3).
