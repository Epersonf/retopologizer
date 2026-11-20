# hat-hair

Gorro de pano com ponta caída + cabelo cacheado, gerados por IA (`input/dd331ba3dd0ac45efb0ede66d5aa438a.glb`, 846 mil
vértices, 1,5 M triângulos; o gorro está em x > 0,15 e o cabelo em x < 0,12). Eixos: Z para cima, frente = −Y, esquerda do
personagem = +X, metros.

## Gorro: pronto
960 quads, fechado embaixo, `quad_only`, erro médio 0,04 mm, UV do usuário, bake 2048. Método: anéis por campo de Laplace
(`docs/02-retopologia/retopo-casca-campo.md`); scripts `hat_measure.py`, `hat_field.py`, `hat_outer.py`, `hat_bake.py`,
`hat_to_cuca.py`.

## Cabelo: capuz + tubos separados
`draft/hair_lowpoly_v3.blend`, objeto `LowPoly`: 1184 quads (2368 triângulos; limite do usuário 3000), só quads, **um grupo
conectado, nada flutuando, zero normais invertidas visíveis** (`qa_strict`, 400 direções: reprovado = não salva). Capuz 352
(dome + frente numa casca só, `hair_part.py hood 32,16,8`, tampa `hair_cap.py`, dobras curadas por `hair_heal.py`) + 19 tubos 832.
Um comando: `python -I projects/hat-hair/hair_build.py` (worker no ar numa cópia com `HairFull`; antes `hair_locks.py 0.03` e
`hair_locks.py 0.04 z`). Peças: `hair_tubes.py`, `hair_connect.py` (liga tubos soltos), `hair_join.py` (junta, portões, salva, exporta
`output/hair_lowpoly.obj`), `hair_cover.py` (cobertura contra `HairFull`). Guia: `docs/02-retopologia/retopo-tubos-cabelo.md`.
`hair_locks_build.py`, `retopo.lock` e as cascas separadas dome/front ficaram como tentativas descartadas.

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

