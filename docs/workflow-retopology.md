# Workflow de um projeto (referência de IA → asset de jogo)

> **PROIBIDO retopologia automática** (QuadriFlow, Remesh, Decimate como entrega). Ver `regras-retopologia.md`.

Modelos gerados por IA têm centenas de milhares de triângulos e nenhuma intenção de topologia. Em vez de "limpar" essa
malha, **mede-se a referência e reconstrói-se a forma** com poucos polígonos, conferindo com números e imagens.
Nunca entrar em Edit Mode no mesh de referência (trava o Blender). Como rodar o Blender: `blender-automacao.md`.

## Estrutura de projeto
```
projects/<nome>/input/    modelo original (.glb), fora do git; guarde uma cópia fora do repo
projects/<nome>/draft/    .blend de trabalho (com a referência), renders, backups; fora do git
projects/<nome>/output/   .fbx dos low-poly + PNGs baked, NUNCA a referência; fora do git
projects/<nome>/*.py      scripts que constroem a malha (no git)
projects/<nome>/README.md origem, medidas, contagens, resultado, pendências
```

## Etapas
1. **Preparar**: `blender --background --python tools/inspect_glb.py -- model.glb` → tris, bbox, materiais. Anotar a
   origem do GLB no README do projeto. Combinar o orçamento de tris com o usuário (`topologia.md`).
2. **Importar** o GLB num `.blend` em `draft/`, nomear a referência (`REFERENCE`, `HiPoly`) e travar a seleção.
3. **Entender a forma**: `render_views(names, outdir, prefix, fit_to=[ref])` (front/right/top/persp, workbench).
   Separar partes independentes (base + tampa; corpo + roupa) e fixar os eixos: **Z up, frente = −Y, esquerda do
   personagem = +X, metros**.
4. **Medir** a referência (abaixo).
5. **Retopologia manual, por partes** (uma parte por rodada, entregue e integrada antes da próxima:
   `retopo-por-partes.md`), escolhendo o método:
   - forma simples (caixa, cilindro, prancha): `mesh_lib.py` (`box`, `loft`, `rect_sweep`, `prism`) com as medidas;
   - peça dura com detalhe: `retopo-snap-mirror.md`;
   - personagem ou forma orgânica: `retopo-llm.md`.
6. **Conferir a forma** a cada iteração (abaixo) e mostrar uma imagem ao usuário.
7. **QA** (`qa.md`) → **UV e bake** (`uv-bake.md`) → **entrega** (`entrega.md`) → **rig**, se for personagem
   (`rigging.md`) → **git** (`git-reproducao.md`).
8. Anotar no `README.md` do projeto: medidas, contagens, erro final, tris, pendências.

## Medir a referência
- `slice_profile(nome, axis=2, step=0.04)`: bbox por fatia (numpy, sem Edit Mode) → alturas de bandas, paredes.
- `slice_plot.py` (Python puro, sobre um `hi_world.npz`; ver `retopo-llm.md`): cortes PNG com grade em cm → centros e
  larguras de membros, onde ficam joelho, cotovelo, pulso.
- Raycast em função de x (`h(x)`) acha cintas, degraus, blocos e chanfros (tampa do baú).
- Peças articuladas: varrer o ângulo que minimiza a área do bbox no plano de rotação → ângulo de abertura. Modelar na
  pose fechada e girar em torno do pivô (resolver o pivô linearmente).
- `ref_part(ref, peça, "REF_X", radius)`: só a parte da ref que pertence a uma peça, no espaço local dela.

## Conferir a forma
- `fit_report(low, ref)` / `compare_mesh.compare(...)`: média/p95/máx em mm nos dois sentidos + onde. ref→novo alto =
  falta detalhe ou parede; novo→ref alto = geometria sobrando ou flutuando.
- `overlay.py ref.png new.png out.png`: vermelho só ref, ciano só novo, cinza os dois (renders com o mesmo `fit_to`).
- `section_overlay`: cortes com a ref colorida e a low branca, para ver onde um anel erra.
- `wire_overlay` (wireframe da low sobre a ref sombreada, só arestas visíveis) + `label_png` (índices dos vértices):
  a vista do artista; é a imagem para mostrar ao usuário.

## Armadilhas de medição
- "Mínimo de z dos vértices" engana em regiões planas: confirmar com overlay.
- Um erro de ~2 cm só apareceu comparando silhuetas (o topo da base do baú era 0.355, não 0.385).
- Paredes fechadas (frente e trás da tampa) só apareceram nos pontos críticos (`hot_k`); o erro sumiu ao fechá-las.
- A superfície da IA é rugosa: raio inclinado oscila ±1,5 cm. Medir paredes com raio perpendicular a elas.
- Referência com cascas internas: o primeiro hit engana; use o hit mais externo (`Ref.outer`, `snap_tree.py`).
