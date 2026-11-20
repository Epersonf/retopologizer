# retopologizer

Transforma modelos 3D gerados por IA (Hunyuan3D e afins: 500 mil+ triângulos, malha suja, sem topologia) em assets
de jogo: low-poly feito à mão com snap na referência, UV, texturas assadas (bake), QA, FBX, rig estilo Mixamo, Godot
e página de loja (Fab). Tudo roda no Blender por script, comandado por um agente: você.

Este README é a porta de entrada. Leia as regras e o jeito de trabalhar, ache a etapa em que está e abra só o guia
dela; cada guia aponta para o próximo.

## Regras inegociáveis
1. **Retopologia é sempre manual**: cada vértice é decidido e colado (snap) na referência. Nunca QuadriFlow, Remesh,
   Instant Meshes ou Decimate para gerar a malha entregue, nem "como primeira passada" (`docs/regras-retopologia.md`).
2. **Só quads**: a retopologia entregue não tem nenhum triângulo nem n-gon (`topo_qa(...)["quad_only"]`).
3. Ferramenta automática **mede e confere** (raycast, BVH, fit, QA); não gera a malha.
4. A referência nunca é editada (Edit Mode num mesh de 500 mil tris trava o Blender) nem vai para `output/` ou o git.
5. O Blender aberto pelo usuário (MCP, porta 9876) é **só leitura**: construir e renderizar numa cópia, no worker
   (porta 9877) ou em one-shot (`docs/blender-automacao.md`).
6. Arquivos com no máximo 150 linhas (separar por responsabilidade). Commit só quando o usuário pedir, nunca com
   `Co-Authored-By` ou atribuição a IA.

## Como um especialista trabalha aqui
- **Medir antes de modelar**: cortes, perfis e raycasts dão as posições em metros; nada no olho.
- **Objetivo pequeno, imagem cedo**: construir uma parte, renderizar uma vista (`wire_overlay`), mostrar, corrigir o
  que está visivelmente errado. Rodadas longas de análise sem imagem frustram o usuário.
- **Por partes**: proponha dividir o modelo (mão, perna sem o pé, pé, cauda...) e fazer uma parte por rodada, entregue
  sozinha (OBJ) e integrada pelo usuário antes da próxima (`docs/retopo-por-partes.md`).
- **Conferir com número e imagem**: erro em mm (`fit_report`, `compare_mesh`), onde erra (`overlay`,
  `section_overlay`), passa ou falha (`qa_all`, `topo_qa`).
- **Continuar o trabalho do artista**: se o usuário começou a malha, partir dela e manter as contagens nas emendas.
- **Tudo em script** (`projects/<nome>/*.py`), reprodutível. Depois que o usuário fez a UV, só mover vértices.
- **Meia malha + espelho** quando há simetria; estátua torta fica "como está" (não simetrizar sem pedido).
- **Orçamento baixo e justificado**: cada loop existe por silhueta, deformação ou bake (`docs/topologia.md`).
- Convenções: Z para cima, frente = −Y, esquerda do personagem = +X, metros.

## Pipeline
| # | etapa | resultado | ferramentas | guia em `docs/` |
|---|---|---|---|---|
| 0 | entrada | GLB em `input/`, com cópia fora do repo | `inspect_glb` | workflow-retopology |
| 1 | entender e medir | vistas, cortes, medidas | `render_views`, `slice_profile`, `slice_plot`, `ref_part` | workflow-retopology |
| 2 | retopologia | low-poly em quads colado na ref | `mesh_lib`, `snap_retopo`, `retopo/` | topologia, retopo-por-partes, retopo-snap-mirror, retopo-llm |
| 3 | conferir forma | erro em mm, sobreposições | `fit_report`, `compare_mesh`, `overlay`, `section_overlay`, `wire_overlay` | workflow-retopology |
| 4 | QA da malha | 0 backface, 0 z-fight, topologia limpa | `qa_all`, `topo_qa` | qa |
| 5 | UV | atlas 0–1 sem overlap, gap ≥ 8 px | `qa_uv`, `unwrap_atlas` | uv-bake |
| 6 | bake | basecolor, normal, roughness, metallic, AO | `bake_robust` | uv-bake |
| 7 | entrega | FBX + PNGs, `.blend` enxuto | `wire_material`, `make_lean_blend`, `export_from_blend` | entrega, git-reproducao |
| 8 | rig | armature Mixamo + pesos | `autorig/`, `rig_mixamo` | rigging |
| 9 | jogo e loja | Godot, thumbnail, descrição | `render_thumbnail` | entrega |

## Preciso de… → leia
| preciso de | leia |
|---|---|
| rodar código no Blender, erro do MCP ou do worker | `docs/blender-automacao.md` |
| começar um projeto (pastas, medir a referência, ordem das etapas) | `docs/workflow-retopology.md` |
| decidir loops, polos, contagens, orçamento | `docs/topologia.md` |
| retopo de um modelo inteiro: dividir em partes, ordem, uma rodada, entrega em OBJ | `docs/retopo-por-partes.md` |
| retopo de peça dura ou prop (baú, tampa, caixa) | `docs/retopo-snap-mirror.md` |
| retopo de personagem ou orgânico (corpo, mão, garras, cauda) | `docs/retopo-llm.md` |
| saber se a malha está pronta | `docs/qa.md` |
| UV, mapas PBR, bake, manchas pretas no bake | `docs/uv-bake.md` |
| exportar FBX, levar à Godot, thumbnail e texto da loja | `docs/entrega.md` |
| rig humanoide, pesos, cauda | `docs/rigging.md` |
| o que commitar, regenerar `output/`, GLB pesado | `docs/git-reproducao.md` |
| como chamar uma ferramenta | `tools/README.md` e o docstring do arquivo |

## Ferramentas
Todas em `tools/`, cada uma com um docstring de uso. Tabela com forma de chamar: `tools/README.md`.
- **Rodar o Blender**: `blender_rpc` (cliente do socket), `blender_worker` (Blender headless numa cópia, porta 9877),
  `blender_once` (roda um script e sai; resultado em `RESULT_JSON:`).
- **Inspecionar e medir**: `inspect_glb` (tris, bbox, materiais), `render_views` (vistas workbench), `slice_profile`
  (bbox por fatia), `slice_plot` (cortes em PNG com grade em cm, fora do Blender), `ref_part` (pedaço da ref no
  espaço local de uma peça).
- **Construir à mão**: `mesh_lib` (caixa, loft, sweep, prisma: props simples); `snap_retopo` com `snap_surface`,
  `snap_mesh` e `snap_section` (anéis colados na ref + espelho: peças duras); pacote `retopo/` (Ref, Topo, contornos,
  patches de 3 e 5 lados, dedos e garras, `topo_qa`, `part_object`/`export_obj` para separar e entregar uma parte:
  personagens).
- **Conferir a forma**: `fit_report` e `compare_mesh` (erro nos dois sentidos e onde falta detalhe), `overlay`
  (silhuetas), `section_overlay` (cortes), `wire_overlay` + `label_png` (wireframe sobre a ref, com índices).
- **QA**: `qa_all` (portão único), `qa_faces` (backfaces, `fix_flipped`), `qa_zfight`, `qa_uv` (`unwrap_atlas`).
- **Bake**: `bake_robust` (validação por texel, re-bake, inpaint), `bake_maps` (bake simples, cage opcional),
  `bake_inpaint` (numpy).
- **Entrega**: `wire_material` (material + FBX só dos low), `finalize_export`, `render_thumbnail` (Fab),
  `make_lean_blend`, `export_from_blend`.
- **Rig**: `autorig/` (auto-rig humanoide estilo Mixamo por linha de comando), `rig_mixamo` (armature Mixamo a partir
  de juntas, skin, FBX).

## Mapa do repo
```
README.md           este arquivo
docs/               guias por assunto (índice: docs/README.md)
tools/              ferramentas (índice: tools/README.md); retopo/ e autorig/ são pacotes Python
projects/<nome>/    scripts e notas do projeto (no git)
  input/            GLB original (fora do git; guarde uma cópia fora do repo)
  draft/            .blend de trabalho com a referência, renders, backups (fora do git)
  output/           FBX + PNGs (fora do git; regeneráveis)
  <nome>.blend      .blend enxuto (low-poly + texturas empacotadas), quando o projeto fecha
```

## Projetos (exemplos para copiar)
| projeto | estado | estude para |
|---|---|---|
| stylized-chest | pronto: 813 tris em 2 peças, bake 2048, listagem Fab | prop duro com snap + espelho (`build_lid_v5.py`); README com medidas |
| stylized-tree | pronto: 380 tris, bake | anéis em volta de eixos; ref com cascas internas (`snap_tree.py`) |
| stylized-saci | pronto: 2864 tris, rig Mixamo, na Godot | personagem de uma perna (scripts só em `draft/`, fora do git) |
| stylized-cuca | pronto: 3756 tris, rig com cauda, na Godot | personagem por partes com `tools/retopo` (`cuca_*.py`); rig à mão (`cuca_rig.py`) |
| stylized-cow | em andamento: tronco, pernas, cabeça e extras em anéis com snap | estátua "como está", partes em cascas separadas |
| hat-hair | não começado (só o GLB) | — |
| autorig-bench | banco de teste do auto-rig (7 casos) | calibrar e validar `tools/autorig` |
