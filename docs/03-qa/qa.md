# QA: quando a malha está pronta

Rodar antes da UV final, do bake e do export. Tudo dentro do Blender; cada teste devolve um dict com `pass`.
Teoria do que é malha boa: `docs/02-retopologia/topologia.md`.

## Comando único: a bateria (`qa.py`) — comece por aqui
```
python -I tools/03-qa/qa.py LowPoly --ref HairFull            # tudo, uma linha por teste (~25 s)
python -I tools/03-qa/qa.py LowPoly --ref HairFull --fast     # strict com 100 direções: para iterar (~8 s)
python -I tools/03-qa/qa.py LowPoly --only fit,attach         # só alguns (--skip tira alguns; --json devolve o dict inteiro)
```
Sai com código 1 se algum teste reprova; cada FAIL traz uma linha `fix:` e **onde** está o problema (coordenadas e região,
`front-top-right` etc.), então o agente não precisa abrir 8 dicts. Dentro do Blender: `qa_suite(nome, ref=..., only=..., fast=...)`.
Ordem (do mais barato ao mais caro): `mesh`, `budget`, `shape`, `floating`, `attach`, `local`, `strict`, `fit`.
Fluxo do agente: **iterar com `--fast`, rodar completo uma vez antes de mostrar ao usuário**; quando o usuário apontar um
defeito que nenhum teste pegou, escrever o teste primeiro (ele deve reprovar o arquivo ruim), depois corrigir.

## O que torna um modelo bom (o que cada teste protege)
1. **Fiel à ref**: silhueta (IoU) de 14 direções, nada da ref sem cobertura (buraco, entalhe), nada no modelo que a ref não tem (`fit`).
2. **Superfície limpa**: fechada, só quads, sem normal invertida vista de longe (`strict`) nem de perto, em frestas e dobras (`local`).
3. **Peças que se seguram**: nada flutuando (`floating`) e cada peça *enterrada* no que a sustenta, não só encostada nem com a
   tampa furando a superfície (`attach`).
4. **Forma que lê bem**: sem espinhos, pontas de agulha, tubos finos (`shape`).
5. **Orçamento** (`budget`).
Passar nos cinco juntos é o mínimo; um modelo que só passa nos de superfície (1 e 2 de normais) ainda pode estar horrível.

## Portão do baú (`qa_all.py`: backfaces + UV + z-fighting)
`exec(open(r"<repo>\tools\03-qa\qa_all.py", encoding="utf-8").read()); qa_all(["chest_base", "chest_lid"])`
levanta erro se algum teste falhar (`raise_on_fail=False` só devolve o relatório).

| teste | ferramenta | falha quando | correção |
|---|---|---|---|
| backfaces | `qa_faces.py` | o primeiro hit de algum raio (400 direções × 200×200, cavidades abertas incluídas) é o lado de trás de uma face, o vermelho do Face Orientation; hits rasantes (\|n·d\| < 0,1) ignorados | `fix_flipped()` inverte faces vistas só por trás; face com 0 votos de frente estava enterrada: apagar |
| **normal invertida visível (portão estrito)** | `qa_strict.py` | **qualquer** raio, de 400 direções em volta (200×200 cada), cuja primeira batida é o verso de uma face, confirmado por 4 raios vizinhos; tolerância zero, o modelo é **reprovado** (não salvar, não entregar) | `heal_flipped()` relaxa as faces reprovadas (cada vez mais forte e mais largo) e reroda; se sobrar, mudar a geometria (bordas da casca, tampa), nunca "flipar" |
| **formas feias** (pontas, finas) | `qa_shape.py` | vértice-espinho (longe do centro dos vizinhos, razão > 0,8); tubo de ponta fina (anel final < 40 % do raio do meio); tubo fino (raio < 2,2 cm); relatório de faces estreitas (ângulo < 20° ou > 165°, aresta > 5× a menor) | `heal_spikes()` relaxa o espinho; tubo: raio mínimo, ponta só até 65 %, nunca em ponto; descartar fio < 1,3 cm |
| **normal invertida vista de perto** | `qa_local.py` | raios saindo da frente de cada face, em hemisfério (48), batem no verso de outra face (≥ 3 votos); pontos dentro de um sólido (raiz enterrada) são ignorados. Pega dobras e tampa de tubo furando a casca, que nenhum raio de longe vê | relaxar as faces (`_relax`) no heal; enterrar a raiz do tubo mais fundo |
| **tubo preso só por encosto** | `qa_attach.py` | a ponta de um tubo (tampa + 1º anel) não está toda dentro de outra peça, ou o ponto mais fundo está < 0,5 raio abaixo da superfície; é a "ponta solta apesar de conectada" | `hair_connect.py`: leva a ponta a 1,3 raio *abaixo* da superfície, na normal, e aprofunda 0,4 por passada |
| **fidelidade à ref** | `qa_fit.py` | só o que o olho vê (primeiro hit de raios ortográficos, 14 direções): IoU médio < 0,88 ou pior < 0,80; > 6 % dos pixels da ref sem modelo ou com o modelo > 3 cm atrás (buraco, "deveria ser preenchido"); > 4 % dos pixels do modelo sem ref ou à frente dela > 3 cm (caroço, vale que não existe). Faces de material `headfill` (substituto da cabeça, tampas) não contam. Mostra clusters com região | cobrir o cluster com casca ou tubo; remover o que sobra |
| **malha** | `qa_mesh.py` | tris/n-gons, borda aberta (buraco), non-manifold, winding em conflito, vértice solto, duplicado, face degenerada | fechar, refazer a peça |
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
