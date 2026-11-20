# cuca-hair

Cabelo loiro da cuca com **fiber cards**: cada card é um plano simples com a textura de fios (cor + normal + alfa); a face de trás pode aparecer, o material
do jogo liga *backface/render both sides*. Os cards são encaixados no formato da cabeça da cuca (modelo em `../stylized-cuca`: `draft/cuca.blend`,
`output/cuca_rigged.fbx`).

## Etapa 1: gerar os fiber cards (feito)
Ferramenta `tools/07-fibercards/` (`docs/07-fibercards/fibercards.md`), porta do app `epersonf/fiber-card-gen`, renderizada no Blender:

    python -I tools/07-fibercards/fibercards.py --out projects/cuca-hair/fibercards/out --tag blender_v1 --blonde

Saída em `fibercards/out/`: `hair_color.png`, `hair_normal.png` (RGBA, 2048, fundo transparente), `blender_v1_preview.png`, `blender_v1_preset.json`
(o preset loiro; cole no app para reproduzir). Folha 4x3: do card mais ralo (13 fios) ao mais denso (130).

## Próximas etapas
2. Importar o modelo da cuca aqui. 3. Criar os planos (UV = célula da folha) e encaixar na cabeça, raiz no couro cabeludo, camadas do ralo ao denso.
