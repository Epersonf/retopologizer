# Topologia: o que um artista decide (e por quê)

Teoria para decidir loops, polos e contagens antes de pôr vértices. Regras do repo: `regras-retopologia.md`.
Métodos práticos: `retopo-snap-mirror.md` (peças duras) e `retopo-llm.md` (personagens e orgânicos).

## Para que serve a malha low-poly
- **Silhueta**: é o que se vê de perfil. Polígonos vão onde o contorno muda; área plana pede poucos.
- **Deformação** (personagens): loops nas articulações para o volume não colapsar ao dobrar.
- **Bake**: a low precisa ficar perto da high (erro pequeno = normal map limpo). Detalhe pequeno (rugas, costuras,
  escamas finas, parafusos) vai para a textura, não para a malha.
- **UV**: loops limpos dão ilhas retas e costuras fáceis de esconder.

A engine triangula tudo: o orçamento é contado em **triângulos**.

## Vocabulário
| termo | o que é |
|---|---|
| quad / tri / n-gon | face de 4 / 3 / 5+ lados |
| edge loop | arestas em sequência atravessando quads pelo lado oposto (o anel em volta do braço) |
| edge ring | as arestas paralelas que um loop corta (o que um "loop cut" cria) |
| polo | vértice com valência ≠ 4: 3-polo (N), 5-polo (E), 6+ (evitar) |
| contorno | anel desenhado em volta de um tubo (membro, dedo, cauda, pescoço) |
| manifold | toda aresta com 1 face (borda) ou 2; 3+ = non-manifold |
| T-junction | vértice no meio da aresta de outra face: abre fresta, o raio do bake e da QA passa |
| sliver | face muito fina: sombreamento ruim, UV ruim |
| winding | ordem dos vértices da face = lado da normal; vizinhas precisam concordar |

## Princípios
1. **Quads em tudo**: deformam e subdividem de forma previsível, formam loops, dão UV limpa. Triângulo só onde ajuda
   (ponta de cone, área rígida que não dobra); n-gon só em face plana e escondida.
2. **Loops seguem a forma**: anéis perpendiculares ao eixo em braço, perna, pescoço, cauda e dedos; concêntricos em
   olhos, boca e narinas; ao longo de quinas e vincos. Um loop atravessa a peça sem morrer no meio.
3. **Contagem constante num tubo**: o mesmo número de vértices em todos os anéis dá tiras de quads sem triângulos
   soltos. Mudar a contagem exige polos planejados.
4. **Polos são ferramentas**: mudam a direção ou a densidade dos loops. Em área plana que não deforma (peito, costas,
   topo da cabeça), nunca no meio de uma dobra. Nunca 6+.
5. **Paridade**: uma região só fecha só com quads se o contorno tiver número **par** de arestas. Por isso a raiz de um
   dedo é um anel par e os dedos saem em colunas alternadas (dedo, membrana, dedo...).
6. **Buraco de 4 lados** = grade (`Topo.grid`, como o Grid Fill). **Buraco de 3 ou 5 lados** = um polo de 3 ou 5 no
   meio e grades nos cantos (`retopo.poly_patch`).
7. **Densidade só onde paga**: silhueta, deformação, bake. Cada loop precisa de motivo; o que é só cor ou relevo raso
   fica na textura.
8. **Simetria**: construir só x ≥ 0 e espelhar (`Mirror` com Clipping + Merge ~1 mm). Vértices da costura exatamente
   em x = 0.

## Mudar a densidade
- Toda mudança de contagem cria polos; decida onde eles ficam antes.
- Paridade manda: numa faixa, **3 → 1** e **4 → 2** fecham só com quads; **2 → 1** não (contorno ímpar) e pede um
  triângulo ou outra redução ao lado.
- **3 → 1** (ou 1 → 3) = dois 3-polos e dois 5-polos. Exemplo: costas da mão da Cuca (`cuca_hand.py`), onde 3 arestas
  da palma viram 5 nos nós dos dedos para os dedos saírem das colunas 0, 2 e 4.
- Região de 5 lados com um 5-polo: costas e topo do ombro da Cuca (`cuca_back.py`); `solve_spokes` diz quantas
  arestas cada raio leva a partir das arestas de cada lado.

## Deformação (personagens)
- **Articulação que dobra = 3 loops**: um no centro da dobra e um de cada lado (cotovelo e joelho da Cuca). Dedos: um
  anel em cada junta.
- **Ombro e quadril**: loops que seguem o deltoide e a virilha. O braço sai de um buraco no tronco (Cuca: buraco 2×2 =
  anel de 8 do braço).
- **Pulso, tornozelo, pescoço**: 1–2 loops, com a contagem do membro que chega.
- **O osso dobra onde há loop**: no rig, as juntas vão para os anéis (`tools/autorig/rings.py`). A cauda da Cuca dobra
  nos vãos entre escamas, um segmento por escama.
- **Rosto que anima**: loops concêntricos em olhos e boca. Rosto stylized estático: só a silhueta manda.

## Peças duras (props)
- Silhueta com poucos cortes; chanfro de 1 segmento nas quinas que pegam luz (ajuda o bake).
- Detalhe saliente (rebite, fecho, placa) pode ser casca separada **afundada ~4 mm** na peça, sem face de baixo.
  Nunca flutuando (vaza raio) nem coplanar a outra face (z-fight: afastar 2–4 mm).
- Caixas sempre fechadas: caixa aberta deixa backface à vista.
- Quina dura (normais divididas) pede costura de UV na mesma aresta, senão o normal map marca a quina.

## Orçamento (triângulos)
Partir de um alvo baixo e justificar cada loop. Neste repo:

| asset | tris |
|---|---|
| baú (2 peças) | 813 (alvo < 1000, máx. 2000) |
| árvore stylized | 380 |
| vaca (estátua) | alvo ~2000 (a versão automática de 6234 foi rejeitada) |
| Saci (personagem) | 2864 |
| Cuca (personagem com cauda e escamas) | 3756 |

Ordem de grandeza em jogos: prop pequeno 100–1000, prop médio 1–5 mil, personagem stylized 3–10 mil.

## Checklist antes de chamar de pronto
- Quads em tudo, exceto triângulos justificados; nenhum n-gon visível.
- Nenhum polo 6+; polos fora das dobras.
- Anéis fechados em volta de cada membro e articulação; contagens iguais nas emendas.
- Sem buraco, non-manifold, duplicado, winding em conflito ou face para dentro (`topo_qa`, ver `qa.md`).
- Erro novo→ref pequeno (tampa do baú: média 3,4 mm) e nenhum detalhe grande faltando (`fit_report`).
