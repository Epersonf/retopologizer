# QA: quando a malha está pronta

Rodar antes da UV final, do bake e do export. Tudo dentro do Blender; cada teste devolve um dict com `pass`.
Teoria do que é malha boa: `docs/02-retopologia/topologia.md`.

## Portão único (`qa_all.py`)
`exec(open(r"<repo>\tools\03-qa\qa_all.py", encoding="utf-8").read()); qa_all(["chest_base", "chest_lid"])`
levanta erro se algum teste falhar (`raise_on_fail=False` só devolve o relatório).

| teste | ferramenta | falha quando | correção |
|---|---|---|---|
| backfaces | `qa_faces.py` | o primeiro hit de algum raio (400 direções × 200×200, cavidades abertas incluídas) é o lado de trás de uma face, o vermelho do Face Orientation; hits rasantes (\|n·d\| < 0,1) ignorados | `fix_flipped()` inverte faces vistas só por trás; face com 0 votos de frente estava enterrada: apagar |
| **normal invertida visível (portão estrito)** | `qa_strict.py` | **qualquer** raio, de 400 direções em volta (200×200 cada), cuja primeira batida é o verso de uma face, confirmado por 4 raios vizinhos; tolerância zero, o modelo é **reprovado** (não salvar, não entregar) | `heal_flipped()` relaxa as faces reprovadas (cada vez mais forte e mais largo) e reroda; se sobrar, mudar a geometria (bordas da casca, tampa), nunca "flipar" |
| partes flutuando | `qa_floating.py` | algum grupo de peças soltas (união por interseção ou < 3 mm) não toca o maior; esperado = nº de grupos da ref (normalmente 1) | alongar a ponta da peça até a superfície que ela devia tocar (`hair_connect.py`); **sempre rodar ao dividir um objeto em várias malhas ou montar peças separadas** |
| z-fighting | `qa_zfight.py` | dois triângulos quase paralelos a < 1 mm com área sobreposta (placa coplanar, face dentro de face) | afastar 2–4 mm ou remover a face |
| UV | `qa_uv.py` | overlap entre ou dentro de ilhas (a 2048 e 4096), fora de 0–1, área zero, invertida, ilhas a < 8 px | refazer a UV (`docs/04-uv-bake/uv-bake.md`) |

## Topologia (`tools/02-retopologia/retopo/qa.py`)
`topo_qa("Cuca_retopo", Ref("HiPoly"), seam_x=0.0)`: faces/tris/quads/n-gons, triângulos após triangular, buracos
(arestas de borda), non-manifold, vértices soltos, duplicados (< 0,5 mm), winding em conflito, faces para dentro
(contra a normal da ref), polos (3 / 5 / 6+), faces degeneradas, distância à ref.
Esperado: `quad_only` True (0 tris, 0 n-gons: regra do repo), buraco só na costura do espelho (`seam_x`), e zero
non-manifold, duplicados, conflitos, faces para dentro e polos 6+.

## Forma (fiel à referência)
- `fit_report(low, ref)`: novo→ref (faces flutuando ou sobrando) e ref→novo (detalhe faltando) em mm, mais as células
  de 5 cm onde a ref está mais longe.
- `compare([ref], [lows], hot_k=10)` (`compare_mesh.py`): o mesmo em % da diagonal, com os pontos críticos.
- `section_overlay` (cortes) e `overlay` (silhuetas) mostram onde está o erro.

## Causas que já apareceram
- Caixas com tampa ou fundo abertos (`skip=` do `mesh_lib.box`): toda caixa fechada.
- Peças enterradas furando a cavidade.
- T-junction entre o fundo da tampa e as paredes depois de mexer em vértices: o raio entra pela fresta e sai por
  trás da parede. Refazer o fundo com `bmesh.ops.bridge_loops` entre o laço externo e o da cavidade.
- Placas coplanares com a borda saíram pretas no Cycles e `BVHTree.overlap` não as viu (ele nunca acusa triângulos
  coplanares); por isso `qa_zfight` tem broad phase própria por AABB.
- `recalc normals` em malha aberta pode inverter a cavidade inteira. Face Orientation vermelho = normal para dentro.
