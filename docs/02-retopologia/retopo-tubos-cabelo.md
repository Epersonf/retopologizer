# Madeixas e tubos fundidos: uma malha separada por tubo (cabelo, tentáculo, chifre, cabo)

Estado: **funciona e o usuário aprovou a direção** (`projects/hat-hair`: 868 quads, dome + 14 tubos). Ainda falta a frente do
cabelo. A primeira tentativa (malha de tubo montada por raios na ref, tudo ligado) foi descartada: lenta, normais invertidas.

## A ideia
Quando a ref é um bloco de tubos que se atravessam (cabelo cacheado, tentáculos), não tente uma malha única e contínua.
**Cada tubo é uma malha fechada própria, sem ligação** com as outras e com a base; elas se sobrepõem como na ref. Para jogo é
aceito pelo usuário, é muito mais barato em polígonos e cada tubo nasce com normais certas. A base (cabeça/tronco) é outra malha.

## Antes de começar
**Pergunte o orçamento de polígonos** (quads ou triângulos?) e reparta entre base e tubos. No cabelo, 1410 quads (2800 tris) foi
grande demais; o alvo passou a 1000. O orçamento decide o espaçamento dos anéis, o número de lados e quais tubos entram.

## Processo
1. **Base**: casca por Laplace sobre o envelope externo (`retopo-casca-campo.md`; `hair_part.py dome 24,12,6`: contagens
   menores nos anéis = menos quads; 24,12,6 deu 174 quads, 48,24,12 deu 552).
2. **Achar as madeixas sem apontar à mão** (`hair_locks.py [persistência_m]`, Python normal + scipy): solda os vértices
   duplicados da UV por posição; geodésica na superfície a partir das faces da base; pontas = máximos; árvore de fusão com
   persistência (0,03 m acha 20 madeixas, 0,05 m acha 17); galho = caminho ponta → sela puxado para o eixo medial pela EDT
   (voxels de 3 mm). Saída: pontos e raio por madeixa. `hair_locks_plot.py` gera o gráfico numerado.
3. **Tubo por madeixa** (`hair_tubes.py [min_len] [orçamento]`, Python puro, segundos): suaviza o eixo, reamostra, anéis de 6
   lados (8 se raio ≥ 3,2 cm) com transporte paralelo, raio da EDT suavizado, **afinamento linear da metade do comprimento até
   30 % na ponta**, tampa de 3 ou 4 quads nas duas pontas. O sentido das faces sai certo da construção (fita pelo sentido
   dos anéis, tampa pela aresta compartilhada). Se passar do orçamento, o espaçamento dos anéis cresce ×1,08 até caber.
4. **Conferir no Blender** (`hair_tubes_load.py`): um objeto por tubo, erro até a ref (média 3 a 4 mm, até 20 mm nos tubos
   que a ref achata), volume com sinal > 0 (normais para fora), arestas sem sentido repetido (fechado).
   Depois junte tudo num objeto (`LowPoly`) para o usuário ver e confira o winding (0 arestas ruins).

## Armadilhas
- Raios de dentro para fora pela ref fundida saem pela parede do vizinho (raio 5 a 10 cm num tubo de 2 cm): por isso o tubo é
  paramétrico, não raycast. TEASAR, cortes por z e o casco do dome nas laterais também falharam (degraus, lóbulos fundidos).
- Winding: `T.orient()` na malha toda não é confiável com tubos que se atravessam. Construa certo por tubo e verifique pelo
  volume com sinal (por face, "normal vs eixo mais próximo" dá falso positivo em curva fechada e em borda côncava).
- Pontas de cachos soltas (4 a 6 cm, que não nascem em outro tubo) ficam **flutuando**; descarte (`min_len` 0,06).
- O QA global (`topo_qa` `inward_area`) fica ~25 % no dome por causa das paredes ocas da ref; não use como critério aqui.
- Pontas que não afinam como na ref: o raio da EDT na ponta já é pequeno, mas a suavização o apaga; por isso o afinamento
  explícito.

## Ainda em aberto
- **Frente do cabelo** (mecha sobre a testa, cortinas junto ao rosto) não está coberta de forma convincente: aguardando o
  usuário dizer o que falta (ou um tubo grosso + dome pequeno só para a frente).
- Cachos finos enrolados viram curvas suaves (6 lados, anéis a 2,5 cm).
- Madeixas achatadas na ref (erro até 20 mm): trocar por seção elíptica.
