# Retopo de madeixas e tubos fundidos (cabelo, tentáculo, chifre, cabo)

Estado: **tentativa, não aprovada**. Entregou 1030 quads sem buracos, mas o usuário abriu o `.blend` e achou normais invertidas
e vários problemas. Este guia registra o que funcionou, o que não funcionou e por onde recomeçar (caso: `projects/hat-hair`).

## Quando usar
Peça feita de muitos tubos que saem de uma base e se fundem na ref (um único componente, paredes ocas de 2 a 4 cm). Não serve
para a base: ela usa casca por campo (`retopo-casca-campo.md`). Aqui: base + um tubo por madeixa.

## Processo (o que existe hoje)
1. **Base (dome)**: casca por Laplace sobre o envelope externo; 552 quads, erro médio 0,03 mm. Esta parte funcionou.
2. **Achar as madeixas sem apontar à mão** (`projects/hat-hair/hair_locks.py`, Python normal + scipy, só mede):
   solda os vértices duplicados da UV por posição; distância geodésica na superfície a partir das faces do dome; as pontas são
   máximos da geodésica; árvore de fusão com persistência (uma ponta conta se sobe >= 5 cm acima da sela onde o cacho se
   junta a um maior); o galho = caminho ponta → sela, puxado para o eixo medial subindo o gradiente da EDT (voxels de 3 mm).
   Saída: `draft/hair_locks.npz` (pontos, raio, raiz) e `hair_locks_plot.py` (gráfico numerado, para escolher ids).
   Com 5 cm saíram 17 cachos. 3,5 cm pega mais cachos pequenos (não foi testado).
3. **Tubo por madeixa** (`retopo.lock`, `tools/02-retopologia/retopo/lock.py`): estações ao longo do eixo espaçadas por
   2πr/n (quads quadrados); em cada estação `section()` lança 3n raios de dentro para fora, aceita só a saída entre 0,45r e
   3,2r e interpola os raios inválidos; `align` ao anel anterior; `strip` entre anéis; leque na ponta e na raiz.
   `projects/hat-hair/hair_locks_build.py` monta uma lista de ids e roda `topo_qa`.

## Dificuldades (sintoma → causa → correção)
- **Esqueleto TEASAR e cortes por z** → caminhos em degraus, lóbulos que se fundem → trocado por geodésica + EDT.
- **Mesmo casco do dome nas laterais** → o envelope visto do centro inclui madeixas e cachos, borda em zigue-zague, tiras
  compridas → não usar casca onde há muitas madeixas.
- **Anéis com raio 5 a 10 cm num tubo de 2 a 3 cm** (`cring`) → o raio sai pela parede do cacho vizinho → `section()` com janela
  de distância e interpolação (corrigiu os anéis; o desvio máximo caiu de 22,5 para 13,1 mm).
- **Arestas soltas perto do topo dos tubos** → seções que cruzam outra madeixa fundida; ainda não resolvido.
- **Normais invertidas / `inward_area` 23,8 %** → causa não confirmada. `hair_locks_build.py` chama `T.orient()` uma vez na
  malha toda; com tubos que se atravessam (e leques de ponta/raiz) isso não é confiável, e `T.strip`/`T.fan` seguem a ordem
  dos anéis, que muda com o `align`. Não corrigido. Quem fizer de novo: orientar cada tubo sozinho, antes de juntar,
  calcular a normal de cada face contra a ref (ou contra o eixo) e inverter a face ou o tubo inteiro; só aceitar o tubo com
  `inward_area` < 2 %.
- **Tubos que se interpenetram** entre si e com o dome: aceito como mecha agrupada, mas gera faces dentro de outros tubos e atrapalha
  UV e bake. Melhor: cortar cada tubo na sela onde encontra o vizinho em vez de atravessá-lo.
- **Cobertura**: faltam cachos menores, pontas enroladas e o cabelo da frente (perto do rosto). Ids 14, 15 e 17 (muito pequenos)
  deviam ser descartados.
- Dois diagnósticos que ajudaram: `wire_overlay` (fio sem linhas ocultas sobre a ref, mas exagera arestas soltas) e o resumo do
  `topo_qa` (`inward_area`, `vert_to_ref`, polos). Quando só uma métrica global aparece, não se acha o tubo ruim: rodar `lock` um
  por vez (`one.py` temporário) e olhar cada um antes de juntar.

## Para a próxima tentativa
1. Rodar `hair_locks.py` com persistência 0,035 e descartar tubos < 4 cm; conferir o plot numerado.
2. Construir **um tubo por vez**, com QA por tubo (quad_only, `inward_area` < 2 %, erro máximo < 8 mm); só entra na cena o que passa.
3. Corrigir o sentido das faces dentro de `lock()` (não depois), e testar com normais em Face Orientation no Blender.
4. Ponta enrolada: dividir o cacho em dois trechos (eixo muda de direção) com anel de junção, em vez de um tubo só.
5. Frente do cabelo: tratar como peça própria (casca por Laplace pequena ou tubos finos), depois das cortinas.
6. Mostrar ao usuário uma vista de cada tubo aprovado antes de seguir; ele só vê o problema abrindo o arquivo.
