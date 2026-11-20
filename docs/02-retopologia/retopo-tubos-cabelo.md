# Madeixas e tubos fundidos: uma malha separada por tubo (cabelo, tentáculo, chifre, cabo)

Estado: **aprovado em direção, em ajuste** (`projects/hat-hair`: 1184 quads = 2368 tris, limite 3000: capuz 352 + 19 tubos 832).
Um comando refaz tudo: `hair_build.py`. **Nenhuma normal invertida visível é aceita** (ver "Portão estrito"). A primeira tentativa (malha
ligada, por raios) foi descartada: lenta, normais invertidas.

## A ideia
Quando a ref é um bloco de tubos que se atravessam (cabelo cacheado, tentáculos), não tente uma malha única e contínua.
**Cada tubo é uma malha fechada própria, sem ligação** com as outras e com a base; elas se sobrepõem como na ref. Para jogo é
aceito pelo usuário, é muito mais barato em polígonos e cada tubo nasce com normais certas. A base (cabeça/tronco) é outra malha.

## Antes de começar
**Pergunte o orçamento de polígonos** (quads ou triângulos?) e reparta entre base e tubos. No cabelo, 1410 quads (2800 tris) foi
grande demais; o alvo passou a 1000. O orçamento decide o espaçamento dos anéis, o número de lados e quais tubos entram.

## Processo
1. **Base**: casca por Laplace sobre o envelope externo (`retopo-casca-campo.md`; `hair_part.py hood 32,16,8` = dome + frente numa casca só; antes `dome 24,12,6`: contagens
   menores nos anéis = menos quads; 24,12,6 deu 174 quads, 48,24,12 deu 552).
2. **Achar as madeixas sem apontar à mão** (`hair_locks.py [persistência_m]`, Python normal + scipy): solda os vértices
   duplicados da UV por posição; geodésica na superfície a partir das faces da base; pontas = máximos; árvore de fusão com
   persistência (0,03 m acha 20 madeixas, 0,05 m acha 17); galho = caminho ponta → sela puxado para o eixo medial pela EDT
   (voxels de 3 mm). Saída: pontos e raio por madeixa. `hair_locks_plot.py` gera o gráfico numerado.
3. **Tubo por madeixa** (`hair_tubes.py [min_len] [orçamento]`, Python puro, segundos): suaviza o eixo, reamostra, anéis de 6
   lados (8 se raio ≥ 3,2 cm) com transporte paralelo, raio da EDT suavizado, **afinamento linear da metade do comprimento até
   30 % na ponta**, tampa de 3 ou 4 quads nas duas pontas. O sentido das faces sai certo da construção (fita pelo sentido
   dos anéis, tampa pela aresta compartilhada). Se passar do orçamento, o espaçamento dos anéis cresce ×1,08 até caber.
4. **Frente (capa extra)**: o dome corta a ±100° da nuca e deixa de fora a franja e o topo da frente (34 % da silhueta de cima
   sem cobertura). Uma segunda casca por Laplace, `hair_part.py front 16,8,4` (janela PH 100..260, TH 0..70; a janela de
   azimute pode passar de 180), cobre isso com 116 quads e baixou a área sem cobertura para 12,7 %.
5. **Conferir no Blender** (`hair_tubes_load.py`): um objeto por tubo, erro até a ref (média 3 a 4 mm, até 20 mm nos tubos
   que a ref achata), volume com sinal > 0 (normais para fora), arestas sem sentido repetido (fechado).
   Depois junte tudo num objeto (`LowPoly`) para o usuário ver e confira o winding (0 arestas ruins).

## Portão estrito: nenhuma normal invertida visível (tolerância zero)
`qa_strict.py` lança raios de 400 direções; se a primeira batida de **qualquer** raio é o verso de uma face (o vermelho do Face
Orientation), o modelo está **reprovado** e nada é salvo. Uma superfície fechada e com winding para fora nunca falha; falha
significa dobra, borda aberta ou face invertida. O que causou falha aqui e a correção:
- **Casca aberta vista de baixo**: fechar com tampa (`hair_cap.py`: um vértice dentro da cabeça + n/2 quads, vértice procurado
  numa grade onde nenhum quad da tampa inverte). Mais barato que solidify (que dobra as faces).
- **Duas cascas se sobrepondo** (dome + capa da frente): dobras e tampas se cortando, 35 a 50 faces reprovadas. Uma casca só
  (`hair_part.py hood`: janelas de direções unidas, `ALSO`) não tem emenda nem sobreposição e passa; o corte inferior em
  polar 120 (e não 140) evita a borda dobrada sob as madeixas.
- **Quads torcidos na borda** (salto de profundidade entre madeixas): `heal_flipped` relaxa os vértices das faces reprovadas
  (mais forte e mais largo a cada rodada). Rodar **antes** de ligar os tubos (ele move vértices; depois o contato se perde).
- **Raio solitário que escapa pela quina**: ruído numérico; só conta se 4 raios a 1/3 de pixel também batem no verso.
Nunca "resolva" invertendo a face (`fix_flipped`): a face vista pelos dois lados fica vermelha do outro.

## Nada flutua, nada fino demais
- `qa_floating.py` devolve a lacuna e o ponto de destino; `hair_connect.py` leva a ponta mais próxima até esse ponto (+ meia
  espessura para dentro) e repete. Rode sempre ao dividir um objeto em várias malhas (`expected` = partes soltas reais da ref).
- **Pescoços finos**: cabelo não afina na junção. Raio nunca abaixo de 0,75 da mediana; só ponta livre afina (últimos 30 % até
  35 %); ponta que foi ligada a outra peça mantém o raio inteiro. (Finura só faz sentido onde a forma real muda, como a
  panturrilha mais larga que o joelho, ou cabelo preso.)

## Como saber o que falta
`hair_cover.py` (worker): renderiza a silhueta da ref e do low poly em várias vistas e pinta de vermelho o que a ref tem e o low
poly não, com a porcentagem. Foi assim que se achou a franja da frente; olhar só a vista de frente enganou (as cortinas
escondiam a falta). Use topo, laterais e 3/4.

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
- Silhueta sem cobertura: 10 a 16 % nas vistas (pontas de cachos, cantos). O detector em modo `z` (`hair_locks.py 0.04 z`) achou os
  tubos que o geodésico perdia (madeixas de baixo). **Referência certa para a cobertura é `HairFull`**: `HiPoly` inclui o gorro e
  inflava o número para 35 %.
- Pontas de raiz estendidas podem sair do outro lado do capuz (espinhos curtos).
- Cachos finos enrolados viram curvas suaves (6 lados, anéis a 2,5 cm).
- Madeixas achatadas na ref (erro até 20 mm): trocar por seção elíptica.
