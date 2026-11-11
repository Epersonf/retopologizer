# Workflow de retopologia por reconstrução (Blender + MCP)

Para modelos gerados por IA (centenas de milhares de tris). Em vez de "retopo em cima do
mesh", **mede-se a referência e reconstrói-se a forma** com poucos polígonos, verificando
com métricas objetivas. Nunca entrar em Edit Mode no mesh de referência (crasha).

## Estrutura de projeto
```
projects/<nome>/input/   modelo original (.glb)
projects/<nome>/draft/   .blend (com a referência), scripts build_*.py, renders (ref/)
projects/<nome>/output/  .fbx dos low-poly + PNGs baked. NUNCA a referência (pesa)
tools/                   scripts gerais (índice em tools/README.md)
docs/                    este workflow + notas por projeto
```

## Passos
1. **Preparar**: `Blender.exe --background --python tools/inspect_glb.py -- model.glb` → tris,
   bbox, materiais. Define orçamento de tris (guideline do usuário; ex.: <1000, máx 2000).
2. **Importar** o GLB na cena (via MCP) e renomear `REF_<nome>_highpoly`, `hide_select=True`.
3. **Entender a forma**: `render_views.py` (front/right/top/persp, workbench, sem edit mode).
   Identificar partes independentes (ex.: base + tampa) e eixos (frente = -Y, Z up).
4. **Medir** com `slice_profile.py` (bbox por fatia) e cortes ASCII (occupancy 2D) para achar
   espessuras de parede, alturas de bandas, posição de dobradiças. Para partes articuladas:
   varrer o ângulo que minimiza a área do bbox no plano de rotação → ângulo de abertura;
   modelar na pose fechada e rotacionar em torno do pivô (resolver pivô linearmente).
5. **Construir** parametricamente com `mesh_lib.py` (rect_sweep, loft, box, prism): anéis de
   4–8 vértices varridos pelo perfil medido = quads limpos, poucos tris.
6. **Verificar** a cada iteração (`run_all.py` do projeto):
   - `compare_mesh.py`: distância média/p95/max em mm nos dois sentidos + `hot_k` (onde
     está o pior erro). ref→new alto = falta detalhe/parede; new→ref alto = geometria sobrando.
   - `overlay.py`: vermelho = só ref, ciano = só novo, por vista. Renderizar com
     `fit_to=[ref]` para o enquadramento ser idêntico.
7. **UV** (feito pelo usuário): sem overlap, todas as partes no mesmo atlas 0-1.
8. **Bake** (abaixo) e **exportar** com `wire_material.py`.

## Retopologia manual: snap + espelho (peças com detalhe, ex.: tampa v5)
É o jeito do artista (vértice a vértice com snap, `Mirror` quando simétrico), automatizado:
1. `ref_part(ref, parte, "REF_X")`: recorta da referência só a peça, **no espaço local dela** (tampa
   na pose fechada, simetria em X). Medir antes: alturas por raycast (`h(x)`), cortes por ângulo.
2. Cortes: de um centro `c` dentro da peça, `Surface.outer(x, c, ângulo)` devolve o ponto do casco;
   `simplify(corte, 6 mm)` (Douglas-Peucker) acha os cantos (tampa: 9 cantos externos, 8 da cavidade).
   Os **mesmos ângulos** valem para todos os anéis => mesma topologia => tiras de quads.
3. Anéis só do meio lado (x>=0): cinta, degrau, corpo, degrau, bloco da ponta, chanfro, tampa da
   ponta. Degrau = dois anéis no mesmo x (parede plana). Pontas do anel: raio horizontal na parede
   (o raio de 18° oscila ±1,5 cm na rugosidade da IA). `Mesh.mirror_x()` = Mirror + apply + solda.
4. Piso plano (rim) entre o laço externo e a cavidade: `fill_flat_ring` (triangulação sem cruzar;
   `bridge_loops` cruzou triângulos em laços com contagens diferentes => overlap de UV/z-fight).
5. Detalhes salientes (fecho, rebites) = `Mesh.prism`: base **projetada na própria malha** e
   afundada 4 mm (sem face de baixo), topo na superfície da ref; furo = `dimple`. Base flutuando
   deixa o raio entrar no slab e a QA acusa backface.
6. Conferir: `fit_report` (novo→ref média 3,4 mm), `section_overlay`, QA (`qa_all`), UV de novo
   (`unwrap_atlas(angle=66)`: 89° dobrou ilhas do arco), `bake_robust`.
   Tampa v5: 340 tris (era 248, mas fiel: cintas, blocos, chanfros, cavidade em arco, fecho, rebites).

## QA obrigatório (antes do UV final, do bake e do export)
`tools/qa_all.py` → `qa_all([...])` levanta erro se qualquer teste falhar.
- **Backfaces** (`qa_faces.py`): 400 direções × 200×200 raios; o primeiro hit de cada raio não pode
  ser a face de trás de nenhuma face (é o vermelho do Face Orientation). Cobre também o interior
  das cavidades abertas. Ignora hits quase rasantes (|n·d| < 0.1). `fix_flipped()` inverte faces
  vistas só por trás; `hidden` = faces com 0 votos de frente são apagadas (estavam enterradas).
- **Z-fighting** (`qa_zfight.py`; broad phase própria por AABB: `BVHTree.overlap` NUNCA reporta triângulos coplanares
  e deixou passar placas de canto coplanares com a borda da base, que no Cycles saíam pretas): nenhum par de triângulos paralelos a <1 mm com área de sobreposição
  (face dentro de face, tampa/placa coplanar). Correção: afastar a placa 2–4 mm ou remover a face.
- **UV** (`qa_uv.py`): zero overlap (entre e dentro de ilhas, rasterizado a 2048 e 4096), nada fora
  de 0-1, sem faces de área zero, gap mínimo de 8 px entre ilhas (a margem do bake é 8 px).
  `unwrap_atlas(names, margin=0.006, angle=89)`: smart project + densidade igual + pack (≈52% do atlas).
- Causas que já apareceram: caixas com tampa/fundo abertos (`skip=`) → todas as caixas devem ser
  fechadas; peças enterradas furando a cavidade; **T-junction entre o fundo da tampa e as paredes**
  depois de mexer nos vértices (raios entram pela fresta e saem por trás da parede) → refazer o
  fundo com `bmesh.ops.bridge_loops` entre o laço externo e o da cavidade.
- Armadilha: `Face Orientation` vermelho = normal para dentro/espaço vazio atrás; `recalc normals`
  em malha aberta pode inverter a cavidade inteira.
- NUNCA usar `raise SystemExit` no `execute_blender_code`: fecha o Blender e perde o que não foi salvo.

## Bake (alta → baixa) — Cycles GPU
Pré-requisito: UV sem overlap, partes dividindo o mesmo atlas. **Selecionar as duas partes e
fazer um bake só**, numa imagem só (`tools/bake_maps.py`).
1. O alvo precisa ser um único objeto ativo: o script junta cópias das partes low (espaço
   mundo, UV intacta) em `_bake_joined`, faz o bake com a referência selecionada
   (selected-to-active) e apaga a cópia. Baker em passes separados, um objeto por vez,
   **apagou** o resultado do primeiro na mesma imagem.
2. **Cage ou método padrão?** Tentar o padrão primeiro: `extrusion` + `max_ray_distance`.
   Normais invertidas (azul ≈ 0) = raio nasce dentro da referência = extrusão menor que o
   desvio entre low e high. Chest: extrusão 0.03 → 31% de pixels invertidos; 0.06 → 16%;
   **0.10 / ray 0.20 → 6%** (o resto são faces escondidas). Regra: extrusão ≈ 3–4× o p95
   do `compare_mesh` (~10% da altura do objeto aqui).
3. **Se precisar de cage** (raios errando em quinas duras): **duplicar o low e dar `Alt+S`
   no Edit Mode** (shrink/fatten ao longo das normais) até cobrir toda a referência; usar
   como Cage Object e apagar depois. No script: `cage_dist=<m>` faz o mesmo via bmesh.
   Um cage fino (0.02) NÃO resolveu: ele precisa cobrir o maior desvio.
4. Mapas: basecolor (Diffuse/Color), normal (tangent), roughness, metallic (emissão do
   canal B do glTF), AO. 2048 px, margem 16 px (EXTEND), 16 samples (AO 128), sem denoise.
5. `wire_material.py` liga os PNGs num Principled e exporta o FBX só com os low-poly (a
   referência nunca vai para `output/`). PNGs e FBX em `output/`; .blend em `draft/`.
6. **Bake robusto** (`tools/bake_robust.py`, substitui o bake simples): além dos mapas, assa por
   texel a posição do hit na referência e a flag Backfacing; texel válido = achou hit + frente +
   hit a < `max_dist` (0.12) da malha low. Inválidos são re-assados com outros extrusion/ray
   (0.10/0.20 → 0.05/0.10 → 0.20/0.40); o que sobrar é preenchido por inpaint dentro da mesma
   ilha UV (`bake_inpaint.py`, equivale ao clone tool) e as ilhas são dilatadas na margem.
   Devolve `worst_unbaked_faces` e `poor_fit_faces_mm` (faces da low longe da ref → ajustar
   vértices) e dá para salvar um mapa de máscara (verde ok, amarelo recuperado, vermelho inpaint).
   Chest: 1.27% inválido no 1º passe → 0.43% inpaint (tiras curvas da tampa/alça).
7. Checar: % de faces pretas no basecolor por objeto (< 3%) e um render workbench TEXTURE.
- Referência escondida no viewport (`hide_set`) faz o bake falhar: "No valid selected objects".

## Ajuste depois do UV/bake (sem quebrar UV)
- Depois que o usuário fez UV, **nunca rodar `run_all.py`/builders** (recriam a malha e perdem a UV).
  Ajustar só posições de vértices (mesma topologia), partindo de um backup em `draft/backups/`.
- Snap automático ao ponto mais próximo da ref amassou as placas pequenas: não usar. Medir os
  perfis da ref no frame fechado (`slice_profile`-style por faixa de x) e deslocar por região.
- Distância assinada alta nas quinas = quina de caixa vs. bisel arredondado da ref (esperado).
- O que gerava artefatos no bake: placas/presilha 2-3 cm além da ref (raio longe) e topo da
  cúpula ~1 cm alto. Corrigido: frente das placas +0.02, topo −0.004…−0.013, cintas ajustadas.

## Listagem / loja (Fab)
Gerar no fim, com o material final ligado: `projects/<nome>/listing/`.
- **Thumbnail**: `render_thumbnail(partes, "listing/thumbnail.jpg", samples=768)` (`tools/render_thumbnail.py`): 1920x1080
  (mínimo do Fab), jpg/png/webp, <= 3 MB (sai ~0,2 MB), **Cycles** (AgX sem look, key suave + fill fraco + 2 rim + spot no chão, material mais fosco, 85 mm,
  DOF leve; ~1 min a 768 amostras com GPU; testar com samples=64). Ajustar `cam`/`look_at` à escala do
  modelo e **olhar o arquivo** antes de subir (enquadramento, nada cortado, textura final).
- **description.md**: título, o que vem, tabela técnica (tris, malhas, UV, tamanho, pivô, formato), checks de QA,
  limitações (ex.: só albedo) e **aviso de IA generativa** (conferir as regras atuais do Fab).
- Só o albedo foi mantido neste projeto: `wire_and_export(..., maps=("basecolor",))`.
- Nunca `img.reload()` antes do export: o que o artista pintou no Blender mora na imagem empacotada do .blend;
  o PNG em disco ainda é o bake antigo (isso já apagou uma edição; recuperada do .blend salvo).

## O que vai para o git e como reproduzir
- Só entra no repo: `tools/`, `docs/`, `inputs.json` e **um `.blend` enxuto por projeto**
  (`projects/<nome>/<nome>.blend`): low-poly + UV + material + **imagens baked empacotadas** (blob).
  Sem a referência de 500k (46 MB), sem backups, sem renders de debug.
- Ignorados (pesados/derivados): `input/*.glb`, `output/`, `draft/`. O GLB é a única coisa que não se
  recria: está em `inputs.json` com sha256 e tamanho; `python tools/verify_inputs.py` confere.
  **Guarde uma cópia do GLB fora do repo** (nuvem/HD). Nada mais é insubstituível.
- Gerar o `.blend` enxuto (dentro do Blender): `make_lean_blend(["chest_base","chest_lid"], "chest_mat", path)`.
- Regenerar `output/` (PNGs idênticos pixel a pixel + FBX) em qualquer máquina:
  `blender -b projects/<nome>/<nome>.blend -P tools/export_from_blend.py -- projects/<nome>/output chest`.
- Refazer o bake do zero: importar o GLB, nomear `REFERENCE`, abrir o .blend enxuto, `bake_all` (ver Bake).
- Modelos nascem de gerações do Hunyuan (não procedural): a malha low-poly é reconstruída medindo a
  referência (passos 3-6) e fica no .blend.

## Armadilhas
- O MCP bloqueia `bpy.ops.wm.read_factory_settings`; limpar a cena removendo objetos.
- `result` no MCP deve ser dict. Não reusar nomes de variável entre `exec`s (ex.: `T`);
  cada chamada precisa de `import bpy` próprio.
- Medir "mínimo de z dos vértices" engana em regiões planas; confirmar com overlay.
- Um erro de ~0.02 m só apareceu comparando silhuetas (topo da base era 0.355, não 0.385).
- Paredes fechadas (frente/trás da tampa) só apareceram no `hot_k`: o erro sumiu ao fechá-las.
- Ao editar docs por script no Windows, usar UTF-8 (`open(..., encoding="utf-8")`).
