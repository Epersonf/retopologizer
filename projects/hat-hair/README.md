# hat-hair

Gorro de pano com ponta caída + cabelo cacheado, gerados por IA (`input/dd331ba3dd0ac45efb0ede66d5aa438a.glb`, 846 mil
vértices, 1,5 M triângulos; o gorro está em x > 0,15 e o cabelo em x < 0,12). Eixos: Z para cima, frente = −Y, esquerda do
personagem = +X, metros.

## Gorro: pronto
960 quads, fechado embaixo, `quad_only`, erro médio 0,04 mm, UV do usuário, bake 2048. Método: anéis por campo de Laplace
(`docs/02-retopologia/retopo-casca-campo.md`); scripts `hat_measure.py`, `hat_field.py`, `hat_outer.py`, `hat_bake.py`,
`hat_to_cuca.py`.

## Cabelo: tentativa 1, não aprovada
O cabelo é uma peça só (um componente), feita de tubos ocos (parede de 2 a 4 cm). De fora: três madeixas grossas na nuca e no
topo, cortinas de madeixas finas em S nas laterais (cada uma termina num cacho) e uma mecha que cruza o topo da frente.

| parte | estado | quads | erro médio / máx | método |
|---|---|---|---|---|
| nuca e topo (`Hair_dome`) | ok, `quad_only`, borda aberta | 552 | 0,03 / 0,9 mm | casco por Laplace |
| 17 madeixas (`Hair_locks`) | **com problemas**: normais invertidas (`inward_area` 23,8 %), arestas soltas, tubos que se atravessam | 1030 | 0,31 / 13,1 mm | `hair_locks.py` + `retopo.lock` |
| cachos pequenos, pontas enroladas, frente | não feito | | | |

Os problemas, as ferramentas que ajudaram e o plano da próxima rodada estão em
`docs/02-retopologia/retopo-tubos-cabelo.md`. Resumo das ferramentas novas:
- `hair_locks.py [persistência_m=0.05]` acha as madeixas sozinho (geodésica a partir do dome + árvore de fusão + eixo medial
  por EDT) e grava `draft/hair_locks.npz`; `hair_locks_plot.py` desenha o gráfico numerado.
- `hair_locks_build.py` (`LOCKS` = ids 1-based, `NAME`) constrói os tubos com `retopo.lock` e imprime o `topo_qa`.
- Scripts descartáveis de teste (um tubo, todos, sheet de vistas) ficaram só em /tmp; recriar se precisar.

Cena de trabalho: `draft/hair_work.blend` (`Hair_dome`, `Hair_locks`, `HairFull`, `HairOuter`, `Hat_retopo`, `HiPoly`; não
versionada). `output/hair_dome.obj` (git-ignored).

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

### Próximo passo
Ver "Para a próxima tentativa" em `docs/02-retopologia/retopo-tubos-cabelo.md`: tubo por tubo com QA, normais por tubo, persistência 3,5 cm.
