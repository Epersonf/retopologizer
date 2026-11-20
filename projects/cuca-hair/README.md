# cuca-hair

Cabelo loiro da cuca com **fiber cards**: cada card é um plano simples com a textura de fios (cor + normal + alfa); a face de trás pode aparecer, o material
do jogo liga *backface/render both sides*. Os cards são encaixados no formato da cabeça da cuca (modelo em `../stylized-cuca`: `draft/cuca.blend`,
`output/cuca_rigged.fbx`).

## Etapa 1: gerar os fiber cards (feito)
`fibercards/` é uma porta em Python do gerador `epersonf/fiber-card-gen` (commit `eccffc9`, `C:\Users\epers\Documents\Repositories\Personal\fiber-card-gen`):
- `fc_params.py` estado do app (mesmas chaves do JSON "copy state") + preset `BLONDE`;
- `fc_strands.py` fios: mulberry32, disco de spawn elíptico inclinado, spread/clump, curl, frizz (ruído de valor, o app usa open-simplex), Catmull-Rom centrípeta;
- `fc_render.py` rasteriza como o export ortográfico do app: cada fio é um tubo (esferas com z-buffer), cor = gradiente raiz→ponta com luz suave, normal = `n*0.5+0.5`, alfa = cobertura;
- `fc_sheet.py` folha 2048 com 12 cards em grade 4x3, do mais ralo (4 fios) ao mais denso (130), um seed por card.

    python -I projects/cuca-hair/fibercards/fc_sheet.py [--preset p.json] [--tag blonde] [--seed 1] [--ss 2] [--set chave=valor ...]

Saída em `fibercards/out/`: `hair_color.png`, `hair_normal.png` (RGBA, fundo transparente), `*_preview.png`, `*_preset.json` (cole no app para reproduzir).
Layout do card: x = largura (0 no meio), y a partir da borda de baixo da célula, a raiz fica no topo da célula e os fios descem.
Diferenças em relação ao app: o ruído do frizz, a luz da cor (luz suave fixa em vez das luzes da cena) e uma variação de brilho por fio (5 %).

## Próximas etapas
2. Importar o modelo da cuca aqui. 3. Criar os planos (UV = célula da folha) e encaixar na cabeça, raiz no couro cabeludo, camadas do ralo ao denso.
