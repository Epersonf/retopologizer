# stylized-chest — notas

Origem: `input/844b92ca...glb` — 1 mesh, 500 000 tris, 0.70×0.71×0.80 m, 1 material + UV.
Saída: `output/stylized-chest.fbx` — **813 tris** (v5: 473 + 340; antes 721) (budget 2000; alvo <1000), 2 objetos:
`chest_base` (492) e `chest_lid` (340, origem no pivô da dobradiça, rotação X = -50°).

## Medidas da referência (Z up, frente = -Y)
- Base: z 0–0.355; parede x ±0.305, y -0.33…0.14, espessura 0.04; piso 0.062; plinto 0–0.06
  (+0.018), banda superior 0.268–0.355 (+0.028), postes 0.087 (+0.022), cantoneiras com
  pentágonos, placa do cadeado (z 0.218–0.35, largura 0.128).
- Tampa: aberta 50° (mínimo do bbox no plano YZ). Pose fechada: profundidade 0.52, topo 0.616
  (+0.014 das cintas), largura ±0.338, paredes frontal/traseira sólidas, cavidade y -0.545…-0.215,
  3 cintas (x -0.25, 0, 0.25), presilha frontal, 2 cantoneiras.

## Resultado (compare_mesh, 6000 amostras, diagonal 1.283 m)
ref→novo média 8.5 mm (0.66%), p95 23 mm, máx 36 mm; novo→ref média 10 mm, máx 49 mm.
Overlays de silhueta em `draft/ref/ov_*.png`.

## Bake (2048, Cycles GPU, ~55 s)
`output/`: stylized-chest.fbx (45 KB, sem referência) + chest_{basecolor,normal,roughness,metallic,ao}.png.
Método padrão (sem cage), extrusão 0.10 / ray 0.20; faces pretas no basecolor: base 2%, tampa 0.3%.
Roughness ≈0.98 e metallic ≈0.04 quase uniformes: é o que a textura original tem.

## Pendências / melhorias
- Furo da chave e janela da presilha; bisel/arredondamento das cantoneiras (cabe no budget).
- Textura feita (bake). Se a geometria mudar, refazer UV e o bake.
- Scripts reprodutíveis: `draft/build_base.py`, `build_lid.py`, `run_all.py`.

## v3 (QA de faces/UV)
Faces vermelhas no Face Orientation: caixas abertas (postes, cantoneiras, placas), peças furando a
cavidade e fresta entre o fundo da tampa e as paredes (T-junction após mexer nos vértices). Corrigido:
buracos de 4 arestas preenchidos, fundo da tampa refeito com bridge, 42 faces enterradas removidas.
QA: 0 backfaces (400 dir × 200²), UV refeito (234 ilhas, 52% do atlas, 0 overlap a 2048/4096, gap ≥ 8 px).
Rebake 2048 (margem 8 px). Backups: `draft/backups/v3_before_face_fix` (ignorado pelo git).
Repo: `stylized-chest.blend` (9 MB, imagens empacotadas).

## v5 (tampa refeita com snap + espelho)
Pedido: a tampa não capturava detalhes e o bake saía com artifacts. Refeita pelo método manual
(anéis colados na ref + Mirror), script reprodutível `build_lid_v5.py` (exemplo do método) (usa `ref_part`).
Medido na ref: cinta central |x|<0.055 (+14 mm), bloco da ponta 0.225–0.31 (+22 mm), chanfro até
x=0.326, cavidade em arco até x=0.26 (teto z=0.251), rim z=0.06; fecho 0.124×0.075 com furo,
rebites nas 4 placas de canto. Ajuste: novo→ref média 3,4 mm, p95 11 mm.
QA: 0 backfaces, UV 0 overlap (66°), 0 z-fight. Bake robusto: 1,14% inválido no 1º passe, 0,18% no fim
(0 faces da tampa entre as piores; sobram faces da base: 36, 102, 174 e a banda inferior).
Backup da tampa editada à mão pelo usuário: `draft/backups/v4_user_edit_lid` (ignorado pelo git).
Pendência: a base ainda tem faces longe da ref (poor_fit_faces_mm no relatório do bake).
