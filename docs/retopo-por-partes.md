# Retopologia por partes (o ciclo que funcionou na Cuca)

Um modelo inteiro numa rodada só é lento, os erros se misturam e o usuário só vê o resultado no fim. Por partes,
cada rodada tem um objetivo pequeno, uma imagem em minutos e uma entrega que o usuário aprova e integra. Foi assim que
a mão, a perna, o pé e a cauda da Cuca saíram aprovados, cada um em poucas voltas.

**Sugira isso ao usuário** quando o pedido for "retopologize o modelo" ou quando uma parte não estiver ficando boa:
proponha a divisão e a ordem, e comece pela parte que ele escolher. Vale para qualquer método: personagens com
`tools/retopo` (`retopo-llm.md`) e peças duras com snap + espelho (`retopo-snap-mirror.md`).

## Dividir o modelo
- **Uma parte = uma forma com fronteira clara**: mão, perna sem o pé, pé, cauda, cabeça, orelha; tampa, alça.
- **A fronteira é um anel**: a parte começa num anel que já existe (o pulso do braço do artista, 12 vértices) e termina
  fechada (ponta dos dedos) ou num anel aberto deixado de propósito para a próxima (o tornozelo da perna). A contagem
  desse anel é o contrato entre as duas partes: par e igual dos dois lados, encaixe 1:1.
- **Ordem: do tronco para as pontas**. O tronco define os buracos dos membros (anel do braço, do pescoço, das pernas);
  depois braço → mão, perna → pé, pescoço → cabeça; por último os extras (cauda, orelhas, chifres) e as costuras que
  fecham o resto (quadril, saia). Prop: corpo principal → peças presas → detalhes (fecho, rebites).
- Parte que encosta numa região que ainda não existe termina num anel aberto escondido e fica como peça separada até a
  vizinha ficar pronta (a perna da Cuca começa num anel sob a saia).

Na Cuca, o artista fez cabeça, tronco e braços. As rodadas foram: mão → perna (sem o pé, anel de 12 no tornozelo) →
pé → cauda (com as escamas).

## Uma rodada
1. **Base atual**: copiar o `.blend` mais recente do usuário (`draft/cuca.blend` → `draft/cuca_retopo_vN.blend`), abrir
   no worker e passar para `OBJECT`. Ele pode ter mexido na malha desde a última rodada: nada de índices antigos.
2. **Guardar a malha dele intocada** como datablock (`LowPoly_user`, fake user). Ela é o ponto de partida de cada
   tentativa (`cuca_user_build.py`) e a base para separar a parte depois.
3. **Isolar a região**:
   - medir só ela: `slice_plot --box` em volta da parte, raycasts e perfis só ali (onde os dedos se separam, o perfil
     dorsal da cauda);
   - ver só ela: `wire_overlay([...], path, view, center=<centro da parte>, size=<largura em m>)`, nas vistas em que a
     forma se lê (mão: persp e de cima; pé: lado e sola; cauda: lado e de cima);
   - achar o anel de emenda: `wire_overlay` + `label_png` mostram os índices; `T.old(...)` pega esses vértices;
   - se os vizinhos confundem o snap (dedos colados na ref), `ref_part` recorta só a referência da parte.
4. **Plano curto**: contagem de cada anel, onde ficam os polos, o que fica aberto (`topologia.md`).
5. **Construir** num script da parte (`projects/<nome>/<nome>_<parte>.py`), rodado pelo driver com `PARTS = [...]`.
6. **Uma imagem já**: renderizar uma vista, abrir, mostrar. Corrigir o que está visivelmente errado e repetir. Outras
   vistas (cima, baixo, lado) só quando essa estiver boa.
7. **Separar e conferir só a parte** (`tools/retopo/part.py`):
   ```python
   p = part_object("LowPoly", "LowPoly_user", "Cuca_pe")   # faces novas ou alteradas nesta rodada
   topo_qa("Cuca_pe", R)                                    # seam_x=0.0 se a parte está no plano do espelho
   ```
   Esperado: só quads (ou triângulos justificados), borda aberta só nos anéis de emenda, 0 non-manifold, 0 duplicados,
   0 winding em conflito, 0% de área para dentro. Faces que o artista começou para essa parte entram com
   `also=[índices]`.
8. **Entregar só a parte**: `export_obj("Cuca_pe", r"C:/Users/epers/Desktop/cuca_pe.obj")`. Usa os eixos padrão do
   Blender: importado com as opções padrão, cai no lugar. Salvar a cópia com a parte já ligada.
9. **Relatar**: arquivo, faces e se são só quads, qual anel ficou aberto e com quantas arestas (encaixa 1:1 em quê),
   onde a próxima parte começa, como refazer (driver + `PARTS`) e o que você não conferiu.
10. **O usuário integra** no arquivo dele (importa o OBJ, solda a emenda) e aprova. A próxima rodada volta ao passo 1
    com o arquivo novo.

Conferido nas rodadas da Cuca: perna 108 quads com 24 arestas abertas (anel sob a saia + tornozelo), pé 136 quads
com 12 (tornozelo), meia cauda 72 quads com só o meio anel sob a saia aberto (fora a costura x = 0).

## O que o usuário disse → o que era → o que fazer
| ele disse | o que era | o que fazer |
|---|---|---|
| "um grudado no outro" (dedos) | anéis dos dedos começando antes da separação real | medir onde os dedos se separam (raios de dentro da palma para fora, em várias alturas) e começar cada dedo depois da membrana |
| membrana entrando no dedo (pé) | membrana fora do lugar | membrana no ponto mais fundo entre os dedos |
| "a cauda poderia ter menos loops" | densidade sem motivo | um segmento por escama, anel só nos vãos |
| "os triângulos em cima da cauda" | escamas dorsais faltando | crista de 2 vértices na costura, subida até o topo da escama |
| "está demorando" | análise longa sem imagem | construir já, mostrar uma vista, corrigir depois |

## Por que funciona
- Objetivo pequeno: a imagem sai em minutos e o usuário corrige cedo.
- O erro fica local: uma parte ruim não contamina o resto, e refazer custa uma rodada.
- O arquivo do usuário é a fonte da verdade: ele integra e pode editar à mão entre as rodadas.
- O anel de emenda é um contrato: mesma contagem, encaixe 1:1, nenhum triângulo de costura.
- Cada parte é um script: refazer é rodar de novo.

## Armadilhas
- Índices de vértices mudam quando o usuário edita: releia com `label_png` a cada rodada e anote no script de onde
  vieram (`cuca_foot.py`: anel do tornozelo = índices 732–743 do LowPoly daquela versão).
- `.blend` salvo em Edit Mode abre em EDIT no worker: `mode_set(mode='OBJECT')` antes de tudo.
- Parte no plano do espelho (cauda): construa só a metade, com a costura em x = 0 e `topo_qa(..., seam_x=0.0)`. O OBJ
  sai como metade e o Mirror do usuário completa.
- Se a rodada mudou faces do artista (limpeza na emenda), o `part_object` as inclui: avise o usuário para apagar as
  antigas ao importar.
