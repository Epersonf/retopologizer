# Retopologia de casca por campo (gorro, capuz, manga, saco)

Para peças de pano com abertura (gorro, capuz, manga, bolsa, chapéu de saci): a malha é feita de **anéis
concêntricos da abertura até a ponta**, como as carreiras de um gorro de tricô. Quem decide onde passa cada anel é um
campo harmônico (Laplace) medido na superfície externa da referência: as linhas de nível dele dão a volta na peça e
nunca se cruzam nem se dividem, mesmo onde a peça dobra ou vira uma cauda caída. O campo só **mede**; cada vértice é
colocado pelo script e colado na ref (regras: `docs/00-regras-e-ferramentas/regras-retopologia.md`).

Exemplo completo: `projects/hat-hair/` (gorro com ponta caída: 960 quads, fechado embaixo, `quad_only`, 0 buraco,
erro médio na casca 0,04 mm). Personagens e tubos simples: `docs/02-retopologia/retopo-llm.md`. Teoria de anéis e polos: `docs/02-retopologia/topologia.md`.

## Quando usar
- A peça é uma casca fina (pano com espessura), aberta num lado, e o eixo dela entorta (a ponta cai de lado, o capuz
  dobra). Cortes por plano ou anéis em volta de um eixo reto se cruzam por dentro da curva.
- Não serve para peça dura com cantos (`docs/02-retopologia/retopo-snap-mirror.md`) nem para corpo com braços/pernas (`docs/02-retopologia/retopo-llm.md`).

## O processo (3 scripts, rodar nesta ordem)
1. **Medir no Blender** (`hat_measure.py`, worker): exporta vértices, normais e triângulos da parte (em mundo), a ponta
   e quais vértices estão do **lado de fora** do pano. Lado de fora = algum raio saindo do vértice (direções com
   `d·n > 0.15`) escapa para o espaço aberto, **usando só direções que não olham pela abertura** (`d·A < -0.1`, A = eixo
   da abertura). Sem esse filtro, a parede de dentro vista pela abertura conta como fora.
2. **Planejar os anéis fora do Blender** (`hat_field.py`, Python normal + scipy):
   - **soldar** os vértices por posição (o GLB duplica vértices nas costuras da UV; sem soldar o grafo se parte);
   - manter só os triângulos de fora e o maior componente conexo;
   - **zero = maior laço de borda** dessa superfície (a borda do pano em volta da abertura), **um = vértices perto da
     ponta**; resolver Laplace com pesos cotangente (`spsolve`);
   - para cada nível (400 níveis pelos quantis de `u`, mais densos perto da ponta), pegar **todos** os pontos onde a
     linha corta as arestas; formar o anel ordenando por ângulo no plano de melhor ajuste (PCA), mediana por fatia de
     ângulo (pedaços soltos de buracos perdem na votação), suavizar, reamostrar com `n` pontos;
   - distância ao longo da peça `s` = soma das distâncias medianas entre níveis vizinhos (não a geodésica da borda,
     que encurta a cauda quando ela passa perto da abertura);
   - escolher anéis com passo = perímetro / n (quads quadrados, mínimo 2,5 cm) e **cortar a contagem pela metade**
     (48 → 24 → 12) quando a aresta fica menor que 2 cm. Salva `draft/hat_rings.npz`.
3. **Construir no Blender** (`hat_outer.py`): cada anel vira vértices com snap (`T.vs`), alinhado ao anterior com
   `align` (no corte 4:2, ao anel anterior pulando de 2 em 2); `T.strip` entre anéis iguais, faixa 4:2 entre contagens
   diferentes (3 quads por grupo: polo de 3 no anel largo, de 5 no estreito; nunca polo de 6), `T.fan` na ponta
   (12 → vértice, 6 quads), `T.relax`, e a **tampa** da abertura: grade 12 × 12 (`T.grid`, `snap=False`) com o lado de
   baixo na quarta parte do anel mais baixa. Por fim `T.orient`, `write`, `topo_qa`.
4. Conferir com `hat_views.py` (`wire_overlay`, cabelo cortado com `clip`) e mostrar uma vista ao usuário.

## Números do gorro
| parte | anéis | quads |
|---|---|---|
| corpo (48 em volta) | 11 | ~530 |
| transição (24) e cauda (12) | 16 | ~260 |
| ponta (fan) | — | 6 |
| tampa embaixo (12 × 12) | — | 144 |
| total | 28 | 960 (limite pedido: 1500) |

## Armadilhas já vistas
| sintoma | causa | correção |
|---|---|---|
| campo zero em quase tudo, contornos vazios | GLB com vértices duplicados na costura da UV | soldar por posição antes do grafo |
| linhas de nível abertas (arcos, não anéis) | o "zero" foi um rim achado por raio, que não é a borda da superfície de fora | zero = maior laço de borda da máscara de fora |
| máscara de fora com buracos perto da cauda | lado de fora decidido pela normal x esqueleto | visibilidade: raio que escapa, sem olhar pela abertura |
| perímetros pulando, anéis pela metade | seguir arestas cortadas num só sentido quebra em malha suja | todos os pontos do nível + ordenar por ângulo (PCA) |
| anéis amontoados na ponta, poucos na cauda | níveis em `u` uniforme / `s` pela geodésica da borda | níveis por quantil de `u`, `s` pela distância entre níveis |
| anéis cruzando a cavidade, cúpula descoberta | anéis interpolados (lerp) entre a boca e a base da cauda | campo de Laplace na superfície |
| relax puxa a tampa para a parede de dentro | relax faz snap de volta na ref | fazer a tampa depois do relax |

## Adaptar a outra peça
Trocar em `hat_measure.py` o eixo da abertura `A`, o corte da parte (`X_HAT`) e o ponto de partida do `track` da ponta;
em `hat_field.py` as contagens `COUNTS` e `MIN_EDGE`. Peça com duas aberturas (manga): zero numa borda, um na outra.
Depois: UV sem overlap (`docs/04-uv-bake/uv-bake.md`), bake na GPU (`hat_bake.py`: extrusões pequenas, 0,02/0,04 m, porque a casca
está colada na ref e uma extrusão grande faz o raio da cúpula bater na cauda), entrega por parte (`docs/02-retopologia/retopo-por-partes.md`).
