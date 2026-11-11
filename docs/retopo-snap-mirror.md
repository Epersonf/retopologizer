# Retopologia snap + espelho (método da tampa v5)

Reproduz o que um artista faz à mão (vértice a vértice com *snap to face*, `Mirror` quando simétrico),
mas por script, então é medido, repetível e passa na QA. Resultado na tampa do baú: 340 tris, erro
médio novo→ref 3,4 mm (p95 11 mm), 0 backfaces, 0 overlap de UV, 0 z-fight. Antes, com formas
simples ajustadas, a tampa tinha 248 tris e perdia cintas, blocos, chanfros, cavidade e fecho.

Código: `tools/snap_retopo.py` (carrega `snap_surface.py` + `snap_mesh.py`), `tools/ref_part.py`,
exemplo completo em `projects/stylized-chest/build_lid_v5.py`.

## Quando usar
Peça com detalhe que a IA gerou (cintas, blocos, chanfros, fecho, rebites) e que precisa ficar fiel
para o bake funcionar. Para caixas/formas simples, `mesh_lib.py` + ajuste por `compare_mesh.py` basta.

## Passo a passo
1. **Isolar a peça da referência** (`ref_part(ref, "chest_lid", "REF_LID", radius=0.06)`).
   Copia só os triângulos da ref perto da peça e os põe no **espaço local da peça** (a tampa na pose
   fechada, eixo de simetria alinhado ao X). Cuidado: a ref pode ter matrix_world girada (+90° X) e
   `BVHTree.FromObject` é local; por isso o BVH é montado em coordenadas de mundo.
2. **Medir antes de modelar**: alturas por raycast em função de x (`h(x)`) acham onde há cinta,
   degrau, bloco da ponta e chanfro. Anote as posições em x (tampa: cinta |x|<0,055 +14 mm,
   bloco 0,225–0,31 +22 mm, chanfro até 0,326, cavidade até 0,26, rim z=0,06).
3. **Cortes por ângulo**: de um centro `c` dentro da peça, `Surface.outer(x, c, ângulo)` devolve o
   ponto do casco; `Surface.inner` o da cavidade. Com `simplify(corte, 6 mm)` (Douglas-Peucker) saem os
   **cantos** do arco (tampa: 9 externos, 8 da cavidade). Use esses mesmos ângulos em todos os anéis:
   mesma contagem de vértices = tiras de quads sem triângulos soltos.
4. **Anéis só do meio lado (x ≥ 0)**: cinta, degrau, corpo, degrau, bloco da ponta, chanfro, tampa da
   ponta. Um degrau são dois anéis no mesmo x (parede plana, sem inclinar). As pontas do anel (no
   rim) usam um raio **horizontal** na parede (`wall_y`): o raio inclinado oscila ±1,5 cm na
   rugosidade da IA. Todo vértice é projetado na ref (snap), nunca digitado.
5. **Tiras** `Mesh.strip(A, B)` entre anéis vizinhos, tampa da ponta como n-gon, cavidade como outra
   tira. `remove_doubles(0,002)` transforma quads-lasca de 2 mm em triângulos.
6. **Espelho**: `Mesh.mirror_x()` = Mirror + apply + soldar o plano central. Só a metade é construída.
7. **Rim plano** entre o laço externo e o da cavidade: `fill_flat_ring` (tessela sem cruzar e remove
   ears de área zero). `bridge_loops` com contagens diferentes cruzou triângulos e gerou overlap de UV.
8. **Detalhes salientes** (fecho, rebites) com `Mesh.prism(base, normal, altura, embed=4 mm, snap)`:
   a base é **projetada na nossa própria malha e afundada 4 mm** (sem face inferior); o topo fica
   na superfície da ref; furo do fecho = `Mesh.dimple`. Base flutuando deixa o raio entrar na laje
   e a QA acusa backface. Placas de canto sobrepostas: afastar 3 mm (coplanar = z-fight).
9. **Conferir**: `fit_report` (erro nos dois sentidos, células sem detalhe), `section_overlay` (cortes
   ref colorida × low branca), `qa_all` (backfaces, UV, z-fight), `unwrap_atlas(angle=66)` (89° dobrou
   ilhas do arco), depois `bake_robust`.

## Por que funciona
- Snap em 100% dos vértices: a malha nasce sobre a superfície, então o bake high→low tem pouco erro.
- Mesmos ângulos em todos os anéis: topologia limpa, quads alinhados com a forma, fácil de UV.
- Espelho: metade do trabalho, simetria exata, UV mais fácil.
- Tudo em script (`build_*.py`): se a ref ou a medida mudar, roda de novo.

## Armadilhas já vistas
| sintoma | causa | correção |
|---|---|---|
| peça extraída no lugar errado | ref com matrix_world girada, BVH local | BVH em mundo (`ref_part`) |
| ilhas de UV dobradas | smart_project 89° em arcos | 66° |
| triângulos cruzados no rim | `bridge_loops` com contagens diferentes | `fill_flat_ring` |
| backface na laje do fecho | base flutuando | projetar na malha e afundar 4 mm |
| quadrados pretos no Cycles | placas coplanares (z-fight) que o BVH não via | `qa_zfight` com AABB; afastar 3 mm |

## Adaptar a outra peça
Trocar `C`, `A_OUT`, `A_IN`, `XS` e o `build_*` (tampa = arco extrudado ao longo de X). Para peças
com simetria radial usar anéis em torno do eixo; para sem simetria, construir tudo sem `mirror_x`.
