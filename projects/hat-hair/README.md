# hat-hair

Gorro de pano com ponta caída + cabelo cacheado, gerados por IA (`input/dd331ba3dd0ac45efb0ede66d5aa438a.glb`, 846 mil
vértices, 1,5 M triângulos; o gorro está em x > 0,15 e o cabelo em x < 0,12). Eixos: Z para cima, frente = −Y, esquerda do
personagem = +X, metros.

## Gorro: pronto
960 quads, fechado embaixo, `quad_only`, erro médio 0,04 mm, UV do usuário, bake 2048. Método: anéis por campo de Laplace
(`docs/02-retopologia/retopo-casca-campo.md`); scripts `hat_measure.py`, `hat_field.py`, `hat_outer.py`, `hat_bake.py`,
`hat_to_cuca.py`.

## Cabelo: em andamento (parte 1 de N)
O cabelo é uma peça só (um componente), feita de tubos ocos (parede de 2 a 4 cm, cavidade fechada). De fora: três madeixas
grossas e longas na nuca e no topo, cortinas de madeixas finas em S nas duas laterais (cada uma termina num cacho) e uma
mecha que cruza o topo da frente.

| parte | estado | quads | erro médio / máx | método |
|---|---|---|---|---|
| nuca e topo (`Hair_dome`) | feito, `quad_only`, borda aberta | 552 | 0,03 / 0,9 mm | casco por Laplace, borda = corte a ±100° da nuca |
| cortina esquerda (+X) | a fazer | | | tubos por madeixa (ver abaixo) |
| cortina direita (−X) | a fazer | | | idem |
| mecha do topo da frente, cachos das pontas | a fazer | | | tubos finos com ponta em leque |

Entrega da parte 1: `output/hair_dome.obj` (git-ignored). Cena de trabalho: `draft/hair_work.blend` (`Hair_dome`,
`HairFull`, `HairOuter`, `Hat_retopo`, `HiPoly`).

### Como a parte 1 é feita (um comando por parte)
Worker no ar em `draft/hair_work.blend` com `HairFull` carregado (`hair_proxy.py` com `NPZ = draft/hair_in.npz`,
`NAME = "HairFull"`), depois `python -I projects/hat-hair/hair_part.py dome`. Etapas:
1. `hair_export.py`: parte do cabelo da ref (x < 0,12) → `draft/hair_in.npz`. `hair_outer_mask.py`: preenche voxels de 3 mm
   e mede o que é superfície de fora (opcional; serviu para ver que as madeixas são ocas).
2. `hair_shell_select.py`: raios disparados de fora para dentro até o centro da cabeça `C = (−0,185; −0,03; 0,30)`; as faces
   acertadas na janela de direções (`PH`, `TH`) são o envelope externo.
3. `hair_shell.py`: fecha as frestas entre madeixas (`CLOSE`), corta as pontas finas (`OPEN`), solda os vértices duplicados
   da UV, acha a borda e o ponto mais longe dela. 4. `hair_field.py`: Laplace (0 na borda, 1 no topo) e curvas de nível
   traçadas aresta a aresta (a borda em U não é plana, então não dá para ordenar por ângulo como no gorro).
5. `hair_shell_build.py`: anéis 48 → 24 → 12 colados na ref, faixa 4:2, leque no topo. Ver: `hair_views.py` / `hair_show.py`.

### O que não funcionou (para as cortinas)
- **Mesmo casco nas laterais** (`PARTS["left"]`/`["right"]`): o envelope visto do centro inclui as madeixas finas e os cachos;
  a borda zigue-zagueia e os anéis viram tiras compridas pela cortina (300 quads cada, inutilizáveis).
- **Esqueleto automático (TEASAR) do volume**: caminhos em degraus que cortam a silhueta e não correspondem às madeixas
  (madeixas fundidas, paredes finas). Cortes por altura (z) mostram lóbulos que se fundem, então rastrear contornos também
  é frágil.
- Fechar frestas na seleção só funciona com a malha completa (a malha "de fora" não tem as faces dentro das frestas).

### Próximo passo proposto
Cortinas e cachos como **tubos por madeixa**: o artista (ou o agente, com imagem) escolhe raiz e direção de cada madeixa
principal olhando a ref com grade em cm; `retopo.track` segue o centro da seção; anéis de 8 com `cring` na referência de
fora (`HairOuter`), `T.strip` entre eles e leque na ponta. Documentar em `docs/02-retopologia/` quando funcionar.
